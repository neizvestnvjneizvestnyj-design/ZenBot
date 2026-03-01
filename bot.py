import os
from dotenv import load_dotenv  
load_dotenv()                   

import discord
from discord.ext import commands
import asyncio
import datetime
import json
from datetime import UTC, timedelta
import time
from flask import Flask
from threading import Thread

# ================= KEEP-ALIVE 24/7 =================
app = Flask('')

@app.route('/')
def home():
    return "Botul este Online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ===================================================

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN nu este setat!")

# ================= BAZA DE DATE =================
def load_data():
    if not os.path.exists("data.json"):
        with open("data.json", "w") as f:
            json.dump({"warnings": {}, "levels": {}}, f)
    with open("data.json") as f:
        return json.load(f)

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

# ================= CONFIG =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.moderation = True
intents.voice_states = True  

bot = commands.Bot(command_prefix="#", intents=intents)

# ================= ID-URI =================
TRIAL_ID = 1444684277110542368
STAFF_ID = 1325279044396126261
LOG_CH_ID = 1444796054313766922

XP_COOLDOWN = 8
last_xp_time = {}

# ================= FIX IMPORTANT =================
@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    log_ch = bot.get_channel(LOG_CH_ID)
    if not log_ch:
        return

    embed = discord.Embed(
        title="🗑️ Mesaj Șters",
        color=0xff0000,
        timestamp=datetime.datetime.now(UTC)
    )
    embed.add_field(name="Autor", value=message.author.mention)
    embed.add_field(name="Canal", value=message.channel.mention)
    embed.add_field(name="Conținut", value=message.content or "Fără text", inline=False)

    await log_ch.send(embed=embed)

# ================= NOU: LOG EDIT MESAJ =================
@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    if before.content == after.content:
        return

    log_ch = bot.get_channel(LOG_CH_ID)
    if not log_ch:
        return

    embed = discord.Embed(
        title="✏️ Mesaj Editat",
        color=0xffa500,
        timestamp=datetime.datetime.now(UTC)
    )
    embed.add_field(name="Autor", value=before.author.mention)
    embed.add_field(name="Canal", value=before.channel.mention)
    embed.add_field(name="Înainte", value=before.content or "Fără text", inline=False)
    embed.add_field(name="După", value=after.content or "Fără text", inline=False)

    await log_ch.send(embed=embed)

# ================= XP SYSTEM =================
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return

    uid = str(message.author.id)
    now = time.time()

    if uid not in last_xp_time or now - last_xp_time[uid] > XP_COOLDOWN:
        last_xp_time[uid] = now
        data = load_data()

        if uid not in data["levels"]:
            data["levels"][uid] = {"xp": 0, "level": 1}

        data["levels"][uid]["xp"] += 10
        xp = data["levels"][uid]["xp"]
        lvl = data["levels"][uid]["level"]

        if xp >= lvl * 100:
            data["levels"][uid]["level"] += 1
            data["levels"][uid]["xp"] = xp - (lvl * 100)
            await message.channel.send(
                f"🎉 {message.author.mention} nivel **{lvl+1}**!",
                delete_after=10
            )

        save_data(data)

    await bot.process_commands(message)

# ================= READY =================
@bot.event
async def on_ready():
    print(f"✅ {bot.user} ONLINE")

keep_alive()
bot.run(TOKEN)