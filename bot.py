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
import sqlite3
from pathlib import Path

# Timezone WIB (UTC+7)
WIB = zoneinfo.ZoneInfo("Asia/Jakarta")

# ===================== CONFIG =====================
PREFIX = "!Doom"
BOT_TOKEN = os.getenv("DISCORD_TOKEN", "YOUR_BOT_TOKEN_HERE")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "0"))
DARK_RED = 0x8B0000

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ===================== PREMIUM PACKAGES =====================
premium_packages = {
    "basic": {
        "name": "Basic",
        "price": "Rp10.000",
        "days": 7,
        "emoji": "⭐"
    },
    "pro": {
        "name": "Pro",
        "price": "Rp25.000",
        "days": 15,
        "emoji": "💎"
    },
    "ultimate": {
        "name": "Ultimate",
        "price": "Rp50.000",
        "days": 30,
        "emoji": "👑"
    }
}

# Command yang butuh premium (guild-based)
premium_commands = ["ticket", "autoreply", "customrole"]

# ===================== DATABASE (SQLite) =====================
DB_PATH = DATA_DIR / "premium.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS premium_guilds (
            guild_id TEXT PRIMARY KEY,
            expired_at INTEGER NOT NULL,
            package_key TEXT NOT NULL,
            activated_at INTEGER NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS premium_roles (
            guild_id TEXT PRIMARY KEY,
            role_id TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def is_guild_premium(guild_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT expired_at FROM premium_guilds WHERE guild_id = ?", (guild_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return False
    return int(time.time()) < row[0]

def get_guild_premium_info(guild_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT expired_at, package_key, activated_at FROM premium_guilds WHERE guild_id = ?", (guild_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        return None
    if int(time.time()) >= row[0]:
        return None
    return {"expired_at": row[0], "package_key": row[1], "activated_at": row[2]}

def set_guild_premium(guild_id: str, package_key: str):
    days = premium_packages[package_key]["days"]
    expired_at = int(time.time()) + days * 86400
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO premium_guilds (guild_id, expired_at, package_key, activated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET
            expired_at=excluded.expired_at,
            package_key=excluded.package_key,
            activated_at=excluded.activated_at
    """, (guild_id, expired_at, package_key, int(time.time())))
    conn.commit()
    conn.close()
    return expired_at

def get_premium_role(guild_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role_id FROM premium_roles WHERE guild_id = ?", (guild_id,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def set_premium_role(guild_id: str, role_id: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO premium_roles (guild_id, role_id) VALUES (?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET role_id=excluded.role_id
    """, (guild_id, role_id))
    conn.commit()
    conn.close()

# ===================== JSON HELPERS =====================
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

# ===================== FISHING DATA =====================
RODS = {
    "Pancing Bambu": {"tier": 1, "price": 50, "catch_bonus": 1.0, "emoji": "🎋"},
    "Pancing Kayu": {"tier": 2, "price": 150, "catch_bonus": 1.3, "emoji": "🪵"},
    "Pancing Besi": {"tier": 3, "price": 400, "catch_bonus": 1.7, "emoji": "🔩"},
    "Pancing Karbon": {"tier": 4, "price": 900, "catch_bonus": 2.2, "emoji": "⚫"},
    "Pancing Titan": {"tier": 5, "price": 2000, "catch_bonus": 3.0, "emoji": "🔱"},
    "Pancing Legenda": {"tier": 6, "price": 5000, "catch_bonus": 5.0, "emoji": "⚡"},
}

BAITS = {
    "Cacing Biasa": {"price": 10, "bonus": 1.0, "emoji": "🪱"},
    "Cacing Gemuk": {"price": 25, "bonus": 1.5, "emoji": "🐛"},
    "Jangkrik": {"price": 40, "bonus": 2.0, "emoji": "🦗"},
    "Udang Kecil": {"price": 60, "bonus": 2.5, "emoji": "🦐"},
    "Ikan Kecil": {"price": 100, "bonus": 3.5, "emoji": "🐟"},
}

FISHES = [
    {"name": "Ikan Lele", "value": 15, "rarity": "common", "emoji": "🐟"},
    {"name": "Ikan Mas", "value": 25, "rarity": "common", "emoji": "🐠"},
    {"name": "Ikan Gurame", "value": 40, "rarity": "uncommon", "emoji": "🐡"},
    {"name": "Ikan Salmon", "value": 60, "rarity": "uncommon", "emoji": "🐟"},
    {"name": "Ikan Tuna", "value": 100, "rarity": "rare", "emoji": "🐟"},
    {"name": "Ikan Hiu Kecil", "value": 200, "rarity": "rare", "emoji": "🦈"},
    {"name": "Ikan Duyung", "value": 500, "rarity": "legendary", "emoji": "🧜"},
    {"name": "Ikan Naga", "value": 1000, "rarity": "legendary", "emoji": "🐉"},
    {"name": "Sampah", "value": 0, "rarity": "trash", "emoji": "🗑️"},
    {"name": "Bot Bekas", "value": 5, "rarity": "trash", "emoji": "🤖"},
]

SHOP_REWARDS = {
    "Role VIP": {"price": 500, "type": "role", "description": "Role VIP eksklusif buat lo"},
    "Role Elite": {"price": 2000, "type": "role", "description": "Role Elite super langka"},
    "Role Legend": {"price": 10000, "type": "role", "description": "Role paling epic di server"},
    "Custom Color Role": {"price": 800, "type": "role", "description": "Role warna custom buat lo"},
}

# ===================== TEBAK-TEBAKAN =====================
TEBAKAN_LIST = [
    {"soal": "Apa yang selalu datang tapi gak pernah sampe?", "jawaban": "besok", "reward": 20},
    {"soal": "Makin diisi makin ringan, apa tuh?", "jawaban": "balon", "reward": 25},
    {"soal": "Punya kaki tapi ga bisa jalan, punya lidah tapi ga bisa ngomong. Apa coba?", "jawaban": "sepatu", "reward": 30},
    {"soal": "Apa yang bisa terbang tapi ga punya sayap?", "jawaban": "waktu", "reward": 25},
    {"soal": "Makin tua makin pendek, apa itu?", "jawaban": "lilin", "reward": 20},
    {"soal": "Ada di depan kita tapi ga bisa diliat. Apaan tuh?", "jawaban": "masa depan", "reward": 35},
    {"soal": "Sekali lahir langsung mati. Apa itu?", "jawaban": "korek api", "reward": 20},
    {"soal": "Semakin banyak diambil, semakin besar. Apaan?", "jawaban": "lubang", "reward": 30},
    {"soal": "Apa yang punya gigi tapi ga bisa gigit?", "jawaban": "sisir", "reward": 25},
    {"soal": "Terbalik tetap sama. Apa itu?", "jawaban": "angka 8", "reward": 30},
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

def dark_red_embed(title="", description="", **kwargs):
    em = discord.Embed(title=title, description=description, color=DARK_RED, **kwargs)
    return em

fishing_cooldowns = {}
active_tebakan = {}

# ===================== PREMIUM CHECK HELPER =====================
def check_premium(guild_id: str) -> bool:
    return is_guild_premium(guild_id)

# ===================== EVENTS =====================
@bot.event
async def on_ready():
    init_db()
    print(f"✅ {bot.user} udah nyala bro!")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="RepublikDooms | !Doom help")
    )
    try:
        synced = await tree.sync()
        print(f"✅ {len(synced)} slash commands synced!")
    except Exception as e:
        print(f"❌ Sync error: {e}")
    check_giveaways.start()
    check_sticky.start()
    check_expired_premium.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = str(message.guild.id) if message.guild else None
    content_lower = message.content.lower()

    # Auto response
    if guild_id:
        ar = get_autoresponse()
        if guild_id in ar:
            for trigger, response in ar[guild_id].items():
                if trigger.lower() in content_lower:
                    await message.channel.send(response)
                    break

    # Tebak-tebakan answer check
    if guild_id and guild_id in active_tebakan:
        tb = active_tebakan[guild_id]
        if message.author.id != tb["asker"] and tb["jawaban"].lower() in content_lower:
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
                channel = guild.get_channel(int(gw["channel_id"]))
                if not channel:
                    continue
                try:
                    msg = await channel.fetch_message(int(msg_id))
                    reaction = discord.utils.get(msg.reactions, emoji="🎉")
                    users = []
                    if reaction:
                        async for user in reaction.users():
                            if not user.bot:
                                users.append(user)
                    if users:
                        winner = random.choice(users)
                        win_em = dark_red_embed(
                            "🎉 GIVEAWAY SELESAI!",
                            f"**Hadiah:** {gw['prize']}\n🏆 **Pemenang:** {winner.mention}\nSelamat ya bro!"
                        )
                        await channel.send(embed=win_em)
                        await msg.edit(embed=dark_red_embed("🎉 GIVEAWAY ENDED", f"**Hadiah:** {gw['prize']}\n🏆 Pemenang: {winner.mention}"))
                    else:
                        await channel.send(embed=dark_red_embed("😢 Giveaway Berakhir", f"**{gw['prize']}** — Gak ada yang ikutan bro!"))
                except Exception as e:
                    print(f"Giveaway error: {e}")
                gw_data[gid][msg_id]["ended"] = True
    save_giveaways(gw_data)

@tasks.loop(seconds=15)
async def check_sticky():
    pass

@tasks.loop(minutes=10)
async def check_expired_premium():
    """Auto-clean expired premium dari DB"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM premium_guilds WHERE expired_at < ?", (int(time.time()),))
    conn.commit()
    conn.close()

# ===================== FISHING VIEW =====================
class FishingMainView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="🎣 Mancing!", style=discord.ButtonStyle.danger, row=0)
    async def mancing(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Ini bukan sesi mancing lo bro!", ephemeral=True)
            return
        uid = str(interaction.user.id)
        now = time.time()
        cooldown = 30
        last = fishing_cooldowns.get(uid, 0)
        sisa = int(cooldown - (now - last))
        if sisa > 0:
            await interaction.response.send_message(f"⏳ Sabar bro! **{sisa} detik** lagi. Emang mancing bisa buru-buru? wkwk", ephemeral=True)
            return
        fishing_cooldowns[uid] = now
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
        weights = []
        fish_pool = FISHES.copy()
        for f in fish_pool:
            w = {"legendary": 2, "rare": 10, "uncommon": 25, "common": 50, "trash": 13}[f["rarity"]]
            weights.append(int(w * rod["catch_bonus"] * bait_bonus) if f["rarity"] != "trash" else w)
        caught = random.choices(fish_pool, weights=weights, k=1)[0]
        coins_earned = int(caught["value"] * rod["catch_bonus"] * bait_bonus)
        udata["coins"] += coins_earned
        udata["total_catch"] += 1
        udata["inventory"].append(caught["name"])
        save_user_fishing(uid, udata)
        rarity_colors = {"legendary": "⭐⭐⭐", "rare": "⭐⭐", "uncommon": "⭐", "common": "", "trash": "💩"}
        em = dark_red_embed(
            f"{caught['emoji']} Hasil Mancing!",
            f"**{interaction.user.display_name}** dapet **{caught['name']}** {rarity_colors[caught['rarity']]}\n"
            f"🪙 +{coins_earned} koin (Total: {udata['coins']})\n"
            f"🎣 Rod: {rod['emoji']} {udata['rod']}\n"
            + (f"🪱 Umpan: {used_bait}" if used_bait else "⚠️ Gak pake umpan!")
        )
        await interaction.response.edit_message(embed=em, view=self)

    @discord.ui.button(label="🎒 Inventori", style=discord.ButtonStyle.secondary, row=0)
    async def inventory(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Lo gak bisa liat inventori orang lain bro!", ephemeral=True)
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
        reward_text = "\n".join([f"🎁 **{k}** - {v['price']} 🪙" for k, v in SHOP_REWARDS.items()])
        em = dark_red_embed(
            "🏪 Fishing Shop",
            f"**Koin lo:** {udata['coins']} 🪙\n\n**🎣 Rod:**\n{rod_text}\n\n**🪱 Umpan:**\n{bait_text}\n\n**🎁 Reward Spesial:**\n{reward_text}"
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
        await interaction.response.send_message(f"✅ Berhasil beli **{item}**! Sisa koin: {udata['coins']} 🪙", ephemeral=True)

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

# ===================== REACTION ROLE VIEW =====================
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

# ===================== LEVELING SETUP VIEW =====================
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

# ===================== TICKET SYSTEM (FIXED) =====================
class TicketView(discord.ui.View):
    def __init__(self, panel_config: dict):
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
        user = interaction.user
        category_id = self.panel_config.get("category_id")
        category = None
        if category_id:
            category = guild.get_channel(int(category_id))

        # Cek apakah sudah punya ticket terbuka
        existing = discord.utils.get(
            guild.text_channels,
            name=f"ticket-{user.name.lower().replace(' ', '-')}"
        )
        if existing:
            await interaction.response.send_message(
                f"❌ Lo udah punya ticket terbuka bro: {existing.mention}",
                ephemeral=True
            )
            return

        # Buat channel ticket
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        # Tambah akses untuk admin
        for role in guild.roles:
            if role.permissions.administrator:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            ticket_ch = await guild.create_text_channel(
                name=f"ticket-{user.name.lower().replace(' ', '-')}",
                overwrites=overwrites,
                category=category,
                topic=f"Ticket milik {user} | ID: {user.id}"
            )
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot gak punya izin buat bikin channel bro!", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"❌ Error bikin ticket: {str(e)[:100]}", ephemeral=True)
            return

        em = dark_red_embed(
            "🎫 Ticket Dibuka!",
            f"Halo {user.mention}! 👋\n\nTiket lo udah dibuat. Ceritain masalah lo di sini ya!\nAdmin akan segera merespons.\n\n**Klik tombol di bawah untuk menutup ticket.**"
        )
        em.set_footer(text=f"Ticket ID: {ticket_ch.id}")
        close_view = TicketCloseView(user.id)
        await ticket_ch.send(content=user.mention, embed=em, view=close_view)
        await interaction.response.send_message(
            f"✅ Ticket lo berhasil dibuat: {ticket_ch.mention}",
            ephemeral=True
        )

class TicketCloseView(discord.ui.View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="🔒 Tutup Ticket", style=discord.ButtonStyle.danger, custom_id="ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Owner ticket atau admin bisa close
        is_admin = interaction.user.guild_permissions.administrator
        is_owner = interaction.user.id == self.owner_id
        if not is_admin and not is_owner:
            await interaction.response.send_message("❌ Hanya owner ticket atau admin yang bisa nutup ini bro!", ephemeral=True)
            return

        em = dark_red_embed("🔒 Ticket Ditutup", f"Ticket ditutup oleh **{interaction.user.display_name}**.\nChannel akan dihapus dalam 5 detik...")
        await interaction.response.send_message(embed=em)
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Ticket ditutup oleh {interaction.user}")
        except Exception:
            pass

# ===================== PREMIUM VIEWS =====================
class PremiumPackageSelect(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        options = [
            discord.SelectOption(
                label=f"{pkg['emoji']} {pkg['name']}",
                value=key,
                description=f"{pkg['price']} - {pkg['days']} hari"
            )
            for key, pkg in premium_packages.items()
        ]
        select = discord.ui.Select(
            placeholder="Pilih paket premium...",
            options=options,
            custom_id="premium_select"
        )
        select.callback = self.on_select
        self.add_item(select)

    async def on_select(self, interaction: discord.Interaction):
        selected_key = interaction.data["values"][0]
        pkg = premium_packages[selected_key]

        em = dark_red_embed(
            f"{pkg['emoji']} Paket {pkg['name']} Dipilih!",
            f"**Harga:** {pkg['price']}\n**Durasi:** {pkg['days']} hari\n\n"
            f"Silakan transfer ke QRIS di bawah, lalu klik **Kirim Bukti** setelah bayar ya bro! 💸"
        )
        em.set_image(url="attachment://qris.png")
        em.set_footer(text="Pembayaran akan diverifikasi oleh admin")

        qris_file = discord.File("qris.png", filename="qris.png")
        proof_view = SendProofView(selected_key, interaction.user, interaction.guild)

        await interaction.response.edit_message(
            embed=em,
            attachments=[qris_file],
            view=proof_view
        )

class SendProofView(discord.ui.View):
    def __init__(self, package_key: str, user: discord.User, guild: discord.Guild):
        super().__init__(timeout=300)
        self.package_key = package_key
        self.user = user
        self.guild = guild

    @discord.ui.button(label="📸 Kirim Bukti Bayar", style=discord.ButtonStyle.success, custom_id="send_proof")
    async def send_proof(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ Ini bukan sesi lo bro!", ephemeral=True)
            return

        await interaction.response.send_message(
            "📸 Kirim screenshot bukti pembayaran lo di sini (timeout: 3 menit):",
            ephemeral=True
        )

        def check(m):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id and m.attachments

        try:
            proof_msg = await bot.wait_for("message", check=check, timeout=180)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Timeout! Coba kirim bukti lagi.", ephemeral=True)
            return

        pkg = premium_packages[self.package_key]

        # Kirim ke log channel
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            now_wib = datetime.datetime.now(tz=WIB)
            log_em = dark_red_embed(
                "📥 Permintaan Premium Baru!",
                f"**👤 User:** {self.user} (`{self.user.id}`)\n"
                f"**🏠 Server:** {self.guild.name} (`{self.guild.id}`)\n"
                f"**📦 Paket:** {pkg['emoji']} {pkg['name']}\n"
                f"**💰 Harga:** {pkg['price']}\n"
                f"**⏳ Durasi:** {pkg['days']} hari\n"
                f"**🕐 Waktu:** {now_wib.strftime('%d/%m/%Y %H:%M')} WIB"
            )
            log_em.set_footer(text=f"Guild ID: {self.guild.id} | Package: {self.package_key}")

            # Kirim bukti pembayaran
            proof_attachment = proof_msg.attachments[0]
            log_em.set_image(url=proof_attachment.url)

            approve_reject_view = ApproveRejectView(
                guild_id=str(self.guild.id),
                user_id=str(self.user.id),
                package_key=self.package_key,
                requester_channel_id=str(interaction.channel.id)
            )
            await log_channel.send(embed=log_em, view=approve_reject_view)

        await interaction.followup.send(
            embed=dark_red_embed(
                "✅ Bukti Terkirim!",
                f"Bukti pembayaran lo udah dikirim ke admin bro!\n"
                f"Tunggu konfirmasi ya, biasanya gak lama kok 🙏\n\n"
                f"**Paket:** {pkg['emoji']} {pkg['name']}\n"
                f"**Harga:** {pkg['price']}\n"
                f"**Durasi:** {pkg['days']} hari"
            ),
            ephemeral=True
        )

        # Hapus pesan bukti dari channel umum
        try:
            await proof_msg.delete()
        except:
            pass

class ApproveRejectView(discord.ui.View):
    def __init__(self, guild_id: str, user_id: str, package_key: str, requester_channel_id: str):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.user_id = user_id
        self.package_key = package_key
        self.requester_channel_id = requester_channel_id

    @discord.ui.button(label="✅ Approve", style=discord.ButtonStyle.success, custom_id="premium_approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Hanya admin yang bisa approve bro!", ephemeral=True)
            return

        pkg = premium_packages[self.package_key]
        expired_at = set_guild_premium(self.guild_id, self.package_key)
        expired_dt = datetime.datetime.fromtimestamp(expired_at, tz=WIB)

        # Tambah role premium jika ada
        guild = bot.get_guild(int(self.guild_id))
        role_warning = ""
        if guild:
            role_id = get_premium_role(self.guild_id)
            if role_id:
                role = guild.get_role(int(role_id))
                member = guild.get_member(int(self.user_id))
                if role and member:
                    try:
                        await member.add_roles(role)
                    except Exception as e:
                        role_warning = f"\n⚠️ Gagal assign role: {str(e)[:50]}"
                else:
                    role_warning = "\n⚠️ Role atau member tidak ditemukan."
            else:
                role_warning = "\n⚠️ Premium role belum diset di server ini."

        # Update embed log
        em = interaction.message.embeds[0]
        em.color = 0x00FF00
        em.title = "✅ APPROVED - " + (em.title or "Premium Request")
        em.add_field(
            name="✅ Diapprove oleh",
            value=f"{interaction.user.mention} • {datetime.datetime.now(tz=WIB).strftime('%d/%m/%Y %H:%M')} WIB",
            inline=False
        )
        em.add_field(
            name="⏳ Expired",
            value=expired_dt.strftime('%d/%m/%Y %H:%M') + " WIB",
            inline=False
        )

        # Disable buttons
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=em, view=self)

        # Notif ke user
        try:
            user = await bot.fetch_user(int(self.user_id))
            notif_em = dark_red_embed(
                "🎉 Premium Diaktifkan!",
                f"Selamat bro! Premium server **{guild.name if guild else self.guild_id}** lo udah aktif!\n\n"
                f"**📦 Paket:** {pkg['emoji']} {pkg['name']}\n"
                f"**⏳ Expired:** {expired_dt.strftime('%d/%m/%Y %H:%M')} WIB\n\n"
                f"Enjoy fitur premium nya ya! 🔥{role_warning}"
            )
            await user.send(embed=notif_em)
        except Exception:
            pass

        await interaction.followup.send(
            f"✅ Premium **{pkg['name']}** berhasil diaktifkan untuk guild `{self.guild_id}`!{role_warning}",
            ephemeral=True
        )

    @discord.ui.button(label="❌ Reject", style=discord.ButtonStyle.danger, custom_id="premium_reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Hanya admin yang bisa reject bro!", ephemeral=True)
            return

        # Update embed log
        em = interaction.message.embeds[0]
        em.color = 0xFF0000
        em.title = "❌ REJECTED - " + (em.title or "Premium Request")
        em.add_field(
            name="❌ Direject oleh",
            value=f"{interaction.user.mention} • {datetime.datetime.now(tz=WIB).strftime('%d/%m/%Y %H:%M')} WIB",
            inline=False
        )

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=em, view=self)

        # Notif ke user
        try:
            user = await bot.fetch_user(int(self.user_id))
            guild = bot.get_guild(int(self.guild_id))
            notif_em = dark_red_embed(
                "❌ Pembayaran Ditolak",
                f"Maaf bro, bukti pembayaran premium server **{guild.name if guild else self.guild_id}** lo ditolak.\n\n"
                f"Kemungkinan alasan:\n"
                f"• Bukti tidak jelas / blur\n"
                f"• Jumlah transfer tidak sesuai\n"
                f"• Bukti sudah kadaluarsa\n\n"
                f"Coba lagi dengan bukti yang valid ya! Atau DM admin untuk info lebih lanjut."
            )
            await user.send(embed=notif_em)
        except Exception:
            pass

        await interaction.followup.send("❌ Pembayaran berhasil direject.", ephemeral=True)

# ===================== PREFIX COMMANDS =====================

# --- AI Chat ---
@bot.command(name="ai")
async def ai_chat(ctx, *, question: str = None):
    if not question:
        await ctx.reply("❓ Tanya apa dulu bro? Contoh: `!Doom ai siapa itu elon musk?`")
        return
    async with ctx.typing():
        resp = await get_ai_response(question)
    em = dark_red_embed(f"🤖 RepublikDooms AI", resp)
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
        "jawaban": soal["jawaban"].lower(),
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
        await ctx.reply("❓ Format: `!Doom addtebak Pertanyaan lo|jawaban|reward_koin`\nContoh: `!Doom addtebak Ibu kota Indonesia?|jakarta|50`")
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
        f"**Soal:** {soal}\n**Jawaban:** {jawaban}\n**Reward:** {reward} koin\n\nTotal soal custom: **{len(custom)}**"
    )
    await ctx.reply(embed=em)

@bot.command(name="listtebak")
async def listtebak_cmd(ctx):
    custom = get_custom_tebakan()
    if not custom:
        await ctx.reply("📋 Belum ada soal tebakan custom. Tambah pake `!Doom addtebak`!")
        return
    lines = [f"{i+1}. {s['soal']} → **{s['jawaban']}** ({s['reward']} koin)" for i, s in enumerate(custom)]
    em = dark_red_embed("📋 Soal Tebakan Custom", "\n".join(lines[:20]))
    em.set_footer(text=f"Total: {len(custom)} soal custom | Default: {len(TEBAKAN_LIST)} soal")
    await ctx.reply(embed=em)

@bot.command(name="removetebak")
@commands.has_permissions(administrator=True)
async def removetebak_cmd(ctx, nomor: int = None):
    if not nomor:
        await ctx.reply("❓ Format: `!Doom removetebak [nomor]` — lihat nomor pake `!Doom listtebak`")
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

@bot.command(name="timeout")
@commands.has_permissions(moderate_members=True)
async def timeout_cmd(ctx, member: discord.Member = None, menit: int = 10, *, reason="Gak ada alasan"):
    if not member:
        await ctx.reply("❓ Mention member dulu bro!")
        return
    until = discord.utils.utcnow() + datetime.timedelta(minutes=menit)
    await member.timeout(until, reason=reason)
    em = dark_red_embed("⏱️ Member Di-Timeout!", f"**{member.display_name}** di-timeout **{menit} menit**!\n**Alasan:** {reason}")
    await ctx.send(embed=em)

@bot.command(name="move")
@commands.has_permissions(move_members=True)
async def move(ctx, member: discord.Member = None, *, channel: discord.VoiceChannel = None):
    if not member or not channel:
        await ctx.reply("❓ Format: `!Doom move @member #channel`")
        return
    await member.move_to(channel)
    em = dark_red_embed("🔀 Member Di-Move!", f"**{member.display_name}** dipindah ke **{channel.name}**!")
    await ctx.send(embed=em)

@bot.command(name="addrole")
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member = None, role: discord.Role = None):
    if not member or not role:
        await ctx.reply("❓ Format: `!Doom addrole @member @role`")
        return
    await member.add_roles(role)
    em = dark_red_embed("✅ Role Ditambah!", f"**{role.name}** dikasih ke **{member.display_name}**!")
    await ctx.send(embed=em)

@bot.command(name="removerole")
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member = None, role: discord.Role = None):
    if not member or not role:
        await ctx.reply("❓ Format: `!Doom removerole @member @role`")
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
        await ctx.reply("❓ Format: `!Doom embed Judul|Deskripsi`")
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
        await ctx.reply("❓ Format:\n`!Doom ar add [trigger] [response]`\n`!Doom ar remove [trigger]`\n`!Doom ar list`")

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
        await ctx.reply("❓ Format:\n`!Doom sticky set [isi pesan]|[min pesan]`\n`!Doom sticky remove`")

@bot.command(name="giveaway", aliases=["ga"])
@commands.has_permissions(administrator=True)
async def giveaway_cmd(ctx, duration: str = None, *, prize: str = None):
    if not duration or not prize:
        await ctx.reply("❓ Format: `!Doom giveaway [durasi:angka][s/m/h] [hadiah]`\nContoh: `!Doom giveaway 30m iPhone 15`")
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
            "❓ Format: `!Doom event Nama Event|Deskripsi|HH:MM|#channel`\n"
            "Contoh: `!Doom event Turnamen ML|Siap-siap gaskeun!|20:00|#announcement`\n"
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
    em.add_field(name="🎣 Fishing", value="`fish` `coins`", inline=True)
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
        name="💎 Premium",
        value="`/premium` `/premiumstatus` `/setpremiumrole` `/approvepremium`",
        inline=False
    )
    em.add_field(
        name="🎰 Slash Commands",
        value="`/ticket` `/leveling` `/reactionrole` `/setfishingreward` `/listfishingreward` `/addtebak` `/ping` dan banyak lagi!",
        inline=False
    )
    em.set_footer(text="Prefix: !Doom | Semua command bisa pake slash juga!")
    await ctx.reply(embed=em)

# ===================== SLASH COMMANDS =====================

# --- Ping ---
@tree.command(name="ping", description="Cek latency bot")
async def slash_ping(interaction: discord.Interaction):
    latency_ms = round(bot.latency * 1000)
    em = dark_red_embed("🏓 Pong!", f"Latency: **{latency_ms}ms**")
    await interaction.response.send_message(embed=em)

# --- AI ---
@tree.command(name="ai", description="Tanya apapun ke RepublikDooms AI!")
@app_commands.describe(pertanyaan="Pertanyaan lo buat AI")
async def slash_ai(interaction: discord.Interaction, pertanyaan: str):
    await interaction.response.defer()
    resp = await get_ai_response(pertanyaan)
    em = dark_red_embed("🤖 RepublikDooms AI", resp)
    await interaction.followup.send(embed=em)

# --- Fish ---
@tree.command(name="fish", description="Mulai mancing!")
async def slash_fish(interaction: discord.Interaction):
    em = dark_red_embed("🎣 Fishing RepublikDooms", f"Halo **{interaction.user.display_name}**! Pilih aksi lo:")
    await interaction.response.send_message(embed=em, view=FishingMainView(interaction.user.id))

# --- Ticket (FIXED) ---
@tree.command(name="ticket", description="Setup panel ticket (Premium)")
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
    gid = str(interaction.guild.id)
    if not check_premium(gid):
        await interaction.response.send_message(
            embed=dark_red_embed("❌ Fitur Premium", "❌ Fitur ini hanya untuk server premium!\nGunakan `/premium` untuk upgrade server lo."),
            ephemeral=True
        )
        return

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

# --- Premium Command ---
@tree.command(name="premium", description="Upgrade server lo ke premium!")
async def slash_premium(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            embed=dark_red_embed("❌ No Permission", "Hanya admin server yang bisa beli premium bro!"),
            ephemeral=True
        )
        return

    gid = str(interaction.guild.id)
    info = get_guild_premium_info(gid)

    # Daftar paket
    pkg_text = ""
    for key, pkg in premium_packages.items():
        pkg_text += f"{pkg['emoji']} **{pkg['name']}** — {pkg['price']} / {pkg['days']} hari\n"

    em = dark_red_embed(
        "💎 RepublikDooms Premium",
        f"Upgrade server **{interaction.guild.name}** ke Premium!\n\n"
        f"**Paket Tersedia:**\n{pkg_text}\n"
        f"**Fitur Premium:**\n"
        f"• 🎫 Ticket System\n"
        f"• 🤖 Auto Reply\n"
        f"• 🎨 Custom Role\n\n"
        f"Pilih paket di bawah untuk mulai!"
    )

    if info:
        expired_dt = datetime.datetime.fromtimestamp(info["expired_at"], tz=WIB)
        pkg = premium_packages.get(info["package_key"], {})
        em.add_field(
            name="✅ Status Premium",
            value=f"Aktif! Expired: **{expired_dt.strftime('%d/%m/%Y %H:%M')} WIB**\nPaket: **{pkg.get('name', info['package_key'])}**",
            inline=False
        )

    await interaction.response.send_message(embed=em, view=PremiumPackageSelect(), ephemeral=True)

# --- Premium Status ---
@tree.command(name="premiumstatus", description="Cek status premium server ini")
async def slash_premiumstatus(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    info = get_guild_premium_info(gid)
    if not info:
        em = dark_red_embed(
            "❌ Bukan Server Premium",
            f"Server **{interaction.guild.name}** belum premium bro!\nGunakan `/premium` untuk upgrade."
        )
    else:
        expired_dt = datetime.datetime.fromtimestamp(info["expired_at"], tz=WIB)
        activated_dt = datetime.datetime.fromtimestamp(info["activated_at"], tz=WIB)
        pkg = premium_packages.get(info["package_key"], {})
        sisa = int((info["expired_at"] - time.time()) / 86400)
        em = dark_red_embed(
            "✅ Server Premium Aktif!",
            f"**Server:** {interaction.guild.name}\n"
            f"**Paket:** {pkg.get('emoji', '')} {pkg.get('name', info['package_key'])}\n"
            f"**Aktif Sejak:** {activated_dt.strftime('%d/%m/%Y %H:%M')} WIB\n"
            f"**Expired:** {expired_dt.strftime('%d/%m/%Y %H:%M')} WIB\n"
            f"**Sisa:** {sisa} hari"
        )
    await interaction.response.send_message(embed=em, ephemeral=True)

# --- Set Premium Role ---
@tree.command(name="setpremiumrole", description="Set role yang dikasih saat server premium (Admin)")
@app_commands.describe(role="Role yang akan dikasih ke pembeli premium")
@app_commands.default_permissions(administrator=True)
async def slash_setpremiumrole(interaction: discord.Interaction, role: discord.Role):
    gid = str(interaction.guild.id)
    set_premium_role(gid, str(role.id))
    await interaction.response.send_message(
        embed=dark_red_embed("✅ Premium Role Diset!", f"Role **{role.name}** akan diberikan saat premium diapprove."),
        ephemeral=True
    )

# --- Manual Approve Premium (Owner Bot) ---
@tree.command(name="approvepremium", description="Approve premium manual untuk sebuah server (Owner Bot)")
@app_commands.describe(guild_id="ID server yang mau di-approve", package="Kunci paket (basic/pro/ultimate)")
@app_commands.default_permissions(administrator=True)
async def slash_approvepremium(interaction: discord.Interaction, guild_id: str, package: str):
    # Hanya owner bot yang bisa gunakan ini
    app_info = await bot.application_info()
    if interaction.user.id != app_info.owner.id:
        await interaction.response.send_message("❌ Command ini hanya untuk owner bot!", ephemeral=True)
        return
    if package not in premium_packages:
        pkg_list = ", ".join(premium_packages.keys())
        await interaction.response.send_message(f"❌ Paket tidak valid! Paket tersedia: {pkg_list}", ephemeral=True)
        return
    expired_at = set_guild_premium(guild_id, package)
    expired_dt = datetime.datetime.fromtimestamp(expired_at, tz=WIB)
    pkg = premium_packages[package]
    await interaction.response.send_message(
        embed=dark_red_embed(
            "✅ Premium Manual Diaktifkan!",
            f"**Guild ID:** {guild_id}\n**Paket:** {pkg['emoji']} {pkg['name']}\n**Expired:** {expired_dt.strftime('%d/%m/%Y %H:%M')} WIB"
        ),
        ephemeral=True
    )

# --- Leveling ---
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

# --- Reaction Role ---
@tree.command(name="reactionrole", description="Setup reaction role dengan button")
@app_commands.describe(
    judul="Judul embed",
    deskripsi="Deskripsi embed",
    role1="Role pertama",
    emoji1="Emoji button 1",
    label1="Label button 1",
    role2="Role kedua (opsional)",
    emoji2="Emoji button 2",
    label2="Label button 2"
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

# --- Giveaway ---
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

# --- Warn ---
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

# --- Kick ---
@tree.command(name="kick", description="Kick member dari server")
@app_commands.default_permissions(kick_members=True)
async def slash_kick(interaction: discord.Interaction, member: discord.Member, alasan: str = "Gak ada alasan"):
    await member.kick(reason=alasan)
    await interaction.response.send_message(embed=dark_red_embed("👢 Di-Kick!", f"**{member.display_name}** dikick. Alasan: {alasan}"))

# --- Ban ---
@tree.command(name="ban", description="Ban member dari server")
@app_commands.default_permissions(ban_members=True)
async def slash_ban(interaction: discord.Interaction, member: discord.Member, alasan: str = "Gak ada alasan"):
    await member.ban(reason=alasan)
    await interaction.response.send_message(embed=dark_red_embed("🔨 Di-Ban!", f"**{member.display_name}** dibanned. Alasan: {alasan}"))

# --- Timeout ---
@tree.command(name="timeout", description="Timeout member")
@app_commands.default_permissions(moderate_members=True)
async def slash_timeout(interaction: discord.Interaction, member: discord.Member, menit: int = 10, alasan: str = "Gak ada alasan"):
    until = discord.utils.utcnow() + datetime.timedelta(minutes=menit)
    await member.timeout(until, reason=alasan)
    await interaction.response.send_message(embed=dark_red_embed("⏱️ Timeout!", f"**{member.display_name}** di-timeout {menit} menit!"))

# --- Clear ---
@tree.command(name="clear", description="Hapus pesan")
@app_commands.describe(jumlah="Jumlah pesan yang mau dihapus")
@app_commands.default_permissions(manage_messages=True)
async def slash_clear(interaction: discord.Interaction, jumlah: int = 5):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=jumlah)
    await interaction.followup.send(f"✅ {jumlah} pesan dihapus!", ephemeral=True)

# --- Avatar ---
@tree.command(name="avatar", description="Lihat avatar member")
async def slash_avatar(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    em = dark_red_embed(f"🖼️ Avatar {member.display_name}")
    em.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=em)

# --- Userinfo ---
@tree.command(name="userinfo", description="Info lengkap user")
async def slash_userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    em = dark_red_embed(f"👤 Info {member.display_name}")
    em.set_thumbnail(url=member.display_avatar.url)
    em.add_field(name="Username", value=str(member), inline=True)
    em.add_field(name="ID", value=member.id, inline=True)
    em.add_field(name="Join Date", value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
    em.add_field(name="Roles", value=", ".join([r.name for r in member.roles[1:]]) or "Gak ada", inline=False)
    await interaction.response.send_message(embed=em)

# --- Addrole ---
@tree.command(name="addrole", description="Tambah role ke member")
@app_commands.default_permissions(manage_roles=True)
async def slash_addrole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await interaction.response.send_message(embed=dark_red_embed("✅ Role Ditambah!", f"**{role.name}** dikasih ke **{member.display_name}**!"))

# --- Removerole ---
@tree.command(name="removerole", description="Copot role dari member")
@app_commands.default_permissions(manage_roles=True)
async def slash_removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await interaction.response.send_message(embed=dark_red_embed("❌ Role Dicopot!", f"**{role.name}** dicopot dari **{member.display_name}**!"))

# --- Embed ---
@tree.command(name="embed", description="Kirim embed message")
@app_commands.describe(judul="Judul embed", deskripsi="Isi embed")
@app_commands.default_permissions(manage_messages=True)
async def slash_embed(interaction: discord.Interaction, judul: str, deskripsi: str):
    await interaction.response.send_message(embed=dark_red_embed(judul, deskripsi))

# --- Sticky ---
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

# --- Autoresponse ---
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

# --- Event ---
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

# --- Tebak Slash ---
@tree.command(name="tebak", description="Main tebak-tebakan!")
async def slash_tebak(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    if gid in active_tebakan:
        await interaction.response.send_message("⚠️ Masih ada tebakan yang belum kejawab bro!", ephemeral=True)
        return
    semua_soal = TEBAKAN_LIST + get_custom_tebakan()
    soal = random.choice(semua_soal)
    active_tebakan[gid] = {"jawaban": soal["jawaban"].lower(), "reward": soal["reward"], "asker": interaction.user.id}
    em = dark_red_embed("🧠 TEBAK-TEBAKAN!", f"**Soal:**\n{soal['soal']}\n\n💡 Reward: **{soal['reward']} koin**")
    await interaction.response.send_message(embed=em)

# --- Addtebak Slash ---
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

# --- Coins Slash ---
@tree.command(name="coins", description="Cek koin lo")
async def slash_coins(interaction: discord.Interaction):
    udata = get_user_fishing(str(interaction.user.id))
    await interaction.response.send_message(
        embed=dark_red_embed("🪙 Koin Lo", f"**{interaction.user.display_name}** punya **{udata['coins']} koin** 🪙"),
        ephemeral=True
    )

# --- Leaderboard ---
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

# --- Setfishingreward ---
@tree.command(name="setfishingreward", description="Edit nilai/harga reward ikan di fishing (Admin)")
@app_commands.describe(
    nama_ikan="Nama ikan yang mau diedit (contoh: Ikan Lele)",
    nilai_baru="Nilai koin baru untuk ikan tersebut"
)
@app_commands.default_permissions(administrator=True)
async def slash_setfishingreward(interaction: discord.Interaction, nama_ikan: str, nilai_baru: int):
    matched = None
    for f in FISHES:
        if f["name"].lower() == nama_ikan.lower():
            matched = f
            break
    if not matched:
        daftar = ", ".join([f["name"] for f in FISHES])
        await interaction.response.send_message(
            f"❌ Ikan **{nama_ikan}** gak ketemu!\nDaftar ikan: {daftar}",
            ephemeral=True
        )
        return
    old_val = matched["value"]
    matched["value"] = nilai_baru
    em = dark_red_embed(
        "✅ Reward Ikan Diupdate!",
        f"{matched['emoji']} **{matched['name']}**\n"
        f"Nilai lama: **{old_val} koin**\n"
        f"Nilai baru: **{nilai_baru} koin**\n"
        f"Rarity: **{matched['rarity']}**"
    )
    await interaction.response.send_message(embed=em)

# --- Listfishingreward ---
@tree.command(name="listfishingreward", description="Lihat semua reward ikan fishing saat ini")
async def slash_listfishingreward(interaction: discord.Interaction):
    rarity_order = ["legendary", "rare", "uncommon", "common", "trash"]
    rarity_label = {"legendary": "⭐ Legendary", "rare": "💎 Rare", "uncommon": "🔵 Uncommon", "common": "⚪ Common", "trash": "💩 Trash"}
    lines = []
    for r in rarity_order:
        group = [f for f in FISHES if f["rarity"] == r]
        if group:
            lines.append(f"**{rarity_label[r]}**")
            for f in group:
                lines.append(f"  {f['emoji']} {f['name']} → **{f['value']} koin**")
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
    else:
        print(f"Error: {error}")

# ===================== RUN =====================
if __name__ == "__main__":
    init_db()
    bot.run(BOT_TOKEN)
