#CREDIT - @EarningxzonYT

import os
import sys
import time
import json
import zipfile
import subprocess
import threading
import html
import psutil
from datetime import datetime

import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# ============================================================
# BOT CONFIG
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OWNER_ID = int(os.getenv("OWNER_ID", ""))

STORAGE_DIR = "user_files"
UPLOAD_DIR = os.path.join(STORAGE_DIR, "uplo556ads")
DATA_FILE = os.path.join(STORAGE_DIR, "users.json")

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

# ============================================================
# GLOBALS
# ============================================================

users = {}

active_scripts = {}
logs_store = {}

install_waiting_users = {}

bot_start_time = time.time()
START_TIME = datetime.now()

RECOMMENDED_PACKAGES = [
    "pip",
    "setuptools",
    "wheel",
    "requests",
    "numpy",
    "pandas",
    "flask",
    "aiohttp",
    "pyrogram",
    "python-dotenv",
    "beautifulsoup4",
    "lxml",
    "pillow",
    "matplotlib",
    "scipy",
    "scikit-learn",
    "pytest"
]

PYTG_CALLS_PACKAGE = "git+https://github.com/pytgcalls/pytgcalls.git"

# ============================================================
# PREMIUM EMOJI
# ============================================================

PREMIUM_EMOJI_IDS = [

    # Existing Premium Emojis
    "5289722755871162900",
    "5372849966689566579",
    "5359664288241829619",
    "5445033158456145975",
    "5445092669522996408",
    "5445358884480916784",
    "5445307250384075361",
    "5447602197439218445",
    "6147460667281511517",
    "6235459831302460476",
    "6244492465353529537",
    "6318817991102305543",

    # New Premium Emojis
    "5231200819986047254",
    "5944970130554359187",
    "6120548140211770562",
    "4987977590812705943",
    "5416081784641168838",
    "6321171873698681876",
    "5915556996215476302",
    "5877443460725739250",
    "4990298741463319592",
    "5462956611033117422",
    "6231214251835397322",
    "6282846669335702032",
    "5210952531676504517",
    "6129639980387015660",
]

PE_FIRE = PREMIUM_EMOJI_IDS[0]
PE_STAR = PREMIUM_EMOJI_IDS[1]
PE_ROCKET = PREMIUM_EMOJI_IDS[2]
PE_CROWN = PREMIUM_EMOJI_IDS[3]
PE_SHIELD = PREMIUM_EMOJI_IDS[4]
PE_MONEY = PREMIUM_EMOJI_IDS[5]
PE_PHONE = PREMIUM_EMOJI_IDS[6]
PE_CHECK = PREMIUM_EMOJI_IDS[7]
PE_CROSS = PREMIUM_EMOJI_IDS[8]
PE_WARNING = PREMIUM_EMOJI_IDS[9]
PE_LOCK = PREMIUM_EMOJI_IDS[10]
PE_GIFT = PREMIUM_EMOJI_IDS[11]

PE_APPROVE = PREMIUM_EMOJI_IDS[12]
PE_USER = PREMIUM_EMOJI_IDS[13]
PE_ADMIN = PREMIUM_EMOJI_IDS[14]
PE_UPLOAD = PREMIUM_EMOJI_IDS[15]
PE_FOLDER = PREMIUM_EMOJI_IDS[16]
PE_SETTINGS = PREMIUM_EMOJI_IDS[17]
PE_SERVER = PREMIUM_EMOJI_IDS[18]
PE_DIAMOND = PREMIUM_EMOJI_IDS[19]
PE_BOT = PREMIUM_EMOJI_IDS[20]


def pe(emoji_id, fallback="💎"):
    """
    Telegram custom premium emoji HTML.
    """
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def safe_html(value):
    return html.escape(str(value), quote=False)


def premium_header(title, emoji_id=PE_CROWN, fallback="👑"):
    return (
        f"{pe(emoji_id, fallback)} "
        f"<b>{safe_html(title)}</b>"
    )


# ============================================================
# TELEGRAM BOT INIT
# ============================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode=None
)


# ============================================================
# DATA PERSISTENCE
# ============================================================

def save_data():
    try:
        temp_file = DATA_FILE + ".tmp"

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(
                users,
                f,
                indent=4,
                ensure_ascii=False
            )

        os.replace(temp_file, DATA_FILE)

    except Exception as e:
        print(f"Save Error: {e}")


def load_data():

    global users

    if not os.path.exists(DATA_FILE):
        users = {}
        return

    try:

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        users.clear()

        for key, value in raw_data.items():

            try:
                uid = int(key)
            except:
                continue

            if not isinstance(value, dict):
                value = {}

            value.setdefault("files", [])

            value.setdefault(
                "approved",
                uid == OWNER_ID
            )

            value.setdefault(
                "rejected",
                False
            )

            users[uid] = value

    except Exception as e:

        print(f"Load Error: {e}")

        users = {}


load_data()


# ============================================================
# USER / APPROVAL SYSTEM
# ============================================================

def ensure_user(uid):

    if uid not in users:

        users[uid] = {
            "files": [],
            "approved": uid == OWNER_ID,
            "rejected": False
        }

        save_data()

    else:

        users[uid].setdefault("files", [])
        users[uid].setdefault(
            "approved",
            uid == OWNER_ID
        )
        users[uid].setdefault(
            "rejected",
            False
        )


def is_owner(uid):

    return uid == OWNER_ID


def is_approved(uid):

    if uid == OWNER_ID:
        return True

    ensure_user(uid)

    return users[uid].get("approved", False)


def approval_buttons(uid):

    markup = InlineKeyboardMarkup()

    markup.row(
        InlineKeyboardButton(
            "✅ APPROVE",
            callback_data=f"approve_{uid}"
        ),
        InlineKeyboardButton(
            "❌ REJECT",
            callback_data=f"reject_{uid}"
        )
    )

    return markup


def send_approval_request(message):

    uid = message.from_user.id

    first_name = (
        message.from_user.first_name
        or "Unknown"
    )

    username = message.from_user.username

    if username:
        username_text = f"@{username}"
    else:
        username_text = "No username"

    text = (
        f"{pe(PE_ADMIN, '👑')} "
        f"<b>NEW USER APPROVAL</b>\n\n"

        f"{pe(PE_USER, '👤')} "
        f"<b>Name:</b> "
        f"{safe_html(first_name)}\n"

        f"{pe(PE_PHONE, '🆔')} "
        f"<b>User ID:</b> "
        f"<code>{uid}</code>\n"

        f"{pe(PE_BOT, '🤖')} "
        f"<b>Username:</b> "
        f"{safe_html(username_text)}\n\n"

        f"{pe(PE_WARNING, '⚠️')} "
        f"<b>Status:</b> Pending Approval"
    )

    try:

        bot.send_message(
            OWNER_ID,
            text,
            reply_markup=approval_buttons(uid),
            parse_mode="HTML"
        )

    except Exception as e:

        print(
            f"Approval notification error: {e}"
        )


def approval_required(message):

    uid = message.from_user.id

    if is_owner(uid):
        return False

    if is_approved(uid):
        return False

    ensure_user(uid)

    bot.reply_to(
        message,
        (
            f"{pe(PE_LOCK, '🔐')} "
            f"<b>ACCESS PENDING</b>\n\n"

            f"{pe(PE_ADMIN, '👑')} "
            f"Your account is waiting for "
            f"<b>Owner Approval</b>.\n\n"

            f"{pe(PE_STAR, '⭐')} "
            f"Please wait until the owner approves "
            f"your account."
        ),
        parse_mode="HTML"
    )

    return True


# ============================================================
# OWNER NOTIFICATION
# ============================================================

def notify_owner(text, index=0):

    try:

        emoji_id = PREMIUM_EMOJI_IDS[
            index % len(PREMIUM_EMOJI_IDS)
        ]

        bot.send_message(
            OWNER_ID,
            f"{pe(emoji_id, '🔔')} {text}",
            parse_mode="HTML"
        )

    except Exception as e:

        print(
            f"Owner notification error: {e}"
        )


# ============================================================
# UTILITIES
# ============================================================

def uptime():

    seconds = int(
        time.time() - bot_start_time
    )

    return (
        f"{seconds // 3600}h "
        f"{(seconds % 3600) // 60}m "
        f"{seconds % 60}s"
    )


def user_folder(uid):

    path = os.path.join(
        UPLOAD_DIR,
        str(uid)
    )

    os.makedirs(
        path,
        exist_ok=True
    )

    return path


def get_system_info():

    cpu_freq = psutil.cpu_freq()

    if cpu_freq:
        cpu_ghz = cpu_freq.current / 1000
    else:
        cpu_ghz = 0

    ram = psutil.virtual_memory()

    total_ram_gb = (
        ram.total /
        (1024 ** 3)
    )

    free_ram_gb = (
        ram.available /
        (1024 ** 3)
    )

    return (
        cpu_ghz,
        total_ram_gb,
        free_ram_gb
    )


def install_requirements(folder):

    req_file = os.path.join(
        folder,
        "requirements.txt"
    )

    if os.path.exists(req_file):

        try:

            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    req_file
                ]
            )

        except Exception as e:

            print(
                f"Requirements install error: {e}"
            )


# ============================================================
# SCRIPT RUNNING
# ============================================================

def run_script_thread(
    user_id,
    file_path
):

    try:

        proc = subprocess.Popen(
            [
                sys.executable,
                os.path.abspath(file_path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        active_scripts.setdefault(
            user_id,
            {}
        )[file_path] = proc

        logs_store.setdefault(
            user_id,
            {}
        )[file_path] = []

        while True:

            line = proc.stdout.readline()

            if not line and proc.poll() is not None:
                break

            if line:

                logs_store[user_id][file_path].append(
                    line.strip()
                )

                logs_store[user_id][file_path] = (
                    logs_store[user_id][file_path][-50:]
                )

        proc.wait()

    except Exception as e:

        print(
            f"Error in script {file_path}: {e}"
        )

    finally:

        if user_id in active_scripts:

            active_scripts[user_id].pop(
                file_path,
                None
            )


def start_script(
    user_id,
    file_path
):

    thread = threading.Thread(
        target=run_script_thread,
        args=(
            user_id,
            file_path
        ),
        daemon=True
    )

    thread.start()


# ============================================================
# INSTALLATION
# ============================================================

def live_install(
    cmd_list,
    chat_id,
    message_id,
    description
):

    try:

        proc = subprocess.Popen(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        output_lines = []

        while True:

            line = proc.stdout.readline()

            if line:

                output_lines.append(
                    line.rstrip()
                )

                if len(output_lines) > 8:
                    output_lines = (
                        output_lines[-8:]
                    )

                live_text = "\n".join(
                    output_lines
                )

                try:

                    bot.edit_message_text(
                        (
                            f"{pe(PE_UPLOAD, '📥')} "
                            f"<b>{safe_html(description)}...</b>\n"
                            f"<pre>{safe_html(live_text)}</pre>"
                        ),
                        chat_id=chat_id,
                        message_id=message_id,
                        parse_mode="HTML"
                    )

                except:
                    pass

            if (
                not line
                and proc.poll() is not None
            ):
                break

        full_output = "\n".join(
            output_lines[-100:]
        )

        if proc.returncode == 0:

            bot.edit_message_text(
                (
                    f"{pe(PE_CHECK, '✅')} "
                    f"<b>{safe_html(description)} "
                    f"installed!</b>\n\n"
                    f"<pre>{safe_html(full_output)}</pre>"
                ),
                chat_id=chat_id,
                message_id=message_id,
                parse_mode="HTML"
            )

        else:

            bot.edit_message_text(
                (
                    f"{pe(PE_CROSS, '❌')} "
                    f"<b>Installation Failed</b>\n\n"
                    f"<pre>{safe_html(full_output)}</pre>"
                ),
                chat_id=chat_id,
                message_id=message_id,
                parse_mode="HTML"
            )

    except Exception as e:

        try:

            bot.edit_message_text(
                (
                    f"{pe(PE_CROSS, '❌')} "
                    f"<b>Exception</b>\n\n"
                    f"<code>{safe_html(e)}</code>"
                ),
                chat_id=chat_id,
                message_id=message_id,
                parse_mode="HTML"
            )

        except:
            pass


def install_recommended_packages(
    chat_id,
    message_id
):

    total = len(RECOMMENDED_PACKAGES)

    for idx, pkg in enumerate(
        RECOMMENDED_PACKAGES,
        start=1
    ):

        live_install(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                pkg
            ],
            chat_id,
            message_id,
            f"{pkg} ({idx}/{total})"
        )

    live_install(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            PYTG_CALLS_PACKAGE
        ],
        chat_id,
        message_id,
        "pytgcalls (GitHub)"
    )


# ============================================================
# MAIN KEYBOARD
# ============================================================

def control_buttons():

    # IMPORTANT:
    # Do NOT pass a list as the first argument.
    # This fixes:
    # ReplyKeyboardMarkup.__init__()
    # got multiple values for resize_keyboard

    markup = ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        KeyboardButton("🌏 Upload"),
        KeyboardButton("📁 𝐌𝐲 𝐅𝐢𝐥𝐞𝐬")
    )

    markup.row(
        KeyboardButton("🔄 𝐑𝐞𝐬𝐭𝐚𝐫𝐭"),
        KeyboardButton("⏹ 𝐒𝐭𝐨𝐩")
    )

    markup.row(
        KeyboardButton("⚡ 𝐒𝐩𝐞𝐞𝐝"),
        KeyboardButton("🚀 𝐒𝐭𝐚𝐭ᴜѕ")
    )

    markup.row(
        KeyboardButton(
            "⚙️ Recommended Install"
        )
    )

    return markup


# ============================================================
# START COMMAND
# ============================================================

@bot.message_handler(
    commands=["start"]
)
def start_command(message):

    uid = message.from_user.id

    first_name = (
        message.from_user.first_name
        or "User"
    )

    is_new = uid not in users

    ensure_user(uid)

    # Owner always has access
    if uid == OWNER_ID:

        users[uid]["approved"] = True
        users[uid]["rejected"] = False

        save_data()

    # New users need owner approval
    if is_new and uid != OWNER_ID:

        send_approval_request(message)

        bot.send_message(
            uid,
            (
                f"{pe(PE_LOCK, '🔐')} "
                f"<b>ACCESS REQUESTED</b>\n\n"

                f"{pe(PE_USER, '👤')} "
                f"Welcome, "
                f"<b>{safe_html(first_name)}</b>!\n\n"

                f"{pe(PE_ADMIN, '👑')} "
                f"Your access request has been "
                f"sent to the owner.\n\n"

                f"{pe(PE_STAR, '⭐')} "
                f"<b>Please wait for approval.</b>"
            ),
            parse_mode="HTML"
        )

        return

    if not is_approved(uid):

        bot.send_message(
            uid,
            (
                f"{pe(PE_LOCK, '🔐')} "
                f"<b>ACCESS PENDING</b>\n\n"

                f"Your account is waiting for "
                f"<b>Owner Approval</b>.\n\n"

                f"{pe(PE_STAR, '⭐')} "
                f"Please wait."
            ),
            parse_mode="HTML"
        )

        return

    welcome = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃ {pe(PE_ROCKET, '🚀')} "
        f"<b>SHIVA HOSTING</b> ┃\n"
        f"┃ <b>VERSION 0.3</b> ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"

        f"{pe(PE_GIFT, '👤')} "
        f"<b>Wᴇʟᴄᴏᴍᴇ</b> "
        f"{safe_html(first_name)}!\n\n"

        f"{pe(PE_PHONE, '🆔')} "
        f"<b>Uꜱᴇʀ ID:</b> "
        f"<code>{uid}</code>\n\n"

        f"{pe(PE_FOLDER, '📁')} "
        f"<b>Fɪʟᴇꜱ:</b> "
        f"{len(users[uid]['files'])}\n\n"

        f"{pe(PE_STAR, '⚡')} "
        f"<b>Fᴇᴀᴛᴜʀᴇꜱ:</b>\n"

        f"• {pe(PE_CHECK, '✅')} "
        f"Aᴜᴛᴏ-Rᴇᴄᴏᴠᴇʀʏ Sʏꜱᴛᴇᴍ\n"

        f"• {pe(PE_BOT, '🤖')} "
        f"Pʏᴛʜᴏɴ / Jꜱ / Zɪᴘ Sᴜᴘᴘᴏʀᴛ\n"

        f"• {pe(PE_DIAMOND, '💎')} "
        f"Pʀᴇᴍɪᴜᴍ Eᴍᴏᴊɪ Sʏꜱᴛᴇᴍ\n\n"

        f"Uꜱᴇ ᴛʜᴇ Bᴜᴛᴛᴏɴs Bᴇʟᴏᴡ."
    )

    bot.send_message(
        uid,
        welcome,
        reply_markup=control_buttons(),
        parse_mode="HTML"
    )

    notify_owner(
        f"<b>User Started Bot</b>\n"
        f"👤 <code>{uid}</code>\n"
        f"Name: {safe_html(first_name)}",
        0
    )


# ============================================================
# TEXT / CONTROL BUTTON HANDLER
# ============================================================

@bot.message_handler(func=lambda message: True, content_types=["text"])
def control_handler(message):

    uid = message.from_user.id
    text = (message.text or "").strip()

    ensure_user(uid)

    if approval_required(message):
        return

    user_data = users[uid]

    # --------------------------------------------------------
    # MY FILES
    # --------------------------------------------------------

    if text.startswith("📁"):

        files = user_data["files"]

        if not files:

            bot.reply_to(
                message,
                (
                    f"{pe(PE_CROSS, '❌')} "
                    f"<b>No files.</b>"
                ),
                parse_mode="HTML"
            )

            return

        buttons = [
            [
                InlineKeyboardButton(
                    f"📄 {f}",
                    callback_data=f"file_{f}"
                )
            ]
            for f in files
        ]

        bot.reply_to(
            message,
            (
                f"{pe(PE_FOLDER, '📁')} "
                f"<b>𝐘𝐨𝐮𝐫 𝐅𝐢𝐥𝐞𝐬:</b>"
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )

    # --------------------------------------------------------
    # SPEED
    # --------------------------------------------------------

    elif text.startswith("⚡"):

        start_time = time.time()

        time.sleep(0.1)

        processing_time = (
            time.time() - start_time
        )

        cpu_ghz, total_ram_gb, free_ram_gb = (
            get_system_info()
        )

        bot.reply_to(
            message,
            (
                f"{pe(PE_FIRE, '⚡')} "
                f"<b>BOT SPEED</b>\n\n"

                f"⏱️ <b>Response:</b> "
                f"{round(processing_time, 4)} sec\n\n"

                f"⚙️ <b>CPU:</b> "
                f"{round(cpu_ghz, 2)} GHz\n"

                f"💾 <b>RAM:</b> "
                f"{round(total_ram_gb, 2)} GB\n"

                f"🟢 <b>FREE:</b> "
                f"{round(free_ram_gb, 2)} GB"
            ),
            parse_mode="HTML"
        )

    # --------------------------------------------------------
    # RESTART
    # --------------------------------------------------------

    elif text.startswith("🔄"):

        if uid in active_scripts:

            for p in list(
                active_scripts[uid].values()
            ):

                try:
                    p.kill()
                except:
                    pass

            active_scripts[uid] = {}

        folder = user_folder(uid)

        for fname in user_data["files"]:

            if fname.endswith(".py"):

                path = os.path.join(
                    folder,
                    fname
                )

                if os.path.exists(path):

                    start_script(
                        uid,
                        path
                    )

        bot.reply_to(
            message,
            (
                f"{pe(PE_ROCKET, '🔄')} "
                f"<b>All your scripts have "
                f"been restarted.</b>"
            ),
            parse_mode="HTML"
        )

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------

    elif text.startswith("⏹"):

        if uid in active_scripts:

            for p in list(
                active_scripts[uid].values()
            ):

                try:
                    p.kill()
                except:
                    pass

            active_scripts[uid] = {}

        bot.reply_to(
            message,
            (
                f"{pe(PE_SHIELD, '⏹')} "
                f"<b>Stopped all your scripts.</b>"
            ),
            parse_mode="HTML"
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    elif text.startswith("🚀"):

        total_users = len(users)

        total_files = sum(
            len(u.get("files", []))
            for u in users.values()
            if u
        )

        running_scripts = sum(
            len(
                active_scripts.get(
                    user_id,
                    {}
                )
            )
            for user_id in users
        )

        approved_users = sum(
            1
            for u in users.values()
            if u.get("approved", False)
        )

        pending_users = sum(
            1
            for u in users.values()
            if (
                not u.get(
                    "approved",
                    False
                )
                and not u.get(
                    "rejected",
                    False
                )
            )
        )

        uptime_seconds = (
            datetime.now() - START_TIME
        ).total_seconds()

        hours, remainder = divmod(
            int(uptime_seconds),
            3600
        )

        minutes, seconds = divmod(
            remainder,
            60
        )

        bot.reply_to(
            message,
            (
                f"📊 <b>LIVE STATISTICS</b>\n\n"

                f"👥 <b>Total Users:</b> "
                f"{total_users}\n"

                f"✅ <b>Approved Users:</b> "
                f"{approved_users}\n"

                f"⏳ <b>Pending Users:</b> "
                f"{pending_users}\n"

                f"📁 <b>Total Files:</b> "
                f"{total_files}\n"

                f"🟢 <b>Running Scripts:</b> "
                f"{running_scripts}\n"

                f"🔒 <b>Bot Status:</b> "
                f"{pe(PE_CHECK, '🟢')} "
                f"<b>ONLINE</b>\n\n"

                f"⏱️ <b>Uptime:</b> "
                f"{hours}h "
                f"{minutes}m "
                f"{seconds}s"
            ),
            parse_mode="HTML"
        )


# ============================================================
# DOCUMENT / FILE HANDLER
# ============================================================

@bot.message_handler(
    content_types=["document"]
)
def document_handler(message):

    uid = message.from_user.id

    ensure_user(uid)

    if approval_required(message):
        return

    user_data = users[uid]

    # File limit for normal users
    if (
        uid != OWNER_ID
        and len(user_data["files"]) >= 2
    ):

        bot.reply_to(
            message,
            (
                f"{pe(PE_WARNING, '⚠️')} "
                f"<b>You have reached the limit "
                f"of 2 files.</b>\n\n"
                f"Contact the owner for more."
            ),
            parse_mode="HTML"
        )

        return

    doc = message.document

    filename = doc.file_name

    # Allowed file types
    if not filename.lower().endswith(
        (".py", ".zip", ".txt")
    ):

        bot.reply_to(
            message,
            (
                f"{pe(PE_CROSS, '❌')} "
                f"<b>Only .py, .zip and .txt "
                f"files are allowed.</b>"
            ),
            parse_mode="HTML"
        )

        return

    folder = user_folder(uid)

    save_path = os.path.join(
        folder,
        filename
    )

    msg = bot.reply_to(
        message,
        (
            f"{pe(PE_UPLOAD, '⬇️')} "
            f"<b>Downloading...</b>"
        ),
        parse_mode="HTML"
    )

    try:

        file_info = bot.get_file(
            doc.file_id
        )

        downloaded_file = bot.download_file(
            file_info.file_path
        )

        with open(
            save_path,
            "wb"
        ) as f:

            f.write(
                downloaded_file
            )

    except Exception as e:

        bot.edit_message_text(
            (
                f"{pe(PE_CROSS, '❌')} "
                f"<b>Download failed.</b>\n\n"
                f"<code>{safe_html(e)}</code>"
            ),
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode="HTML"
        )

        return

    if filename not in user_data["files"]:

        user_data["files"].append(
            filename
        )

        save_data()

    # --------------------------------------------------------
    # ZIP FILE
    # --------------------------------------------------------

    if filename.lower().endswith(".zip"):

        try:

            with zipfile.ZipFile(
                save_path,
                "r"
            ) as zip_ref:

                zip_ref.extractall(
                    folder
                )

            install_requirements(
                folder
            )

            bot.edit_message_text(
                (
                    f"{pe(PE_CHECK, '📦')} "
                    f"<b>ZIP extracted "
                    f"successfully.</b>"
                ),
                chat_id=message.chat.id,
                message_id=msg.message_id,
                parse_mode="HTML"
            )

        except Exception as e:

            bot.edit_message_text(
                (
                    f"{pe(PE_CROSS, '❌')} "
                    f"<b>ZIP extraction failed.</b>\n\n"
                    f"<code>{safe_html(e)}</code>"
                ),
                chat_id=message.chat.id,
                message_id=msg.message_id,
                parse_mode="HTML"
            )

    # --------------------------------------------------------
    # TXT / REQUIREMENTS
    # --------------------------------------------------------

    elif filename.lower().endswith(".txt"):

        install_requirements(
            folder
        )

        bot.edit_message_text(
            (
                f"{pe(PE_CHECK, '📦')} "
                f"<b>Requirements installed.</b>"
            ),
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode="HTML"
        )

    # --------------------------------------------------------
    # PYTHON FILE
    # --------------------------------------------------------

    elif filename.lower().endswith(".py"):

        start_script(
            uid,
            save_path
        )

        bot.edit_message_text(
            (
                f"{pe(PE_ROCKET, '⚡')} "
                f"<b>Starting "
                f"{safe_html(filename)}...</b>"
            ),
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode="HTML"
        )

    notify_owner(
        (
            f"<b>File Uploaded</b>\n"
            f"{pe(PE_USER, '👤')} "
            f"User: <code>{uid}</code>\n"
            f"{pe(PE_FOLDER, '📁')} "
            f"File: <code>"
            f"{safe_html(filename)}"
            f"</code>"
        ),
        1
    )


# ============================================================
# CALLBACK QUERY
# ============================================================

@bot.callback_query_handler(
    func=lambda call: True
)
def callback_query(call):

    uid = call.from_user.id

    ensure_user(uid)

    data = call.data or ""

    # --------------------------------------------------------
    # APPROVE USER
    # --------------------------------------------------------

    if data.startswith("approve_"):

        if uid != OWNER_ID:

            bot.answer_callback_query(
                call.id,
                "❌ Owner only!"
            )

            return

        try:

            target_id = int(
                data.split(
                    "_",
                    1
                )[1]
            )

        except:

            bot.answer_callback_query(
                call.id,
                "❌ Invalid user ID."
            )

            return

        ensure_user(
            target_id
        )

        users[target_id]["approved"] = True
        users[target_id]["rejected"] = False

        save_data()

        bot.answer_callback_query(
            call.id,
            "✅ User Approved!"
        )

        try:

            bot.edit_message_text(
                (
                    f"{pe(PE_APPROVE, '✅')} "
                    f"<b>USER APPROVED</b>\n\n"

                    f"{pe(PE_USER, '👤')} "
                    f"<b>User ID:</b> "
                    f"<code>{target_id}</code>\n\n"

                    f"{pe(PE_ADMIN, '👑')} "
                    f"Approved by Owner."
                ),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )

        except:
            pass

        try:

            bot.send_message(
                target_id,
                (
                    f"{pe(PE_GIFT, '🎁')} "
                    f"<b>ACCESS APPROVED!</b>\n\n"

                    f"{pe(PE_CHECK, '✅')} "
                    f"Your account has been "
                    f"approved by the owner.\n\n"

                    f"{pe(PE_ROCKET, '🚀')} "
                    f"You can now use "
                    f"<b>SHIVA HOSTING</b>."
                ),
                reply_markup=control_buttons(),
                parse_mode="HTML"
            )

        except Exception as e:

            print(
                f"Approval notification error: {e}"
            )

        return

    # --------------------------------------------------------
    # REJECT USER
    # --------------------------------------------------------

    if data.startswith("reject_"):

        if uid != OWNER_ID:

            bot.answer_callback_query(
                call.id,
                "❌ Owner only!"
            )

            return

        try:

            target_id = int(
                data.split(
                    "_",
                    1
                )[1]
            )

        except:

            bot.answer_callback_query(
                call.id,
                "❌ Invalid user ID."
            )

            return

        ensure_user(
            target_id
        )

        users[target_id]["approved"] = False
        users[target_id]["rejected"] = True

        save_data()

        bot.answer_callback_query(
            call.id,
            "❌ User Rejected!"
        )

        try:

            bot.edit_message_text(
                (
                    f"{pe(PE_CROSS, '❌')} "
                    f"<b>USER REJECTED</b>\n\n"

                    f"{pe(PE_USER, '👤')} "
                    f"<b>User ID:</b> "
                    f"<code>{target_id}</code>\n\n"

                    f"{pe(PE_ADMIN, '👑')} "
                    f"Rejected by Owner."
                ),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )

        except:
            pass

        try:

            bot.send_message(
                target_id,
                (
                    f"{pe(PE_CROSS, '❌')} "
                    f"<b>ACCESS REJECTED</b>\n\n"
                    f"Your request was rejected "
                    f"by the owner."
                ),
                parse_mode="HTML"
            )

        except:
            pass

        return

    # --------------------------------------------------------
    # APPROVAL CHECK
    # --------------------------------------------------------

    if not is_approved(uid):

        bot.answer_callback_query(
            call.id,
            "🔐 Owner approval required."
        )

        return

    # --------------------------------------------------------
    # FILE DETAILS
    # --------------------------------------------------------

    if data.startswith("file_"):

        filename = data[5:]

        user_data = users.get(
            uid,
            {"files": []}
        )

        if filename not in user_data.get(
            "files",
            []
        ):

            bot.answer_callback_query(
                call.id,
                "❌ File not found."
            )

            return

        user_name = (
            call.from_user.first_name
            or "User"
        )

        path = os.path.join(
            user_folder(uid),
            filename
        )

        running = (
            path in active_scripts.get(
                uid,
                {}
            )
        )

        msg = (
            f"{pe(PE_STAR, '⚡')} "
            f"<b>𝐀𝐜𝐭𝐢𝐨𝐧𝐬 𝐟𝐨𝐫</b>\n"
            f"<code>{safe_html(filename)}</code>\n\n"

            f"{pe(PE_PHONE, '🆔')} "
            f"<b>𝐔𝐬ᴇʀ ID:</b> "
            f"<code>{uid}</code>\n"

            f"{pe(PE_USER, '👤')} "
            f"<b>𝐍ᴀᴍᴇ:</b> "
            f"<code>{safe_html(user_name)}</code>\n"

            f"{pe(PE_CHECK, '🟢')} "
            f"<b>𝐑ᴜɴɴɪɴɢ:</b> "
            f"<code>{1 if running else 0}</code>"
        )

        buttons = [
            [
                InlineKeyboardButton(
                    "▶ Run",
                    callback_data=f"run_{filename}"
                ),
                InlineKeyboardButton(
                    "⏹ Stop",
                    callback_data=f"stop_{filename}"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅ Back",
                    callback_data="myfiles"
                )
            ]
        ]

        bot.edit_message_text(
            msg,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=InlineKeyboardMarkup(
                buttons
            ),
            parse_mode="HTML"
        )

        return
            # --------------------------------------------------------
    # MY FILES BACK BUTTON
    # --------------------------------------------------------

    if data == "myfiles":

        files = users[uid]["files"]

        if not files:

            bot.edit_message_text(
                (
                    f"{pe(PE_CROSS, '❌')} "
                    f"<b>No files.</b>"
                ),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )

            return

        buttons = [
            [
                InlineKeyboardButton(
                    f"📄 {f}",
                    callback_data=f"file_{f}"
                )
            ]
            for f in files
        ]

        bot.edit_message_text(
            (
                f"{pe(PE_FOLDER, '📁')} "
                f"<b>𝐘𝐨ᴜʀ 𝐅ɪ𝐥ᴇs:</b>"
            ),
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=InlineKeyboardMarkup(
                buttons
            ),
            parse_mode="HTML"
        )

        return

    # --------------------------------------------------------
    # RUN FILE
    # --------------------------------------------------------

    if data.startswith("run_"):

        fname = data[4:]

        if fname not in users[uid]["files"]:

            bot.answer_callback_query(
                call.id,
                "❌ File not found."
            )

            return

        path = os.path.join(
            user_folder(uid),
            fname
        )

        if not os.path.exists(path):

            bot.answer_callback_query(
                call.id,
                "❌ File not found."
            )

            return

        if not fname.lower().endswith(".py"):

            bot.answer_callback_query(
                call.id,
                "❌ Only Python files can run."
            )

            return

        start_script(
            uid,
            path
        )

        bot.answer_callback_query(
            call.id,
            f"▶ {fname} started"
        )

        notify_owner(
            (
                f"<b>Script Started</b>\n"
                f"User: <code>{uid}</code>\n"
                f"File: <code>"
                f"{safe_html(fname)}"
                f"</code>"
            ),
            2
        )

        return

    # --------------------------------------------------------
    # STOP FILE
    # --------------------------------------------------------

    if data.startswith("stop_"):

        fname = data[5:]

        path = os.path.join(
            user_folder(uid),
            fname
        )

        proc = active_scripts.get(
            uid,
            {}
        ).get(path)

        if proc:

            try:
                proc.kill()
            except:
                pass

            active_scripts[uid].pop(
                path,
                None
            )

            bot.answer_callback_query(
                call.id,
                f"⏹ {fname} stopped"
            )

            notify_owner(
                (
                    f"<b>Script Stopped</b>\n"
                    f"User: <code>{uid}</code>\n"
                    f"File: <code>"
                    f"{safe_html(fname)}"
                    f"</code>"
                ),
                3
            )

        else:

            bot.answer_callback_query(
                call.id,
                "❌ Script not running"
            )

        return


# ============================================================
# RESTORE ALL SCRIPTS
# ============================================================

def restore_all():

    load_data()

    print(
        "🔄 Restoring scripts..."
    )

    for uid, data in users.items():

        if (
            uid != OWNER_ID
            and not data.get(
                "approved",
                False
            )
        ):
            continue

        folder = user_folder(uid)

        for f in data.get(
            "files",
            []
        ):

            if f.endswith(".py"):

                path = os.path.join(
                    folder,
                    f
                )

                if os.path.exists(path):

                    start_script(
                        uid,
                        path
                    )

    print(
        "✅ System Ready"
    )


# ============================================================
# BOT START
# ============================================================

if __name__ == "__main__":

    print(
        "=================================================="
    )

    print(
        "🔧 SHIVA HOSTING BOT"
    )

    print(
        "=================================================="
    )

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN is not configured!"
        )

        print(
            "Set BOT_TOKEN in Render Environment Variables."
        )

        sys.exit(1)

    restore_all()

    print(
        "SHIVA HOSTING BoT IS RUNNING 🏃"
    )

    bot.infinity_polling(
        skip_pending=True,
        timeout=60,
        long_polling_timeout=60
    )
