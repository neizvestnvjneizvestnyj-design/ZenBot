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

# --- CHANGELOG AUTOMAT ---
VERSION = "2.7"
CHANGES_LOG = """
✅ **Self Roles**: Adăugat panoul de roluri.
✅ **Apply Staff**: Adăugată comanda #setup_apply.
"""

XP_COOLDOWN = 8
last_xp_time = {}  

# ================= CLASA APPLY (NOU ADĂUGAT) =================
class ApplyModal(discord.ui.Modal, title='Cerere Staff / Helper'):
    nume = discord.ui.TextInput(label='Nume și Vârstă', placeholder='Ex: Andrei, 17 ani', min_length=3, max_length=50)
    experienta = discord.ui.TextInput(label='Ai mai fost staff?', placeholder='Spune-ne experiența ta...', style=discord.TextStyle.paragraph)
    timp = discord.ui.TextInput(label='Timp alocat zilnic', placeholder='Ex: 4-5 ore', max_length=20)
    de_ce = discord.ui.TextInput(label='De ce tu?', style=discord.TextStyle.paragraph, min_length=10)

    async def on_submit(self, interaction: discord.Interaction):
        log_ch = bot.get_channel(MOD_LOG_CH_ID)
        embed = discord.Embed(title="📝 Cerere Staff Nouă", color=0xFFD700, timestamp=datetime.datetime.now(UTC))
        embed.add_field(name="Utilizator", value=f"{interaction.user.mention} ({interaction.user.id})")
        embed.add_field(name="Nume/Vârstă", value=self.nume.value)
        embed.add_field(name="Experiență", value=self.experienta.value, inline=False)
        embed.add_field(name="Timp", value=self.timp.value)
        embed.add_field(name="Motiv", value=self.de_ce.value, inline=False)
        await log_ch.send(embed=embed)
        await interaction.response.send_message("✅ Cererea a fost trimisă!", ephemeral=True)

class ApplyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="APPLY HERE", style=discord.ButtonStyle.success, custom_id="apply_staff", emoji="📜")
    async def apply_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplyModal())

# ================= CLASA NOUĂ: SELF-ROLES =================
class SelfRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def toggle_role(self, interaction: discord.Interaction, role_id: int):
        role = interaction.guild.get_role(role_id)
        if not role:
            return await interaction.response.send_message("❌ Rolul nu a fost găsit!", ephemeral=True)
        
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Rolul {role.name} a fost scos.", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Rolul {role.name} a fost adăugat!", ephemeral=True)

    @discord.ui.button(label="18+", style=discord.ButtonStyle.secondary, custom_id="role_18plus", emoji="<:18Plus:1455072960812548157>")
    async def role_18plus(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, 1455073585306800128)

    @discord.ui.button(label="Under 18", style=discord.ButtonStyle.secondary, custom_id="role_under18", emoji="<:Under18:1455078800307126334>")
    async def role_under18(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, 1455080987146064014)

    @discord.ui.button(label="Girl", style=discord.ButtonStyle.secondary, custom_id="role_girl", emoji="<:emoji_15:1448074655775719444>")
    async def role_girl(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, 1455080720409034907)

    @discord.ui.button(label="Boy", style=discord.ButtonStyle.secondary, custom_id="role_boy", emoji="<:emoji_16:1448074879961268451>")
    async def role_boy(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, 1455079548445130883)

    @discord.ui.button(label="Giveaway", style=discord.ButtonStyle.secondary, custom_id="role_giveaway", emoji="<a:purplepresent:1455082484604604531>")
    async def role_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, 1455081282009694258)

    @discord.ui.button(label="Wake Up", style=discord.ButtonStyle.secondary, custom_id="role_wakeup", emoji="<:__:1451889127581548648>")
    async def role_wakeup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_role(interaction, 1455082758094327922)
# [CONTINUARE DIN PARTEA 1...]
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket(self, interaction: discord.Interaction, category_name: str):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ID)
        channel_name = f"{category_name}-{interaction.user.name.lower()}"
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        if existing_channel:
            return await interaction.response.send_message(f"❌ Ai deja un ticket deschis!", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role: overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        category = guild.get_channel(TICKET_CATEGORY_ID)
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
        embed = discord.Embed(title=f"🎫 Ticket: {category_name.upper()}", description="Echipa Staff va prelua cererea ta în scurt timp.", color=0x2b2d31)
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket creat: {channel.mention}", ephemeral=True)

    @discord.ui.button(label="REPORT STAFF", style=discord.ButtonStyle.secondary, custom_id="t_staff", emoji="⚠️")
    async def t_staff(self, interaction: discord.Interaction, button: discord.ui.Button): await self.create_ticket(interaction, "staff")
    @discord.ui.button(label="REPORT MEMBER", style=discord.ButtonStyle.secondary, custom_id="t_member", emoji="👥")
    async def t_member(self, interaction: discord.Interaction, button: discord.ui.Button): await self.create_ticket(interaction, "member")
    @discord.ui.button(label="BAN REPORTS", style=discord.ButtonStyle.secondary, custom_id="t_ban", emoji="🚫")
    async def t_ban(self, interaction: discord.Interaction, button: discord.ui.Button): await self.create_ticket(interaction, "ban")
    @discord.ui.button(label="CONTACT OWNER", style=discord.ButtonStyle.secondary, custom_id="t_owner", emoji="👑")
    async def t_owner(self, interaction: discord.Interaction, button: discord.ui.Button): await self.create_ticket(interaction, "owner")
    @discord.ui.button(label="INFO & OTHERS", style=discord.ButtonStyle.secondary, custom_id="t_info", emoji="❓")
    async def t_info(self, interaction: discord.Interaction, button: discord.ui.Button): await self.create_ticket(interaction, "info")

class CloseTicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Închide Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Tichetul se va închide...")
        await asyncio.sleep(2)
        await interaction.channel.delete()

async def send_boost_announcement(member, guild):
    channel = bot.get_channel(BOOST_CH_ID)
    if not channel: return
    content = f"{member.mention} is RICH ASFFF!! 💸"
    embed = discord.Embed(title=f"{CUSTOM_EMOJI} **Another Star on the Board!**", color=0xf47fff)
    embed.description = f"💎 | A huge shoutout to **{member.name}** for boosting!\n📈 | We are now at **{guild.premium_subscription_count}** boosts!"
    embed.set_image(url=BOOST_GIF)
    await channel.send(content=content, embed=embed)

async def send_sanction_log(action, staff, member, reason="Nespecificat", duration=None):
    act_low = action.lower()
    target_ch_id = BAN_LOG_CH_ID if "ban" in act_low else (MOD_LOG_CH_ID if any(x in act_low for x in ["mute", "kick", "warn"]) else LOG_CH_ID)
    channel = bot.get_channel(target_ch_id)
    if not channel: return
    embed = discord.Embed(title=f"⛔ {action} | {member.name if hasattr(member, 'name') else str(member)}", color=0x2b2d31, timestamp=datetime.datetime.now(UTC))
    embed.add_field(name="👤 User", value=member.mention if hasattr(member, 'mention') else str(member))
    embed.add_field(name="🛡️ Staff", value=staff.mention if staff else "@Sistem Automat")
    embed.add_field(name="📄 Motiv", value=reason)
    await channel.send(embed=embed)

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

@bot.command()
@is_staff_up()
async def setup_apply(ctx):
    await ctx.message.delete()
    embed = discord.Embed(title="🛡️ RECRUTARE HELPER", description="Dacă vrei să te alături echipei, apasă pe buton!", color=0x2ecc71)
    await ctx.send(embed=embed, view=ApplyView())

@bot.command()
@is_staff_up()
async def setup_roles(ctx):
    await ctx.message.delete()
    embed = discord.Embed(description="🎭 **ALEGE-ȚI ROLURILE**", color=0x2b2d31)
    await ctx.send(embed=embed, view=SelfRoleView())

@bot.command()
@is_staff_up()
async def setup_ticket(ctx):
    await ctx.message.delete()
    embed = discord.Embed(description="🎫 **TICKETS**", color=0x2b2d31)
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
@is_staff_up()
async def ban(ctx, member: discord.Member, *, reason="Nespecificat"):
    await member.ban(reason=reason)
    await send_sanction_log("Ban", ctx.author, member, reason)

@bot.command()
@is_trial_up()
async def mute(ctx, member: discord.Member, duration: str, *, reason="Nespecificat"):
    unit = duration[-1].lower()
    amt = int(duration[:-1])
    secs = {"s": amt, "m": amt*60, "h": amt*3600, "d": amt*86400}.get(unit, 3600)
    await member.timeout(timedelta(seconds=secs), reason=reason)
    await send_sanction_log("Mute", ctx.author, member, reason)

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    if message.content.startswith("#"):
        await asyncio.sleep(10)
        try: await message.delete()
        except: pass
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} ONLINE")
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    bot.add_view(SelfRoleView())
    bot.add_view(ApplyView())

keep_alive()
bot.run(TOKEN)
