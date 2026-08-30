import os
import sys
import time
import logging
import threading
import ctypes
import winreg

from logging.handlers import RotatingFileHandler

from wechatauto import WeChatDB
from win11toast import notify

import pystray
from PIL import Image, ImageDraw


# ============================================================
# 0. 程序基本信息
# ============================================================

APP_NAME = "微信消息提醒器"
APP_ID = "WeChatNotifier"

POLL_SECONDS = 1.0
SESSION_LIMIT = 500

# 每 15 秒刷新一次：
# 1. 群消息免打扰
# 2. 公众号 / 服务号
POLICY_REFRESH_SECONDS = 15

# 如果微信暂时没有启动 / 数据库读取失败，
# 每隔多少秒重新连接
RECONNECT_SECONDS = 5


# ============================================================
# 1. --noconsole 兼容
# ============================================================

if sys.stdout is None:
    sys.stdout = open(
        os.devnull,
        "w",
        encoding="utf-8"
    )

if sys.stderr is None:
    sys.stderr = open(
        os.devnull,
        "w",
        encoding="utf-8"
    )


# ============================================================
# 2. Windows AppUserModelID
# ============================================================

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        APP_ID
    )
except Exception:
    pass


# ============================================================
# 3. 日志
# ============================================================

LOCAL_APPDATA = os.environ.get(
    "LOCALAPPDATA",
    os.path.expanduser("~")
)

APP_DIR = os.path.join(
    LOCAL_APPDATA,
    "WeChatNotifier"
)

os.makedirs(
    APP_DIR,
    exist_ok=True
)

LOG_FILE = os.path.join(
    APP_DIR,
    "app.log"
)


logger = logging.getLogger(
    "WeChatNotifier"
)

logger.setLevel(
    logging.INFO
)

handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=2 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)

handler.setFormatter(
    logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
)

logger.addHandler(
    handler
)


def log(message):
    logger.info(message)

    try:
        print(
            message,
            flush=True
        )
    except Exception:
        pass


def log_error(message):
    logger.exception(message)

    try:
        print(
            message,
            flush=True
        )
    except Exception:
        pass


# ============================================================
# 4. 防止重复启动
# ============================================================

ERROR_ALREADY_EXISTS = 183

MUTEX_NAME = (
    "Local\\WeChatNotifier_SingleInstance"
)

MUTEX_HANDLE = ctypes.windll.kernel32.CreateMutexW(
    None,
    False,
    MUTEX_NAME
)

if (
    ctypes.windll.kernel32.GetLastError()
    == ERROR_ALREADY_EXISTS
):
    # 已经有一个 WeChatNotifier 在运行
    sys.exit(0)


# ============================================================
# 5. 运行状态
# ============================================================

stop_event = threading.Event()

pause_event = threading.Event()

# 从暂停恢复时重新建立 unread 基线，
# 防止暂停期间积累的消息一次性全部弹出
reset_baseline_event = threading.Event()


# ============================================================
# 6. 微信特殊会话过滤
# ============================================================

IGNORE_USERS = {
    # 公众号聚合
    "brandsessionholder",

    # 服务号聚合
    "brandservicesessionholder",

    # 公众号 / 通知入口
    "officialaccounts",
    "notification_messages",

    # 微信系统
    "newsapp",
    "weixin",
    "weixinreminder",
    "userexperience_alarm",
}


IGNORE_NAMES = {
    "公众号",
    "服务号",
}


# ============================================================
# 7. 基础数据库函数
# ============================================================

def get_sessions(db):
    sessions = db.get_sessions(
        limit=SESSION_LIMIT
    )

    result = {}

    for session in sessions:

        username = session.get(
            "username"
        )

        if username:
            result[str(username)] = session

    return result


def unread_value(session):

    try:
        return int(
            session.get("unread") or 0
        )

    except Exception:
        return 0


def get_name(db, username):

    try:

        name = db.get_nickname(
            username
        )

        if name:
            return str(name).strip()

    except Exception:
        pass

    return str(username)


# ============================================================
# 8. 读取免打扰群 + 公众号
# ============================================================

def get_contact_policy(db):
    """
    本机微信 4.1.13.12 已实际验证：

    chat_room_notify == 0
        → 群消息免打扰

    chat_room_notify == 1
        → 群正常通知

    verify_flag & 8 != 0
        → 公众号 / 服务号
    """

    muted_groups = set()
    official_accounts = set()

    try:

        for rel, path, _ in db._db_files:

            if not str(path).lower().endswith(
                "contact.db"
            ):
                continue

            conn = db._open(rel)

            rows = conn.execute(
                """
                SELECT
                    username,
                    chat_room_notify,
                    verify_flag
                FROM contact
                """
            ).fetchall()

            for row in rows:

                try:

                    username = str(
                        row[0] or ""
                    ).strip()

                    chat_room_notify = row[1]

                    verify_flag = (
                        row[2] or 0
                    )

                except Exception:
                    continue

                if not username:
                    continue

                # -------------------------------
                # 群消息免打扰
                # -------------------------------

                if username.endswith(
                    "@chatroom"
                ):

                    try:

                        if int(
                            chat_room_notify
                        ) == 0:

                            muted_groups.add(
                                username
                            )

                    except Exception:
                        pass

                # -------------------------------
                # 公众号 / 服务号
                # -------------------------------

                try:

                    if int(
                        verify_flag
                    ) & 8:

                        official_accounts.add(
                            username
                        )

                except Exception:
                    pass

    except Exception:

        log_error(
            "读取 contact.db 策略失败"
        )

    return (
        muted_groups,
        official_accounts
    )


# ============================================================
# 9. 判断是否忽略
# ============================================================

def should_ignore(
    db,
    username,
    muted_groups,
    official_accounts
):

    username = str(
        username or ""
    ).strip()

    if not username:
        return True

    username_lower = (
        username.lower()
    )

    # --------------------------------------------------------
    # 微信内部折叠 / placeholder
    # --------------------------------------------------------

    if username_lower.startswith(
        "@placeholder_"
    ):
        return True

    # --------------------------------------------------------
    # 特殊系统会话
    # --------------------------------------------------------

    if username_lower in IGNORE_USERS:
        return True

    # --------------------------------------------------------
    # gh_xxx 公众号
    # --------------------------------------------------------

    if username_lower.startswith(
        "gh_"
    ):
        return True

    # --------------------------------------------------------
    # verify_flag 识别的公众号 / 服务号
    # --------------------------------------------------------

    if username in official_accounts:
        return True

    # --------------------------------------------------------
    # 群消息免打扰
    # --------------------------------------------------------

    if (
        username.endswith("@chatroom")
        and
        username in muted_groups
    ):
        return True

    # --------------------------------------------------------
    # 名称兜底
    # --------------------------------------------------------

    try:

        name = get_name(
            db,
            username
        )

        if name in IGNORE_NAMES:
            return True

    except Exception:
        pass

    return False


# ============================================================
# 10. Windows 通知
# ============================================================

def send_notification(
    db,
    username,
    session
):

    name = get_name(
        db,
        username
    )

    summary = str(
        session.get("summary") or ""
    ).strip()

    if not summary:
        summary = "收到一条新消息"

    if len(summary) > 180:

        summary = (
            summary[:180]
            + "……"
        )

    log(
        f"发送通知 | "
        f"{username} | "
        f"{name} | "
        f"{summary}"
    )

    try:

        notify(
            f"微信 · {name}",
            summary,
            app_id=APP_ID
        )

    except Exception:

        log_error(
            "Windows Toast 发送失败"
        )


# ============================================================
# 11. 测试通知
# ============================================================

def send_test_notification():

    try:

        notify(
            APP_NAME,
            "测试通知正常。",
            app_id=APP_ID
        )

        log(
            "发送测试通知"
        )

    except Exception:

        log_error(
            "测试通知发送失败"
        )


# ============================================================
# 12. 微信监控线程
# ============================================================

def monitor_loop():

    db = None

    previous = {}

    muted_groups = set()

    official_accounts = set()

    last_policy_refresh = 0


    while not stop_event.is_set():

        # ====================================================
        # A. 微信尚未连接
        # ====================================================

        if db is None:

            try:

                log(
                    "正在连接微信数据库……"
                )

                db = WeChatDB()

                previous = get_sessions(
                    db
                )

                (
                    muted_groups,
                    official_accounts
                ) = get_contact_policy(
                    db
                )

                last_policy_refresh = (
                    time.time()
                )

                log(
                    f"微信数据库连接成功 | "
                    f"会话={len(previous)} | "
                    f"免打扰群={len(muted_groups)} | "
                    f"公众号/服务号="
                    f"{len(official_accounts)}"
                )

            except Exception:

                db = None

                log_error(
                    "微信数据库连接失败，"
                    "稍后自动重试"
                )

                stop_event.wait(
                    RECONNECT_SECONDS
                )

                continue


        # ====================================================
        # B. 暂停模式
        # ====================================================

        if pause_event.is_set():

            stop_event.wait(
                0.5
            )

            continue


        try:

            # =================================================
            # 从暂停状态恢复以后重新建立基线
            # =================================================

            if reset_baseline_event.is_set():

                previous = get_sessions(
                    db
                )

                reset_baseline_event.clear()

                log(
                    "恢复通知："
                    "已重新建立 unread 基线"
                )


            # =================================================
            # 定期刷新免打扰 / 公众号信息
            # =================================================

            if (
                time.time()
                - last_policy_refresh
                >= POLICY_REFRESH_SECONDS
            ):

                (
                    muted_groups,
                    official_accounts
                ) = get_contact_policy(
                    db
                )

                last_policy_refresh = (
                    time.time()
                )


            # =================================================
            # 当前微信会话
            # =================================================

            current = get_sessions(
                db
            )


            for (
                username,
                session
            ) in current.items():

                new_unread = (
                    unread_value(
                        session
                    )
                )

                old_session = (
                    previous.get(
                        username
                    )
                )


                # =============================================
                # 新会话
                # =============================================

                if old_session is None:

                    if new_unread <= 0:
                        continue

                    if should_ignore(
                        db,
                        username,
                        muted_groups,
                        official_accounts
                    ):

                        log(
                            f"已忽略新会话 | "
                            f"{username} | "
                            f"{get_name(db, username)}"
                        )

                        continue

                    send_notification(
                        db,
                        username,
                        session
                    )

                    continue


                # =============================================
                # 已有会话
                # =============================================

                old_unread = (
                    unread_value(
                        old_session
                    )
                )

                if (
                    new_unread
                    <= old_unread
                ):
                    continue


                name = get_name(
                    db,
                    username
                )


                log(
                    f"检测到未读变化 | "
                    f"{username} | "
                    f"{name} | "
                    f"{old_unread}"
                    f" -> "
                    f"{new_unread}"
                )


                # =============================================
                # 是否过滤
                # =============================================

                if should_ignore(
                    db,
                    username,
                    muted_groups,
                    official_accounts
                ):

                    log(
                        f"已忽略 | "
                        f"{username} | "
                        f"{name}"
                    )

                    continue


                # =============================================
                # 发送通知
                # =============================================

                send_notification(
                    db,
                    username,
                    session
                )


            previous = current


        except Exception:

            # 微信退出、数据库发生变化等情况下，
            # 不直接结束程序，而是重新连接。

            log_error(
                "微信消息读取异常，"
                "准备重新连接微信"
            )

            db = None

            previous = {}

            stop_event.wait(
                RECONNECT_SECONDS
            )

            continue


        stop_event.wait(
            POLL_SECONDS
        )


    log(
        "微信监控线程结束"
    )


# ============================================================
# 13. 开机启动
# ============================================================

RUN_KEY = (
    r"Software\Microsoft\Windows"
    r"\CurrentVersion\Run"
)

STARTUP_NAME = (
    "WeChatNotifier"
)


def current_program_command():

    # PyInstaller EXE
    if getattr(
        sys,
        "frozen",
        False
    ):

        return (
            f'"{sys.executable}"'
        )

    # Python 调试状态
    script = os.path.abspath(
        __file__
    )

    return (
        f'"{sys.executable}" '
        f'"{script}"'
    )


def startup_enabled():

    try:

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_READ
        ) as key:

            value, _ = (
                winreg.QueryValueEx(
                    key,
                    STARTUP_NAME
                )
            )

        return bool(
            value
        )

    except Exception:
        return False


def set_startup(
    enabled
):

    try:

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            RUN_KEY,
            0,
            winreg.KEY_SET_VALUE
        ) as key:

            if enabled:

                winreg.SetValueEx(
                    key,
                    STARTUP_NAME,
                    0,
                    winreg.REG_SZ,
                    current_program_command()
                )

                log(
                    "已启用开机启动"
                )

            else:

                try:

                    winreg.DeleteValue(
                        key,
                        STARTUP_NAME
                    )

                except FileNotFoundError:
                    pass

                log(
                    "已关闭开机启动"
                )

        return True

    except Exception:

        log_error(
            "修改开机启动失败"
        )

        return False


# ============================================================
# 14. 托盘图标
# ============================================================

def create_tray_image():

    size = 64

    image = Image.new(
        "RGBA",
        (size, size),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(
        image
    )

    # 主聊天气泡
    draw.rounded_rectangle(
        (6, 8, 58, 50),
        radius=16,
        fill=(20, 190, 90, 255)
    )

    # 气泡尾巴
    draw.polygon(
        [
            (20, 46),
            (16, 58),
            (34, 49)
        ],
        fill=(20, 190, 90, 255)
    )

    # 两个白色点
    draw.ellipse(
        (19, 25, 25, 31),
        fill=(255, 255, 255, 255)
    )

    draw.ellipse(
        (39, 25, 45, 31),
        fill=(255, 255, 255, 255)
    )

    return image


# ============================================================
# 15. 托盘菜单事件
# ============================================================

def tray_toggle_pause(
    icon,
    item
):

    if pause_event.is_set():

        pause_event.clear()

        reset_baseline_event.set()

        log(
            "用户恢复微信通知"
        )

    else:

        pause_event.set()

        log(
            "用户暂停微信通知"
        )

    icon.update_menu()


def tray_test_notification(
    icon,
    item
):

    send_test_notification()


def tray_open_log(
    icon,
    item
):

    try:

        if not os.path.exists(
            LOG_FILE
        ):

            open(
                LOG_FILE,
                "a",
                encoding="utf-8"
            ).close()

        os.startfile(
            LOG_FILE
        )

    except Exception:

        log_error(
            "打开日志失败"
        )


def tray_open_log_dir(
    icon,
    item
):

    try:

        os.startfile(
            APP_DIR
        )

    except Exception:

        log_error(
            "打开日志目录失败"
        )


def tray_toggle_startup(
    icon,
    item
):

    enabled = not startup_enabled()

    set_startup(
        enabled
    )

    icon.update_menu()


def tray_exit(
    icon,
    item
):

    log(
        "用户选择退出"
    )

    stop_event.set()

    icon.stop()


# ============================================================
# 16. 托盘菜单
# ============================================================

menu = pystray.Menu(

    pystray.MenuItem(
        "暂停通知",
        tray_toggle_pause,
        checked=lambda item: (
            pause_event.is_set()
        )
    ),

    pystray.Menu.SEPARATOR,

    pystray.MenuItem(
        "发送测试通知",
        tray_test_notification
    ),

    pystray.MenuItem(
        "打开日志",
        tray_open_log
    ),

    pystray.MenuItem(
        "打开日志目录",
        tray_open_log_dir
    ),

    pystray.Menu.SEPARATOR,

    pystray.MenuItem(
        "开机自动启动",
        tray_toggle_startup,
        checked=lambda item: (
            startup_enabled()
        )
    ),

    pystray.Menu.SEPARATOR,

    pystray.MenuItem(
        "退出",
        tray_exit
    )
)


# ============================================================
# 17. 主程序
# ============================================================

def main():

    log(
        "=" * 60
    )

    log(
        "WeChatNotifier 最终版启动"
    )

    # ----------------------------------------
    # 微信监控放到后台线程
    # ----------------------------------------

    monitor_thread = threading.Thread(
        target=monitor_loop,
        name="WeChatMonitor",
        daemon=True
    )

    monitor_thread.start()


    # ----------------------------------------
    # 托盘运行在主线程
    # ----------------------------------------

    icon = pystray.Icon(
        APP_ID,
        create_tray_image(),
        APP_NAME,
        menu
    )

    try:

        icon.run()

    except Exception:

        log_error(
            "托盘程序发生异常"
        )

    finally:

        stop_event.set()

        log(
            "WeChatNotifier 主程序结束"
        )


if __name__ == "__main__":
    main()