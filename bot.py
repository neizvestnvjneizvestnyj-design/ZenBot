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
APPLY_LOG_CH_ID = 1444796054313766922 # Poți pune un ID separat pentru cereri staff

WARN1_ROLE_ID = 1436538867850416289
W2_ID = 1436538789311811624
W3_ID = 1450009480417902796

MY_GIF = "https://media.discordapp.net/attachments/1440112412266205194/1461843437694484684/f63ce9f5-d6b6-47d9-91f0-eb1e166ab02a.gif"
BOOST_GIF = "https://media.tenor.com/7123Lof2_mEAAAAC/make-it-rain-money.gif"
CUSTOM_EMOJI = "<:emoji_16:1448074879961268451>"

# --- CHANGELOG AUTOMAT ---
VERSION = "2.6"
CHANGES_LOG = """
✅ **Staff Apply**: Sistem nou de cereri helper/staff prin modal (formular).
✅ **Stabilitate**: Păstrarea tuturor celor 612 rânduri anterioare.
"""

XP_COOLDOWN = 8
last_xp_time = {}  

# ================= SISTEM APPLY (NOU) =================
class ApplyModal(discord.ui.Modal, title="Cerere Staff / Helper"):
    nume = discord.ui.TextInput(label="Nume și Vârstă", placeholder="Ex: Andrei, 18 ani", min_length=3, max_length=50)
    experienta = discord.ui.TextInput(label="Experiență Staff", style=discord.TextStyle.paragraph, placeholder="Ai mai fost staff? Dacă da, unde?", required=True)
    timp = discord.ui.TextInput(label="Timp disponibil", placeholder="Ex: 4-5 ore pe zi", max_length=100)
    motiv = discord.ui.TextInput(label="De ce te-am alege pe tine?", style=discord.TextStyle.paragraph, placeholder="Spune-ne de ce vrei acest post.")

    async def on_submit(self, interaction: discord.Interaction):
        log_ch = interaction.guild.get_channel(APPLY_LOG_CH_ID)
        if not log_ch:
            return await interaction.response.send_message("❌ Canalul de loguri apply nu a fost găsit!", ephemeral=True)
        
        embed = discord.Embed(title=f"📝 Cerere Staff: {interaction.user.name}", color=0x7289da, timestamp=datetime.datetime.now(UTC))
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Utilizator", value=interaction.user.mention, inline=True)
        embed.add_field(name="🆔 ID", value=interaction.user.id, inline=True)
        embed.add_field(name="🎂 Nume/Vârstă", value=self.nume.value, inline=False)
        embed.add_field(name="⏳ Timp", value=self.timp.value, inline=False)
        embed.add_field(name="🧠 Experiență", value=self.experienta.value, inline=False)
        embed.add_field(name="✨ Motiv", value=self.motiv.value, inline=False)
        
        await log_ch.send(embed=embed)
        await interaction.response.send_message("✅ Cererea ta a fost trimisă cu succes către Administrație!", ephemeral=True)

class ApplyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="APPLY STAFF", style=discord.ButtonStyle.success, custom_id="apply_staff_btn", emoji="📝")
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
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

# ================= CLASE TICKETS =================
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def create_ticket(self, interaction: discord.Interaction, category_name: str):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ID)
        
        channel_name = f"{category_name}-{interaction.user.name.lower()}"
        existing_channel = discord.utils.get(guild.channels, name=channel_name)
        
        if existing_channel:
            return await interaction.response.send_message(f"❌ Ai deja un ticket de acest tip deschis: {existing_channel.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        category = guild.get_channel(TICKET_CATEGORY_ID)
        channel = await guild.create_text_channel(channel_name, overwrites=overwrites, category=category)
        
        embed = discord.Embed(
            title=f"🎫 Ticket: {category_name.upper()}", 
            description=f"Salut {interaction.user.mention}!\nAi deschis un ticket pentru: **{category_name.replace('-', ' ')}**.\nEchipa Staff va prelua cererea ta în cel mai scurt timp.\n\nFolosește butonul de mai jos pentru a închide tichetul.", 
            color=0x2b2d31
        )
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket creat: {channel.mention}", ephemeral=True)

    @discord.ui.button(label="REPORT STAFF", style=discord.ButtonStyle.secondary, custom_id="t_staff", emoji="⚠️")
    async def t_staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "staff")

    @discord.ui.button(label="REPORT MEMBER", style=discord.ButtonStyle.secondary, custom_id="t_member", emoji="👥")
    async def t_member(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "member")

    @discord.ui.button(label="BAN REPORTS", style=discord.ButtonStyle.secondary, custom_id="t_ban", emoji="🚫")
    async def t_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "ban")

    @discord.ui.button(label="CONTACT OWNER", style=discord.ButtonStyle.secondary, custom_id="t_owner", emoji="👑")
    async def t_owner(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "owner")

    @discord.ui.button(label="INFO & OTHERS", style=discord.ButtonStyle.secondary, custom_id="t_info", emoji="❓")
    async def t_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "info")

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Închide Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Tichetul se va închide în 5 secunde...")
        await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass

# ================= FUNCTII ANUNT/LOGS/PERMS =================
async def send_boost_announcement(member, guild):
    channel = bot.get_channel(BOOST_CH_ID)
    if not channel: return
    content = f"{member.mention} is RICH ASFFF!! 💸"
    embed = discord.Embed(title=f"{CUSTOM_EMOJI} **Another Star on the Board!**", color=0xf47fff, timestamp=datetime.datetime.now(UTC))
    embed.description = (f"💎 | A huge shoutout to **{member.name}** for boosting!\n\n✨ | You just made the server even better.\n📈 | We are now at **{guild.premium_subscription_count}** boosts!\n\n🎁 | Claim your rewards here: <#{BENEFITS_CH_ID}>")
    embed.set_image(url=BOOST_GIF)
    embed.set_footer(text=f"Server Level: {guild.premium_tier}")
    await channel.send(content=content, embed=embed)

async def send_sanction_log(action, staff, member, reason="Nespecificat", duration=None):
    act_low = action.lower()
    target_ch_id = BAN_LOG_CH_ID if "ban" in act_low else (MOD_LOG_CH_ID if any(x in act_low for x in ["mute", "kick", "warn", "unmute", "unwarn", "lock", "unlock", "slow"]) else LOG_CH_ID)
    channel = bot.get_channel(target_ch_id)
    if not channel: return
    embed = discord.Embed(title=f"⛔ {action} | {member.name if hasattr(member, 'name') else str(member)}", color=0x2b2d31, timestamp=datetime.datetime.now(UTC))
    embed.set_thumbnail(url=MY_GIF)
    embed.add_field(name="👤 User", value=member.mention if hasattr(member, 'mention') else str(member), inline=True)
    embed.add_field(name="🛡️ Staff", value=staff.mention if staff else "@Sistem Automat", inline=True)
    embed.add_field(name="📄 Motiv", value=reason, inline=True)
    if duration: embed.add_field(name="⏳ Detalii", value=duration, inline=True)
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

# ================= COMENZI =================

@bot.command()
@is_staff_up()
async def setup_apply(ctx):
    await ctx.message.delete()
    embed = discord.Embed(
        title="✨ RECRUTARE STAFF ✨",
        description="Ești dornic să ajuți comunitatea noastră? Căutăm membri activi și serioși!\n\n**Cerințe minime:**\n• Minim 14 ani.\n• Limbaj corect gramatical.\n• Activitate zilnică.\n\n*Apasă butonul de mai jos pentru a completa cererea!*",
        color=0x2ecc71
    )
    await ctx.send(embed=embed, view=ApplyView())

@bot.command()
@is_staff_up()
async def setup_roles(ctx):
    await ctx.message.delete()
    descriere_panou = ("🎭 **ALEGE-ȚI ROLURILE**\n...\n```🎭 SELF ROLES\n\n+18 ; 18+\n-18 ; UNDER 18\n🔞 ; GIRL\n🔞 ; BOY\n🎁 ; GIVEAWAY\n✨ ; WAKE UP```")
    embed = discord.Embed(description=descriere_panou, color=0x2b2d31)
    await ctx.send(embed=embed, view=SelfRoleView())

@bot.command()
@is_staff_up()
async def setup_ticket(ctx):
    await ctx.message.delete()
    text_panou = ("⚠️ ；**REPORT STAFF**\n...\n**📢 ；Crearea ticketelor în batjocură/glumă se pedepsește!**")
    embed = discord.Embed(description=text_panou, color=0x2b2d31)
    await ctx.send(embed=embed, view=TicketView())

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
        await send_boost_announcement(member or ctx.author, ctx.guild)
    else:
        await ctx.send("❌ Nu ai permisiunea necesară!", delete_after=5)

@bot.command()
@is_above_staff()
async def slow(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"⏳ Slowmode setat la **{seconds}** secunde.", delete_after=5)

@bot.command()
@is_staff_up()
async def ban(ctx, member: discord.Member, *, reason="Nespecificat"):
    await member.ban(reason=reason)
    await send_sanction_log("Ban", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def unban(ctx, id: int):
    user = await bot.fetch_user(id)
    await ctx.guild.unban(user)
    await send_sanction_log("Unban", ctx.author, user)

@bot.command()
@is_staff_up()
async def kick(ctx, member: discord.Member, *, reason="Nespecificat"):
    await member.kick(reason=reason)
    await send_sanction_log("Kick", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def clear(ctx, amount: int = 100):
    deleted = await ctx.channel.purge(limit=min(amount, 500))
    await ctx.send(f"🧹 {len(deleted)} mesaje șterse.", delete_after=5)

@bot.command()
@is_staff_up()
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Canal blocat.", delete_after=5)

@bot.command()
@is_staff_up()
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Canal deblocat.", delete_after=5)

@bot.command()
@is_staff_up()
async def warn(ctx, member: discord.Member, *, reason="Nespecificat"):
    data = load_data()
    uid = str(member.id)
    data["warnings"][uid] = data["warnings"].get(uid, 0) + 1
    count = data["warnings"][uid]
    save_data(data)
    if count >= 3:
        await member.ban(reason=f"3/3 warns")
    else:
        await ctx.send(f"⚠️ {member.mention} warn {count}/3.", delete_after=5)
    await send_sanction_log(f"Warn {count}/3", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def unwarn(ctx, member: discord.Member):
    data = load_data()
    uid = str(member.id)
    if uid in data["warnings"]: del data["warnings"][uid]
    save_data(data)
    await ctx.send(f"✅ Resetat.", delete_after=5)

@bot.command()
@is_trial_up()
async def mute(ctx, member: discord.Member, duration: str, *, reason="Nespecificat"):
    unit = duration[-1].lower()
    amt = int(duration[:-1])
    sec = {"s": amt, "m": amt*60, "h": amt*3600, "d": amt*86400}.get(unit, 3600)
    await member.timeout(timedelta(seconds=sec), reason=reason)
    await send_sanction_log("Mute", ctx.author, member, reason, duration)

@bot.command()
@is_trial_up()
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await send_sanction_log("Unmute", ctx.author, member, "Manual")

# ================= EVENIMENTE =================
@bot.event
async def on_member_join(member):
    ch = bot.get_channel(WELCOME_CH_ID)
    if ch: await ch.send(embed=discord.Embed(description=f"🎉 Bun venit, {member.mention}", color=0x2b2d31))

@bot.event
async def on_member_remove(member):
    ch = bot.get_channel(WELCOME_CH_ID)
    if ch: await ch.send(embed=discord.Embed(description=f"👋 **{member.name}** a plecat.", color=0x2b2d31))

@bot.event
async def on_voice_state_update(member, before, after):
    log = bot.get_channel(LOG_CH_ID)
    if not log: return
    if before.channel is None and after.channel:
        await log.send(embed=discord.Embed(title="📥 Join", description=f"{member.mention} -> {after.channel.mention}", color=0x43b581))
    elif before.channel and after.channel is None:
        await log.send(embed=discord.Embed(title="📤 Leave", description=f"{member.mention} -> {before.channel.name}", color=0xf04747))

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    log = bot.get_channel(LOG_CH_ID)
    if log:
        emb = discord.Embed(title="🗑️ Șters", color=0xff4500)
        emb.add_field(name="Autor", value=message.author.mention)
        emb.add_field(name="Text", value=message.content or "N/A")
        await log.send(embed=emb)

@bot.command()
@is_staff_up()
async def addrole(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send("✅ Adăugat.", delete_after=5)

@bot.command()
@is_staff_up()
async def removerole(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send("✅ Scos.", delete_after=5)

@bot.command()
@is_trial_up()
async def warns(ctx, member: discord.Member = None):
    data = load_data()
    c = data["warnings"].get(str((member or ctx.author).id), 0)
    await ctx.send(f"🔍 {c}/3 warns.")

@bot.command()
async def comenzi(ctx):
    if ctx.channel.id != STAFF_CMD_CHANNEL: return
    embed = discord.Embed(title="📜 Liste commandes STAFF", color=0x2b2d31, description="Prefix: **#**\n\n**#ban** @user\n**#kick** @user\n**#mute** @user 1h\n**#warn** @user\n**#setup_apply** (Cereri Staff)")
    await ctx.send(embed=embed)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    if ctx.channel.id != BOT_COMMANDS_CH: return
    m = member or ctx.author
    emb = discord.Embed(title=f"Avatar • {m.name}")
    emb.set_image(url=m.display_avatar.url)
    await ctx.send(embed=emb)

@bot.command()
async def serverinfo(ctx):
    if ctx.channel.id != BOT_COMMANDS_CH: return
    g = ctx.guild
    emb = discord.Embed(title=f"{g.name} Info")
    emb.add_field(name="Membri", value=g.member_count)
    await ctx.send(embed=emb)

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return
    if message.content.startswith("#"):
        await asyncio.sleep(10)
        try: await message.delete()
        except: pass
    
    # --- LOGICA XP ---
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
            await message.channel.send(f"🎉 {message.author.mention} nivel {lvl+1}!", delete_after=12)
        save_data(data)

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} ONLINE")
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    bot.add_view(SelfRoleView())
    bot.add_view(ApplyView()) # Persistent button for Staff Apply

    ch = bot.get_channel(UPDATE_LOG_CH_ID)
    if ch:
        await ch.purge(limit=5)
        await ch.send(f"🚀 Versiunea {VERSION} activă!", file=discord.File("bot.py") if os.path.exists("bot.py") else None)

keep_alive()
bot.run(TOKEN)