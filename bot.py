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
def home(): return "Botul este Online!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()
# ===================================================

TOKEN = os.getenv("DISCORD_TOKEN")

def load_data():
    if not os.path.exists("data.json"):
        with open("data.json", "w") as f:
            json.dump({"warnings": {}, "levels": {}}, f)
    with open("data.json") as f: return json.load(f)

def save_data(data):
    with open("data.json", "w") as f: json.dump(data, f, indent=4)

# ================= CONFIGURARE BOT =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.moderation = True       
intents.voice_states = True  

bot = commands.Bot(command_prefix="#", intents=intents)

# ================= ID-URI SISTEM (Păstrate intacte) =================
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

VERSION = "3.0"
CHANGES_LOG = "✅ Versiune Finală: Toate comenzile STAFF + Self-Roles + Tickets."

XP_COOLDOWN = 8
last_xp_time = {}  

# ================= CLASA SELF-ROLES (Modelul tău) =================
class SelfRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def toggle_role(self, interaction: discord.Interaction, role_id: int):
        role = interaction.guild.get_role(role_id)
        if not role: return await interaction.response.send_message("❌ Rol negăsit.", ephemeral=True)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Rol scos: {role.name}", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Rol adăugat: {role.name}", ephemeral=True)

    @discord.ui.button(label="18+", style=discord.ButtonStyle.secondary, custom_id="r_18", emoji="<:18Plus:1455072960812548157>")
    async def r_18(self, i, b): await self.toggle_role(i, 1455073585306800128)

    @discord.ui.button(label="-18", style=discord.ButtonStyle.secondary, custom_id="r_u18", emoji="<:Under18:1455078800307126334>")
    async def r_u18(self, i, b): await self.toggle_role(i, 1455080987146064014)

    @discord.ui.button(label="GIRL", style=discord.ButtonStyle.secondary, custom_id="r_girl", emoji="<:emoji_15:1448074655775719444>")
    async def r_girl(self, i, b): await self.toggle_role(i, 1455080720409034907)

    @discord.ui.button(label="BOY", style=discord.ButtonStyle.secondary, custom_id="r_boy", emoji="<:emoji_16:1448074879961268451>")
    async def r_boy(self, i, b): await self.toggle_role(i, 1455079548445130883)

    @discord.ui.button(label="GIVEAWAY", style=discord.ButtonStyle.secondary, custom_id="r_give", emoji="<a:purplepresent:1455082484604604531>")
    async def r_give(self, i, b): await self.toggle_role(i, 1455081282009694258)

    @discord.ui.button(label="WAKE UP", style=discord.ButtonStyle.secondary, custom_id="r_wake", emoji="<:__:1451889127581548648>")
    async def r_wake(self, i, b): await self.toggle_role(i, 1455082758094327922)

# ================= CLASE TICKETS =================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket(self, interaction: discord.Interaction, category: str):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ID)
        ch_name = f"{category}-{interaction.user.name.lower()}"
        if discord.utils.get(guild.channels, name=ch_name):
            return await interaction.response.send_message("❌ Ai deja un ticket deschis!", ephemeral=True)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role: overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(ch_name, overwrites=overwrites, category=guild.get_channel(TICKET_CATEGORY_ID))
        await channel.send(embed=discord.Embed(title=f"🎫 Ticket: {category.upper()}", description="Staff-ul te va prelua imediat.", color=0x2b2d31), view=CloseTicketView())
        await interaction.response.send_message(f"✅ Creat: {channel.mention}", ephemeral=True)

    @discord.ui.button(label="REPORT STAFF", style=discord.ButtonStyle.secondary, custom_id="t_staff", emoji="⚠️")
    async def t_staff(self, i, b): await self.create_ticket(i, "staff")
    @discord.ui.button(label="REPORT MEMBER", style=discord.ButtonStyle.secondary, custom_id="t_member", emoji="👥")
    async def t_member(self, i, b): await self.create_ticket(i, "member")
    @discord.ui.button(label="BAN REPORTS", style=discord.ButtonStyle.secondary, custom_id="t_ban", emoji="🚫")
    async def t_ban(self, i, b): await self.create_ticket(i, "ban")
    @discord.ui.button(label="CONTACT OWNER", style=discord.ButtonStyle.secondary, custom_id="t_owner", emoji="👑")
    async def t_owner(self, i, b): await self.create_ticket(i, "owner")
    @discord.ui.button(label="INFO & OTHERS", style=discord.ButtonStyle.secondary, custom_id="t_info", emoji="❓")
    async def t_info(self, i, b): await self.create_ticket(i, "info")

class CloseTicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Închide Ticket", style=discord.ButtonStyle.danger, custom_id="close_t", emoji="🔒")
    async def close(self, i, b):
        await i.response.send_message("Închidere în 5s...")
        await asyncio.sleep(5)
        try: await i.channel.delete()
        except: pass
# ================= FUNCȚII LOGS & UTILS =================
async def send_boost_announcement(member, guild):
    channel = bot.get_channel(BOOST_CH_ID)
    if not channel: return
    content = f"{member.mention} is RICH ASFFF!! 💸"
    embed = discord.Embed(title=f"{CUSTOM_EMOJI} **Another Star on the Board!**", color=0xf47fff, timestamp=datetime.datetime.now(UTC))
    embed.description = (f"💎 | A huge shoutout to **{member.name}** for boosting!\n\n📈 | We are now at **{guild.premium_subscription_count}** boosts!")
    embed.set_image(url=BOOST_GIF)
    await channel.send(content=content, embed=embed)

async def send_sanction_log(action, staff, member, reason="Nespecificat", duration=None):
    target_id = BAN_LOG_CH_ID if "ban" in action.lower() else MOD_LOG_CH_ID
    ch = bot.get_channel(target_id)
    if not ch: return
    emb = discord.Embed(title=f"⛔ {action}", color=0x2b2d31, timestamp=datetime.datetime.now(UTC))
    emb.add_field(name="User", value=member.mention); emb.add_field(name="Staff", value=staff.mention if staff else "Sistem")
    emb.add_field(name="Motiv", value=reason); emb.set_thumbnail(url=MY_GIF)
    if duration: emb.add_field(name="Detalii", value=duration)
    await ch.send(embed=emb)

def is_staff_up():
    async def pred(ctx):
        r = ctx.guild.get_role(STAFF_ID)
        return r and ctx.author.top_role.position >= r.position
    return commands.check(pred)

def is_trial_up():
    async def pred(ctx):
        r = ctx.guild.get_role(TRIAL_ID)
        return r and ctx.author.top_role.position >= r.position
    return commands.check(pred)

# ================= TOATE COMENZILE STAFF =================

@bot.command()
@is_staff_up()
async def setup_roles(ctx):
    await ctx.message.delete()
    desc = (
        "<:18Plus:1455072960812548157> <@&1455073585306800128>\n"
        "<:Under18:1455078800307126334> <@&1455080987146064014>\n"
        "<:emoji_15:1448074655775719444> <@&1455080720409034907>\n"
        "<:emoji_16:1448074879961268451> <@&1455079548445130883>\n"
        "<a:purplepresent:1455082484604604531> <@&1455081282009694258>\n"
        "<:__:1451889127581548648> <@&1455082758094327922>\n\n"
        "**Apasă butoanele de mai jos pentru a-ți alege rolul!**"
    )
    await ctx.send(embed=discord.Embed(title="🎭 ROLES", description=desc, color=0x2b2d31), view=SelfRoleView())

@bot.command()
@is_staff_up()
async def setup_ticket(ctx):
    await ctx.message.delete()
    text = ("⚠️ ；**REPORT STAFF**\n👥 ；**REPORT MEMBER**\n🚫 ；**BAN REPORTS**\n👑 ；**CONTACT OWNER**\n❓ ；**INFO & OTHERS**\n\n**📢 ；Tichetele la mișto se pedepsesc!**")
    await ctx.send(embed=discord.Embed(description=text, color=0x2b2d31), view=TicketView())

@bot.command()
@is_staff_up()
async def ban(ctx, member: discord.Member, *, reason="Nespecificat"):
    await member.ban(reason=reason); await ctx.send(f"✅ Banat {member.name}", delete_after=5)
    await send_sanction_log("Ban", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def unban(ctx, id: int):
    user = await bot.fetch_user(id); await ctx.guild.unban(user)
    await ctx.send(f"✅ Unban {user.name}", delete_after=5); await send_sanction_log("Unban", ctx.author, user)

@bot.command()
@is_staff_up()
async def kick(ctx, member: discord.Member, *, reason="Nespecificat"):
    await member.kick(reason=reason); await send_sanction_log("Kick", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def mute(ctx, member: discord.Member, duration: str, *, reason="Nespecificat"):
    unit = duration[-1].lower(); amt = int(duration[:-1])
    sec = {"s": amt, "m": amt*60, "h": amt*3600, "d": amt*86400}.get(unit, 3600)
    await member.timeout(timedelta(seconds=sec), reason=reason)
    await send_sanction_log("Mute", ctx.author, member, reason, duration)

@bot.command()
@is_trial_up()
async def unmute(ctx, member: discord.Member):
    await member.timeout(None); await ctx.send(f"🔊 Unmuted {member.mention}")

@bot.command()
@is_staff_up()
async def warn(ctx, member: discord.Member, *, reason="Nespecificat"):
    data = load_data(); uid = str(member.id)
    data["warnings"][uid] = data["warnings"].get(uid, 0) + 1
    save_data(data); count = data["warnings"][uid]
    if count >= 3: await member.ban(reason="3/3 Warns"); await send_sanction_log("Ban (3/3 Warns)", None, member, reason)
    else: await send_sanction_log(f"Warn {count}/3", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def clear(ctx, amount: int = 100):
    await ctx.channel.purge(limit=amount)

@bot.command()
@is_staff_up()
async def say(ctx, *, msg):
    await ctx.message.delete(); await ctx.send(msg)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(embed=discord.Embed(title=f"Avatar {member.name}").set_image(url=member.display_avatar.url))

# ================= EVENIMENTE & LOGICA AUTOMATĂ =================
@bot.event
async def on_ready():
    print(f"✅ {bot.user} ONLINE")
    bot.add_view(TicketView()); bot.add_view(CloseTicketView()); bot.add_view(SelfRoleView())
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="https://discord.gg/S96dauCsH"))

@bot.event
async def on_member_join(member):
    ch = bot.get_channel(WELCOME_CH_ID)
    if ch: await ch.send(embed=discord.Embed(description=f"🎉 Bun venit {member.mention}!", color=0x2b2d31))

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    # Auto-Delete Comenzi
    if message.content.startswith("#"):
        await asyncio.sleep(10); try: await message.delete()
        except: pass

    # Sistem XP
    uid = str(message.author.id); now = time.time()
    if uid not in last_xp_time or now - last_xp_time[uid] > XP_COOLDOWN:
        last_xp_time[uid] = now
        data = load_data()
        if uid not in data["levels"]: data["levels"][uid] = {"xp": 0, "level": 1}
        data["levels"][uid]["xp"] += 10
        save_data(data)

    await bot.process_commands(message)

keep_alive()
bot.run(TOKEN)
