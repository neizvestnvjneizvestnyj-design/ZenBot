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

# ================= Încărcare token =================
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
BOOST_ROLE_MIN = 1411137733975347293  
BOOST_CH_ID = 1476419627482611762      
BENEFITS_CH_ID = 1476425405304012843   

LOG_CH_ID = 1444796054313766922         
BAN_LOG_CH_ID = 1436891992150769664     
MOD_LOG_CH_ID = 1464383652866556039     

WELCOME_CH_ID = 1325279589915955321 
BOT_COMMANDS_CH = 1436559828859359373
CHAT_CHANNEL_ID = 1436554745622827258
STAFF_CMD_CHANNEL = 1449824932371632248
UPDATE_LOG_CH_ID = 1477448913827921922 

TICKET_CATEGORY_ID = 1444684157833056256 

WARN1_ROLE_ID = 1436538867850416289
W2_ID = 1436538789311811624
W3_ID = 1450009480417902796

MY_GIF = "https://media.discordapp.net/attachments/1440112412266205194/1461843437694484684/f63ce9f5-d6b6-47d9-91f0-eb1e166ab02a.gif"
BOOST_GIF = "https://media.tenor.com/7123Lof2_mEAAAAC/make-it-rain-money.gif"
CUSTOM_EMOJI = "<:emoji_16:1448074879961268451>"

VERSION = "2.5"
CHANGES_LOG = "✅ Sistem Self-Roles activat."

XP_COOLDOWN = 8
last_xp_time = {}  

# ================= SELF-ROLES =================
class SelfRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def toggle_role(self, interaction: discord.Interaction, role_id: int):
        role = interaction.guild.get_role(role_id)
        if not role: return
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Scos: {role.name}", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Adăugat: {role.name}", ephemeral=True)

    @discord.ui.button(label="18+", style=discord.ButtonStyle.secondary, custom_id="r_18", emoji="<:18Plus:1455072960812548157>")
    async def r1(self, i, b): await self.toggle_role(i, 1455073585306800128)
    @discord.ui.button(label="Under 18", style=discord.ButtonStyle.secondary, custom_id="r_u18", emoji="<:Under18:1455078800307126334>")
    async def r2(self, i, b): await self.toggle_role(i, 1455080987146064014)
    @discord.ui.button(label="Girl", style=discord.ButtonStyle.secondary, custom_id="r_girl", emoji="<:emoji_15:1448074655775719444>")
    async def r3(self, i, b): await self.toggle_role(i, 1455080720409034907)
    @discord.ui.button(label="Boy", style=discord.ButtonStyle.secondary, custom_id="r_boy", emoji="<:emoji_16:1448074879961268451>")
    async def r4(self, i, b): await self.toggle_role(i, 1455079548445130883)
    @discord.ui.button(label="Giveaway", style=discord.ButtonStyle.secondary, custom_id="r_give", emoji="<a:purplepresent:1455082484604604531>")
    async def r5(self, i, b): await self.toggle_role(i, 1455081282009694258)
    @discord.ui.button(label="Wake Up", style=discord.ButtonStyle.secondary, custom_id="r_wake", emoji="<:__:1451889127581548648>")
    async def r6(self, i, b): await self.toggle_role(i, 1455082758094327922)

# ================= TICKETS =================
class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    async def create_ticket(self, interaction: discord.Interaction, category_name: str):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ID)
        channel_name = f"{category_name}-{interaction.user.name.lower()}"
        if discord.utils.get(guild.channels, name=channel_name):
            return await interaction.response.send_message("❌ Ai deja un ticket!", ephemeral=True)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role: overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        category = guild.get_channel(TICKET_CATEGORY_ID)
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
        await channel.send(embed=discord.Embed(title=f"🎫 Ticket {category_name.upper()}", description="Staff-ul va veni curând.", color=0x2b2d31), view=CloseTicketView())
        await interaction.response.send_message(f"✅ Creat: {channel.mention}", ephemeral=True)

    @discord.ui.button(label="REPORT STAFF", style=discord.ButtonStyle.secondary, custom_id="t_staff", emoji="⚠️")
    async def t1(self, i, b): await self.create_ticket(i, "staff")
    @discord.ui.button(label="REPORT MEMBER", style=discord.ButtonStyle.secondary, custom_id="t_member", emoji="👥")
    async def t2(self, i, b): await self.create_ticket(i, "member")
    @discord.ui.button(label="BAN REPORTS", style=discord.ButtonStyle.secondary, custom_id="t_ban", emoji="🚫")
    async def t3(self, i, b): await self.create_ticket(i, "ban")
    @discord.ui.button(label="CONTACT OWNER", style=discord.ButtonStyle.secondary, custom_id="t_owner", emoji="👑")
    async def t4(self, i, b): await self.create_ticket(i, "owner")
    @discord.ui.button(label="INFO & OTHERS", style=discord.ButtonStyle.secondary, custom_id="t_info", emoji="❓")
    async def t5(self, i, b): await self.create_ticket(i, "info")

class CloseTicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Închide Ticket", style=discord.ButtonStyle.danger, custom_id="c_t", emoji="🔒")
    async def close(self, i, b):
        await i.response.send_message("Se închide..."); await asyncio.sleep(5); await i.channel.delete()

# ================= LOGS =================
async def send_sanction_log(action, staff, member, reason="Nespecificat", duration=None):
    ch = bot.get_channel(MOD_LOG_CH_ID)
    if not ch: return
    embed = discord.Embed(title=f"⛔ {action}", color=0x2b2d31, timestamp=datetime.datetime.now(UTC))
    embed.add_field(name="User", value=member.mention); embed.add_field(name="Staff", value=staff.mention if staff else "Sistem")
    embed.add_field(name="Motiv", value=reason)
    if duration: embed.add_field(name="Durată", value=duration)
    await ch.send(embed=embed)

# ================= PERMISIUNI =================
def is_staff_up():
    async def pred(ctx):
        role = ctx.guild.get_role(STAFF_ID)
        return role and ctx.author.top_role.position >= role.position
    return commands.check(pred)

# ================= COMENZI =================
@bot.command()
@is_staff_up()
async def setup_roles(ctx):
    await ctx.message.delete()
    emb = discord.Embed(title="🎭 SELF ROLES", description="Alege-ți rolurile apăsând butoanele!", color=0x2b2d31)
    await ctx.send(embed=emb, view=SelfRoleView())

@bot.command()
@is_staff_up()
async def setup_ticket(ctx):
    await ctx.message.delete()
    await ctx.send(embed=discord.Embed(description="Deschide un ticket pentru ajutor.", color=0x2b2d31), view=TicketView())

@bot.command()
@is_staff_up()
async def ban(ctx, member: discord.Member, *, reason="Nespecificat"):
    await member.ban(reason=reason); await send_sanction_log("Ban", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def clear(ctx, amount: int = 100):
    await ctx.channel.purge(limit=amount)

# ================= EVENIMENTE =================
@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    # XP System
    uid = str(message.author.id); now = time.time()
    if uid not in last_xp_time or now - last_xp_time[uid] > XP_COOLDOWN:
        last_xp_time[uid] = now; data = load_data()
        if uid not in data["levels"]: data["levels"][uid] = {"xp": 0, "level": 1}
        data["levels"][uid]["xp"] += 10
        if data["levels"][uid]["xp"] >= data["levels"][uid]["level"] * 100:
            data["levels"][uid]["level"] += 1; data["levels"][uid]["xp"] = 0
            await message.channel.send(f"🎉 {message.author.mention} nivel nou!", delete_after=5)
        save_data(data)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} ONLINE")
    bot.add_view(TicketView()); bot.add_view(CloseTicketView()); bot.add_view(SelfRoleView())

keep_alive()
bot.run(TOKEN)
