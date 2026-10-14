# CREDIT - @Mrdk_Sharma_07
# MAIN CHANNEL - @Mrdk_Sharma_07

import os
import sys
import time
import json
import shutil
import zipfile
import subprocess
import threading
import html
import psutil
from datetime import datetime
from flask import Flask

import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# ============================================================
# FLASK KEEP-ALIVE SERVER (FIXES RENDER "NO PORT DETECTED")
# ============================================================

app = Flask(__name__)

@app.route("/")
def home():
    return "DK HOSTING BOT IS LIVE AND RUNNING!", 200

@app.route("/health")
def health():
    return {"status": "ok", "service": "DK HOSTING", "credit": "DK"}, 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ============================================================
# BOT CONFIG
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
try:
    OWNER_ID = int(os.getenv("OWNER_ID", "8753914631").strip() or "0")
except ValueError:
    OWNER_ID = 0

STORAGE_DIR = "user_files"
UPLOAD_DIR = os.path.join(STORAGE_DIR, "uplo556ads")
DATA_FILE = os.path.join(STORAGE_DIR, "users.json")

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# ============================================================
# GLOBALS
# ============================================================

users = {}
active_scripts = {}
logs_store = {}
admin_states = {}  # Tracks admin actions like broadcast or custom pip install

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
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'


def safe_html(value):
    return html.escape(str(value), quote=False)


def premium_header(title, emoji_id=PE_CROWN, fallback="👑"):
    return f"{pe(emoji_id, fallback)} <b>{safe_html(title)}</b>"


# ============================================================
# TELEGRAM BOT INIT
# ============================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None, threaded=True)


# ============================================================
# DATA PERSISTENCE
# ============================================================

def save_data():
    try:
        temp_file = DATA_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
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
            except Exception:
                continue

            if not isinstance(value, dict):
                value = {}

            value.setdefault("files", [])
            value.setdefault("approved", uid == OWNER_ID)
            value.setdefault("rejected", False)
            value.setdefault("file_limit", 2)
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
            "rejected": False,
            "file_limit": 2
        }
        save_data()
    else:
        users[uid].setdefault("files", [])
        users[uid].setdefault("approved", uid == OWNER_ID)
        users[uid].setdefault("rejected", False)
        users[uid].setdefault("file_limit", 2)
        if uid == OWNER_ID and not users[uid]["approved"]:
            users[uid]["approved"] = True
            save_data()


def is_owner(uid):
    return OWNER_ID != 0 and uid == OWNER_ID


def is_approved(uid):
    if is_owner(uid):
        return True
    ensure_user(uid)
    return users[uid].get("approved", False)


def approval_buttons(uid):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{uid}"),
        InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{uid}")
    )
    return markup


def send_approval_request(message):
    if OWNER_ID == 0:
        return

    uid = message.from_user.id
    first_name = message.from_user.first_name or "Unknown"
    username = message.from_user.username
    username_text = f"@{username}" if username else "No username"

    text = (
        f"{pe(PE_ADMIN, '👑')} <b>NEW USER APPROVAL - DK HOSTING</b>\n\n"
        f"{pe(PE_USER, '👤')} <b>Name:</b> {safe_html(first_name)}\n"
        f"{pe(PE_PHONE, '🆔')} <b>User ID:</b> <code>{uid}</code>\n"
        f"{pe(PE_BOT, '🤖')} <b>Username:</b> {safe_html(username_text)}\n\n"
        f"{pe(PE_WARNING, '⚠️')} <b>Status:</b> Pending Approval"
    )

    try:
        bot.send_message(
            OWNER_ID,
            text,
            reply_markup=approval_buttons(uid),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Approval notification error: {e}")


def approval_required(message):
    uid = message.from_user.id
    if is_owner(uid) or is_approved(uid):
        return False

    ensure_user(uid)
    bot.reply_to(
        message,
        (
            f"{pe(PE_LOCK, '🔐')} <b>ACCESS PENDING</b>\n\n"
            f"{pe(PE_ADMIN, '👑')} Your account is waiting for <b>Owner Approval</b>.\n\n"
            f"{pe(PE_STAR, '⭐')} Please wait until the owner approves your account.\n"
            f"<b>Credit:</b> DK"
        ),
        parse_mode="HTML"
    )
    return True


# ============================================================
# OWNER NOTIFICATION
# ============================================================

def notify_owner(text, index=0):
    if OWNER_ID == 0:
        return
    try:
        emoji_id = PREMIUM_EMOJI_IDS[index % len(PREMIUM_EMOJI_IDS)]
        bot.send_message(
            OWNER_ID,
            f"{pe(emoji_id, '🔔')} {text}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Owner notification error: {e}")


# ============================================================
# UTILITIES
# ============================================================

def uptime():
    seconds = int(time.time() - bot_start_time)
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m {seconds % 60}s"


def user_folder(uid):
    path = os.path.join(UPLOAD_DIR, str(uid))
    os.makedirs(path, exist_ok=True)
    return path


def get_system_info():
    cpu_freq = psutil.cpu_freq()
    cpu_ghz = (cpu_freq.current / 1000) if cpu_freq else 0
    ram = psutil.virtual_memory()
    total_ram_gb = ram.total / (1024 ** 3)
    free_ram_gb = ram.available / (1024 ** 3)
    return cpu_ghz, total_ram_gb, free_ram_gb


def install_requirements(folder):
    req_file = os.path.join(folder, "requirements.txt")
    if os.path.exists(req_file):
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", req_file]
            )
        except Exception as e:
            print(f"Requirements install error: {e}")


# ============================================================
# SCRIPT RUNNING
# ============================================================

def stop_user_script(user_id, file_path):
    abs_path = os.path.abspath(file_path)
    proc = active_scripts.get(user_id, {}).get(abs_path)
    if proc:
        try:
            proc.kill()
        except Exception:
            pass
        active_scripts[user_id].pop(abs_path, None)
        return True
    return False


def run_script_thread(user_id, file_path):
    abs_path = os.path.abspath(file_path)
    script_dir = os.path.dirname(abs_path)

    # Stop previous instance if already running
    stop_user_script(user_id, abs_path)

    try:
        proc = subprocess.Popen(
            [sys.executable, abs_path],
            cwd=script_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        active_scripts.setdefault(user_id, {})[abs_path] = proc
        logs_store.setdefault(user_id, {})[abs_path] = []

        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if line:
                logs_store[user_id][abs_path].append(line.strip())
                logs_store[user_id][abs_path] = logs_store[user_id][abs_path][-50:]

        proc.wait()

    except Exception as e:
        logs_store.setdefault(user_id, {}).setdefault(abs_path, []).append(f"Error: {e}")
        print(f"Error in script {abs_path}: {e}")

    finally:
        if user_id in active_scripts:
            if active_scripts[user_id].get(abs_path) == proc:
                active_scripts[user_id].pop(abs_path, None)


def start_script(user_id, file_path):
    thread = threading.Thread(
        target=run_script_thread,
        args=(user_id, file_path),
        daemon=True
    )
    thread.start()


# ============================================================
# INSTALLATION
# ============================================================

def live_install(cmd_list, chat_id, message_id, description):
    try:
        proc = subprocess.Popen(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        output_lines = []
        last_edit = 0

        while True:
            line = proc.stdout.readline()
            if line:
                output_lines.append(line.rstrip())
                if len(output_lines) > 8:
                    output_lines = output_lines[-8:]

                now = time.time()
                if now - last_edit > 1.5:
                    live_text = "\n".join(output_lines)
                    try:
                        bot.edit_message_text(
                            (
                                f"{pe(PE_UPLOAD, '📥')} <b>{safe_html(description)}...</b>\n"
                                f"<pre>{safe_html(live_text)}</pre>"
                            ),
                            chat_id=chat_id,
                            message_id=message_id,
                            parse_mode="HTML"
                        )
                        last_edit = now
                    except Exception:
                        pass

            if not line and proc.poll() is not None:
                break

        full_output = "\n".join(output_lines[-20:]) or "Completed."

        if proc.returncode == 0:
            bot.edit_message_text(
                (
                    f"{pe(PE_CHECK, '✅')} <b>{safe_html(description)} installed!</b>\n\n"
                    f"<pre>{safe_html(full_output)}</pre>"
                ),
                chat_id=chat_id,
                message_id=message_id,
                parse_mode="HTML"
            )
        else:
            bot.edit_message_text(
                (
                    f"{pe(PE_CROSS, '❌')} <b>Installation Failed</b>\n\n"
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
                    f"{pe(PE_CROSS, '❌')} <b>Exception</b>\n\n"
                    f"<code>{safe_html(e)}</code>"
                ),
                chat_id=chat_id,
                message_id=message_id,
                parse_mode="HTML"
            )
        except Exception:
            pass


def install_recommended_packages(chat_id, message_id):
    total = len(RECOMMENDED_PACKAGES)
    for idx, pkg in enumerate(RECOMMENDED_PACKAGES, start=1):
        live_install(
            [sys.executable, "-m", "pip", "install", pkg],
            chat_id,
            message_id,
            f"Installing {pkg} ({idx}/{total})"
        )

    live_install(
        [sys.executable, "-m", "pip", "install", "--no-deps", PYTG_CALLS_PACKAGE],
        chat_id,
        message_id,
        "pytgcalls (GitHub)"
    )


# ============================================================
# MAIN KEYBOARD & ADMIN PANEL MARKUP
# ============================================================

def control_buttons(uid=None):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)

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
        KeyboardButton("⚙️ Recommended Install")
    )

    if uid and is_owner(uid):
        markup.row(
            KeyboardButton("👑 Admin Panel")
        )

    return markup


def admin_panel_markup():
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("👥 All Users", callback_data="admin_users"),
        InlineKeyboardButton("⏳ Pending Users", callback_data="admin_pending")
    )
    markup.row(
        InlineKeyboardButton("🟢 Running Scripts", callback_data="admin_running"),
        InlineKeyboardButton("🛑 Stop All Scripts", callback_data="admin_stop_all")
    )
    markup.row(
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        InlineKeyboardButton("📦 Pip Install", callback_data="admin_pip")
    )
    return markup


def get_admin_panel_text():
    total_users = len(users)
    approved_users = sum(1 for u in users.values() if u.get("approved", False))
    pending_users = sum(
        1 for u in users.values()
        if not u.get("approved", False) and not u.get("rejected", False)
    )
    total_files = sum(len(u.get("files", [])) for u in users.values())
    running_scripts = sum(len(active_scripts.get(u_id, {})) for u_id in users)

    return (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃ {pe(PE_ADMIN, '👑')} <b>DK HOSTING ADMIN PANEL</b> ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"👥 <b>Total Users:</b> <code>{total_users}</code>\n"
        f"✅ <b>Approved Users:</b> <code>{approved_users}</code>\n"
        f"⏳ <b>Pending Users:</b> <code>{pending_users}</code>\n"
        f"📁 <b>Total Uploaded Files:</b> <code>{total_files}</code>\n"
        f"🟢 <b>Active Scripts:</b> <code>{running_scripts}</code>\n"
        f"⏱️ <b>Uptime:</b> <code>{uptime()}</code>\n\n"
        f"✨ <b>Credit:</b> DK"
    )


# ============================================================
# START & ADMIN COMMANDS
# ============================================================

@bot.message_handler(commands=["start"])
def start_command(message):
    uid = message.from_user.id
    first_name = message.from_user.first_name or "User"
    is_new = uid not in users

    ensure_user(uid)

    if is_owner(uid):
        users[uid]["approved"] = True
        users[uid]["rejected"] = False
        save_data()

    if is_new and not is_owner(uid):
        send_approval_request(message)
        bot.send_message(
            uid,
            (
                f"{pe(PE_LOCK, '🔐')} <b>ACCESS REQUESTED</b>\n\n"
                f"{pe(PE_USER, '👤')} Welcome, <b>{safe_html(first_name)}</b>!\n\n"
                f"{pe(PE_ADMIN, '👑')} Your access request has been sent to the owner.\n\n"
                f"{pe(PE_STAR, '⭐')} <b>Please wait for approval.</b>\n"
                f"💎 <b>Powered by:</b> DK HOSTING"
            ),
            parse_mode="HTML"
        )
        return

    if not is_approved(uid):
        bot.send_message(
            uid,
            (
                f"{pe(PE_LOCK, '🔐')} <b>ACCESS PENDING</b>\n\n"
                f"Your account is waiting for <b>Owner Approval</b>.\n\n"
                f"{pe(PE_STAR, '⭐')} Please wait.\n"
                f"💎 <b>Powered by:</b> DK HOSTING"
            ),
            parse_mode="HTML"
        )
        return

    welcome = (
        f"┏━━━━━━━━━━━━━━━━━━━━━━━━┓\n"
        f"┃ {pe(PE_ROCKET, '🚀')} <b>DK HOSTING</b> ┃\n"
        f"┃ <b>VERSION 0.3 | CREDIT: DK</b> ┃\n"
        f"┗━━━━━━━━━━━━━━━━━━━━━━━━┛\n\n"
        f"{pe(PE_GIFT, '👤')} <b>Wᴇʟᴄᴏᴍᴇ</b> {safe_html(first_name)}!\n\n"
        f"{pe(PE_PHONE, '🆔')} <b>Uꜱᴇʀ ID:</b> <code>{uid}</code>\n\n"
        f"{pe(PE_FOLDER, '📁')} <b>Fɪʟᴇꜱ:</b> {len(users[uid]['files'])}\n\n"
        f"{pe(PE_STAR, '⚡')} <b>Fᴇᴀᴛᴜʀᴇꜱ:</b>\n"
        f"• {pe(PE_CHECK, '✅')} Aᴜᴛᴏ-Rᴇᴄᴏᴠᴇʀʏ Sʏꜱᴛᴇᴍ\n"
        f"• {pe(PE_BOT, '🤖')} Pʏᴛʜᴏɴ / Zɪᴘ / Tхᴛ Sᴜᴘᴘᴏʀᴛ\n"
        f"• {pe(PE_DIAMOND, '💎')} Pʀᴇᴍɪᴜᴍ Eᴍᴏᴊɪ Sʏꜱᴛᴇᴍ\n"
        f"• {pe(PE_CROWN, '👑')} Dᴇᴠᴇʟᴏᴘᴇʀ & Cʀᴇᴅɪᴛ: <b>DK</b>\n\n"
        f"Uꜱᴇ ᴛʜᴇ Bᴜᴛᴛᴏɴs Bᴇʟᴏᴡ."
    )

    bot.send_message(
        uid,
        welcome,
        reply_markup=control_buttons(uid),
        parse_mode="HTML"
    )

    if not is_owner(uid):
        notify_owner(
            f"<b>User Started Bot</b>\n"
            f"👤 <code>{uid}</code>\n"
            f"Name: {safe_html(first_name)}",
            0
        )


@bot.message_handler(commands=["admin"])
def admin_command(message):
    uid = message.from_user.id
    if not is_owner(uid):
        bot.reply_to(
            message,
            f"{pe(PE_CROSS, '❌')} <b>Access Denied! Owner Only.</b>",
            parse_mode="HTML"
        )
        return

    bot.send_message(
        uid,
        get_admin_panel_text(),
        reply_markup=admin_panel_markup(),
        parse_mode="HTML"
    )


# ============================================================
# TEXT / CONTROL BUTTON HANDLER
# ============================================================

@bot.message_handler(func=lambda message: True, content_types=["text"])
def control_handler(message):
    uid = message.from_user.id
    text = (message.text or "").strip()

    ensure_user(uid)

    # Check if Owner is in an interactive Admin State (Broadcast / Pip Install)
    if is_owner(uid) and uid in admin_states:
        state = admin_states.pop(uid)

        if text.lower() == "/cancel":
            bot.reply_to(message, "✅ Action cancelled.")
            return

        if state == "broadcast":
            sent = 0
            failed = 0
            for target_uid in list(users.keys()):
                try:
                    bot.send_message(
                        target_uid,
                        f"📢 <b>ANNOUNCEMENT FROM DK HOSTING</b>\n\n{safe_html(text)}",
                        parse_mode="HTML"
                    )
                    sent += 1
                except Exception:
                    failed += 1
            bot.reply_to(
                message,
                f"✅ <b>Broadcast Completed!</b>\nSent: <code>{sent}</code> | Failed: <code>{failed}</code>",
                parse_mode="HTML"
            )
            return

        elif state == "pip_install":
            msg = bot.reply_to(
                message,
                f"📥 <b>Installing <code>{safe_html(text)}</code>...</b>",
                parse_mode="HTML"
            )
            threading.Thread(
                target=live_install,
                args=(
                    [sys.executable, "-m", "pip", "install", text],
                    message.chat.id,
                    msg.message_id,
                    f"Package {text}"
                ),
                daemon=True
            ).start()
            return

    if approval_required(message):
        return

    user_data = users[uid]

    # --------------------------------------------------------
    # UPLOAD BUTTON
    # --------------------------------------------------------
    if text.startswith("🌏"):
        limit = "Unlimited (Owner)" if is_owner(uid) else user_data.get("file_limit", 2)
        bot.reply_to(
            message,
            (
                f"{pe(PE_UPLOAD, '📤')} <b>UPLOAD YOUR FILES</b>\n\n"
                f"Send any of the following files directly to this chat:\n"
                f"• <code>.py</code> (Python Script - Auto Runs)\n"
                f"• <code>.txt</code> (requirements.txt - Auto Installs)\n"
                f"• <code>.zip</code> (Project Archive - Auto Extracts)\n\n"
                f"📁 <b>Your Current Files:</b> <code>{len(user_data['files'])} / {limit}</code>\n"
                f"👑 <b>DK HOSTING</b>"
            ),
            parse_mode="HTML"
        )

    # --------------------------------------------------------
    # MY FILES
    # --------------------------------------------------------
    elif text.startswith("📁"):
        files = user_data["files"]
        if not files:
            bot.reply_to(
                message,
                f"{pe(PE_CROSS, '❌')} <b>No files uploaded yet. Send a .py or .zip file!</b>",
                parse_mode="HTML"
            )
            return

        buttons = [
            [InlineKeyboardButton(f"📄 {f}", callback_data=f"file_{f}")]
            for f in files
        ]

        bot.reply_to(
            message,
            f"{pe(PE_FOLDER, '📁')} <b>𝐘𝐨𝐮𝐫 𝐅𝐢𝐥𝐞𝐬 (DK HOSTING):</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )

    # --------------------------------------------------------
    # SPEED
    # --------------------------------------------------------
    elif text.startswith("⚡"):
        start_time = time.time()
        time.sleep(0.05)
        processing_time = time.time() - start_time
        cpu_ghz, total_ram_gb, free_ram_gb = get_system_info()

        bot.reply_to(
            message,
            (
                f"{pe(PE_FIRE, '⚡')} <b>DK HOSTING SPEED</b>\n\n"
                f"⏱️ <b>Response:</b> {round(processing_time, 4)} sec\n\n"
                f"⚙️ <b>CPU:</b> {round(cpu_ghz, 2)} GHz\n"
                f"💾 <b>RAM:</b> {round(total_ram_gb, 2)} GB\n"
                f"🟢 <b>FREE:</b> {round(free_ram_gb, 2)} GB\n\n"
                f"👑 <b>Credit:</b> DK"
            ),
            parse_mode="HTML"
        )

    # --------------------------------------------------------
    # RESTART
    # --------------------------------------------------------
    elif text.startswith("🔄"):
        if uid in active_scripts:
            for p in list(active_scripts[uid].values()):
                try:
                    p.kill()
                except Exception:
                    pass
            active_scripts[uid] = {}

        folder = user_folder(uid)
        restarted_count = 0
        for fname in user_data["files"]:
            if fname.endswith(".py"):
                path = os.path.join(folder, fname)
                if os.path.exists(path):
                    start_script(uid, path)
                    restarted_count += 1

        bot.reply_to(
            message,
            (
                f"{pe(PE_ROCKET, '🔄')} <b>All your scripts ({restarted_count}) have been restarted!</b>"
            ),
            parse_mode="HTML"
        )

    # --------------------------------------------------------
    # STOP
    # --------------------------------------------------------
    elif text.startswith("⏹"):
        if uid in active_scripts:
            for p in list(active_scripts[uid].values()):
                try:
                    p.kill()
                except Exception:
                    pass
            active_scripts[uid] = {}

        bot.reply_to(
            message,
            f"{pe(PE_SHIELD, '⏹')} <b>Stopped all your running scripts.</b>",
            parse_mode="HTML"
        )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------
    elif text.startswith("🚀"):
        total_users = len(users)
        total_files = sum(len(u.get("files", [])) for u in users.values() if u)
        running_scripts = sum(len(active_scripts.get(u_id, {})) for u_id in users)
        approved_users = sum(1 for u in users.values() if u.get("approved", False))
        pending_users = sum(
            1 for u in users.values()
            if not u.get("approved", False) and not u.get("rejected", False)
        )

        uptime_seconds = (datetime.now() - START_TIME).total_seconds()
        hours, remainder = divmod(int(uptime_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)

        bot.reply_to(
            message,
            (
                f"📊 <b>DK HOSTING LIVE STATISTICS</b>\n\n"
                f"👥 <b>Total Users:</b> {total_users}\n"
                f"✅ <b>Approved Users:</b> {approved_users}\n"
                f"⏳ <b>Pending Users:</b> {pending_users}\n"
                f"📁 <b>Total Files:</b> {total_files}\n"
                f"🟢 <b>Running Scripts:</b> {running_scripts}\n"
                f"🔒 <b>Bot Status:</b> {pe(PE_CHECK, '🟢')} <b>ONLINE</b>\n\n"
                f"⏱️ <b>Uptime:</b> {hours}h {minutes}m {seconds}s\n"
                f"👑 <b>Credit:</b> DK"
            ),
            parse_mode="HTML"
        )

    # --------------------------------------------------------
    # RECOMMENDED INSTALL
    # --------------------------------------------------------
    elif text.startswith("⚙️"):
        msg = bot.reply_to(
            message,
            f"{pe(PE_SETTINGS, '⚙️')} <b>Starting Recommended Packages Installation...</b>",
            parse_mode="HTML"
        )
        threading.Thread(
            target=install_recommended_packages,
            args=(message.chat.id, msg.message_id),
            daemon=True
        ).start()

    # --------------------------------------------------------
    # ADMIN PANEL BUTTON
    # --------------------------------------------------------
    elif text.startswith("👑"):
        if not is_owner(uid):
            bot.reply_to(
                message,
                f"{pe(PE_CROSS, '❌')} <b>Owner only!</b>",
                parse_mode="HTML"
            )
            return

        bot.send_message(
            uid,
            get_admin_panel_text(),
            reply_markup=admin_panel_markup(),
            parse_mode="HTML"
        )


# ============================================================
# DOCUMENT / FILE HANDLER
# ============================================================

@bot.message_handler(content_types=["document"])
def document_handler(message):
    uid = message.from_user.id
    ensure_user(uid)

    if approval_required(message):
        return

    user_data = users[uid]
    file_limit = user_data.get("file_limit", 2)

    if not is_owner(uid) and len(user_data["files"]) >= file_limit:
        bot.reply_to(
            message,
            (
                f"{pe(PE_WARNING, '⚠️')} <b>You have reached the limit of {file_limit} files.</b>\n\n"
                f"Delete an old file from <b>📁 My Files</b> or contact the owner (DK) for more."
            ),
            parse_mode="HTML"
        )
        return

    doc = message.document
    filename = doc.file_name

    if not filename.lower().endswith((".py", ".zip", ".txt")):
        bot.reply_to(
            message,
            f"{pe(PE_CROSS, '❌')} <b>Only .py, .zip and .txt files are allowed.</b>",
            parse_mode="HTML"
        )
        return

    folder = user_folder(uid)
    save_path = os.path.join(folder, filename)

    msg = bot.reply_to(
        message,
        f"{pe(PE_UPLOAD, '⬇️')} <b>Downloading {safe_html(filename)}...</b>",
        parse_mode="HTML"
    )

    try:
        file_info = bot.get_file(doc.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(save_path, "wb") as f:
            f.write(downloaded_file)
    except Exception as e:
        bot.edit_message_text(
            f"{pe(PE_CROSS, '❌')} <b>Download failed.</b>\n\n<code>{safe_html(e)}</code>",
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode="HTML"
        )
        return

    if filename not in user_data["files"]:
        user_data["files"].append(filename)
        save_data()

    # ZIP FILE
    if filename.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(save_path, "r") as zip_ref:
                zip_ref.extractall(folder)
                extracted_names = zip_ref.namelist()

            for ext_f in extracted_names:
                if ext_f.endswith(".py") and "/" not in ext_f and "\\" not in ext_f:
                    if ext_f not in user_data["files"]:
                        user_data["files"].append(ext_f)
            save_data()

            install_requirements(folder)

            bot.edit_message_text(
                f"{pe(PE_CHECK, '📦')} <b>ZIP extracted & requirements checked successfully!</b>",
                chat_id=message.chat.id,
                message_id=msg.message_id,
                parse_mode="HTML"
            )
        except Exception as e:
            bot.edit_message_text(
                f"{pe(PE_CROSS, '❌')} <b>ZIP extraction failed.</b>\n\n<code>{safe_html(e)}</code>",
                chat_id=message.chat.id,
                message_id=msg.message_id,
                parse_mode="HTML"
            )

    # TXT / REQUIREMENTS
    elif filename.lower().endswith(".txt"):
        bot.edit_message_text(
            f"{pe(PE_SETTINGS, '⚙️')} <b>Installing requirements from {safe_html(filename)}...</b>",
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode="HTML"
        )
        threading.Thread(
            target=live_install,
            args=(
                [sys.executable, "-m", "pip", "install", "-r", save_path],
                message.chat.id,
                msg.message_id,
                f"Requirements ({filename})"
            ),
            daemon=True
        ).start()

    # PYTHON FILE
    elif filename.lower().endswith(".py"):
        start_script(uid, save_path)
        bot.edit_message_text(
            (
                f"{pe(PE_ROCKET, '⚡')} <b>Started <code>{safe_html(filename)}</code> on DK HOSTING!</b>\n"
                f"Use <b>📁 My Files</b> to check logs or stop it."
            ),
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode="HTML"
        )

    notify_owner(
        (
            f"<b>File Uploaded</b>\n"
            f"{pe(PE_USER, '👤')} User: <code>{uid}</code>\n"
            f"{pe(PE_FOLDER, '📁')} File: <code>{safe_html(filename)}</code>"
        ),
        1
    )


# ============================================================
# CALLBACK QUERY HANDLER
# ============================================================

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    uid = call.from_user.id
    ensure_user(uid)
    data = call.data or ""

    # --------------------------------------------------------
    # APPROVE USER
    # --------------------------------------------------------
    if data.startswith("approve_"):
        if not is_owner(uid):
            bot.answer_callback_query(call.id, "❌ Owner only!")
            return

        try:
            target_id = int(data.split("_", 1)[1])
        except Exception:
            bot.answer_callback_query(call.id, "❌ Invalid user ID.")
            return

        ensure_user(target_id)
        users[target_id]["approved"] = True
        users[target_id]["rejected"] = False
        save_data()

        bot.answer_callback_query(call.id, "✅ User Approved!")

        try:
            bot.edit_message_text(
                (
                    f"{pe(PE_APPROVE, '✅')} <b>USER APPROVED</b>\n\n"
                    f"{pe(PE_USER, '👤')} <b>User ID:</b> <code>{target_id}</code>\n\n"
                    f"{pe(PE_ADMIN, '👑')} Approved by Owner (DK)."
                ),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
        except Exception:
            pass

        try:
            bot.send_message(
                target_id,
                (
                    f"{pe(PE_GIFT, '🎁')} <b>ACCESS APPROVED!</b>\n\n"
                    f"{pe(PE_CHECK, '✅')} Your account has been approved by the owner.\n\n"
                    f"{pe(PE_ROCKET, '🚀')} You can now use <b>DK HOSTING</b>."
                ),
                reply_markup=control_buttons(target_id),
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"Approval notification error: {e}")
        return

    # --------------------------------------------------------
    # REJECT USER
    # --------------------------------------------------------
    if data.startswith("reject_"):
        if not is_owner(uid):
            bot.answer_callback_query(call.id, "❌ Owner only!")
            return

        try:
            target_id = int(data.split("_", 1)[1])
        except Exception:
            bot.answer_callback_query(call.id, "❌ Invalid user ID.")
            return

        ensure_user(target_id)
        users[target_id]["approved"] = False
        users[target_id]["rejected"] = True
        save_data()

        bot.answer_callback_query(call.id, "❌ User Rejected!")

        try:
            bot.edit_message_text(
                (
                    f"{pe(PE_CROSS, '❌')} <b>USER REJECTED</b>\n\n"
                    f"{pe(PE_USER, '👤')} <b>User ID:</b> <code>{target_id}</code>\n\n"
                    f"{pe(PE_ADMIN, '👑')} Rejected by Owner (DK)."
                ),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
        except Exception:
            pass

        try:
            bot.send_message(
                target_id,
                (
                    f"{pe(PE_CROSS, '❌')} <b>ACCESS REJECTED</b>\n\n"
                    f"Your request was rejected by the owner."
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    # --------------------------------------------------------
    # ADMIN PANEL CALLBACKS
    # --------------------------------------------------------
    if data.startswith("admin_"):
        if not is_owner(uid):
            bot.answer_callback_query(call.id, "❌ Owner only!")
            return

        if data == "admin_home":
            bot.edit_message_text(
                get_admin_panel_text(),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=admin_panel_markup(),
                parse_mode="HTML"
            )
            return

        elif data == "admin_users":
            markup = InlineKeyboardMarkup()
            for u_id, u_info in list(users.items())[:25]:
                status_icon = "✅" if u_info.get("approved") else ("❌" if u_info.get("rejected") else "⏳")
                markup.row(
                    InlineKeyboardButton(
                        f"{status_icon} User {u_id} ({len(u_info.get('files', []))} files)",
                        callback_data=f"admin_uview_{u_id}"
                    )
                )
            markup.row(InlineKeyboardButton("⬅ Back to Admin Panel", callback_data="admin_home"))
            bot.edit_message_text(
                "👥 <b>ALL USERS LIST (Click to Manage):</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML"
            )
            return

        elif data.startswith("admin_uview_"):
            target_id = int(data.split("_")[2])
            ensure_user(target_id)
            u_info = users[target_id]
            status = "Approved ✅" if u_info.get("approved") else ("Rejected ❌" if u_info.get("rejected") else "Pending ⏳")
            running_cnt = len(active_scripts.get(target_id, {}))

            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{target_id}"),
                InlineKeyboardButton("❌ Block/Reject", callback_data=f"reject_{target_id}")
            )
            markup.row(
                InlineKeyboardButton("➕ Limit +2", callback_data=f"admin_limit_{target_id}"),
                InlineKeyboardButton("🛑 Stop Scripts", callback_data=f"admin_ustop_{target_id}")
            )
            markup.row(InlineKeyboardButton("⬅ Back to Users", callback_data="admin_users"))

            bot.edit_message_text(
                (
                    f"👤 <b>USER MANAGEMENT</b>\n\n"
                    f"🆔 <b>User ID:</b> <code>{target_id}</code>\n"
                    f"📌 <b>Status:</b> {status}\n"
                    f"📁 <b>Files:</b> <code>{len(u_info.get('files', []))} / {u_info.get('file_limit', 2)}</code>\n"
                    f"🟢 <b>Running Scripts:</b> <code>{running_cnt}</code>"
                ),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML"
            )
            return

        elif data.startswith("admin_limit_"):
            target_id = int(data.split("_")[2])
            ensure_user(target_id)
            users[target_id]["file_limit"] = users[target_id].get("file_limit", 2) + 2
            save_data()
            bot.answer_callback_query(call.id, f"✅ Limit increased to {users[target_id]['file_limit']}!")
            return

        elif data.startswith("admin_ustop_"):
            target_id = int(data.split("_")[2])
            if target_id in active_scripts:
                for p in list(active_scripts[target_id].values()):
                    try:
                        p.kill()
                    except Exception:
                        pass
                active_scripts[target_id] = {}
            bot.answer_callback_query(call.id, "🛑 Stopped user's running scripts!")
            return

        elif data == "admin_pending":
            pending_list = [
                u_id for u_id, u_info in users.items()
                if not u_info.get("approved") and not u_info.get("rejected")
            ]
            markup = InlineKeyboardMarkup()
            for u_id in pending_list[:20]:
                markup.row(
                    InlineKeyboardButton(f"✅ Approve {u_id}", callback_data=f"approve_{u_id}"),
                    InlineKeyboardButton(f"❌ Reject {u_id}", callback_data=f"reject_{u_id}")
                )
            markup.row(InlineKeyboardButton("⬅ Back", callback_data="admin_home"))
            bot.edit_message_text(
                f"⏳ <b>PENDING APPROVAL USERS ({len(pending_list)}):</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML"
            )
            return

        elif data == "admin_running":
            lines = ["🟢 <b>ACTIVE RUNNING SCRIPTS:</b>\n"]
            count = 0
            for u_id, scripts_dict in active_scripts.items():
                for path in scripts_dict:
                    count += 1
                    lines.append(f"• User <code>{u_id}</code>: <code>{safe_html(os.path.basename(path))}</code>")
            if count == 0:
                lines.append("No scripts currently running.")

            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("⬅ Back", callback_data="admin_home"))
            bot.edit_message_text(
                "\n".join(lines),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML"
            )
            return

        elif data == "admin_stop_all":
            for u_id in list(active_scripts.keys()):
                for p in list(active_scripts[u_id].values()):
                    try:
                        p.kill()
                    except Exception:
                        pass
                active_scripts[u_id] = {}
            bot.answer_callback_query(call.id, "🛑 All scripts across the server stopped!")
            bot.edit_message_text(
                get_admin_panel_text(),
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=admin_panel_markup(),
                parse_mode="HTML"
            )
            return

        elif data == "admin_broadcast":
            admin_states[uid] = "broadcast"
            bot.answer_callback_query(call.id)
            bot.send_message(
                uid,
                "📢 <b>Send the message you want to broadcast to all users</b> (or send /cancel):",
                parse_mode="HTML"
            )
            return

        elif data == "admin_pip":
            admin_states[uid] = "pip_install"
            bot.answer_callback_query(call.id)
            bot.send_message(
                uid,
                "📦 <b>Send the package name to install via pip</b> (e.g. <code>pyTelegramBotAPI</code>) or /cancel:",
                parse_mode="HTML"
            )
            return

    # --------------------------------------------------------
    # APPROVAL CHECK FOR USER ACTIONS
    # --------------------------------------------------------
    if not is_approved(uid):
        bot.answer_callback_query(call.id, "🔐 Owner approval required.")
        return

    # --------------------------------------------------------
    # FILE DETAILS
    # --------------------------------------------------------
    if data.startswith("file_"):
        filename = data[5:]
        user_data = users.get(uid, {"files": []})

        if filename not in user_data.get("files", []):
            bot.answer_callback_query(call.id, "❌ File not found.")
            return

        user_name = call.from_user.first_name or "User"
        abs_path = os.path.abspath(os.path.join(user_folder(uid), filename))
        running = abs_path in active_scripts.get(uid, {})

        msg = (
            f"{pe(PE_STAR, '⚡')} <b>𝐀𝐜𝐭𝐢𝐨𝐧𝐬 𝐟𝐨𝐫</b>\n"
            f"<code>{safe_html(filename)}</code>\n\n"
            f"{pe(PE_PHONE, '🆔')} <b>𝐔𝐬ᴇʀ ID:</b> <code>{uid}</code>\n"
            f"{pe(PE_USER, '👤')} <b>𝐍ᴀᴍᴇ:</b> <code>{safe_html(user_name)}</code>\n"
            f"{pe(PE_CHECK, '🟢')} <b>𝐑ᴜɴɴɪɴɢ:</b> <code>{'Yes (1)' if running else 'No (0)'}</code>\n"
            f"👑 <b>DK HOSTING</b>"
        )

        buttons = [
            [
                InlineKeyboardButton("▶ Run", callback_data=f"run_{filename}"),
                InlineKeyboardButton("⏹ Stop", callback_data=f"stop_{filename}")
            ],
            [
                InlineKeyboardButton("📜 Logs", callback_data=f"logs_{filename}"),
                InlineKeyboardButton("🗑 Delete", callback_data=f"del_{filename}")
            ],
            [
                InlineKeyboardButton("⬅ Back", callback_data="myfiles")
            ]
        ]

        bot.edit_message_text(
            msg,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=InlineKeyboardMarkup(buttons),
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
                f"{pe(PE_CROSS, '❌')} <b>No files.</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
            return

        buttons = [
            [InlineKeyboardButton(f"📄 {f}", callback_data=f"file_{f}")]
            for f in files
        ]

        bot.edit_message_text(
            f"{pe(PE_FOLDER, '📁')} <b>𝐘𝐨ᴜʀ 𝐅ɪ𝐥ᴇs (DK HOSTING):</b>",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )
        return

    # --------------------------------------------------------
    # RUN FILE
    # --------------------------------------------------------
    if data.startswith("run_"):
        fname = data[4:]
        if fname not in users[uid]["files"]:
            bot.answer_callback_query(call.id, "❌ File not found.")
            return

        path = os.path.join(user_folder(uid), fname)
        if not os.path.exists(path):
            bot.answer_callback_query(call.id, "❌ File not found on disk.")
            return

        if not fname.lower().endswith(".py"):
            bot.answer_callback_query(call.id, "❌ Only Python (.py) files can run.")
            return

        start_script(uid, path)
        bot.answer_callback_query(call.id, f"▶ {fname} started!")

        notify_owner(
            f"<b>Script Started</b>\nUser: <code>{uid}</code>\nFile: <code>{safe_html(fname)}</code>",
            2
        )
        return

    # --------------------------------------------------------
    # STOP FILE
    # --------------------------------------------------------
    if data.startswith("stop_"):
        fname = data[5:]
        path = os.path.join(user_folder(uid), fname)

        if stop_user_script(uid, path):
            bot.answer_callback_query(call.id, f"⏹ {fname} stopped!")
            notify_owner(
                f"<b>Script Stopped</b>\nUser: <code>{uid}</code>\nFile: <code>{safe_html(fname)}</code>",
                3
            )
        else:
            bot.answer_callback_query(call.id, "❌ Script is not running.")
        return

    # --------------------------------------------------------
    # VIEW LOGS
    # --------------------------------------------------------
    if data.startswith("logs_"):
        fname = data[5:]
        abs_path = os.path.abspath(os.path.join(user_folder(uid), fname))
        file_logs = logs_store.get(uid, {}).get(abs_path, [])

        log_text = "\n".join(file_logs[-25:]) if file_logs else "No output logs recorded yet."
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🔄 Refresh Logs", callback_data=f"logs_{fname}"),
            InlineKeyboardButton("⬅ Back", callback_data=f"file_{fname}")
        )

        try:
            bot.edit_message_text(
                f"📜 <b>Logs for <code>{safe_html(fname)}</code>:</b>\n\n<pre>{safe_html(log_text[-3500:])}</pre>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=markup,
                parse_mode="HTML"
            )
        except Exception:
            bot.answer_callback_query(call.id, "Logs unchanged.")
        return

    # --------------------------------------------------------
    # DELETE FILE
    # --------------------------------------------------------
    if data.startswith("del_"):
        fname = data[4:]
        path = os.path.join(user_folder(uid), fname)

        stop_user_script(uid, path)

        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

        if fname in users[uid]["files"]:
            users[uid]["files"].remove(fname)
            save_data()

        bot.answer_callback_query(call.id, f"🗑 {fname} deleted!")

        files = users[uid]["files"]
        if not files:
            bot.edit_message_text(
                f"{pe(PE_CROSS, '❌')} <b>No files remaining.</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="HTML"
            )
        else:
            buttons = [[InlineKeyboardButton(f"📄 {f}", callback_data=f"file_{f}")] for f in files]
            bot.edit_message_text(
                f"{pe(PE_FOLDER, '📁')} <b>𝐘𝐨ᴜʀ 𝐅ɪ𝐥ᴇs (DK HOSTING):</b>",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode="HTML"
            )
        return


# ============================================================
# RESTORE ALL SCRIPTS
# ============================================================

def restore_all():
    load_data()
    print("🔄 Restoring scripts...")

    for uid, data in users.items():
        if not is_owner(uid) and not data.get("approved", False):
            continue

        folder = user_folder(uid)
        for f in data.get("files", []):
            if f.endswith(".py"):
                path = os.path.join(folder, f)
                if os.path.exists(path):
                    start_script(uid, path)

    print("✅ System Ready")


# ============================================================
# BOT START
# ============================================================

if __name__ == "__main__":
    print("==================================================")
    print("🔧 DK HOSTING BOT | CREDIT: DK")
    print("==================================================")

    if not BOT_TOKEN:
        print("❌ BOT_TOKEN is not configured!")
        print("Set BOT_TOKEN in Render Environment Variables.")
        sys.exit(1)

    # 1. Start Flask server in background thread for Render Port Check
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    print("✅ Web Server started for Render Port Binding")

    # 2. Restore user scripts
    restore_all()

    # 3. Remove any previous webhook to prevent 409 Conflict
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception as e:
        print(f"Webhook removal warning: {e}")

    print("DK HOSTING BOT IS RUNNING 🏃")

    bot.infinity_polling(
        skip_pending=True,
        timeout=60,
        long_polling_timeout=60
    )
