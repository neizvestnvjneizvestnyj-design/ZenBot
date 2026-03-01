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
REJECT_ROLE_ID = 1477702698936701019  # Rolul pentru cereri respinse

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
VERSION = "5.0"
CHANGES_LOG = """
✅ **Staff Apply Integration**: Cererile se fac acum prin tichete private.
✅ **Auto-Reject Role**: La respingere, se oferă automat rolul de Reject.
✅ **Role Expiry**: Rolul de Reject este scos automat după 3 zile.
✅ **Full Code Integrity**: Toate sistemele vechi au fost păstrate intacte.
"""

XP_COOLDOWN = 8
last_xp_time = {}  

# ================= SISTEM APPLY (TICHETE + REJECT) =================

class ApplyActionView(discord.ui.View):
    def __init__(self, applicant_id: int):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id

    @discord.ui.button(label="Acceptă (Trial)", style=discord.ButtonStyle.success, custom_id="apply_accept_v5")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.applicant_id)
        role_trial = guild.get_role(TRIAL_ID)
        
        if member and role_trial:
            await member.add_roles(role_trial)
            try: await member.send(f"🎉 Cererea ta pe **{guild.name}** a fost acceptată! Bine ai venit în Staff.")
            except: pass
            await interaction.response.send_message(f"✅ {member.mention} a fost acceptat ca Trial. Canalul se închide în 10s.")
            await asyncio.sleep(10)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ Utilizatorul nu a fost găsit sau rolul lipsește.", ephemeral=True)

    @discord.ui.button(label="Respinge", style=discord.ButtonStyle.danger, custom_id="apply_deny_v5")
    async def deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.applicant_id)
        reject_role = guild.get_role(REJECT_ROLE_ID)

        if member:
            # 1. Adăugăm rolul de reject
            if reject_role:
                await member.add_roles(reject_role)
            
            # 2. Trimitem mesaj privat
            try: await member.send(f"❌ Cererea ta de Staff pe **{guild.name}** a fost respinsă. Ai primit rolul de reject pentru 3 zile.")
            except: pass

            # 3. Task de scoatere automată după 3 zile (259200 secunde)
            async def remove_reject_task(m, r):
                await asyncio.sleep(259200) 
                try: await m.remove_roles(r)
                except: pass
            
            bot.loop.create_task(remove_reject_task(member, reject_role))

        await interaction.response.send_message("🚫 Cerere respinsă. Utilizatorul a primit rolul de reject (3 zile). Canalul se șterge...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class ApplyModal(discord.ui.Modal, title="Formular Staff"):
    nume = discord.ui.TextInput(label="Nume și Vârstă", placeholder="Ex: Marius, 19 ani", min_length=2)
    experienta = discord.ui.TextInput(label="Experiență", style=discord.TextStyle.paragraph, placeholder="Ai mai fost Staff? Dacă da, unde?")
    motiv = discord.ui.TextInput(label="De ce noi?", style=discord.TextStyle.paragraph, placeholder="Spune-ne de ce să te alegem pe tine.")

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ID)
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role: overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        category = guild.get_channel(TICKET_CATEGORY_ID)
        channel = await guild.create_text_channel(f"apply-{interaction.user.name}", category=category, overwrites=overwrites)
        
        embed = discord.Embed(title=f"📝 Cerere Staff: {interaction.user.name}", color=0x3498db, timestamp=datetime.datetime.now(UTC))
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(name="👤 Aplicant", value=interaction.user.mention)
        embed.add_field(name="🎂 Nume/Vârstă", value=self.nume.value)
        embed.add_field(name="🧠 Experiență", value=self.experienta.value, inline=False)
        embed.add_field(name="✨ Motiv", value=self.motiv.value, inline=False)
        
        await channel.send(content=f"🔔 <@&{STAFF_ID}>", embed=embed, view=ApplyActionView(interaction.user.id))
        await interaction.response.send_message(f"✅ Tichetul tău de apply a fost creat: {channel.mention}", ephemeral=True)

class ApplyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="APPLY STAFF", style=discord.ButtonStyle.success, custom_id="main_apply_btn", emoji="📝")
    async def apply_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplyModal())

# ================= ALTE CLASE UI PERSISTENTE =================

class SelfRoleView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    async def toggle_role(self, interaction: discord.Interaction, role_id: int):
        role = interaction.guild.get_role(role_id)
        if not role: return await interaction.response.send_message("❌ Rol negăsit.", ephemeral=True)
        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"🗑️ Scos: {role.name}", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Adăugat: {role.name}", ephemeral=True)

    @discord.ui.button(label="18+", style=discord.ButtonStyle.secondary, custom_id="r1", emoji="<:18Plus:1455072960812548157>")
    async def r1(self, i, b): await self.toggle_role(i, 1455073585306800128)
    @discord.ui.button(label="Under 18", style=discord.ButtonStyle.secondary, custom_id="r2", emoji="<:Under18:1455078800307126334>")
    async def r2(self, i, b): await self.toggle_role(i, 1455080987146064014)
    @discord.ui.button(label="Girl", style=discord.ButtonStyle.secondary, custom_id="r3", emoji="<:emoji_15:1448074655775719444>")
    async def r3(self, i, b): await self.toggle_role(i, 1455080720409034907)
    @discord.ui.button(label="Boy", style=discord.ButtonStyle.secondary, custom_id="r4", emoji="<:emoji_16:1448074879961268451>")
    async def r4(self, i, b): await self.toggle_role(i, 1455079548445130883)
    @discord.ui.button(label="Giveaway", style=discord.ButtonStyle.secondary, custom_id="r5", emoji="<a:purplepresent:1455082484604604531>")
    async def r5(self, i, b): await self.toggle_role(i, 1455081282009694258)
    @discord.ui.button(label="Wake Up", style=discord.ButtonStyle.secondary, custom_id="r6", emoji="<:__:1451889127581548648>")
    async def r6(self, i, b): await self.toggle_role(i, 1455082758094327922)

class TicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    async def create_ticket(self, interaction: discord.Interaction, category_name: str):
        guild = interaction.guild
        staff_role = guild.get_role(STAFF_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role: overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        category = guild.get_channel(TICKET_CATEGORY_ID)
        channel = await guild.create_text_channel(f"{category_name}-{interaction.user.name}", overwrites=overwrites, category=category)
        await channel.send(f"🎫 Ticket deschis de {interaction.user.mention}", view=CloseTicketView())
        await interaction.response.send_message(f"✅ Creat: {channel.mention}", ephemeral=True)

    @discord.ui.button(label="REPORT STAFF", style=discord.ButtonStyle.secondary, custom_id="ts1", emoji="⚠️")
    async def ts1(self, i, b): await self.create_ticket(i, "staff")
    @discord.ui.button(label="REPORT MEMBER", style=discord.ButtonStyle.secondary, custom_id="ts2", emoji="👥")
    async def ts2(self, i, b): await self.create_ticket(i, "member")
    @discord.ui.button(label="BAN REPORTS", style=discord.ButtonStyle.secondary, custom_id="ts3", emoji="🚫")
    async def ts3(self, i, b): await self.create_ticket(i, "ban")
    @discord.ui.button(label="CONTACT OWNER", style=discord.ButtonStyle.secondary, custom_id="ts4", emoji="👑")
    async def ts4(self, i, b): await self.create_ticket(i, "owner")
    @discord.ui.button(label="INFO & OTHERS", style=discord.ButtonStyle.secondary, custom_id="ts5", emoji="❓")
    async def ts5(self, i, b): await self.create_ticket(i, "info")

class CloseTicketView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Închide Ticket", style=discord.ButtonStyle.danger, custom_id="close_t_v5", emoji="🔒")
    async def close_t(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Se închide în 5s...")
        await asyncio.sleep(5)
        try: await interaction.channel.delete()
        except: pass

# ================= FUNCȚII AJUTĂTOARE (LOGURI, BOOST) =================

async def send_boost_announcement(member, guild):
    channel = bot.get_channel(BOOST_CH_ID)
    if not channel: return
    content = f"{member.mention} is RICH ASFFF!! 💸"
    embed = discord.Embed(title=f"{CUSTOM_EMOJI} **Another Star on the Board!**", color=0xf47fff, timestamp=datetime.datetime.now(UTC))
    embed.description = (f"💎 | A huge shoutout to **{member.name}** for boosting!\n\n"
                        f"✨ | You just made the server even better.\n"
                        f"📈 | We are now at **{guild.premium_subscription_count}** boosts!\n\n"
                        f"🎁 | Claim your rewards here: <#{BENEFITS_CH_ID}>")
    embed.set_image(url=BOOST_GIF)
    embed.set_footer(text=f"Server Level: {guild.premium_tier} • We appreciate you!")
    await channel.send(content=content, embed=embed)

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

# ================= VERIFICĂRI PERMISIUNI =================

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

# ================= COMENZI SETUP & MODERARE =================

@bot.command()
@is_staff_up()
async def setup_apply(ctx):
    await ctx.message.delete()
    embed = discord.Embed(title="✨ RECRUTARE STAFF ✨", description="Apasă butonul pentru a deschide un tichet privat de aplicare.", color=0x2ecc71)
    await ctx.send(embed=embed, view=ApplyView())

@bot.command()
@is_staff_up()
async def setup_roles(ctx):
    await ctx.message.delete()
    await ctx.send(embed=discord.Embed(title="🎭 SELF ROLES", color=0x2b2d31), view=SelfRoleView())

@bot.command()
@is_staff_up()
async def setup_ticket(ctx):
    await ctx.message.delete()
    await ctx.send(embed=discord.Embed(title="🎫 PANOU SUPORT", color=0x2b2d31), view=TicketView())

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
    else: await ctx.send("❌ Lipsă permisiuni!", delete_after=5)

@bot.command()
@is_above_staff()
async def slow(ctx, seconds: int):
    await ctx.channel.edit(slowmode_delay=seconds)
    await ctx.send(f"⏳ Slowmode: **{seconds}**s.", delete_after=5)
    await send_sanction_log("Slowmode", ctx.author, ctx.channel, f"Delay: {seconds}s")

@bot.command()
@is_staff_up()
async def ban(ctx, member: discord.Member, *, reason="Nespecificat"):
    await member.ban(reason=reason)
    await ctx.send(f"✅ Banat: {member.name}", delete_after=5)
    await send_sanction_log("Ban", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def unban(ctx, id: int):
    user = await bot.fetch_user(id)
    await ctx.guild.unban(user)
    await ctx.send(f"✅ Unban: {user.name}", delete_after=5)
    await send_sanction_log("Unban", ctx.author, user)

@bot.command()
@is_staff_up()
async def kick(ctx, member: discord.Member, *, reason="Nespecificat"):
    await member.kick(reason=reason)
    await ctx.send(f"✅ Kick: {member.name}", delete_after=5)
    await send_sanction_log("Kick", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def clear(ctx, amount: int = 100):
    if amount > 500: amount = 500
    deleted = await ctx.channel.purge(limit=amount)
    await send_sanction_log("Clear", ctx.author, ctx.channel, f"Mesaje: {len(deleted)}")
    await ctx.send(f"🧹 Șters {len(deleted)} mesaje.", delete_after=5)

@bot.command()
@is_staff_up()
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Blocat.", delete_after=5)
    await send_sanction_log("Lock", ctx.author, ctx.channel)

@bot.command()
@is_staff_up()
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Deblocat.", delete_after=5)
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
        await member.ban(reason=f"3/3 warns")
        await send_sanction_log("Ban Automat", None, member, "3/3 Warns")
    else:
        rls = [WARN1_ROLE_ID, W2_ID, W3_ID]
        if count <= len(rls):
            r = ctx.guild.get_role(rls[count-1])
            if r: await member.add_roles(r)
        await ctx.send(f"⚠️ Warn {count}/3 pentru {member.mention}.", delete_after=5)
        await send_sanction_log(f"Warn {count}/3", ctx.author, member, reason)

@bot.command()
@is_staff_up()
async def unwarn(ctx, member: discord.Member):
    data = load_data()
    uid = str(member.id)
    if uid in data["warnings"]: del data["warnings"][uid]
    save_data(data)
    for rid in [WARN1_ROLE_ID, W2_ID, W3_ID]:
        r = ctx.guild.get_role(rid); 
        if r and r in member.roles: await member.remove_roles(r)
    await ctx.send(f"✅ Resetat warn-uri: {member.mention}", delete_after=5)

@bot.command()
@is_trial_up()
async def mute(ctx, member: discord.Member, duration: str, *, reason="Nespecificat"):
    unit = duration[-1].lower()
    amt = int(duration[:-1])
    sec = {"s": amt, "m": amt*60, "h": amt*3600, "d": amt*86400}.get(unit, 3600)
    await member.timeout(timedelta(seconds=sec), reason=reason)
    await ctx.send(f"🔇 Mute {duration}.", delete_after=5)
    await send_sanction_log("Mute", ctx.author, member, reason, duration)

@bot.command()
@is_trial_up()
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"🔊 Unmute.", delete_after=5)

@bot.command()
@is_staff_up()
async def addrole(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"✅ Adăugat {role.name}", delete_after=5)

@bot.command()
@is_staff_up()
async def removerole(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(f"✅ Scos {role.name}", delete_after=5)

@bot.command()
async def avatar(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"✅ Adăugat {role.name}", delete_after=5)

@bot.command()
@is_staff_up()
async def removerole(ctx, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await ctx.send(f"✅ Scos {role.name}", delete_after=5)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    await ctx.send(embed=discord.Embed().set_image(url=member.display_avatar.url))

# ================= EVENIMENTE & SISTEM XP =================

@bot.event
async def on_member_join(member):
    ch = bot.get_channel(WELCOME_CH_ID)
    if ch: await ch.send(embed=discord.Embed(description=f"🎉 Bun venit {member.mention}!", color=0x2b2d31))

@bot.event
async def on_message(message):
    if message.author.bot or not message.guild: return

    # Auto-delete comenzi
    if message.content.startswith("#"):
        async def del_msg():
            await asyncio.sleep(10); await message.delete()
        bot.loop.create_task(del_msg())

    # Protectie Link-uri (Auto-Mod)
    content_low = message.content.lower()
    if ("http" in content_low or "discord.gg/" in content_low) and not any(x in content_low for x in ["youtube.com", "youtu.be", "imgur.com"]):
        trial_role = message.guild.get_role(TRIAL_ID)
        if not (trial_role and message.author.top_role.position >= trial_role.position):
            await message.delete()
            await message.channel.send(f"❌ {message.author.mention}, link-urile sunt interzise!", delete_after=5)
            return

    # Sistem XP
    uid = str(message.author.id)
    now = time.time()
    if uid not in last_xp_time or now - last_xp_time[uid] > XP_COOLDOWN:
        last_xp_time[uid] = now
        data = load_data()
        if uid not in data["levels"]: data["levels"][uid] = {"xp": 0, "level": 1}
        data["levels"][uid]["xp"] += 10
        if data["levels"][uid]["xp"] >= data["levels"][uid]["level"] * 100:
            data["levels"][uid]["level"] += 1
            await message.channel.send(f"🎉 {message.author.mention} nivel **{data['levels'][uid]['level']}**!", delete_after=5)
        save_data(data)

    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} ONLINE")
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    bot.add_view(SelfRoleView())
    bot.add_view(ApplyView())
    # Register persistent views for apply buttons in tickets
    bot.add_view(ApplyActionView(0)) 

    ch = bot.get_channel(UPDATE_LOG_CH_ID)
    if ch:
        embed = discord.Embed(title=f"🚀 Versiunea {VERSION} Activă!", color=0x00ff00)
        embed.add_field(name="Modificări:", value=CHANGES_LOG)
        await ch.send(embed=embed)

keep_alive()
bot.run(TOKEN)