import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import json
import os
import random
import time
import datetime
import zoneinfo
from pathlib import Path

# Timezone WIB (UTC+7)
WIB = zoneinfo.ZoneInfo("Asia/Jakarta")

# ===================== CONFIG =====================
PREFIX = "!Kingdoom"
BOT_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
DARK_RED = 0x8B0000

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def load_json(filename, default=None):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(filename, data):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ===================== INTENTS =====================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX + " ", intents=intents, help_command=None, case_insensitive=True)
tree = bot.tree

# ===================== FISHING CONFIG (DYNAMIC) =====================
# Default fishing config - bisa diubah via !Kingdoom setfishing
DEFAULT_FISHING_CONFIG = {
    "rod_price": 100,         # harga rod default
    "fish_list": [
        {"name": "Ikan Lele",      "sell_price": 15,   "luck_chance": 40.0, "rarity": "common",    "emoji": "🐟"},
        {"name": "Ikan Mas",       "sell_price": 25,   "luck_chance": 30.0, "rarity": "common",    "emoji": "🐠"},
        {"name": "Ikan Gurame",    "sell_price": 40,   "luck_chance": 15.0, "rarity": "uncommon",  "emoji": "🐡"},
        {"name": "Ikan Salmon",    "sell_price": 60,   "luck_chance": 8.0,  "rarity": "uncommon",  "emoji": "🐟"},
        {"name": "Ikan Tuna",      "sell_price": 100,  "luck_chance": 3.5,  "rarity": "rare",      "emoji": "🐟"},
        {"name": "Ikan Hiu Kecil", "sell_price": 200,  "luck_chance": 1.5,  "rarity": "rare",      "emoji": "🦈"},
        {"name": "Ikan Duyung",    "sell_price": 500,  "luck_chance": 0.5,  "rarity": "legendary", "emoji": "🧜"},
        {"name": "Ikan Naga",      "sell_price": 1000, "luck_chance": 0.2,  "rarity": "legendary", "emoji": "🐉"},
        {"name": "Sampah",         "sell_price": 0,    "luck_chance": 0.8,  "rarity": "trash",     "emoji": "🗑️"},
        {"name": "Bot Bekas",      "sell_price": 5,    "luck_chance": 0.5,  "rarity": "trash",     "emoji": "🤖"},
    ]
}

def get_fishing_config():
    cfg = load_json("fishing_config.json", None)
    if cfg is None:
        save_json("fishing_config.json", DEFAULT_FISHING_CONFIG)
        return DEFAULT_FISHING_CONFIG
    return cfg

def save_fishing_config(cfg):
    save_json("fishing_config.json", cfg)

def get_fish_list():
    return get_fishing_config()["fish_list"]

def get_rod_price():
    return get_fishing_config().get("rod_price", 100)

RODS = {
    "Pancing Bambu":   {"tier": 1, "price": 50,   "catch_bonus": 1.0, "emoji": "🎋"},
    "Pancing Kayu":    {"tier": 2, "price": 150,  "catch_bonus": 1.3, "emoji": "🪵"},
    "Pancing Besi":    {"tier": 3, "price": 400,  "catch_bonus": 1.7, "emoji": "🔩"},
    "Pancing Karbon":  {"tier": 4, "price": 900,  "catch_bonus": 2.2, "emoji": "⚫"},
    "Pancing Titan":   {"tier": 5, "price": 2000, "catch_bonus": 3.0, "emoji": "🔱"},
    "Pancing Legenda": {"tier": 6, "price": 5000, "catch_bonus": 5.0, "emoji": "⚡"},
}

BAITS = {
    "Cacing Biasa": {"price": 10,  "bonus": 1.0, "emoji": "🪱"},
    "Cacing Gemuk": {"price": 25,  "bonus": 1.5, "emoji": "🐛"},
    "Jangkrik":     {"price": 40,  "bonus": 2.0, "emoji": "🦗"},
    "Udang Kecil":  {"price": 60,  "bonus": 2.5, "emoji": "🦐"},
    "Ikan Kecil":   {"price": 100, "bonus": 3.5, "emoji": "🐟"},
}

SHOP_REWARDS = {
    "Role VIP":          {"price": 500,   "type": "role", "description": "Role VIP eksklusif buat lo"},
    "Role Elite":        {"price": 2000,  "type": "role", "description": "Role Elite super langka"},
    "Role Legend":       {"price": 10000, "type": "role", "description": "Role paling epic di server"},
    "Custom Color Role": {"price": 800,   "type": "role", "description": "Role warna custom buat lo"},
}

# ===================== TEBAK-TEBAKAN =====================
TEBAKAN_LIST = [
    {"soal": "Apa yang selalu datang tapi gak pernah sampe?",                               "jawaban": "besok",       "reward": 20},
    {"soal": "Makin diisi makin ringan, apa tuh?",                                          "jawaban": "balon",       "reward": 25},
    {"soal": "Punya kaki tapi ga bisa jalan, punya lidah tapi ga bisa ngomong. Apa coba?", "jawaban": "sepatu",      "reward": 30},
    {"soal": "Apa yang bisa terbang tapi ga punya sayap?",                                  "jawaban": "waktu",       "reward": 25},
    {"soal": "Makin tua makin pendek, apa itu?",                                            "jawaban": "lilin",       "reward": 20},
    {"soal": "Ada di depan kita tapi ga bisa diliat. Apaan tuh?",                          "jawaban": "masa depan",  "reward": 35},
    {"soal": "Sekali lahir langsung mati. Apa itu?",                                        "jawaban": "korek api",   "reward": 20},
    {"soal": "Semakin banyak diambil, semakin besar. Apaan?",                               "jawaban": "lubang",      "reward": 30},
    {"soal": "Apa yang punya gigi tapi ga bisa gigit?",                                     "jawaban": "sisir",       "reward": 25},
    {"soal": "Terbalik tetap sama. Apa itu?",                                               "jawaban": "angka 8",     "reward": 30},
]

JAWABAN_BENAR_GAUL = [
    "GOKIL LO BRO! Tepat banget, lo emang jago sih! 🔥",
    "YAAMPUN BENERRRR!!! Otaknya encer banget sih wkwkwk 🧠💥",
    "MANTAP JIWA! Lo jawab beneran bro, gaskeun! 🚀",
    "GILAAAK BENER! Lo tuh emang sultan otak ya bestie ✨",
    "SABI BANGET! Jawaban lo pas banget, auto sultan nih! 💯",
    "WOOO BENERRR! Gila sih lo, padahal susah kan? Keren abis! 🎉",
    "ANJIRR BENER! Lo pinter banget sih, respect bro! 👏",
    "GAS POLLLL! Jawaban lo bener, lo emang the best! 🏆",
    "DAGING BANGET! Bener semua, lo emang ga ada lawan! 💪",
    "KEREN ABIS BRO! Gw kagum sama lo, jawaban lo tepat sasaran! 🎯",
]

def get_custom_tebakan():
    return load_json("custom_tebakan.json", [])

def save_custom_tebakan(data):
    save_json("custom_tebakan.json", data)

# ===================== AI CHAT =====================
import aiohttp

async def get_ai_response(question: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "❌ API key belum diset bro! Minta admin set `ANTHROPIC_API_KEY` dulu."

    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "x-api-key": api_key,
    }
    payload = {
        "model": "claude-haiku-4-5",
        "max_tokens": 500,
        "system": (
            "Lo adalah RepublikDooms AI, bot Discord gaul dan nyantai. "
            "Jawab pake bahasa Indonesia gaul, singkat, informatif, dan asik. "
            "Pake singkatan gaul kayak 'btw', 'gw', 'lo', 'bro', 'sis', 'wkwk', dll. "
            "Jangan formal banget, tapi tetep bermanfaat. Max 3 paragraf."
        ),
        "messages": [{"role": "user", "content": question}]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=20)
            ) as resp:
                if resp.status != 200:
                    err_text = await resp.text()
                    return f"❌ API error {resp.status} bro 😅 — {err_text[:80]}"
                data = await resp.json()
                return data["content"][0]["text"]
    except asyncio.TimeoutError:
        return "⏰ Timeout bro, API-nya lagi lambat. Coba lagi ya!"
    except Exception as e:
        return f"❌ Error gak terduga: {str(e)[:80]}"

# ===================== HELPER FUNCTIONS =====================
def get_fishing_data():
    return load_json("fishing.json", {})

def save_fishing_data(data):
    save_json("fishing.json", data)

def get_user_fishing(user_id: str):
    data = get_fishing_data()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "coins": 100,
            "rod": "Pancing Bambu",
            "bait": {"Cacing Biasa": 3},
            "inventory": [],
            "total_catch": 0,
            "last_fish": 0
        }
        save_fishing_data(data)
    return data[uid]

def save_user_fishing(user_id: str, udata: dict):
    data = get_fishing_data()
    data[str(user_id)] = udata
    save_fishing_data(data)

def get_warns():
    return load_json("warns.json", {})

def save_warns(data):
    save_json("warns.json", data)

def get_levels():
    return load_json("levels.json", {})

def save_levels(data):
    save_json("levels.json", data)

def get_config():
    return load_json("config.json", {})

def save_config(data):
    save_json("config.json", data)

def get_autoresponse():
    return load_json("autoresponse.json", {})

def save_autoresponse(data):
    save_json("autoresponse.json", data)

def get_sticky():
    return load_json("sticky.json", {})

def save_sticky(data):
    save_json("sticky.json", data)

def get_giveaways():
    return load_json("giveaways.json", {})

def save_giveaways(data):
    save_json("giveaways.json", data)

def get_tickets():
    return load_json("tickets.json", {"panels": {}, "tickets": {}})

def save_tickets(data):
    save_json("tickets.json", data)

# ===================== PREMIUM SYSTEM =====================
def get_premium_config():
    return load_json("premium_config.json", {
        "webhook_url": "",
        "price": 0,
        "duration_days": 30,
        "features": [],
        "owner_id": ""
    })

def save_premium_config(data):
    save_json("premium_config.json", data)

def get_premium_users():
    return load_json("premium_users.json", {})

def save_premium_users(data):
    save_json("premium_users.json", data)

def is_premium_user(user_id: str) -> bool:
    users = get_premium_users()
    uid = str(user_id)
    if uid not in users:
        return False
    expiry = users[uid].get("expiry", 0)
    if expiry == -1:
        return True  # lifetime
    return time.time() < expiry

def get_premium_expiry_str(user_id: str) -> str:
    users = get_premium_users()
    uid = str(user_id)
    if uid not in users:
        return "Tidak aktif"
    expiry = users[uid].get("expiry", 0)
    if expiry == -1:
        return "Seumur hidup ♾️"
    if time.time() >= expiry:
        return "Sudah kadaluarsa ❌"
    dt = datetime.datetime.fromtimestamp(expiry, tz=WIB)
    return dt.strftime("%d/%m/%Y %H:%M WIB")

def is_bot_owner(ctx_or_interaction) -> bool:
    """Check apakah user adalah owner bot (dari env variable atau config)"""
    owner_id = os.getenv("BOT_OWNER_ID", "")
    if hasattr(ctx_or_interaction, "author"):
        uid = str(ctx_or_interaction.author.id)
    else:
        uid = str(ctx_or_interaction.user.id)
    return uid == owner_id

# ===================== MAINTENANCE SYSTEM =====================
def get_maintenance():
    return load_json("maintenance.json", {
        "active": False,
        "message": "Bot sedang maintenance, mohon tunggu!",
        "end_time": 0,
        "channel_id": ""
    })

def save_maintenance(data):
    save_json("maintenance.json", data)

def is_maintenance() -> bool:
    m = get_maintenance()
    if not m.get("active", False):
        return False
    end_time = m.get("end_time", 0)
    if end_time and end_time > 0 and time.time() > end_time:
        m["active"] = False
        save_maintenance(m)
        return False
    return True

def dark_red_embed(title="", description="", **kwargs):
    em = discord.Embed(title=title, description=description, color=DARK_RED, **kwargs)
    return em

fishing_cooldowns = {}
active_tebakan = {}

# ===================== EVENTS =====================
@bot.event
async def on_ready():
    print(f"✅ {bot.user} udah nyala bro!")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="RepublikDooms | !Kingdoom help")
    )
    try:
        synced = await tree.sync()
        print(f"✅ {len(synced)} slash commands synced!")
    except Exception as e:
        print(f"❌ Sync error: {e}")
    check_giveaways.start()
    check_sticky.start()
    check_maintenance.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = str(message.guild.id) if message.guild else None
    content_lower = message.content.lower().strip()

    # Cek maintenance - blokir semua command kecuali owner
    if is_maintenance() and not is_bot_owner_by_id(message.author.id):
        if message.content.startswith(PREFIX):
            m = get_maintenance()
            em = dark_red_embed(
                "🔧 Bot Maintenance",
                f"{m.get('message', 'Bot sedang maintenance!')}\n\n⏳ Mohon tunggu ya!"
            )
            await message.channel.send(embed=em)
            return

    # Auto response
    if guild_id:
        ar = get_autoresponse()
        if guild_id in ar:
            for trigger, response in ar[guild_id].items():
                if trigger.lower() in content_lower:
                    await message.channel.send(response)
                    break

    # Tebak-tebakan answer check — deteksi jawaban dari pesan text
    if guild_id and guild_id in active_tebakan:
        tb = active_tebakan[guild_id]
        if message.author.id != tb["asker"]:
            jawaban_benar = tb["jawaban"].lower().strip()
            # Cek apakah jawaban tepat (exact match atau contained dalam pesan)
            pesan_clean = content_lower.strip()
            if pesan_clean == jawaban_benar or jawaban_benar in pesan_clean.split():
                udata = get_user_fishing(str(message.author.id))
                reward = tb["reward"]
                udata["coins"] += reward
                save_user_fishing(str(message.author.id), udata)
                gaul_response = random.choice(JAWABAN_BENAR_GAUL)
                em = dark_red_embed(
                    "🎉 BENERRR!!!",
                    f"{gaul_response}\n\n"
                    f"**{message.author.display_name}** jawab bener!\n"
                    f"💰 Dapet **+{reward} koin** cuy!\n"
                    f"✅ Jawaban: **{tb['jawaban'].title()}**\n"
                    f"🪙 Total koin lo: **{udata['coins']}**"
                )
                em.set_thumbnail(url=message.author.display_avatar.url)
                await message.channel.send(embed=em)
                del active_tebakan[guild_id]

    # Leveling
    if guild_id and message.content and not message.content.startswith(PREFIX):
        await handle_leveling(message)

    # Sticky message
    if guild_id:
        sticky_data = get_sticky()
        ch_id = str(message.channel.id)
        if guild_id in sticky_data and ch_id in sticky_data[guild_id]:
            s = sticky_data[guild_id][ch_id]
            s["count"] = s.get("count", 0) + 1
            if s["count"] >= s.get("min_messages", 3):
                s["count"] = 0
                try:
                    old_id = s.get("last_message_id")
                    if old_id:
                        try:
                            old_msg = await message.channel.fetch_message(old_id)
                            await old_msg.delete()
                        except:
                            pass
                    em = dark_red_embed("📌 Sticky Message", s["content"])
                    sent = await message.channel.send(embed=em)
                    s["last_message_id"] = sent.id
                except:
                    pass
            sticky_data[guild_id][ch_id] = s
            save_sticky(sticky_data)

    await bot.process_commands(message)

def is_bot_owner_by_id(user_id) -> bool:
    owner_id = os.getenv("BOT_OWNER_ID", "")
    return str(user_id) == owner_id

async def handle_leveling(message):
    config = get_config()
    gid = str(message.guild.id)
    if gid not in config or not config[gid].get("leveling_enabled", True):
        return
    levels = get_levels()
    uid = str(message.author.id)
    if gid not in levels:
        levels[gid] = {}
    if uid not in levels[gid]:
        levels[gid][uid] = {"xp": 0, "level": 0}
    xp_gain = random.randint(10, 25)
    levels[gid][uid]["xp"] += xp_gain
    needed = (levels[gid][uid]["level"] + 1) * 100
    if levels[gid][uid]["xp"] >= needed:
        levels[gid][uid]["level"] += 1
        levels[gid][uid]["xp"] = 0
        new_level = levels[gid][uid]["level"]
        channel_id = config[gid].get("level_channel")
        ch = message.guild.get_channel(int(channel_id)) if channel_id else message.channel
        em = dark_red_embed(
            "🆙 LEVEL UP GAES!",
            f"Selamat **{message.author.mention}** naik ke level **{new_level}**! 🎉\nTerus aktif ya bro!"
        )
        em.set_thumbnail(url=message.author.display_avatar.url)
        await ch.send(embed=em)
        level_roles = config[gid].get("level_roles", {})
        if str(new_level) in level_roles:
            role = message.guild.get_role(int(level_roles[str(new_level)]))
            if role:
                try:
                    await message.author.add_roles(role)
                    await ch.send(f"🏆 {message.author.mention} dapet role **{role.name}** karena udah level {new_level}!")
                except:
                    pass
    save_levels(levels)

# ===================== TASKS =====================
@tasks.loop(seconds=30)
async def check_giveaways():
    gw_data = get_giveaways()
    now = time.time()
    for gid in list(gw_data.keys()):
        for msg_id in list(gw_data[gid].keys()):
            gw = gw_data[gid][msg_id]
            if gw.get("ended"):
                continue
            if now >= gw["end_time"]:
                guild = bot.get_guild(int(gid))
                if not guild:
                    continue
                ch = guild.get_channel(int(gw["channel_id"]))
                if not ch:
                    continue
                try:
                    msg = await ch.fetch_message(int(msg_id))
                    reaction = discord.utils.get(msg.reactions, emoji="🎉")
                    users = []
                    if reaction:
                        async for u in reaction.users():
                            if not u.bot:
                                users.append(u)
                    if users:
                        winner = random.choice(users)
                        em = dark_red_embed(
                            "🎉 GIVEAWAY SELESAI!",
                            f"**Hadiah:** {gw['prize']}\n**Pemenang:** {winner.mention}\nSelamat ya bestie! 🥳"
                        )
                        await ch.send(embed=em)
                    else:
                        await ch.send("😢 Gak ada yang ikut giveaway, hadiahnya disimpen aja deh...")
                    gw_data[gid][msg_id]["ended"] = True
                except:
                    pass
    save_giveaways(gw_data)

@tasks.loop(seconds=60)
async def check_sticky():
    pass  # handled in on_message

@tasks.loop(seconds=30)
async def check_maintenance():
    """Auto-disable maintenance saat waktu habis"""
    m = get_maintenance()
    if not m.get("active", False):
        return
    end_time = m.get("end_time", 0)
    if end_time and end_time > 0 and time.time() > end_time:
        m["active"] = False
        save_maintenance(m)
        channel_id = m.get("channel_id", "")
        if channel_id:
            for guild in bot.guilds:
                ch = guild.get_channel(int(channel_id))
                if ch:
                    em = dark_red_embed(
                        "✅ Maintenance Selesai!",
                        "Bot sudah kembali normal! Silakan gunakan bot seperti biasa. 🎉"
                    )
                    try:
                        await ch.send(embed=em)
                    except:
                        pass

# ===================== FISHING VIEWS =====================

class FishingMainView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id

    def do_catch(self, uid: str):
        """Logic mancing, return (caught_fish, coins_earned, used_bait, udata)"""
        udata = get_user_fishing(uid)
        rod = RODS.get(udata["rod"], RODS["Pancing Bambu"])
        bait_list = udata.get("bait", {})
        bait_bonus = 1.0
        used_bait = None
        for bname, qty in list(bait_list.items()):
            if qty > 0 and bname in BAITS:
                bait_bonus = BAITS[bname]["bonus"]
                bait_list[bname] -= 1
                if bait_list[bname] <= 0:
                    del bait_list[bname]
                used_bait = bname
                break
        udata["bait"] = bait_list

        fish_pool = get_fish_list()
        weights = []
        for f in fish_pool:
            base_chance = f.get("luck_chance", 10.0)
            # Trash tidak kena bonus rod/bait
            if f.get("rarity") == "trash":
                weights.append(base_chance)
            else:
                weights.append(base_chance * rod["catch_bonus"] * bait_bonus)

        caught = random.choices(fish_pool, weights=weights, k=1)[0]
        coins_earned = int(caught.get("sell_price", caught.get("value", 0)) * rod["catch_bonus"] * bait_bonus)
        udata["coins"] += coins_earned
        udata["total_catch"] += 1
        udata["inventory"].append(caught["name"])
        save_user_fishing(uid, udata)
        return caught, coins_earned, used_bait, udata

    def build_catch_embed(self, caught, coins_earned, used_bait, udata, display_name):
        rarity = caught.get("rarity", "common")
        rarity_stars = {"legendary": "⭐⭐⭐", "rare": "⭐⭐", "uncommon": "⭐", "common": "", "trash": "💩"}
        rod_info = RODS.get(udata["rod"], RODS["Pancing Bambu"])
        bait_text = f"🪱 Umpan: {used_bait}" if used_bait else "⚠️ Gak pake umpan!"

        if rarity == "legendary":
            em = discord.Embed(
                title=f"🌟✨ LEGENDARY CATCH! ✨🌟",
                description=(
                    f"**{display_name}** berhasil mendapatkan **{caught['name']}** {caught.get('emoji','')} {rarity_stars[rarity]}\n\n"
                    f"🪙 **+{coins_earned} koin** (Total: {udata['coins']})\n"
                    f"🎣 Rod: {rod_info.get('emoji','')} {udata['rod']}\n"
                    f"{bait_text}\n\n"
                    f"🎊 **WOW! LO DAPET IKAN LEGENDARY! LANGKA BANGET!** 🎊"
                ),
                color=0xFFD700  # Gold color untuk legendary
            )
            em.set_footer(text="⭐ Legendary Fish! Congrats!")
        elif rarity == "rare":
            em = discord.Embed(
                title=f"💎 RARE CATCH! {caught.get('emoji','')}",
                description=(
                    f"**{display_name}** dapet **{caught['name']}** {rarity_stars[rarity]}\n\n"
                    f"🪙 **+{coins_earned} koin** (Total: {udata['coins']})\n"
                    f"🎣 Rod: {rod_info.get('emoji','')} {udata['rod']}\n"
                    f"{bait_text}\n\n"
                    f"✨ **Ikan Rare! Lumayan langka tuh!** ✨"
                ),
                color=0x00BFFF  # Blue untuk rare
            )
        else:
            em = dark_red_embed(
                f"{caught.get('emoji','🐟')} Hasil Mancing!",
                f"**{display_name}** dapet **{caught['name']}** {rarity_stars.get(rarity,'')}\n"
                f"🪙 +{coins_earned} koin (Total: {udata['coins']})\n"
                f"🎣 Rod: {rod_info.get('emoji','')} {udata['rod']}\n"
                f"{bait_text}"
            )
        return em

    @discord.ui.button(label="🎣 Mancing", style=discord.ButtonStyle.danger, row=0)
    async def fish(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Ini bukan mancing lo bro!", ephemeral=True)
            return
        now = time.time()
        uid = str(interaction.user.id)
        if uid in fishing_cooldowns and now - fishing_cooldowns[uid] < 10:
            sisa = round(10 - (now - fishing_cooldowns[uid]))
            await interaction.response.send_message(f"⏳ Sabar bro! **{sisa} detik** lagi. Emang mancing bisa buru-buru? wkwk", ephemeral=True)
            return
        fishing_cooldowns[uid] = now
        caught, coins_earned, used_bait, udata = self.do_catch(uid)
        em = self.build_catch_embed(caught, coins_earned, used_bait, udata, interaction.user.display_name)
        await interaction.response.edit_message(embed=em, view=self)

    @discord.ui.button(label="🎒 Inventori", style=discord.ButtonStyle.secondary, row=0)
    async def inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Lo gak bisa liat inventori orang lain bro! Privasi dong 😤", ephemeral=True)
            return
        udata = get_user_fishing(str(interaction.user.id))
        inv = udata.get("inventory", [])
        inv_count = {}
        for item in inv:
            inv_count[item] = inv_count.get(item, 0) + 1
        inv_text = "\n".join([f"• {k}: x{v}" for k, v in inv_count.items()]) if inv_count else "Inventori kosong bro, ayo mancing dulu!"
        em = dark_red_embed(
            f"🎒 Inventori {interaction.user.display_name}",
            f"**Koin:** {udata['coins']} 🪙\n**Rod:** {udata['rod']}\n**Total Tangkapan:** {udata['total_catch']}\n\n**Ikan:**\n{inv_text}"
        )
        em.add_field(name="🪱 Umpan", value="\n".join([f"{k}: x{v}" for k, v in udata.get('bait', {}).items()]) or "Habis!", inline=True)
        await interaction.response.send_message(embed=em, ephemeral=True)

    @discord.ui.button(label="🏪 Shop", style=discord.ButtonStyle.primary, row=0)
    async def shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Buka shop sendiri bro!", ephemeral=True)
            return
        udata = get_user_fishing(str(interaction.user.id))
        rod_text = "\n".join([f"{v['emoji']} **{k}** - {v['price']} 🪙 (Tier {v['tier']})" for k, v in RODS.items()])
        bait_text = "\n".join([f"{v['emoji']} **{k}** - {v['price']} 🪙" for k, v in BAITS.items()])
        em = dark_red_embed(
            "🏪 Fishing Shop",
            f"**Koin lo:** {udata['coins']} 🪙\n\n**🎣 Rod:**\n{rod_text}\n\n**🪱 Umpan:**\n{bait_text}"
        )
        await interaction.response.send_message(embed=em, view=ShopBuyView(interaction.user.id), ephemeral=True)

class ShopBuyView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id
        rod_select = discord.ui.Select(
            placeholder="Beli Rod...",
            custom_id="buy_rod",
            options=[discord.SelectOption(label=k, description=f"Tier {v['tier']} - {v['price']} koin", emoji=v["emoji"]) for k, v in RODS.items()]
        )
        rod_select.callback = self.buy_rod
        self.add_item(rod_select)
        bait_select = discord.ui.Select(
            placeholder="Beli Umpan...",
            custom_id="buy_bait",
            options=[discord.SelectOption(label=k, description=f"{v['price']} koin", emoji=v["emoji"]) for k, v in BAITS.items()]
        )
        bait_select.callback = self.buy_bait
        self.add_item(bait_select)

    async def buy_rod(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Belanja sendiri bro!", ephemeral=True)
            return
        item = interaction.data["values"][0]
        udata = get_user_fishing(str(interaction.user.id))
        price = RODS[item]["price"]
        if udata["coins"] < price:
            await interaction.response.send_message(f"❌ Koin lo kurang bro! Butuh {price} 🪙, lo cuma punya {udata['coins']} 🪙", ephemeral=True)
            return
        udata["coins"] -= price
        udata["rod"] = item
        save_user_fishing(str(interaction.user.id), udata)
        await interaction.response.send_message(f"✅ Berhasil beli **{item}**! Sekarang lo pake rod baru. Sisa koin: {udata['coins']} 🪙", ephemeral=True)

    async def buy_bait(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Belanja sendiri bro!", ephemeral=True)
            return
        item = interaction.data["values"][0]
        udata = get_user_fishing(str(interaction.user.id))
        price = BAITS[item]["price"]
        if udata["coins"] < price:
            await interaction.response.send_message(f"❌ Koin lo kurang bro! Butuh {price} 🪙", ephemeral=True)
            return
        udata["coins"] -= price
        if "bait" not in udata:
            udata["bait"] = {}
        udata["bait"][item] = udata["bait"].get(item, 0) + 5
        save_user_fishing(str(interaction.user.id), udata)
        await interaction.response.send_message(f"✅ Beli **{item}** x5! Sisa koin: {udata['coins']} 🪙", ephemeral=True)

# ===================== FISHING CONFIG VIEWS =====================

class FishingConfigView(discord.ui.View):
    """View untuk !Kingdoom setfishing"""
    def __init__(self, guild_id):
        super().__init__(timeout=300)
        self.guild_id = str(guild_id)

    @discord.ui.button(label="🐟 Tambah/Edit Ikan", style=discord.ButtonStyle.primary, row=0)
    async def edit_fish(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Hanya admin yang bisa ubah ini!", ephemeral=True)
            return
        await interaction.response.send_message(
            "📝 Ketik detail ikan dengan format:\n"
            "`nama_ikan|harga_jual|luck_chance|rarity|emoji`\n\n"
            "**Rarity:** `common`, `uncommon`, `rare`, `legendary`, `trash`\n"
            "**luck_chance:** angka desimal (semakin kecil = semakin langka)\n"
            "Contoh: `Ikan Mas Langka|300|0.5|legendary|🐟`\n\n"
            "⚠️ Jika ikan sudah ada, data akan diupdate.",
            ephemeral=True
        )
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            parts = msg.content.split("|")
            if len(parts) < 4:
                await msg.reply("❌ Format salah! Harus ada minimal nama|harga_jual|luck_chance|rarity")
                return
            nama = parts[0].strip()
            sell_price = int(parts[1].strip()) if parts[1].strip().isdigit() else 50
            try:
                luck_chance = float(parts[2].strip())
            except:
                luck_chance = 10.0
            rarity = parts[3].strip().lower()
            emoji = parts[4].strip() if len(parts) > 4 else "🐟"
            if rarity not in ["common", "uncommon", "rare", "legendary", "trash"]:
                await msg.reply("❌ Rarity tidak valid! Gunakan: common, uncommon, rare, legendary, trash")
                return
            cfg = get_fishing_config()
            fish_list = cfg["fish_list"]
            updated = False
            for f in fish_list:
                if f["name"].lower() == nama.lower():
                    f["sell_price"] = sell_price
                    f["luck_chance"] = luck_chance
                    f["rarity"] = rarity
                    f["emoji"] = emoji
                    updated = True
                    break
            if not updated:
                fish_list.append({
                    "name": nama, "sell_price": sell_price,
                    "luck_chance": luck_chance, "rarity": rarity, "emoji": emoji
                })
            cfg["fish_list"] = fish_list
            save_fishing_config(cfg)
            action = "diupdate" if updated else "ditambah"
            em = dark_red_embed(
                f"✅ Ikan {action.title()}!",
                f"{emoji} **{nama}**\n💰 Harga jual: **{sell_price} koin**\n🎲 Luck chance: **{luck_chance}%**\n⭐ Rarity: **{rarity}**"
            )
            await msg.reply(embed=em)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timeout!", ephemeral=True)

    @discord.ui.button(label="🗑️ Hapus Ikan", style=discord.ButtonStyle.danger, row=0)
    async def delete_fish(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Hanya admin!", ephemeral=True)
            return
        cfg = get_fishing_config()
        fish_list = cfg["fish_list"]
        fish_names = [f["name"] for f in fish_list]
        await interaction.response.send_message(
            f"🗑️ Ketik nama ikan yang mau dihapus:\n{', '.join(fish_names)}",
            ephemeral=True
        )
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            nama = msg.content.strip()
            before = len(fish_list)
            fish_list = [f for f in fish_list if f["name"].lower() != nama.lower()]
            if len(fish_list) == before:
                await msg.reply(f"❌ Ikan **{nama}** tidak ditemukan!")
                return
            cfg["fish_list"] = fish_list
            save_fishing_config(cfg)
            await msg.reply(embed=dark_red_embed("✅ Ikan Dihapus!", f"**{nama}** berhasil dihapus dari daftar ikan."))
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timeout!", ephemeral=True)

    @discord.ui.button(label="📋 Lihat Daftar Ikan", style=discord.ButtonStyle.secondary, row=0)
    async def list_fish(self, interaction: discord.Interaction, button: discord.ui.Button):
        cfg = get_fishing_config()
        fish_list = cfg["fish_list"]
        rarity_order = ["legendary", "rare", "uncommon", "common", "trash"]
        rarity_label = {
            "legendary": "⭐ Legendary", "rare": "💎 Rare",
            "uncommon": "🔵 Uncommon", "common": "⚪ Common", "trash": "💩 Trash"
        }
        lines = []
        for r in rarity_order:
            group = [f for f in fish_list if f.get("rarity") == r]
            if group:
                lines.append(f"**{rarity_label[r]}**")
                for f in group:
                    sell = f.get("sell_price", f.get("value", 0))
                    luck = f.get("luck_chance", 0)
                    lines.append(f"  {f.get('emoji','🐟')} {f['name']} | Jual: **{sell}** 🪙 | Luck: **{luck}%**")
        em = dark_red_embed("🐟 Daftar Ikan", "\n".join(lines) if lines else "Belum ada ikan!")
        await interaction.response.send_message(embed=em, ephemeral=True)

    @discord.ui.button(label="🎣 Set Harga Rod", style=discord.ButtonStyle.secondary, row=1)
    async def set_rod_price(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Hanya admin!", ephemeral=True)
            return
        await interaction.response.send_message(
            "💰 Ketik nama rod dan harga baru dengan format:\n`nama_rod|harga`\n\n"
            "Daftar rod: " + ", ".join(RODS.keys()),
            ephemeral=True
        )
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            parts = msg.content.split("|")
            if len(parts) < 2:
                await msg.reply("❌ Format salah! `nama_rod|harga`")
                return
            rod_name = parts[0].strip()
            price = int(parts[1].strip()) if parts[1].strip().isdigit() else None
            if rod_name not in RODS or price is None:
                await msg.reply(f"❌ Rod **{rod_name}** tidak ditemukan atau harga tidak valid!")
                return
            RODS[rod_name]["price"] = price
            await msg.reply(embed=dark_red_embed("✅ Harga Rod Diupdate!", f"**{rod_name}** sekarang harganya **{price} 🪙**"))
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timeout!", ephemeral=True)

    @discord.ui.button(label="🔄 Reset ke Default", style=discord.ButtonStyle.danger, row=1)
    async def reset_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Hanya admin!", ephemeral=True)
            return
        save_fishing_config(DEFAULT_FISHING_CONFIG)
        await interaction.response.send_message(
            embed=dark_red_embed("🔄 Config Direset!", "Konfigurasi fishing sudah dikembalikan ke default!"),
            ephemeral=True
        )

# ===================== PREMIUM VIEWS =====================

class PremiumSetupView(discord.ui.View):
    """View untuk setup premium"""
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="🔗 Set Webhook URL", style=discord.ButtonStyle.primary, row=0)
    async def set_webhook(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_bot_owner_by_id(interaction.user.id):
            await interaction.response.send_message("❌ Hanya owner bot yang bisa set webhook!", ephemeral=True)
            return
        await interaction.response.send_message(
            "🔗 Kirim URL webhook yang mau digunakan untuk notifikasi premium:",
            ephemeral=True
        )
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            url = msg.content.strip()
            if not url.startswith("https://"):
                await msg.reply("❌ URL tidak valid! Harus diawali dengan `https://`")
                return
            cfg = get_premium_config()
            cfg["webhook_url"] = url
            save_premium_config(cfg)
            try:
                await msg.delete()
            except:
                pass
            await interaction.followup.send("✅ Webhook URL berhasil disimpan!", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timeout!", ephemeral=True)

    @discord.ui.button(label="💰 Set Harga Premium", style=discord.ButtonStyle.secondary, row=0)
    async def set_price(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_bot_owner_by_id(interaction.user.id):
            await interaction.response.send_message("❌ Hanya owner bot!", ephemeral=True)
            return
        await interaction.response.send_message("💰 Ketik harga premium (dalam angka, misal: 50000):", ephemeral=True)
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            price = int(msg.content.strip()) if msg.content.strip().isdigit() else None
            if price is None:
                await msg.reply("❌ Harga harus berupa angka!")
                return
            cfg = get_premium_config()
            cfg["price"] = price
            save_premium_config(cfg)
            await msg.reply(embed=dark_red_embed("✅ Harga Premium Diset!", f"Harga premium: **Rp {price:,}**"))
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timeout!", ephemeral=True)

    @discord.ui.button(label="⏳ Set Durasi (Hari)", style=discord.ButtonStyle.secondary, row=0)
    async def set_duration(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_bot_owner_by_id(interaction.user.id):
            await interaction.response.send_message("❌ Hanya owner bot!", ephemeral=True)
            return
        await interaction.response.send_message("⏳ Ketik durasi premium dalam hari (contoh: 30):", ephemeral=True)
        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            days = int(msg.content.strip()) if msg.content.strip().isdigit() else None
            if days is None:
                await msg.reply("❌ Durasi harus berupa angka hari!")
                return
            cfg = get_premium_config()
            cfg["duration_days"] = days
            save_premium_config(cfg)
            await msg.reply(embed=dark_red_embed("✅ Durasi Premium Diset!", f"Durasi premium: **{days} hari**"))
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timeout!", ephemeral=True)

    @discord.ui.button(label="📋 Lihat Config Premium", style=discord.ButtonStyle.secondary, row=1)
    async def view_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_bot_owner_by_id(interaction.user.id):
            await interaction.response.send_message("❌ Hanya owner bot!", ephemeral=True)
            return
        cfg = get_premium_config()
        webhook_status = "✅ Sudah diset" if cfg.get("webhook_url") else "❌ Belum diset"
        em = dark_red_embed(
            "⚙️ Config Premium",
            f"**Webhook:** {webhook_status}\n"
            f"**Harga:** Rp {cfg.get('price', 0):,}\n"
            f"**Durasi:** {cfg.get('duration_days', 30)} hari\n"
            f"**Fitur:** {', '.join(cfg.get('features', [])) or 'Belum ada'}"
        )
        await interaction.response.send_message(embed=em, ephemeral=True)

    @discord.ui.button(label="👤 Lihat Member Premium", style=discord.ButtonStyle.secondary, row=1)
    async def view_members(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_bot_owner_by_id(interaction.user.id):
            await interaction.response.send_message("❌ Hanya owner bot!", ephemeral=True)
            return
        users = get_premium_users()
        if not users:
            await interaction.response.send_message("📋 Belum ada member premium!", ephemeral=True)
            return
        lines = []
        for uid, data in users.items():
            expiry = data.get("expiry", 0)
            if expiry == -1:
                exp_str = "Lifetime"
            elif time.time() > expiry:
                exp_str = "❌ Expired"
            else:
                dt = datetime.datetime.fromtimestamp(expiry, tz=WIB)
                exp_str = dt.strftime("%d/%m/%Y")
            lines.append(f"• <@{uid}> — {exp_str}")
        em = dark_red_embed("👑 Member Premium", "\n".join(lines[:20]))
        await interaction.response.send_message(embed=em, ephemeral=True)

# ===================== OTHER VIEWS =====================

class TicketView(discord.ui.View):
    def __init__(self, panel_config):
        super().__init__(timeout=None)
        self.panel_config = panel_config
        btn = discord.ui.Button(
            label=panel_config.get("button_label", "Buka Ticket"),
            emoji=panel_config.get("button_emoji", "🎫"),
            style=discord.ButtonStyle.danger,
            custom_id=f"ticket_open_{panel_config['panel_id']}"
        )
        btn.callback = self.open_ticket
        self.add_item(btn)

    async def open_ticket(self, interaction: discord.Interaction):
        guild = interaction.guild
        config = self.panel_config
        existing = discord.utils.get(guild.channels, name=f"ticket-{interaction.user.name.lower()}")
        if existing:
            await interaction.response.send_message(f"Lo udah punya ticket aktif: {existing.mention} bro!", ephemeral=True)
            return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        cat = guild.get_channel(int(config["category_id"])) if config.get("category_id") else None
        ch = await guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            overwrites=overwrites,
            category=cat,
            topic=f"Ticket milik {interaction.user}"
        )
        em = dark_red_embed(
            f"🎫 Ticket - {interaction.user.display_name}",
            config.get("description", "Hai! Cerita masalah lo di sini, tim kami bakal bantu ASAP!")
        )
        close_view = TicketCloseView()
        await ch.send(content=interaction.user.mention, embed=em, view=close_view)
        await interaction.response.send_message(f"Ticket lo udah kebuka bro! {ch.mention}", ephemeral=True)

class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Tutup Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        em = dark_red_embed("🔒 Ticket Ditutup", f"Ticket ditutup oleh {interaction.user.mention}.\nChannel akan dihapus dalam 5 detik.")
        await interaction.response.send_message(embed=em)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class ReactionRoleView(discord.ui.View):
    def __init__(self, roles_config):
        super().__init__(timeout=None)
        for cfg in roles_config:
            btn = discord.ui.Button(
                label=cfg["label"],
                emoji=cfg.get("emoji"),
                style=discord.ButtonStyle.danger,
                custom_id=f"rr_{cfg['role_id']}"
            )
            btn.callback = self.toggle_role
            self.add_item(btn)

    async def toggle_role(self, interaction: discord.Interaction):
        role_id = int(interaction.data["custom_id"].split("_")[1])
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message("❌ Role gak ketemu bro!", ephemeral=True)
            return
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"✅ Role **{role.name}** dicopot dari lo!", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Role **{role.name}** berhasil dapet!", ephemeral=True)

class LevelingSetupView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=300)
        self.guild_id = str(guild_id)

    @discord.ui.button(label="Toggle Leveling ON/OFF", style=discord.ButtonStyle.danger, row=0)
    async def toggle_leveling(self, interaction: discord.Interaction, button: discord.ui.Button):
        config = get_config()
        gid = self.guild_id
        if gid not in config:
            config[gid] = {}
        config[gid]["leveling_enabled"] = not config[gid].get("leveling_enabled", True)
        save_config(config)
        status = "✅ AKTIF" if config[gid]["leveling_enabled"] else "❌ NONAKTIF"
        await interaction.response.send_message(f"Leveling sekarang: **{status}**", ephemeral=True)

    @discord.ui.button(label="Set Channel Level", style=discord.ButtonStyle.secondary, row=0)
    async def set_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Mention channel yang mau dipake buat notif level up (contoh: #general):",
            ephemeral=True
        )
        def check(m):
            return m.author.id == interaction.user.id and m.channel_mentions
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            ch = msg.channel_mentions[0]
            config = get_config()
            gid = self.guild_id
            if gid not in config:
                config[gid] = {}
            config[gid]["level_channel"] = str(ch.id)
            save_config(config)
            await msg.reply(f"✅ Channel level up diset ke {ch.mention}!")
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timeout! Coba lagi.", ephemeral=True)

    @discord.ui.button(label="Set Role per Level", style=discord.ButtonStyle.secondary, row=0)
    async def set_role_level(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Ketik: `level:role_id` (contoh: `5:123456789`)",
            ephemeral=True
        )
        def check(m):
            return m.author.id == interaction.user.id and ":" in m.content
        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            parts = msg.content.split(":")
            lvl, rid = parts[0].strip(), parts[1].strip()
            config = get_config()
            gid = self.guild_id
            if gid not in config:
                config[gid] = {}
            if "level_roles" not in config[gid]:
                config[gid]["level_roles"] = {}
            config[gid]["level_roles"][lvl] = rid
            save_config(config)
            await msg.reply(f"✅ Level {lvl} akan dapet role ID {rid}!")
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timeout!", ephemeral=True)

# ===================== PREFIX COMMANDS =====================

# --- Maintenance ---
@bot.command(name="maintenance")
async def maintenance_cmd(ctx, action: str = None, *, args: str = None):
    """!Kingdoom maintenance on/off/set/status"""
    if not is_bot_owner_by_id(ctx.author.id) and not ctx.author.guild_permissions.administrator:
        await ctx.reply(embed=dark_red_embed("❌ No Permission!", "Hanya owner bot atau admin yang bisa menggunakan command ini!"))
        return

    m = get_maintenance()

    if action == "on":
        m["active"] = True
        m["end_time"] = 0  # tanpa durasi
        save_maintenance(m)
        em = dark_red_embed("🔧 Maintenance Aktif!", f"Bot sekarang dalam mode maintenance.\n**Pesan:** {m.get('message','...')}")
        await ctx.send(embed=em)

        # Kirim notif ke main channel jika sudah diset
        ch_id = m.get("channel_id", "")
        if ch_id:
            ch = ctx.guild.get_channel(int(ch_id))
            if ch and ch != ctx.channel:
                await ch.send(embed=em)

    elif action == "off":
        m["active"] = False
        m["end_time"] = 0
        save_maintenance(m)
        em = dark_red_embed("✅ Maintenance Selesai!", "Bot sudah kembali normal!")
        await ctx.send(embed=em)
        ch_id = m.get("channel_id", "")
        if ch_id:
            ch = ctx.guild.get_channel(int(ch_id))
            if ch and ch != ctx.channel:
                await ch.send(embed=em)

    elif action == "set":
        await ctx.reply(
            "⚙️ Setup maintenance:\n"
            "Ketik dengan format: `pesan|durasi_menit|#channel`\n\n"
            "- **pesan**: pesan maintenance yang ditampilkan\n"
            "- **durasi_menit**: berapa menit maintenance (0 = tanpa batas)\n"
            "- **#channel**: mention channel untuk announce (opsional)\n\n"
            "Contoh: `Server sedang diperbaiki|60|#announcement`"
        )
        def check(m_msg):
            return m_msg.author.id == ctx.author.id and m_msg.channel.id == ctx.channel.id
        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            parts = msg.content.split("|")
            pesan = parts[0].strip()
            durasi = 0
            if len(parts) > 1 and parts[1].strip().isdigit():
                durasi = int(parts[1].strip())
            channel_id = ""
            if len(parts) > 2 and msg.channel_mentions:
                channel_id = str(msg.channel_mentions[0].id)
            m["message"] = pesan
            m["end_time"] = time.time() + (durasi * 60) if durasi > 0 else 0
            m["channel_id"] = channel_id
            save_maintenance(m)
            durasi_str = f"{durasi} menit" if durasi > 0 else "Tanpa batas waktu"
            em = dark_red_embed(
                "✅ Maintenance Dikonfigurasi!",
                f"**Pesan:** {pesan}\n**Durasi:** {durasi_str}\n**Channel:** {'<#' + channel_id + '>' if channel_id else 'Tidak diset'}\n\n"
                f"Gunakan `!Kingdoom maintenance on` untuk mengaktifkan!"
            )
            await msg.reply(embed=em)
        except asyncio.TimeoutError:
            await ctx.reply("⏰ Timeout!")

    elif action == "status":
        status = "🔧 AKTIF" if m.get("active", False) else "✅ Normal"
        end_time = m.get("end_time", 0)
        if end_time > 0:
            dt = datetime.datetime.fromtimestamp(end_time, tz=WIB)
            end_str = dt.strftime("%d/%m/%Y %H:%M WIB")
        else:
            end_str = "Tanpa batas"
        ch_id = m.get("channel_id", "")
        em = dark_red_embed(
            "⚙️ Status Maintenance",
            f"**Status:** {status}\n"
            f"**Pesan:** {m.get('message', '...')}\n"
            f"**Berakhir:** {end_str}\n"
            f"**Channel:** {'<#' + ch_id + '>' if ch_id else 'Tidak diset'}"
        )
        await ctx.reply(embed=em)

    else:
        em = dark_red_embed(
            "🔧 Maintenance Command",
            "**Usage:**\n"
            "`!Kingdoom maintenance on` — Aktifkan maintenance\n"
            "`!Kingdoom maintenance off` — Matikan maintenance\n"
            "`!Kingdoom maintenance set` — Konfigurasi maintenance (pesan, durasi, channel)\n"
            "`!Kingdoom maintenance status` — Lihat status maintenance"
        )
        await ctx.reply(embed=em)

# --- Premium ---
@bot.command(name="premium")
async def premium_cmd(ctx, action: str = None, member: discord.Member = None, *, extra: str = None):
    """!Kingdoom premium [setup/add/remove/check]"""

    if action == "setup":
        if not is_bot_owner_by_id(ctx.author.id):
            await ctx.reply(embed=dark_red_embed("❌ No Permission!", "Hanya owner bot yang bisa setup premium!"))
            return
        cfg = get_premium_config()
        webhook_status = "✅ Sudah diset" if cfg.get("webhook_url") else "❌ Belum diset"
        em = dark_red_embed(
            "👑 Premium Setup Panel",
            f"**Webhook:** {webhook_status}\n"
            f"**Harga:** Rp {cfg.get('price', 0):,}\n"
            f"**Durasi:** {cfg.get('duration_days', 30)} hari\n\n"
            "Gunakan button di bawah untuk konfigurasi!"
        )
        await ctx.send(embed=em, view=PremiumSetupView())

    elif action == "add":
        if not is_bot_owner_by_id(ctx.author.id):
            await ctx.reply(embed=dark_red_embed("❌ No Permission!", "Hanya owner bot yang bisa tambah member premium!"))
            return
        if not member:
            await ctx.reply("❓ Format: `!Kingdoom premium add @member [hari/lifetime]`")
            return
        cfg = get_premium_config()
        duration_days = cfg.get("duration_days", 30)
        lifetime = False
        if extra:
            if extra.lower() == "lifetime":
                lifetime = True
            elif extra.isdigit():
                duration_days = int(extra)
        users = get_premium_users()
        uid = str(member.id)
        if lifetime:
            expiry = -1
            exp_str = "Seumur hidup ♾️"
        else:
            expiry = time.time() + (duration_days * 86400)
            dt = datetime.datetime.fromtimestamp(expiry, tz=WIB)
            exp_str = dt.strftime("%d/%m/%Y %H:%M WIB")
        users[uid] = {"expiry": expiry, "added_by": str(ctx.author.id), "added_at": time.time()}
        save_premium_users(users)
        em = dark_red_embed(
            "👑 Member Premium Ditambah!",
            f"**Member:** {member.mention}\n**Expired:** {exp_str}"
        )
        await ctx.send(embed=em)
        # Notif ke webhook jika ada
        webhook_url = cfg.get("webhook_url", "")
        if webhook_url:
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "embeds": [{
                            "title": "👑 Premium Baru!",
                            "description": f"**{member.display_name}** ({member.id}) mendapatkan akses premium!\nDurasi: {exp_str}",
                            "color": 0xFFD700
                        }]
                    }
                    await session.post(webhook_url, json=payload)
            except:
                pass
        # Notif ke member
        try:
            dm_em = dark_red_embed(
                "👑 Selamat! Lo Dapet Premium!",
                f"Lo sekarang punya akses **Premium** di server!\n**Expired:** {exp_str}\n\nNikmatin semua fitur premium ya! 🎉"
            )
            await member.send(embed=dm_em)
        except:
            pass

    elif action == "remove":
        if not is_bot_owner_by_id(ctx.author.id):
            await ctx.reply(embed=dark_red_embed("❌ No Permission!", "Hanya owner bot!"))
            return
        if not member:
            await ctx.reply("❓ Format: `!Kingdoom premium remove @member`")
            return
        users = get_premium_users()
        uid = str(member.id)
        if uid not in users:
            await ctx.reply(f"❌ **{member.display_name}** bukan member premium!")
            return
        del users[uid]
        save_premium_users(users)
        await ctx.send(embed=dark_red_embed("✅ Premium Dicabut!", f"**{member.display_name}** sudah tidak premium lagi."))

    elif action == "check":
        target = member or ctx.author
        premium = is_premium_user(str(target.id))
        expiry_str = get_premium_expiry_str(str(target.id))
        cfg = get_premium_config()
        if premium:
            em = dark_red_embed(
                "👑 Status Premium",
                f"**{target.display_name}** adalah member **PREMIUM** 👑\n**Expired:** {expiry_str}"
            )
        else:
            em = dark_red_embed(
                "❌ Bukan Member Premium",
                f"**{target.display_name}** belum punya akses premium.\n\n"
                f"💰 **Harga:** Rp {cfg.get('price', 0):,}\n"
                f"⏳ **Durasi:** {cfg.get('duration_days', 30)} hari\n\n"
                f"Hubungi admin untuk beli premium!"
            )
        await ctx.reply(embed=em)

    else:
        cfg = get_premium_config()
        em = dark_red_embed(
            "👑 Premium RepublikDooms",
            f"💰 **Harga:** Rp {cfg.get('price', 0):,}\n"
            f"⏳ **Durasi:** {cfg.get('duration_days', 30)} hari\n\n"
            "**Commands:**\n"
            "`!Kingdoom premium check [@member]` — Cek status premium\n"
            "`!Kingdoom premium add @member [hari/lifetime]` — Tambah premium (owner only)\n"
            "`!Kingdoom premium remove @member` — Hapus premium (owner only)\n"
            "`!Kingdoom premium setup` — Konfigurasi premium (owner only)"
        )
        await ctx.reply(embed=em)

def check_premium_required(feature_name: str):
    """Decorator untuk mengecek apakah fitur butuh premium"""
    async def predicate(ctx):
        if is_premium_user(str(ctx.author.id)):
            return True
        cfg = get_premium_config()
        price = cfg.get("price", 0)
        days = cfg.get("duration_days", 30)
        em = dark_red_embed(
            "👑 Fitur Premium!",
            f"Fitur **{feature_name}** hanya tersedia untuk member **Premium** 👑\n\n"
            f"💰 **Harga:** Rp {price:,}\n"
            f"⏳ **Durasi:** {days} hari\n\n"
            f"Hubungi admin atau owner untuk membeli akses premium!\n"
            f"Gunakan `!Kingdoom premium check` untuk cek status lo."
        )
        await ctx.send(embed=em)
        return False
    return commands.check(predicate)

# --- Fishing Config ---
@bot.command(name="setfishing")
@commands.has_permissions(administrator=True)
async def setfishing_cmd(ctx):
    """!Kingdoom setfishing — Konfigurasi sistem fishing"""
    cfg = get_fishing_config()
    fish_count = len(cfg.get("fish_list", []))
    rod_price = cfg.get("rod_price", 100)
    em = dark_red_embed(
        "🎣 Fishing Configuration Panel",
        f"**Jumlah Ikan:** {fish_count}\n"
        f"**Harga Rod Default:** {rod_price} 🪙\n\n"
        "Gunakan button di bawah untuk mengatur sistem fishing!"
    )
    await ctx.send(embed=em, view=FishingConfigView(ctx.guild.id))

# --- AI Chat ---
@bot.command(name="ai")
async def ai_chat(ctx, *, question: str = None):
    if not question:
        await ctx.reply("❓ Tanya apa dulu bro? Contoh: `!Kingdoom ai siapa itu elon musk?`")
        return
    async with ctx.typing():
        resp = await get_ai_response(question)
    em = dark_red_embed("🤖 RepublikDooms AI", resp)
    em.set_footer(text=f"Ditanya oleh {ctx.author.display_name}")
    await ctx.reply(embed=em)

# --- Fishing ---
@bot.command(name="fish", aliases=["mancing", "fishing"])
async def fishing(ctx):
    em = dark_red_embed(
        "🎣 Fishing RepublikDooms",
        f"Halo **{ctx.author.display_name}**! Pilih aksi lo:"
    )
    await ctx.reply(embed=em, view=FishingMainView(ctx.author.id))

# --- Tebak-Tebakan ---
@bot.command(name="tebak")
async def tebak(ctx):
    gid = str(ctx.guild.id)
    if gid in active_tebakan:
        await ctx.reply("⚠️ Masih ada tebakan yang belum kejawab bro! Jawab dulu yang itu.")
        return
    semua_soal = TEBAKAN_LIST + get_custom_tebakan()
    soal = random.choice(semua_soal)
    active_tebakan[gid] = {
        "jawaban": soal["jawaban"].lower().strip(),
        "reward": soal["reward"],
        "asker": ctx.author.id
    }
    em = dark_red_embed(
        "🧠 TEBAK-TEBAKAN NIH!",
        f"**Soal:**\n{soal['soal']}\n\n"
        f"💡 Jawab di chat! Reward: **{soal['reward']} koin** buat yang bener!\n"
        f"⚠️ Si penanya ga bisa menang ya."
    )
    await ctx.send(embed=em)

@bot.command(name="addtebak")
@commands.has_permissions(administrator=True)
async def addtebak_cmd(ctx, *, content: str = None):
    if not content:
        await ctx.reply("❓ Format: `!Kingdoom addtebak Pertanyaan lo|jawaban|reward_koin`\nContoh: `!Kingdoom addtebak Ibu kota Indonesia?|jakarta|50`")
        return
    parts = content.split("|")
    if len(parts) < 2:
        await ctx.reply("❌ Format salah! Harus ada soal dan jawaban dipisah `|`")
        return
    soal = parts[0].strip()
    jawaban = parts[1].strip().lower()
    reward = int(parts[2].strip()) if len(parts) > 2 and parts[2].strip().isdigit() else 25
    custom = get_custom_tebakan()
    custom.append({"soal": soal, "jawaban": jawaban, "reward": reward})
    save_custom_tebakan(custom)
    em = dark_red_embed(
        "✅ Soal Tebakan Ditambah!",
        f"**Soal:** {soal}\n**Jawaban:** {jawaban}\n**Reward:** {reward} koin\n\n"
        f"Total soal custom: **{len(custom)}**"
    )
    await ctx.reply(embed=em)

@bot.command(name="listtebak")
async def listtebak_cmd(ctx):
    custom = get_custom_tebakan()
    if not custom:
        await ctx.reply("📋 Belum ada soal tebakan custom. Tambah pake `!Kingdoom addtebak`!")
        return
    lines = [f"{i+1}. {s['soal']} → **{s['jawaban']}** ({s['reward']} koin)" for i, s in enumerate(custom)]
    em = dark_red_embed("📋 Soal Tebakan Custom", "\n".join(lines[:20]))
    em.set_footer(text=f"Total: {len(custom)} soal custom | Default: {len(TEBAKAN_LIST)} soal")
    await ctx.reply(embed=em)

@bot.command(name="removetebak")
@commands.has_permissions(administrator=True)
async def removetebak_cmd(ctx, nomor: int = None):
    if not nomor:
        await ctx.reply("❓ Format: `!Kingdoom removetebak [nomor]` — lihat nomor pake `!Kingdoom listtebak`")
        return
    custom = get_custom_tebakan()
    if nomor < 1 or nomor > len(custom):
        await ctx.reply(f"❌ Nomor soal tidak valid! Soal custom ada {len(custom)}.")
        return
    removed = custom.pop(nomor - 1)
    save_custom_tebakan(custom)
    await ctx.reply(embed=dark_red_embed("🗑️ Soal Dihapus!", f"Soal **\"{removed['soal']}\"** berhasil dihapus!"))

@bot.command(name="coins", aliases=["koin", "saldo"])
async def check_coins(ctx):
    udata = get_user_fishing(str(ctx.author.id))
    em = dark_red_embed("🪙 Koin Lo", f"**{ctx.author.display_name}** punya **{udata['coins']} koin** 🪙")
    await ctx.reply(embed=em)

# --- Warn ---
@bot.command(name="warn")
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member = None, *, reason: str = "Gak ada alasan"):
    if not member:
        await ctx.reply("❓ Mention member yang mau di-warn bro!")
        return
    warns = get_warns()
    gid = str(ctx.guild.id)
    uid = str(member.id)
    if gid not in warns:
        warns[gid] = {}
    if uid not in warns[gid]:
        warns[gid][uid] = []
    warns[gid][uid].append({"reason": reason, "by": str(ctx.author.id), "time": time.time()})
    save_warns(warns)
    count = len(warns[gid][uid])
    dm_status = ""
    try:
        dm_em = dark_red_embed(
            "⚠️ Lo Kena Warn!",
            f"Lo di-warn di server **{ctx.guild.name}**\n**Alasan:** {reason}\n**Total Warn lo:** {count}\n\n⚠️ Hati-hati ya, jangan sampe nambah lagi!"
        )
        dm_em.set_footer(text=f"Warn oleh: {ctx.author.display_name}")
        await member.send(embed=dm_em)
        dm_status = "\n✅ Notifikasi DM berhasil dikirim."
    except discord.Forbidden:
        dm_status = "\n⚠️ Gagal kirim DM (member mungkin menonaktifkan DM dari server)."
    except discord.HTTPException as e:
        dm_status = f"\n⚠️ Gagal kirim DM: {str(e)[:60]}"
    em = dark_red_embed(
        "⚠️ Member Di-Warn!",
        f"**{member.display_name}** dapet warn!\n**Alasan:** {reason}\n**Total Warn:** {count}{dm_status}"
    )
    await ctx.send(embed=em)

@bot.command(name="warns")
async def check_warns(ctx, member: discord.Member = None):
    member = member or ctx.author
    warns = get_warns()
    gid = str(ctx.guild.id)
    uid = str(member.id)
    user_warns = warns.get(gid, {}).get(uid, [])
    if not user_warns:
        await ctx.reply(f"✅ **{member.display_name}** bersih, gak ada warn!")
        return
    warn_text = "\n".join([f"{i+1}. {w['reason']}" for i, w in enumerate(user_warns)])
    em = dark_red_embed(f"⚠️ Warn {member.display_name}", f"Total: **{len(user_warns)} warn**\n\n{warn_text}")
    await ctx.reply(embed=em)

# --- Moderation ---
@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member = None, *, reason="Gak ada alasan"):
    if not member:
        await ctx.reply("❓ Mention member dulu bro!")
        return
    await member.kick(reason=reason)
    em = dark_red_embed("👢 Member Di-Kick!", f"**{member.display_name}** di-kick!\n**Alasan:** {reason}")
    await ctx.send(embed=em)

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason="Gak ada alasan"):
    if not member:
        await ctx.reply("❓ Mention member dulu bro!")
        return
    await member.ban(reason=reason)
    em = dark_red_embed("🔨 Member Di-Ban!", f"**{member.display_name}** di-ban!\n**Alasan:** {reason}")
    await ctx.send(embed=em)

@bot.command(name="timeout", aliases=["mute"])
@commands.has_permissions(moderate_members=True)
async def timeout_cmd(ctx, member: discord.Member = None, minutes: int = 10, *, reason="Gak ada alasan"):
    if not member:
        await ctx.reply("❓ Mention member dulu!")
        return
    until = discord.utils.utcnow() + datetime.timedelta(minutes=minutes)
    await member.timeout(until, reason=reason)
    em = dark_red_embed("⏱️ Member Di-Timeout!", f"**{member.display_name}** di-timeout {minutes} menit!\n**Alasan:** {reason}")
    await ctx.send(embed=em)

@bot.command(name="move")
@commands.has_permissions(move_members=True)
async def move(ctx, member: discord.Member = None, *, channel: discord.VoiceChannel = None):
    if not member or not channel:
        await ctx.reply("❓ Format: `!Kingdoom move @member #channel`")
        return
    await member.move_to(channel)
    em = dark_red_embed("🔀 Member Di-Move!", f"**{member.display_name}** dipindah ke **{channel.name}**!")
    await ctx.send(embed=em)

@bot.command(name="addrole")
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member = None, role: discord.Role = None):
    if not member or not role:
        await ctx.reply("❓ Format: `!Kingdoom addrole @member @role`")
        return
    await member.add_roles(role)
    em = dark_red_embed("✅ Role Ditambah!", f"**{role.name}** dikasih ke **{member.display_name}**!")
    await ctx.send(embed=em)

@bot.command(name="removerole")
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member = None, role: discord.Role = None):
    if not member or not role:
        await ctx.reply("❓ Format: `!Kingdoom removerole @member @role`")
        return
    await member.remove_roles(role)
    em = dark_red_embed("❌ Role Dicopot!", f"**{role.name}** dicopot dari **{member.display_name}**!")
    await ctx.send(embed=em)

@bot.command(name="avatar", aliases=["av"])
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    em = dark_red_embed(f"🖼️ Avatar {member.display_name}")
    em.set_image(url=member.display_avatar.url)
    await ctx.reply(embed=em)

@bot.command(name="userinfo", aliases=["ui", "whois"])
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    em = dark_red_embed(f"👤 Info User: {member.display_name}")
    em.set_thumbnail(url=member.display_avatar.url)
    em.add_field(name="Username", value=str(member), inline=True)
    em.add_field(name="ID", value=member.id, inline=True)
    em.add_field(name="Bergabung Server", value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
    em.add_field(name="Akun Dibuat", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
    em.add_field(name="Roles", value=", ".join([r.name for r in member.roles[1:]]) or "Gak ada", inline=False)
    premium_status = "👑 PREMIUM" if is_premium_user(str(member.id)) else "Bukan Premium"
    em.add_field(name="Premium", value=premium_status, inline=True)
    await ctx.reply(embed=em)

@bot.command(name="clear", aliases=["purge"])
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(embed=dark_red_embed("🗑️ Pesan Dihapus!", f"**{amount}** pesan berhasil dihapus!"))
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name="embed")
@commands.has_permissions(manage_messages=True)
async def embed_cmd(ctx, *, content: str = None):
    if not content:
        await ctx.reply("❓ Format: `!Kingdoom embed Judul|Deskripsi`")
        return
    parts = content.split("|", 1)
    title = parts[0].strip()
    desc = parts[1].strip() if len(parts) > 1 else ""
    em = dark_red_embed(title, desc)
    await ctx.send(embed=em)
    try:
        await ctx.message.delete()
    except:
        pass

@bot.command(name="autoresponse", aliases=["ar"])
@commands.has_permissions(administrator=True)
async def autoresponse_cmd(ctx, action: str = None, trigger: str = None, *, response: str = None):
    gid = str(ctx.guild.id)
    ar = get_autoresponse()
    if gid not in ar:
        ar[gid] = {}
    if action == "add" and trigger and response:
        ar[gid][trigger] = response
        save_autoresponse(ar)
        await ctx.reply(f"✅ Auto-respon untuk **'{trigger}'** ditambah!")
    elif action == "remove" and trigger:
        if trigger in ar[gid]:
            del ar[gid][trigger]
            save_autoresponse(ar)
            await ctx.reply(f"✅ Auto-respon **'{trigger}'** dihapus!")
        else:
            await ctx.reply("❌ Trigger gak ketemu!")
    elif action == "list":
        if ar[gid]:
            text = "\n".join([f"• **{k}** → {v}" for k, v in ar[gid].items()])
            await ctx.reply(embed=dark_red_embed("📋 Daftar Auto-Respon", text))
        else:
            await ctx.reply("📋 Belum ada auto-respon yang diset.")
    else:
        await ctx.reply("❓ Format:\n`!Kingdoom ar add [trigger] [response]`\n`!Kingdoom ar remove [trigger]`\n`!Kingdoom ar list`")

@bot.command(name="sticky")
@commands.has_permissions(manage_messages=True)
async def sticky_cmd(ctx, action: str = None, *, content: str = None):
    gid = str(ctx.guild.id)
    cid = str(ctx.channel.id)
    sticky = get_sticky()
    if gid not in sticky:
        sticky[gid] = {}
    if action == "set" and content:
        parts = content.split("|")
        msg_content = parts[0].strip()
        min_msg = int(parts[1].strip()) if len(parts) > 1 else 3
        sticky[gid][cid] = {"content": msg_content, "min_messages": min_msg, "count": 0}
        save_sticky(sticky)
        await ctx.reply(f"✅ Sticky message diset! Trigger tiap **{min_msg} pesan**.")
    elif action == "remove":
        if cid in sticky[gid]:
            del sticky[gid][cid]
            save_sticky(sticky)
            await ctx.reply("✅ Sticky message dihapus!")
        else:
            await ctx.reply("❌ Gak ada sticky di channel ini!")
    else:
        await ctx.reply("❓ Format:\n`!Kingdoom sticky set [isi pesan]|[min pesan]`\n`!Kingdoom sticky remove`")

@bot.command(name="giveaway", aliases=["ga"])
@commands.has_permissions(administrator=True)
async def giveaway_cmd(ctx, duration: str = None, *, prize: str = None):
    if not duration or not prize:
        await ctx.reply("❓ Format: `!Kingdoom giveaway [durasi:angka][s/m/h] [hadiah]`\nContoh: `!Kingdoom giveaway 30m iPhone 15`")
        return
    multipliers = {"s": 1, "m": 60, "h": 3600}
    unit = duration[-1].lower()
    if unit not in multipliers:
        await ctx.reply("❌ Unit waktu salah! Pake s, m, atau h.")
        return
    seconds = int(duration[:-1]) * multipliers[unit]
    end_time = time.time() + seconds
    end_dt = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    em = dark_red_embed(
        "🎉 GIVEAWAY NIH!",
        f"**Hadiah:** {prize}\n**Berakhir:** {end_dt.strftime('%d/%m/%Y %H:%M')}\n\n🎉 React buat ikutan!"
    )
    em.set_footer(text="Klik 🎉 buat ikut giveaway!")
    msg = await ctx.send(embed=em)
    await msg.add_reaction("🎉")
    gw_data = get_giveaways()
    gid = str(ctx.guild.id)
    if gid not in gw_data:
        gw_data[gid] = {}
    gw_data[gid][str(msg.id)] = {
        "prize": prize,
        "end_time": end_time,
        "channel_id": str(ctx.channel.id),
        "ended": False
    }
    save_giveaways(gw_data)

@bot.command(name="event")
@commands.has_permissions(administrator=True)
async def event_cmd(ctx, *, content: str = None):
    if not content:
        await ctx.reply(
            "❓ Format: `!Kingdoom event Nama Event|Deskripsi|HH:MM|#channel`\n"
            "Contoh: `!Kingdoom event Turnamen ML|Siap-siap gaskeun!|20:00|#announcement`\n"
            "Channel opsional (default: channel saat ini). Jam pakai WIB (UTC+7)."
        )
        return
    parts = content.split("|")
    name = parts[0].strip()
    desc = parts[1].strip() if len(parts) > 1 else "Event seru nih!"
    start_time_str = parts[2].strip() if len(parts) > 2 else "Belum ditentukan"
    target_channel = ctx.channel
    if len(parts) > 3 and ctx.message.channel_mentions:
        target_channel = ctx.message.channel_mentions[0]
    elif len(parts) > 3:
        ch_name = parts[3].strip().replace("#", "")
        found = discord.utils.get(ctx.guild.channels, name=ch_name)
        if found:
            target_channel = found
    em = dark_red_embed(
        f"📅 EVENT: {name}",
        f"{desc}\n\n⏰ **Jam Mulai:** {start_time_str} WIB\n\n📢 Jangan sampe ketinggalan ya! Gas ikutan! 🔥"
    )
    em.set_footer(text=f"Event dibuat oleh {ctx.author.display_name}")
    em.timestamp = datetime.datetime.now(tz=WIB)
    event_msg = await target_channel.send(content="@everyone", embed=em)
    if target_channel != ctx.channel:
        await ctx.reply(f"✅ Event **{name}** berhasil dikirim ke {target_channel.mention}!")
    try:
        now_wib = datetime.datetime.now(tz=WIB)
        naive = datetime.datetime.strptime(start_time_str, "%H:%M")
        event_time = now_wib.replace(hour=naive.hour, minute=naive.minute, second=0, microsecond=0)
        if event_time <= now_wib:
            event_time += datetime.timedelta(days=1)
        delay = (event_time - now_wib).total_seconds()

        async def send_event_start(target_ch, ev_msg, ev_name, ev_desc, ev_time_str, scheduled_ts):
            await asyncio.sleep(max(0, (scheduled_ts - datetime.datetime.now(tz=WIB)).total_seconds()))
            start_em = dark_red_embed(
                f"🚨 EVENT MULAI SEKARANG: {ev_name}!",
                f"**{ev_desc}**\n\n🔥 EVENT UDAH DIMULAI GAES! BURUAN GABUNG!\n⏰ Jam: **{ev_time_str} WIB**"
            )
            start_em.set_footer(text="Jangan sampai ketinggalan! 🔥")
            start_em.timestamp = datetime.datetime.now(tz=WIB)
            try:
                await ev_msg.edit(embed=start_em)
            except Exception:
                pass
            try:
                await target_ch.send(content="@everyone 🚨 **EVENT DIMULAI SEKARANG!** 🚨")
            except Exception:
                pass

        asyncio.create_task(send_event_start(
            target_channel, event_msg, name, desc, start_time_str, event_time
        ))
        if target_channel == ctx.channel:
            await ctx.reply(
                f"✅ Event **{name}** dikirim ke {target_channel.mention}!\n"
                f"⏰ Auto-announce dijadwalkan jam **{start_time_str} WIB** (delay: {int(delay//60)} menit lagi)."
            )
    except ValueError:
        if target_channel == ctx.channel:
            await ctx.reply(f"✅ Event **{name}** berhasil dikirim! ⚠️ Format jam tidak dikenali (gunakan HH:MM), reminder otomatis dinonaktifkan.")

@bot.command(name="addemoji", aliases=["emoji"])
@commands.has_permissions(manage_emojis=True)
async def addemoji_cmd(ctx):
    await ctx.reply("🖼️ Kirim/forward emoji yang mau lo tambah ke server ini! (timeout 60 detik)")
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    try:
        msg = await bot.wait_for("message", check=check, timeout=60)
        added = []
        for emoji in msg.emojis:
            url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{'gif' if emoji.animated else 'png'}"
            import urllib.request as ur
            with ur.urlopen(url) as resp:
                img_bytes = resp.read()
            new_emoji = await ctx.guild.create_custom_emoji(name=emoji.name, image=img_bytes)
            added.append(str(new_emoji))
        if added:
            await ctx.reply(embed=dark_red_embed("✅ Emoji Ditambah!", f"Berhasil tambah: {' '.join(added)}"))
        else:
            await ctx.reply("❌ Gak ada emoji yang ketangkep bro. Pastiin lo forward pesan yang ada emoji custom-nya.")
    except asyncio.TimeoutError:
        await ctx.reply("⏰ Timeout! Coba lagi.")
    except Exception as e:
        await ctx.reply(f"❌ Error: {str(e)[:100]}")

@bot.command(name="help", aliases=["h"])
async def help_cmd(ctx):
    em = dark_red_embed(
        "📖 RepublikDooms - Help",
        "Bot gaul lengkap buat server lo!"
    )
    em.add_field(name="🤖 AI", value="`ai [pertanyaan]`", inline=False)
    em.add_field(name="🎣 Fishing", value="`fish` `coins` `setfishing` (admin)", inline=True)
    em.add_field(
        name="🧠 Tebak-Tebakan",
        value="`tebak` `addtebak [soal|jawaban|reward]` `listtebak` `removetebak [no]`",
        inline=False
    )
    em.add_field(name="⚠️ Mod", value="`warn` `warns` `kick` `ban` `timeout` `move` `clear`", inline=False)
    em.add_field(name="👤 Info", value="`avatar` `userinfo`", inline=True)
    em.add_field(name="🎭 Role", value="`addrole` `removerole`", inline=True)
    em.add_field(
        name="📢 Utility",
        value="`embed` `sticky` `autoresponse` `giveaway` `event [nama|desc|HH:MM|#channel]` `addemoji`",
        inline=False
    )
    em.add_field(
        name="👑 Premium",
        value="`premium` `premium check` `premium add` (owner) `premium setup` (owner)",
        inline=False
    )
    em.add_field(
        name="🔧 Maintenance",
        value="`maintenance on/off/set/status` (admin/owner)",
        inline=False
    )
    em.add_field(
        name="🎰 Slash Commands",
        value="`/ticket` `/leveling` `/reactionrole` `/listfishingreward` `/addtebak` dan banyak lagi!",
        inline=False
    )
    em.set_footer(text="Prefix: !Kingdoom | Semua command bisa pake slash juga!")
    await ctx.reply(embed=em)

# ===================== SLASH COMMANDS =====================

@tree.command(name="ai", description="Tanya apapun ke RepublikDooms AI!")
@app_commands.describe(pertanyaan="Pertanyaan lo buat AI")
async def slash_ai(interaction: discord.Interaction, pertanyaan: str):
    await interaction.response.defer()
    resp = await get_ai_response(pertanyaan)
    em = dark_red_embed("🤖 RepublikDooms AI", resp)
    await interaction.followup.send(embed=em)

@tree.command(name="fish", description="Mulai mancing!")
async def slash_fish(interaction: discord.Interaction):
    em = dark_red_embed("🎣 Fishing RepublikDooms", f"Halo **{interaction.user.display_name}**! Pilih aksi lo:")
    await interaction.response.send_message(embed=em, view=FishingMainView(interaction.user.id))

@tree.command(name="ticket", description="Setup panel ticket")
@app_commands.describe(
    judul="Judul embed panel",
    deskripsi="Deskripsi panel ticket",
    button_label="Label button",
    button_emoji="Emoji button",
    kategori="ID kategori channel ticket"
)
@app_commands.default_permissions(administrator=True)
async def slash_ticket(
    interaction: discord.Interaction,
    judul: str = "🎫 Support Ticket",
    deskripsi: str = "Klik button di bawah untuk buka ticket!",
    button_label: str = "Buka Ticket",
    button_emoji: str = "🎫",
    kategori: str = None
):
    panel_id = str(int(time.time()))
    panel_config = {
        "panel_id": panel_id,
        "button_label": button_label,
        "button_emoji": button_emoji,
        "description": deskripsi,
        "category_id": kategori
    }
    em = dark_red_embed(judul, deskripsi)
    view = TicketView(panel_config)
    await interaction.response.send_message(embed=em, view=view)
    td = get_tickets()
    if "panels" not in td:
        td["panels"] = {}
    td["panels"][panel_id] = panel_config
    save_tickets(td)

@tree.command(name="leveling", description="Setup fitur leveling server")
@app_commands.default_permissions(administrator=True)
async def slash_leveling(interaction: discord.Interaction):
    config = get_config()
    gid = str(interaction.guild.id)
    if gid not in config:
        config[gid] = {}
    status = "✅ AKTIF" if config[gid].get("leveling_enabled", True) else "❌ NONAKTIF"
    em = dark_red_embed(
        "⚙️ Setup Leveling",
        f"**Status Leveling:** {status}\n\nPake button di bawah buat setup step by step!"
    )
    await interaction.response.send_message(embed=em, view=LevelingSetupView(interaction.guild.id))

@tree.command(name="reactionrole", description="Setup reaction role dengan button")
@app_commands.describe(
    judul="Judul embed",
    deskripsi="Deskripsi embed",
    role1="Role pertama",
    emoji1="Emoji button 1",
    label1="Label button 1",
    role2="Role kedua (opsional)",
    emoji2="Emoji button 2 (opsional)",
    label2="Label button 2 (opsional)"
)
@app_commands.default_permissions(administrator=True)
async def slash_reactionrole(
    interaction: discord.Interaction,
    judul: str,
    deskripsi: str,
    role1: discord.Role,
    emoji1: str = "🎭",
    label1: str = "Ambil Role",
    role2: discord.Role = None,
    emoji2: str = "🎭",
    label2: str = "Ambil Role 2"
):
    roles_config = [{"role_id": role1.id, "label": label1, "emoji": emoji1}]
    if role2:
        roles_config.append({"role_id": role2.id, "label": label2, "emoji": emoji2})
    em = dark_red_embed(judul, deskripsi)
    view = ReactionRoleView(roles_config)
    await interaction.response.send_message(embed=em, view=view)

@tree.command(name="giveaway", description="Mulai giveaway!")
@app_commands.describe(durasi_menit="Durasi giveaway dalam menit", hadiah="Hadiah yang mau di-giveaway")
@app_commands.default_permissions(administrator=True)
async def slash_giveaway(interaction: discord.Interaction, durasi_menit: int, hadiah: str):
    end_time = time.time() + durasi_menit * 60
    end_dt = datetime.datetime.now() + datetime.timedelta(minutes=durasi_menit)
    em = dark_red_embed(
        "🎉 GIVEAWAY NIH!",
        f"**Hadiah:** {hadiah}\n**Berakhir:** {end_dt.strftime('%d/%m/%Y %H:%M')}\n\n🎉 React buat ikutan!"
    )
    await interaction.response.send_message(embed=em)
    msg = await interaction.original_response()
    await msg.add_reaction("🎉")
    gw_data = get_giveaways()
    gid = str(interaction.guild.id)
    if gid not in gw_data:
        gw_data[gid] = {}
    gw_data[gid][str(msg.id)] = {
        "prize": hadiah,
        "end_time": end_time,
        "channel_id": str(interaction.channel.id),
        "ended": False
    }
    save_giveaways(gw_data)

@tree.command(name="warn", description="Warn member")
@app_commands.describe(member="Member yang mau di-warn", alasan="Alasan warn")
@app_commands.default_permissions(manage_messages=True)
async def slash_warn(interaction: discord.Interaction, member: discord.Member, alasan: str = "Gak ada alasan"):
    warns = get_warns()
    gid = str(interaction.guild.id)
    uid = str(member.id)
    if gid not in warns:
        warns[gid] = {}
    if uid not in warns[gid]:
        warns[gid][uid] = []
    warns[gid][uid].append({"reason": alasan, "by": str(interaction.user.id), "time": time.time()})
    save_warns(warns)
    count = len(warns[gid][uid])
    dm_status = ""
    try:
        dm_em = dark_red_embed(
            "⚠️ Lo Kena Warn!",
            f"Lo di-warn di server **{interaction.guild.name}**\n**Alasan:** {alasan}\n**Total Warn lo:** {count}\n\n⚠️ Hati-hati ya, jangan sampe nambah lagi!"
        )
        dm_em.set_footer(text=f"Warn oleh: {interaction.user.display_name}")
        await member.send(embed=dm_em)
        dm_status = "\n✅ Notifikasi DM terkirim."
    except discord.Forbidden:
        dm_status = "\n⚠️ Gagal kirim DM (member nonaktifkan DM)."
    except discord.HTTPException as e:
        dm_status = f"\n⚠️ Gagal kirim DM: {str(e)[:60]}"
    em = dark_red_embed("⚠️ Member Di-Warn!", f"**{member.display_name}** dapet warn!\n**Alasan:** {alasan}\n**Total:** {count}{dm_status}")
    await interaction.response.send_message(embed=em)

@tree.command(name="kick", description="Kick member dari server")
@app_commands.default_permissions(kick_members=True)
async def slash_kick(interaction: discord.Interaction, member: discord.Member, alasan: str = "Gak ada alasan"):
    await member.kick(reason=alasan)
    await interaction.response.send_message(embed=dark_red_embed("👢 Di-Kick!", f"**{member.display_name}** dikick. Alasan: {alasan}"))

@tree.command(name="ban", description="Ban member dari server")
@app_commands.default_permissions(ban_members=True)
async def slash_ban(interaction: discord.Interaction, member: discord.Member, alasan: str = "Gak ada alasan"):
    await member.ban(reason=alasan)
    await interaction.response.send_message(embed=dark_red_embed("🔨 Di-Ban!", f"**{member.display_name}** dibanned. Alasan: {alasan}"))

@tree.command(name="timeout", description="Timeout member")
@app_commands.default_permissions(moderate_members=True)
async def slash_timeout(interaction: discord.Interaction, member: discord.Member, menit: int = 10, alasan: str = "Gak ada alasan"):
    until = discord.utils.utcnow() + datetime.timedelta(minutes=menit)
    await member.timeout(until, reason=alasan)
    await interaction.response.send_message(embed=dark_red_embed("⏱️ Timeout!", f"**{member.display_name}** di-timeout {menit} menit!"))

@tree.command(name="clear", description="Hapus pesan")
@app_commands.describe(jumlah="Jumlah pesan yang mau dihapus")
@app_commands.default_permissions(manage_messages=True)
async def slash_clear(interaction: discord.Interaction, jumlah: int = 5):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=jumlah)
    await interaction.followup.send(f"✅ {jumlah} pesan dihapus!", ephemeral=True)

@tree.command(name="avatar", description="Lihat avatar member")
async def slash_avatar(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    em = dark_red_embed(f"🖼️ Avatar {member.display_name}")
    em.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=em)

@tree.command(name="userinfo", description="Info lengkap user")
async def slash_userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    em = dark_red_embed(f"👤 Info {member.display_name}")
    em.set_thumbnail(url=member.display_avatar.url)
    em.add_field(name="Username", value=str(member), inline=True)
    em.add_field(name="ID", value=member.id, inline=True)
    em.add_field(name="Join Date", value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
    em.add_field(name="Roles", value=", ".join([r.name for r in member.roles[1:]]) or "Gak ada", inline=False)
    premium_status = "👑 PREMIUM" if is_premium_user(str(member.id)) else "Bukan Premium"
    em.add_field(name="Premium", value=premium_status, inline=True)
    await interaction.response.send_message(embed=em)

@tree.command(name="addrole", description="Tambah role ke member")
@app_commands.default_permissions(manage_roles=True)
async def slash_addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await interaction.response.send_message(embed=dark_red_embed("✅ Role Ditambah!", f"**{role.name}** dikasih ke **{member.display_name}**!"))

@tree.command(name="removerole", description="Copot role dari member")
@app_commands.default_permissions(manage_roles=True)
async def slash_removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await interaction.response.send_message(embed=dark_red_embed("❌ Role Dicopot!", f"**{role.name}** dicopot dari **{member.display_name}**!"))

@tree.command(name="embed", description="Kirim embed message")
@app_commands.describe(judul="Judul embed", deskripsi="Isi embed")
@app_commands.default_permissions(manage_messages=True)
async def slash_embed(interaction: discord.Interaction, judul: str, deskripsi: str):
    await interaction.response.send_message(embed=dark_red_embed(judul, deskripsi))

@tree.command(name="sticky", description="Setup sticky message di channel")
@app_commands.describe(aksi="set atau remove", pesan="Isi sticky message", min_pesan="Minimum pesan sebelum sticky muncul")
@app_commands.default_permissions(manage_messages=True)
async def slash_sticky(interaction: discord.Interaction, aksi: str, pesan: str = None, min_pesan: int = 3):
    gid = str(interaction.guild.id)
    cid = str(interaction.channel.id)
    sticky = get_sticky()
    if gid not in sticky:
        sticky[gid] = {}
    if aksi == "set" and pesan:
        sticky[gid][cid] = {"content": pesan, "min_messages": min_pesan, "count": 0}
        save_sticky(sticky)
        await interaction.response.send_message(f"✅ Sticky diset! Trigger tiap **{min_pesan} pesan**.", ephemeral=True)
    elif aksi == "remove":
        if cid in sticky.get(gid, {}):
            del sticky[gid][cid]
            save_sticky(sticky)
        await interaction.response.send_message("✅ Sticky dihapus!", ephemeral=True)
    else:
        await interaction.response.send_message("❓ Aksi: `set` atau `remove`", ephemeral=True)

@tree.command(name="autoresponse", description="Setup auto response")
@app_commands.describe(aksi="add/remove/list", trigger="Kata trigger", balasan="Balasan bot")
@app_commands.default_permissions(administrator=True)
async def slash_autoresponse(interaction: discord.Interaction, aksi: str, trigger: str = None, balasan: str = None):
    gid = str(interaction.guild.id)
    ar = get_autoresponse()
    if gid not in ar:
        ar[gid] = {}
    if aksi == "add" and trigger and balasan:
        ar[gid][trigger] = balasan
        save_autoresponse(ar)
        await interaction.response.send_message(f"✅ Auto-respon **'{trigger}'** ditambah!", ephemeral=True)
    elif aksi == "remove" and trigger:
        ar[gid].pop(trigger, None)
        save_autoresponse(ar)
        await interaction.response.send_message(f"✅ Auto-respon **'{trigger}'** dihapus!", ephemeral=True)
    elif aksi == "list":
        text = "\n".join([f"• **{k}** → {v}" for k, v in ar.get(gid, {}).items()]) or "Belum ada"
        await interaction.response.send_message(embed=dark_red_embed("📋 Auto-Respon", text), ephemeral=True)
    else:
        await interaction.response.send_message("❓ Aksi: `add`, `remove`, atau `list`", ephemeral=True)

@tree.command(name="event", description="Kirim pesan event ke channel")
@app_commands.describe(
    nama="Nama event",
    deskripsi="Deskripsi event",
    jam_mulai="Jam mulai event WIB (contoh: 19:00)",
    channel="Channel tujuan announce (opsional)"
)
@app_commands.default_permissions(administrator=True)
async def slash_event(interaction: discord.Interaction, nama: str, deskripsi: str, jam_mulai: str, channel: discord.TextChannel = None):
    target_channel = channel or interaction.channel
    em = dark_red_embed(
        f"📅 EVENT: {nama}",
        f"{deskripsi}\n\n⏰ **Jam Mulai:** {jam_mulai} WIB\n\n📢 Jangan sampe ketinggalan! Gas ikutan! 🔥"
    )
    em.set_footer(text=f"Event dibuat oleh {interaction.user.display_name}")
    em.timestamp = datetime.datetime.now(tz=WIB)
    event_msg = await target_channel.send(content="@everyone", embed=em)
    reply_text = f"✅ Event **{nama}** berhasil dikirim ke {target_channel.mention}!"
    try:
        now_wib = datetime.datetime.now(tz=WIB)
        naive = datetime.datetime.strptime(jam_mulai, "%H:%M")
        event_time = now_wib.replace(hour=naive.hour, minute=naive.minute, second=0, microsecond=0)
        if event_time <= now_wib:
            event_time += datetime.timedelta(days=1)
        delay = (event_time - now_wib).total_seconds()

        async def send_event_start(target_ch, ev_msg, ev_nama, ev_desc, ev_jam, scheduled_ts):
            await asyncio.sleep(max(0, (scheduled_ts - datetime.datetime.now(tz=WIB)).total_seconds()))
            start_em = dark_red_embed(
                f"🚨 EVENT MULAI SEKARANG: {ev_nama}!",
                f"**{ev_desc}**\n\n🔥 EVENT UDAH DIMULAI GAES! BURUAN GABUNG!\n⏰ Jam: **{ev_jam} WIB**"
            )
            start_em.set_footer(text="Jangan sampai ketinggalan! 🔥")
            start_em.timestamp = datetime.datetime.now(tz=WIB)
            try:
                await ev_msg.edit(embed=start_em)
            except Exception:
                pass
            try:
                await target_ch.send(content="@everyone 🚨 **EVENT DIMULAI SEKARANG!** 🚨")
            except Exception:
                pass

        asyncio.create_task(send_event_start(
            target_channel, event_msg, nama, deskripsi, jam_mulai, event_time
        ))
        reply_text += f"\n⏰ Auto-announce dijadwalkan jam **{jam_mulai} WIB** ({int(delay//60)} menit lagi)."
    except ValueError:
        reply_text += "\n⚠️ Format jam tidak dikenali (gunakan HH:MM), reminder otomatis dinonaktifkan."
    await interaction.response.send_message(reply_text, ephemeral=True)

@tree.command(name="tebak", description="Main tebak-tebakan!")
async def slash_tebak(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    if gid in active_tebakan:
        await interaction.response.send_message("⚠️ Masih ada tebakan yang belum kejawab bro!", ephemeral=True)
        return
    semua_soal = TEBAKAN_LIST + get_custom_tebakan()
    soal = random.choice(semua_soal)
    active_tebakan[gid] = {"jawaban": soal["jawaban"].lower().strip(), "reward": soal["reward"], "asker": interaction.user.id}
    em = dark_red_embed("🧠 TEBAK-TEBAKAN!", f"**Soal:**\n{soal['soal']}\n\n💡 Reward: **{soal['reward']} koin**")
    await interaction.response.send_message(embed=em)

@tree.command(name="addtebak", description="Tambah soal tebakan custom (Admin)")
@app_commands.describe(soal="Pertanyaan tebakan", jawaban="Jawaban benar", reward="Reward koin (default: 25)")
@app_commands.default_permissions(administrator=True)
async def slash_addtebak(interaction: discord.Interaction, soal: str, jawaban: str, reward: int = 25):
    custom = get_custom_tebakan()
    custom.append({"soal": soal, "jawaban": jawaban.lower(), "reward": reward})
    save_custom_tebakan(custom)
    em = dark_red_embed(
        "✅ Soal Tebakan Ditambah!",
        f"**Soal:** {soal}\n**Jawaban:** {jawaban}\n**Reward:** {reward} koin\n\nTotal soal custom: **{len(custom)}**"
    )
    await interaction.response.send_message(embed=em, ephemeral=True)

@tree.command(name="coins", description="Cek koin lo")
async def slash_coins(interaction: discord.Interaction):
    udata = get_user_fishing(str(interaction.user.id))
    await interaction.response.send_message(
        embed=dark_red_embed("🪙 Koin Lo", f"**{interaction.user.display_name}** punya **{udata['coins']} koin** 🪙"),
        ephemeral=True
    )

@tree.command(name="leaderboard", description="Lihat leaderboard level")
async def slash_leaderboard(interaction: discord.Interaction):
    levels = get_levels()
    gid = str(interaction.guild.id)
    guild_levels = levels.get(gid, {})
    sorted_users = sorted(guild_levels.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)[:10]
    if not sorted_users:
        await interaction.response.send_message("📊 Belum ada data level nih!", ephemeral=True)
        return
    text = ""
    for i, (uid, data) in enumerate(sorted_users):
        member = interaction.guild.get_member(int(uid))
        name = member.display_name if member else f"User {uid[:6]}"
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
        text += f"{medal} **{name}** - Level {data['level']} ({data['xp']} XP)\n"
    await interaction.response.send_message(embed=dark_red_embed("🏆 Leaderboard Level", text))

@tree.command(name="listfishingreward", description="Lihat semua reward ikan fishing saat ini")
async def slash_listfishingreward(interaction: discord.Interaction):
    fish_list = get_fish_list()
    rarity_order = ["legendary", "rare", "uncommon", "common", "trash"]
    rarity_label = {
        "legendary": "⭐ Legendary", "rare": "💎 Rare",
        "uncommon": "🔵 Uncommon", "common": "⚪ Common", "trash": "💩 Trash"
    }
    lines = []
    for r in rarity_order:
        group = [f for f in fish_list if f.get("rarity") == r]
        if group:
            lines.append(f"**{rarity_label[r]}**")
            for f in group:
                sell = f.get("sell_price", f.get("value", 0))
                luck = f.get("luck_chance", 0)
                lines.append(f"  {f.get('emoji','🐟')} {f['name']} → Jual: **{sell}** 🪙 | Luck: **{luck}%**")
    em = dark_red_embed("🐟 Daftar Reward Fishing", "\n".join(lines))
    await interaction.response.send_message(embed=em, ephemeral=True)

# ===================== ERROR HANDLERS =====================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply(embed=dark_red_embed("❌ No Permission!", "Lo gak punya izin buat command ini bro!"))
    elif isinstance(error, commands.MemberNotFound):
        await ctx.reply(embed=dark_red_embed("❌ Member Gak Ketemu!", "Member yang lo mention gak ada bro!"))
    elif isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.CheckFailure):
        pass  # Sudah dihandle di check function
    else:
        print(f"Error: {error}")

# ===================== RUN =====================
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
