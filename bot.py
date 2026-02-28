import os
from dotenv import load_dotenv  
load_dotenv()                   

import discord
from discord.ext import commands
import asyncio
import datetime
import json
from datetime import UTC, timedelta
import time  # pentru cooldown XP
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

# ================= Încărcare token (obligatoriu!) =================
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("❌ DISCORD_TOKEN nu este setat în variabile de mediu!")

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

# ================= CONFIGURARE BOT =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.moderation = True       
intents.voice_states = True  

bot = commands.Bot(command_prefix="#", intents=intents)

# ================= ID-URI ACTUALIZATE =================
TRIAL_ID = 1444684277110542368
STAFF_ID = 1325279044396126261
BOOST_ROLE_MIN = 1411137733975347293  # Rolul minim care poate folosi #boost
BOOST_CH_ID = 1476419627482611762      # Canalul de boost-uri
BENEFITS_CH_ID = 1476425405304012843   # Noul canal de beneficii

LOG_CH_ID = 1444796054313766922         
BAN_LOG_CH_ID = 1436891992150769664     
MOD_LOG_CH_ID = 1464383652866556039     

BOT_COMMANDS_CH = 1436559828859359373
CHAT_CHANNEL_ID = 1436554745622827258
STAFF_CMD_CHANNEL = 1449824932371632248

WARN1_ROLE_ID = 1436538867850416289
W2_ID = 1436538789311811624
W3_ID = 1450009480417902796

MY_GIF = "https://media.discordapp.net/attachments/1440112412266205194/1461843437694484684/f63ce9f5-d6b6-47d9-91f0-eb1e166ab02a.gif"
BOOST_GIF = "https://media.tenor.com/7123Lof2_mEAAAAC/make-it-rain-money.gif"
CUSTOM_EMOJI = "<:emoji_16:1448074879961268451>"

XP_COOLDOWN = 8
last_xp_time = {}  

# ================= FUNCTIE ANUNT BOOST =================
async def send_boost_announcement(member, guild):
    channel = bot.get_channel(BOOST_CH_ID)
    if not channel: return

    # Mesaj text deasupra embed-ului (fără <3)
    content = f"{member.mention} is RICH ASFFF!! 💸"

    embed = discord.Embed(
        title=f"{CUSTOM_EMOJI} **Another Star on the Board!**",
        color=0xf47fff,
        timestamp=datetime.datetime.now(UTC)
    )
    
    embed.description = (
        f"💎 | A big shoutout to **{member.name}** for the support!\n\n"
        f"✨ | You just made the server a better place.\n"
        f"📈 | Current boost count: **{guild.premium_subscription_count}**\n\n"
        f"🎁 | Don't forget to check your rewards in <#{BENEFITS_CH_ID}>"
    )
    
    embed.set_image(url=BOOST_GIF)
    embed.set_footer(text=f"Server Level: {guild.premium_tier} • We appreciate you!")
    
    await channel.send(content=content, embed=embed)

# ================= FUNCTIE LOGURI =================
async def send_sanction_log(action, staff, member, reason="Nespecificat", duration=None):
    act_low = action.lower()
    if "ban" in act_low: target_ch_id = BAN_LOG_CH_ID
    elif any(x in act_low for x in ["mute", "kick", "warn", "unmute", "unwarn", "lock", "unlock", "slow"]):
        target_ch_id = MOD_LOG_CH_ID
    else: target_ch_id = LOG_CH_ID

    channel = bot.get_channel(target_ch_id)
    if not channel: return

    embed = discord.Embed(title=f"⛔ {action} | {member.name if hasattr(member, 'name') else str(member)}", color=0x2b2d31, timestamp=datetime.datetime.now(UTC))
    embed.set_thumbnail(url=MY_GIF)
    embed.add_field(name="👤 User", value=member.mention if hasattr(member, 'mention') else str(member), inline=True)
    embed.add_field(name="🛡️ Staff", value=staff.mention if staff else "@Sistem Automat", inline=True)
    embed.add_field(name="📄 Motiv", value=reason if reason else "Nespecificat", inline=True)
    if duration: embed.add_field(name="⏳ Detalii", value=duration, inline=True)
    embed.set_footer(text=f"ID: {member.id if hasattr(member, 'id') else 'N/A'}")
    await channel.send(embed=embed)

# ================= VERIFICARI PERMISIUNI =================
def is_trial_up():
    async def pred(ctx):
        role = ctx.guild.get_role(TRIAL_ID)
        return role and ctx.author.top_role.position >= role.position
    return commands.check(pred)

def is_staff_up():
    async def pred(ctx):
        role = ctx.guild.get_role(STAFF_ID)
        return role and ctx.author.top_role.position >= role.position
    return commands.check(pred)

def is_above_staff():
    async def pred(ctx):
        role_staff = ctx.guild.get_role(STAFF_ID)
        return role_staff and ctx.author.top_role.position > role_staff.position
    return commands.check(pred)

# ================= COMENZI =================

@bot.command()
@is_staff_up()
async def say(ctx, *, message: str):
    await ctx.message.delete()
    await ctx.send(message)

@bot.command()
async def boost(ctx, member: discord.Member = None):
    required_role = ctx.guild.get_role(BOOST_ROLE_MIN)
    if required_role and ctx.author.top_role.position >= required_role.position:
        await ctx.message.delete()
        target = member or ctx.author
        await send_boost_announcement(target, ctx.guild)
    else:
        await ctx.send("❌ Nu ai permisiunea necesară!", delete_after=5)

@bot.command()
@is_above_staff()
async def slow(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"⏳ Slowmode setat la **{seconds}** secunde.", delete_after=5)
    await send_sanction_log("Slowmode", ctx.author, ctx.channel, f"Delay: {seconds}s")

@bot.command()
@is_staff_up()
async def ban(ctx, member: discord.Member, *, reason="Nespecificat"):
    await member.ban(reason=reason)
    await ctx.send(f"✅ {member.name} a fost banat.", delete_after=5)
    await send_sanction_log("Ban", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def unban(ctx, id: int):
    user = await bot.fetch_user(id)
    await ctx.guild.unban(user)
    await ctx.send(f"✅ {user.name} a primit unban.", delete_after=5)
    await send_sanction_log("Unban", ctx.author, user)

@bot.command()
@is_staff_up()
async def kick(ctx, member: discord.Member, *, reason="Nespecificat"):
    await member.kick(reason=reason)
    await ctx.send(f"✅ {member.name} a fost dat afară.", delete_after=5)
    await send_sanction_log("Kick", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def clear(ctx, amount: int = 100):
    if amount > 500: amount = 500
    deleted = await ctx.channel.purge(limit=amount)
    await send_sanction_log("Clear", ctx.author, ctx.channel, f"Mesaje șterse: {len(deleted)}")
    await ctx.send(f"🧹 {len(deleted)} mesaje șterse.", delete_after=5)

@bot.command()
@is_staff_up()
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Canal blocat.", delete_after=5)
    await send_sanction_log("Lock", ctx.author, ctx.channel)

@bot.command()
@is_staff_up()
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Canal deblocat.", delete_after=5)
    await send_sanction_log("Unlock", ctx.author, ctx.channel)

@bot.command()
@is_staff_up()
async def warn(ctx, member: discord.Member, *, reason="Nespecificat"):
    data = load_data()
    uid = str(member.id)
    data["warnings"][uid] = data["warnings"].get(uid, 0) + 1
    count = data["warnings"][uid]
    save_data(data)

    if count >= 3:
        try:
            await member.ban(reason=f"3/3 warns | Ultimul: {reason}")
            await ctx.send(f"⛔ {member.mention} BAN automat (3/3 warns).")
            await send_sanction_log("Ban", None, member, reason)
        except:
            await ctx.send("❌ Eroare la ban automat.")
    else:
        warn_roles = [WARN1_ROLE_ID, W2_ID, W3_ID]
        if count <= len(warn_roles):
            role = ctx.guild.get_role(warn_roles[count-1])
            if role: await member.add_roles(role)
        await ctx.send(f"⚠️ {member.mention} warn {count}/3.", delete_after=5)
        await send_sanction_log(f"Warn {count}/3", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def unwarn(ctx, member: discord.Member):
    data = load_data()
    uid = str(member.id)
    if uid in data["warnings"]: del data["warnings"][uid]
    save_data(data)
    for rid in [WARN1_ROLE_ID, W2_ID, W3_ID]:
        role = ctx.guild.get_role(rid)
        if role and role in member.roles: await member.remove_roles(role)
    await ctx.send(f"✅ Warn-urile lui {member.mention} resetate.", delete_after=5)
    await send_sanction_log("Unwarn", ctx.author, member, "Reset total")

@bot.command()
@is_trial_up()
async def mute(ctx, member: discord.Member, duration: str, *, reason="Nespecificat"):
    try:
        unit = duration[-1].lower()
        amt = int(duration[:-1])
        seconds = {"s": amt, "m": amt*60, "h": amt*3600, "d": amt*86400}.get(unit, 3600)
        await member.timeout(timedelta(seconds=seconds), reason=reason)
        await ctx.send(f"🔇 {member.mention} mute {duration}.", delete_after=5)
        await send_sanction_log("Mute", ctx.author, member, reason, duration)
    except:
        await ctx.send("❌ Eroare la mute.")

@bot.command()
@is_trial_up()
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"🔊 {member.mention} unmute.", delete_after=5)
    await send_sanction_log("Unmute", ctx.author, member, "Manual")

# ================= EVENIMENTE =================
@bot.event
async def on_voice_state_update(member, before, after):
    log_ch = bot.get_channel(LOG_CH_ID)
    if not log_ch: return
    if before.channel is None and after.channel is not None:
        emb = discord.Embed(title="📥 Voice Join", description=f"{member.mention} a intrat pe {after.channel.mention}", color=0x43b581, timestamp=datetime.datetime.now(UTC))
        await log_ch.send(embed=emb)
    elif before.channel is not None and after.channel is None:
        emb = discord.Embed(title="📤 Voice Leave", description=f"{member.mention} a ieșit de pe **{before.channel.name}**", color=0xf04747, timestamp=datetime.datetime.now(UTC))
        await log_ch.send(embed=emb)

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    log_ch = bot.get_channel(LOG_CH_ID)
    if not log_ch: return
    emb = discord.Embed(title="🗑️ Mesaj Șters", color=0xff4500, timestamp=datetime.datetime.now(UTC))
    emb.add_field(name="Autor", value=message.author.mention)
    emb.add_field(name="Conținut", value=message.content or "*Fără text*", inline=False)
    await log_ch.send(embed=emb)

@bot.command()
@is_staff_up()
async def addrole(ctx, member: discord.Member, role: discord.Role):
    if role.position >= ctx.author.top_role.position:
        return await ctx.send("❌ Nu poți adăuga un rol ≥ cu al tău!", delete_after=5)
    await member.add_roles(role)
    await ctx.send(f"✅ Rol {role.name} adăugat.", delete_after=5)
    await send_sanction_log("Role Add", ctx.author, member, f"Rol: {role.name}")

@bot.command()
@is_staff_up()
async def removerole(ctx, member: discord.Member, role: discord.Role):
    if role.position >= ctx.author.top_role.position:
        return await ctx.send("❌ Nu poți scoate un rol ≥ cu al tău!", delete_after=5)
    await member.remove_roles(role)
    await ctx.send(f"✅ Rol {role.name} scos.", delete_after=5)
    await send_sanction_log("Role Remove", ctx.author, member, f"Rol: {role.name}")

@bot.command()
@is_trial_up()
async def warns(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = load_data()
    count = data["warnings"].get(str(member.id), 0)
    await ctx.send(f"🔎 {member.mention} are **{count}/3** warn-uri.", delete_after=8)

@bot.command()
async def comenzi(ctx):
    if ctx.channel.id != STAFF_CMD_CHANNEL: return await ctx.send(f"❌ Doar în <#{STAFF_CMD_CHANNEL}>", delete_after=6)
    embed = discord.Embed(title="📜 Liste commandes STAFF", color=0x2b2d31, description="Prefix: **#**\n\n**#ban** @user motiv\n**#unban** ID\n**#kick** @user motiv\n**#mute** @user 1h/30m/2d motiv\n**#unmute** @user\n**#warn** @user motiv\n**#unwarn** @user\n**#warns** @user\n**#clear** 50\n**#lock** / **#unlock**\n**#addrole** @user @rol\n**#removerole** @user @rol\n**#avatar** [@user]\n**#serverinfo**\n**#slow** secunde\n\n❗ Abuz = sancțiune!")
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    if ctx.channel.id != BOT_COMMANDS_CH: return await ctx.send(f"❌ Doar în <#{BOT_COMMANDS_CH}>", delete_after=6)
    member = member or ctx.author
    embed = discord.Embed(title=f"Avatar • {member.name}", color=0x2b2d31)
    embed.set_image(url=member.display_avatar.url)
    await ctx.send(embed=embed, delete_after=30)

@bot.command()
async def serverinfo(ctx):
    if ctx.channel.id != BOT_COMMANDS_CH: return await ctx.send(f"❌ Doar în <#{BOT_COMMANDS_CH}>", delete_after=6)
    g = ctx.guild
    embed = discord.Embed(title=f"{g.name} • Info", color=0x2b2d31)
    embed.set_thumbnail(url=g.icon.url if g.icon else None)
    embed.add_field(name="👥 Membri", value=g.member_count)
    embed.add_field(name="🚀 Boost", value=g.premium_subscription_count)
    embed.add_field(name="📅 Creat", value=g.created_at.strftime("%d %b %Y"))
    await ctx.send(embed=embed, delete_after=25)

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return

    # Boost automat (sistem)
    if "premium_guild_subscription" in str(message.type):
        await send_boost_announcement(message.author, message.guild)

    if message.channel.id == CHAT_CHANNEL_ID:
        low = message.content.lower()
        if low in ["neata", "neatza", "buna dimineata", "ntz"]: await message.channel.send(f"{CUSTOM_EMOJI} Bună dimineața {message.author.mention}, ce mai faci? 😊")
        elif low in ["nb", "noapte buna"]: await message.channel.send(f"{CUSTOM_EMOJI} Noapte bună {message.author.mention}!")
        elif low in ["salut", "sall", "ciao", "buna"]: await message.channel.send(f"{CUSTOM_EMOJI} Salut maan {message.author.mention}, ce faci boss?")

    content_low = message.content.lower()
    if ("http" in content_low or "discord.gg/" in content_low) and not any(x in content_low for x in ["youtube.com", "youtu.be", "googleusercontent.com", "imgur.com"]):
        trial_role = message.guild.get_role(TRIAL_ID)
        if not (trial_role and message.author.top_role.position >= trial_role.position):
            try:
                await message.delete()
                data = load_data()
                uid = str(message.author.id)
                data["warnings"][uid] = data["warnings"].get(uid, 0) + 1
                count = data["warnings"][uid]
                save_data(data)
                await message.author.timeout(timedelta(hours=3), reason="Link neautorizat")
                if count >= 3: await message.author.ban(reason="3/3 Warns (Link-uri)")
                else:
                    warn_roles = [WARN1_ROLE_ID, W2_ID, W3_ID]
                    role = message.guild.get_role(warn_roles[count-1])
                    if role: await message.author.add_roles(role)
                await message.channel.send(f"❌ {message.author.mention} link interzis → warn **{count}/3**", delete_after=10)
            except: pass
            return

    uid = str(message.author.id)
    now = time.time()
    if uid not in last_xp_time or now - last_xp_time[uid] > XP_COOLDOWN:
        last_xp_time[uid] = now
        data = load_data()
        if uid not in data["levels"]: data["levels"][uid] = {"xp": 0, "level": 1}
        data["levels"][uid]["xp"] += 10
        xp, lvl = data["levels"][uid]["xp"], data["levels"][uid]["level"]
        if xp >= lvl * 100:
            data["levels"][uid]["level"] += 1
            data["levels"][uid]["xp"] = xp - (lvl * 100)
            await message.channel.send(f"🎉 {message.author.mention} nivel **{lvl+1}**!", delete_after=12)
        save_data(data)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} ONLINE")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="https://discord.gg/S96dauCsH"))

keep_alive()
bot.run(TOKEN)
