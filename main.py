import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
import json
import random
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Bot configuration
TOKEN = os.getenv('DISCORD_TOKEN')
PREFIX = os.getenv('COMMAND_PREFIX', '!')

# Warning system storage (JSON file)
WARNINGS_FILE = 'warnings.json'

def load_warnings():
    """Load warnings from JSON file"""
    if os.path.exists(WARNINGS_FILE):
        with open(WARNINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_warnings(warnings):
    """Save warnings to JSON file"""
    with open(WARNINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(warnings, f, indent=4, ensure_ascii=False)

def add_warning(guild_id, user_id, reason, moderator_id):
    """Add a warning to a user"""
    warnings = load_warnings()
    guild_id = str(guild_id)
    user_id = str(user_id)
    
    if guild_id not in warnings:
        warnings[guild_id] = {}
    if user_id not in warnings[guild_id]:
        warnings[guild_id][user_id] = []
    
    warning = {
        'reason': reason,
        'moderator_id': moderator_id,
        'timestamp': datetime.now().isoformat()
    }
    warnings[guild_id][user_id].append(warning)
    save_warnings(warnings)
    return len(warnings[guild_id][user_id])

def get_warnings(guild_id, user_id):
    """Get all warnings for a user"""
    warnings = load_warnings()
    guild_id = str(guild_id)
    user_id = str(user_id)
    return warnings.get(guild_id, {}).get(user_id, [])

def clear_user_warnings(guild_id, user_id):
    """Clear all warnings for a user"""
    warnings = load_warnings()
    guild_id = str(guild_id)
    user_id = str(user_id)
    
    if guild_id in warnings and user_id in warnings[guild_id]:
        del warnings[guild_id][user_id]
        save_warnings(warnings)
        return True
    return False

# ───────────────────────────────────────────────
# MODERATION LOGS SYSTEM
# ───────────────────────────────────────────────

MODLOGS_FILE = 'modlogs.json'

def load_modlogs():
    """Load moderation logs from JSON file"""
    if os.path.exists(MODLOGS_FILE):
        with open(MODLOGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_modlogs(logs):
    """Save moderation logs to JSON file"""
    with open(MODLOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)

def add_modlog(guild_id, action, target_id, target_name, moderator_id, moderator_name, reason=None, duration=None):
    """Add a moderation log entry"""
    logs = load_modlogs()
    guild_id = str(guild_id)
    
    if guild_id not in logs:
        logs[guild_id] = []
    
    log_entry = {
        'id': len(logs[guild_id]) + 1,
        'action': action,
        'target_id': str(target_id),
        'target_name': target_name,
        'moderator_id': str(moderator_id),
        'moderator_name': moderator_name,
        'reason': reason or "Tiada sebab diberikan",
        'duration': duration,
        'timestamp': datetime.now().isoformat()
    }
    
    logs[guild_id].insert(0, log_entry)  # Add to beginning (newest first)
    save_modlogs(logs)
    return log_entry['id']

def get_modlogs(guild_id, user_id=None, limit=50):
    """Get moderation logs for a guild or specific user"""
    logs = load_modlogs()
    guild_id = str(guild_id)
    
    if guild_id not in logs:
        return []
    
    guild_logs = logs[guild_id]
    
    if user_id:
        user_id = str(user_id)
        guild_logs = [log for log in guild_logs if log['target_id'] == user_id]
    
    return guild_logs[:limit]

def get_user_modlog_count(guild_id, user_id):
    """Get total moderation actions against a user"""
    logs = get_modlogs(guild_id, user_id)
    counts = {}
    for log in logs:
        action = log['action']
        counts[action] = counts.get(action, 0) + 1
    return counts, len(logs)

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content
intents.members = True  # Required for member-related events

# Create bot instance
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'[BOT] {bot.user.name} telah berjaya log masuk!')
    print(f'[ID] Bot ID: {bot.user.id}')
    print(f'[SERVER] Berada di {len(bot.guilds)} server')
    print('-' * 40)
    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f'{PREFIX}help untuk bantuan'
        ),
        status=discord.Status.online
    )

# Event: Member joins server
@bot.event
async def on_member_join(member):
    print(f'[JOIN] {member.name} telah menyertai {member.guild.name}')
    
    # Send welcome embed to specific channel
    WELCOME_CHANNEL_ID = 1490320988766867548
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        # Calculate account age
        account_age = (datetime.now() - member.created_at).days
        
        embed = discord.Embed(
            title='ByteWolf Studio',
            description=f'{member.mention} **Selamat datang ke ByteWolf Studio!** 🎉\n\n'
                       f'Kami sangat gembira **Awak** ada di sini! Semoga seronok dan jangan segan-segan untuk tanya apa-apa. 😊',
            color=0x10b981,  # Green
            timestamp=datetime.now()
        )
        
        # List format (single column)
        embed.add_field(name='Nama:', value=f'```{member.name}```', inline=False)
        embed.add_field(name='ID:', value=f'```{member.id}```', inline=False)
        embed.add_field(name='Ahli:', value=f'```{member.guild.member_count}```', inline=False)
        embed.add_field(name='Join Server:', value=f'```{datetime.now().strftime("%d/%m/%Y")}\n(Today)```', inline=False)
        embed.add_field(name='Akaun Dibuat:', value=f'```{member.created_at.strftime("%d/%m/%Y")}\n({account_age} hari)```', inline=False)
        embed.add_field(name='Invite By:', value='```Unknown```', inline=False)
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.set_footer(text=f'Server: {member.guild.name}', icon_url=member.guild.icon.url if member.guild.icon else None)
        
        try:
            await channel.send(embed=embed)
        except:
            pass  # Channel might not have permission

# Event: Member leaves server
@bot.event
async def on_member_remove(member):
    print(f'[LEAVE] {member.name} telah meninggalkan {member.guild.name}')
    
    # Send leave embed to specific channel
    WELCOME_CHANNEL_ID = 1490320988766867548
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        # Calculate days stayed
        if member.joined_at:
            days_stayed = (datetime.now() - member.joined_at).days
            join_date = member.joined_at.strftime('%d/%m/%Y')
        else:
            days_stayed = 'Unknown'
            join_date = 'Unknown'
        
        leave_date = datetime.now().strftime('%d/%m/%Y')
        
        embed = discord.Embed(
            title='ByteWolf Studio',
            description=f'{member.mention} **Terima kasih kerana bersama kami di ByteWolf Studio!**\n\n'
                       f'Semoga berjumpa lagi di lain waktu. Jaga diri dan datanglah lagi bila-bila masa! 😊',
            color=0xef4444,  # Red
            timestamp=datetime.now()
        )
        
        # Calculate account age for leave embed too
        account_age = (datetime.now() - member.created_at).days
        account_created = f'```{member.created_at.strftime("%d/%m/%Y")}\n({account_age} hari)```'
        
        # List format (single column)
        embed.add_field(name='Nama:', value=f'```{member.name}```', inline=False)
        embed.add_field(name='ID:', value=f'```{member.id}```', inline=False)
        embed.add_field(name='Ahli:', value=f'```{member.guild.member_count}```', inline=False)
        embed.add_field(name='Akaun Dibuat:', value=account_created, inline=False)
        embed.add_field(name='Ahli Sejak:', value=f'```{join_date}```', inline=False)
        embed.add_field(name='Keluar Server:', value=f'```{leave_date}```', inline=False)
        embed.add_field(name='Total Stay:', value=f'```{days_stayed} hari```', inline=False)
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.set_footer(text=f'Server: {member.guild.name}', icon_url=member.guild.icon.url if member.guild.icon else None)
        
        try:
            await channel.send(embed=embed)
        except:
            pass  # Channel might not have permission

# Event: When a message is received
@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Ignore DMs and messages without guild
    if not message.guild:
        return
    
    # Check if owner is mentioned and auto-reply if offline >15 mins
    await check_owner_mention(message)
    
    # Check for spam
    is_spam = await check_spam(message)
    if is_spam:
        await send_spam_warning(message)
        return  # Stop processing if spam detected
    
    # Check for profanity
    has_profanity, bad_word = await check_profanity(message)
    if has_profanity:
        await send_profanity_warning(message, bad_word)
        return  # Stop processing if profanity detected
    
    # Process commands
    await bot.process_commands(message)

# Auto-reply when owner mentioned
owner_last_online = {}
owner_id = None  # Will be set from .env or first guild owner

async def check_owner_mention(message):
    """Check if owner is mentioned and send auto-reply if offline >15 mins"""
    global owner_id
    
    # Skip bot commands (messages starting with ? or !)
    if message.content.startswith('?') or message.content.startswith('!'):
        return
    
    if owner_id is None:
        # Try to get owner from first guild
        for guild in bot.guilds:
            owner_id = guild.owner_id
            break
    
    if owner_id is None:
        return
    
    # Check if owner is mentioned in the message
    if owner_id not in [m.id for m in message.mentions]:
        return
    
    # Check owner's current status
    owner = message.guild.get_member(owner_id) if message.guild else None
    if not owner:
        return
    
    # If owner is offline or idle for >15 mins
    if owner.status in [discord.Status.offline, discord.Status.idle]:
        last_online = owner_last_online.get(owner_id)
        now = datetime.now()
        
        # If never tracked or offline >15 mins (900 seconds)
        if last_online is None or (now - last_online).total_seconds() > 900:
            # Send auto-reply with clean embed
            embed = discord.Embed(
                description=f"Hai {message.author.mention}, terima kasih sebab mesej! "
                           f"{owner.display_name} akan balas dalam masa terdekat. "
                           f"Mesej ni dari bot je, jadi jangan risau ya!",
                color=0x6366f1,
                timestamp=datetime.now()
            )
            embed.set_author(
                name=f"{owner.display_name} - Sedang Tidak Online",
                icon_url=owner.avatar.url if owner.avatar else None
            )
            embed.set_footer(text="Auto-Reply System")
            await message.channel.send(embed=embed, delete_after=60)

# Event: Track when owner comes online
@bot.event
async def on_presence_update(before, after):
    """Track when owner comes online"""
    global owner_id, owner_last_online
    
    if owner_id is None:
        return
    
    if after.id == owner_id:
        # Owner is now online
        if after.status in [discord.Status.online, discord.Status.dnd]:
            owner_last_online[owner_id] = datetime.now()
            print(f'[ONLINE] Owner {after.display_name} is now online')

# ───────────────────────────────────────────────
# AUTO-REMINDER & SPAM/PROFANITY FILTER
# ───────────────────────────────────────────────

# Message tracking for spam detection
user_message_history = {}  # {user_id: [(timestamp, message_content), ...]}
user_violations = {}  # {user_id: {'spam': count, 'profanity': count}}

# Bad words list (Malay + English profanity)
BAD_WORDS = [
    # English
    'fuck', 'shit', 'damn', 'bitch', 'asshole', 'bastard', 'crap', 'dick', 'piss',
    # Malay vulgar
    'babi', 'anjing', 'sial', 'bodoh', 'bangang', 'bengap', 'tak guna', 'tolol',
    'celaka', 'setan', 'jahannam', 'mampus', 'mati', 'kurang ajar', 'biadab',
]

SPAM_THRESHOLD = 5  # Messages within time window
SPAM_TIME_WINDOW = 5  # Seconds
MAX_VIOLATIONS = 3  # Max warnings before action

async def check_spam(message):
    """Check if user is spamming"""
    user_id = message.author.id
    now = datetime.now()
    
    # Get or create user history
    if user_id not in user_message_history:
        user_message_history[user_id] = []
    
    # Add current message
    user_message_history[user_id].append((now, message.content))
    
    # Clean old messages outside time window
    cutoff = now - timedelta(seconds=SPAM_TIME_WINDOW)
    user_message_history[user_id] = [
        (t, m) for t, m in user_message_history[user_id] if t > cutoff
    ]
    
    # Check if spamming
    if len(user_message_history[user_id]) >= SPAM_THRESHOLD:
        return True
    return False

async def check_profanity(message):
    """Check if message contains bad words"""
    content_lower = message.content.lower()
    
    for word in BAD_WORDS:
        if word in content_lower:
            return True, word
    return False, None

async def send_spam_warning(message):
    """Send spam warning to user"""
    user_id = message.author.id
    
    # Track violations
    if user_id not in user_violations:
        user_violations[user_id] = {'spam': 0, 'profanity': 0}
    user_violations[user_id]['spam'] += 1
    
    embed = discord.Embed(
        title='🚨 Peringatan! 🚨',
        description=f'Hey {message.author.mention}! Elakkan spam dalam chat, ya! '
                   f'Untuk pastikan semua orang selesa, tindakan akan diambil '
                   f'jika spam berterusan. Terima kasih atas kerjasama! 😊',
        color=0xf59e0b,  # Orange warning
        timestamp=datetime.now()
    )
    embed.set_footer(text=f'Auto-Reminder System | Peringatan #{user_violations[user_id]["spam"]}/3')
    
    await message.channel.send(embed=embed, delete_after=30)
    
    # Take action if too many violations
    if user_violations[user_id]['spam'] >= MAX_VIOLATIONS:
        await take_action(message, 'spam')

async def send_profanity_warning(message, word):
    """Send profanity warning to user"""
    user_id = message.author.id
    
    # Track violations
    if user_id not in user_violations:
        user_violations[user_id] = {'spam': 0, 'profanity': 0}
    user_violations[user_id]['profanity'] += 1
    
    embed = discord.Embed(
        title='🚨 Peringatan! 🚨',
        description=f'Hey {message.author.mention}! Sila elakkan daripada '
                   f'menggunakan kata-kata kesat dalam chat. Kami ingin kekalkan '
                   f'suasana yang positif untuk semua. Tindakan akan diambil '
                   f'jika ia berterusan. Terima kasih atas kerjasama! 😊',
        color=0xef4444,  # Red warning
        timestamp=datetime.now()
    )
    embed.set_footer(text=f'Auto-Reminder System | Peringatan #{user_violations[user_id]["profanity"]}/3')
    
    # Delete the offensive message
    try:
        await message.delete()
    except:
        pass
    
    await message.channel.send(embed=embed, delete_after=30)
    
    # Take action if too many violations
    if user_violations[user_id]['profanity'] >= MAX_VIOLATIONS:
        await take_action(message, 'profanity')

async def take_action(message, violation_type):
    """Notify admins about repeated violations (no auto-mute)"""
    member = message.author
    
    # Send notification to channel about repeated violations
    embed = discord.Embed(
        title='⚠️ Pengguna Mencapai Had Peringatan',
        description=f'{member.mention} telah mencapai **3 peringatan** untuk {violation_type}.\n\n'
                   f'Sila ambil tindakan yang sesuai (warn/mute/kick).',
        color=0xef4444
    )
    embed.add_field(name='Pengguna', value=f'{member.name} ({member.id})', inline=True)
    embed.add_field(name='Jenis', value=violation_type, inline=True)
    embed.add_field(name='Saluran', value=message.channel.mention, inline=False)
    embed.set_footer(text='Admin Action Required - No auto-mute applied')
    
    await message.channel.send(embed=embed)

# ───────────────────────────────────────────────
# COMMANDS
# ───────────────────────────────────────────────

# Ping command - Check bot latency
@bot.command(name='ping')
async def ping(ctx):
    """Semak kelewatan (latency) bot"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title='🏓 Pong!',
        description=f'Kelewatan: **{latency}ms**',
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

# Premium Help View with Pagination
class HelpView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.current_page = 0
        self.total_pages = 3
        self.prefix = PREFIX
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "[Hanya pemohon boleh guna button ini]", ephemeral=True
            )
            return False
        return True
    
    def get_page_embed(self, page_num: int) -> discord.Embed:
        if page_num == 0:
            return self.get_main_page()
        elif page_num == 1:
            return self.get_public_page()
        else:
            return self.get_admin_page()
    
    def get_main_page(self) -> discord.Embed:
        embed = discord.Embed(
            title="[ BUKU PANDUAN BOT ]",
            description=f"Selamat datang ke **{self.ctx.bot.user.name}**\n\n"
                       f"Gunakan button di bawah untuk navigasi antara halaman.",
            color=0x6366f1,  # Premium indigo color
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="[ INFO SISTEM ]",
            value=f"```asciidoc\n"
                  f"Prefix Bot :: {self.prefix}\n"
                  f"Jumlah Command :: 19 commands\n"
                  f"Versi :: 1.0.0\n"
                  f"```",
            inline=False
        )
        
        embed.add_field(
            name="[ KATEGORI ]",
            value=f"> **Halaman 2** - Commands Awam (10)\n"
                  f"> **Halaman 3** - Commands Admin (9)\n",
            inline=False
        )
        
        embed.add_field(
            name="[ NOTA ]",
            value="```diff\n"
                  "+ Commands awam - semua pengguna boleh guna\n"
                  "- Commands admin - memerlukan kebenaran khas\n"
                  "```",
            inline=False
        )
        
        embed.set_author(
            name=f"{self.ctx.bot.user.name} Help System",
            icon_url=self.ctx.bot.user.avatar.url if self.ctx.bot.user.avatar else None
        )
        embed.set_footer(
            text=f"Diminta oleh {self.ctx.author.display_name} | Halaman 1/{self.total_pages}",
            icon_url=self.ctx.author.avatar.url if self.ctx.author.avatar else None
        )
        return embed
    
    def get_public_page(self) -> discord.Embed:
        embed = discord.Embed(
            title="[ COMMANDS AWAM ]",
            description="Commands yang boleh digunakan oleh semua pengguna tanpa kebenaran khas.",
            color=0x10b981,  # Emerald green
            timestamp=datetime.now()
        )
        
        public_commands = [
            ("ping", "Semak kelewatan bot", "-"),
            ("help", "Papar buku panduan ini", "-"),
            ("info", "Maklumat tentang bot", "-"),
            ("say <teks>", "Ulang balik mesej anda", "Hapus command"),
            ("userinfo [@user]", "Maklumat pengguna", "Default: diri sendiri"),
            ("serverinfo", "Maklumat server", "-"),
            ("warns [@user]", "Semak amaran pengguna", "Default: diri sendiri"),
            ("roll [sisi]", "Roll dadu", "Default: 6 sisi"),
            ("coinflip", "Flip syiling", "-"),
            ("8ball <soalan>", "Magic 8-ball", "-"),
            ("tictactoe @user", "Game Tic Tac Toe", "2 player"),
        ]
        
        for cmd, desc, note in public_commands:
            name = f"{self.prefix}{cmd}"
            value = f"> {desc}"
            if note != "-":
                value += f"\n> *{note}*"
            embed.add_field(name=name, value=value, inline=True)
        
        embed.set_author(
            name=f"{self.ctx.bot.user.name} Help System",
            icon_url=self.ctx.bot.user.avatar.url if self.ctx.bot.user.avatar else None
        )
        embed.set_footer(
            text=f"Diminta oleh {self.ctx.author.display_name} | Halaman 2/{self.total_pages}",
            icon_url=self.ctx.author.avatar.url if self.ctx.author.avatar else None
        )
        return embed
    
    def get_admin_page(self) -> discord.Embed:
        embed = discord.Embed(
            title="[ COMMANDS ADMIN ]",
            description="Commands yang memerlukan kebenaran pentadbir (admin/moderator).",
            color=0xef4444,  # Red for admin
            timestamp=datetime.now()
        )
        
        admin_commands = [
            ("clear <bil>", "Padam mesej", "Manage Messages"),
            ("kick @user [sebab]", "Keluarkan pengguna", "Kick Members"),
            ("ban @user [sebab]", "Haram pengguna", "Ban Members"),
            ("unban <ID>", "Buka haram pengguna", "Ban Members"),
            ("mute @user [minit] [sebab]", "Senyapkan pengguna", "Moderate Members"),
            ("unmute @user", "Buka senyap pengguna", "Moderate Members"),
            ("warn @user [sebab]", "Amar pengguna", "Moderate Members"),
            ("clearwarns @user", "Padam amaran", "Moderate Members"),
            ("slowmode [saat]", "Set slowmode channel", "Manage Channels"),
        ]
        
        for cmd, desc, perm in admin_commands:
            name = f"{self.prefix}{cmd}"
            value = f"> {desc}\n> `Kebenaran: {perm}`"
            embed.add_field(name=name, value=value, inline=True)
        
        embed.set_author(
            name=f"{self.ctx.bot.user.name} Help System",
            icon_url=self.ctx.bot.user.avatar.url if self.ctx.bot.user.avatar else None
        )
        embed.set_footer(
            text=f"Diminta oleh {self.ctx.author.display_name} | Halaman 3/{self.total_pages}",
            icon_url=self.ctx.author.avatar.url if self.ctx.author.avatar else None
        )
        return embed
    
    @discord.ui.button(label="<<", style=discord.ButtonStyle.secondary, custom_id="first")
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        await self.update_message(interaction)
    
    @discord.ui.button(label="<", style=discord.ButtonStyle.primary, custom_id="prev")
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        await self.update_message(interaction)
    
    @discord.ui.button(label="Halaman", style=discord.ButtonStyle.secondary, custom_id="page", disabled=True)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass
    
    @discord.ui.button(label=">", style=discord.ButtonStyle.primary, custom_id="next")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        await self.update_message(interaction)
    
    @discord.ui.button(label=">>", style=discord.ButtonStyle.secondary, custom_id="last")
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.total_pages - 1
        await self.update_message(interaction)
    
    async def update_message(self, interaction: discord.Interaction):
        # Update page indicator
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id == "page":
                item.label = f"Halaman {self.current_page + 1}/{self.total_pages}"
        
        embed = self.get_page_embed(self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)

# Help command - Premium book-style
@bot.command(name='help')
async def help_command(ctx):
    """Papar buku panduan dengan UI premium"""
    view = HelpView(ctx)
    embed = view.get_page_embed(0)
    
    # Update page indicator
    for item in view.children:
        if isinstance(item, discord.ui.Button) and item.custom_id == "page":
            item.label = f"Halaman 1/{view.total_pages}"
    
    await ctx.send(embed=embed, view=view)

# Info command - Bot information
@bot.command(name='info')
async def info(ctx):
    """Maklumat tentang bot"""
    embed = discord.Embed(
        title='🤖 Maklumat Bot',
        color=discord.Color.blue()
    )
    embed.add_field(name='Nama', value=bot.user.name, inline=True)
    embed.add_field(name='ID', value=bot.user.id, inline=True)
    embed.add_field(name='Prefix', value=PREFIX, inline=True)
    embed.add_field(name='Server', value=len(bot.guilds), inline=True)
    embed.add_field(name='Users', value=len(set(bot.get_all_members())), inline=True)
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    await ctx.send(embed=embed)

# Say command - Echo user message
@bot.command(name='say')
async def say(ctx, *, message=None):
    """Bot akan ulang kata-kata anda"""
    if message is None:
        await ctx.send('❌ Sila masukkan teks. Contoh: `!say Hello World`')
        return
    
    # Delete the command message
    await ctx.message.delete()
    # Send the message
    await ctx.send(message)

# Clear command - Delete messages (admin only)
@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 5):
    """Padam mesej (admin sahaja)"""
    if amount < 1 or amount > 100:
        await ctx.send('❌ Sila masukkan nombor antara 1-100.')
        return
    
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f'✅ {len(deleted) - 1} mesej telah dipadam.')
    await asyncio.sleep(3)
    await msg.delete()

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')

# Ban command - Ban user from server
@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    """Ban pengguna dari server"""
    if member == ctx.author:
        await ctx.send('❌ Anda tidak boleh ban diri sendiri!')
        return
    
    if member.top_role >= ctx.author.top_role:
        await ctx.send('❌ Anda tidak boleh ban pengguna dengan role yang lebih tinggi!')
        return
    
    reason = reason or "Tiada sebab diberikan"
    await member.ban(reason=reason)
    
    # Add to modlogs
    add_modlog(ctx.guild.id, 'BAN', member.id, member.name, ctx.author.id, ctx.author.name, reason)
    
    embed = discord.Embed(
        title='🔨 Pengguna Dibanned',
        description=f'{member.mention} telah dibanned daripada server',
        color=discord.Color.red()
    )
    embed.add_field(name='Sebab', value=reason, inline=False)
    embed.add_field(name='Dibanned oleh', value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Sila mention pengguna yang nak diban. Contoh: `!ban @user spam`')

# Unban command - Unban user from server
@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    """Unban pengguna daripada server"""
    banned_users = [entry async for entry in ctx.guild.bans()]
    
    for ban_entry in banned_users:
        user = ban_entry.user
        if user.id == user_id:
            await ctx.guild.unban(user)
            
            # Add to modlogs
            add_modlog(ctx.guild.id, 'UNBAN', user.id, user.name, ctx.author.id, ctx.author.name, 'Unbanned by admin')
            
            embed = discord.Embed(
                title='✅ Pengguna Diunban',
                description=f'{user.mention} telah diunban daripada server',
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            return
    
    await ctx.send('❌ Pengguna dengan ID tersebut tidak dijumpai dalam senarai ban.')

@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Sila masukkan ID pengguna. Contoh: `!unban 123456789`')

# Mute/Timeout command - Timeout user
@bot.command(name='mute')
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, duration: int = 10, *, reason=None):
    """
    Timeout/mute pengguna (dalam minit)
    Contoh: !mute @user 10 spamming
    """
    if member == ctx.author:
        await ctx.send('❌ Anda tidak boleh mute diri sendiri!')
        return
    
    if member.top_role >= ctx.author.top_role:
        await ctx.send('❌ Anda tidak boleh mute pengguna dengan role yang lebih tinggi!')
        return
    
    # Discord timeout maximum is 28 days (40320 minutes)
    if duration < 1 or duration > 40320:
        await ctx.send('❌ Durasi mestilah antara 1 minit hingga 28 hari (40320 minit).')
        return
    
    reason = reason or "Tiada sebab diberikan"
    
    await member.timeout(timedelta(minutes=duration), reason=reason)
    
    # Add to modlogs
    add_modlog(ctx.guild.id, 'MUTE', member.id, member.name, ctx.author.id, ctx.author.name, reason, f'{duration} minit')
    
    embed = discord.Embed(
        title='🔇 Pengguna Ditutup Suara',
        description=f'{member.mention} telah di-mute selama {duration} minit',
        color=discord.Color.orange()
    )
    embed.add_field(name='Sebab', value=reason, inline=False)
    embed.add_field(name='Dimute oleh', value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)

@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Sila mention pengguna. Contoh: `!mute @user 10 spamming`')

# Unmute command - Remove timeout from user
@bot.command(name='unmute')
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    """Buka mute/timeout pengguna"""
    if member.is_timed_out():
        await member.timeout(None)
        
        # Add to modlogs
        add_modlog(ctx.guild.id, 'UNMUTE', member.id, member.name, ctx.author.id, ctx.author.name, 'Timeout removed')
        
        embed = discord.Embed(
            title='🔊 Pengguna Dibuka Mutenya',
            description=f'{member.mention} telah dibuka mutenya',
            color=discord.Color.green()
        )
        embed.add_field(name='Dibuka oleh', value=ctx.author.mention, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f'❌ {member.mention} tidak sedang di-mute.')

@unmute.error
async def unmute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Sila mention pengguna. Contoh: `!unmute @user`')

# Kick command - Kick user from server
@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """Kick pengguna dari server"""
    if member == ctx.author:
        await ctx.send('❌ Anda tidak boleh kick diri sendiri!')
        return
    
    if member.top_role >= ctx.author.top_role:
        await ctx.send('❌ Anda tidak boleh kick pengguna dengan role yang lebih tinggi!')
        return
    
    reason = reason or "Tiada sebab diberikan"
    await member.kick(reason=reason)
    
    # Add to modlogs
    add_modlog(ctx.guild.id, 'KICK', member.id, member.name, ctx.author.id, ctx.author.name, reason)
    
    embed = discord.Embed(
        title='👢 Pengguna Dikick',
        description=f'{member.mention} telah dikick daripada server',
        color=discord.Color.orange()
    )
    embed.add_field(name='Sebab', value=reason, inline=False)
    embed.add_field(name='Dikick oleh', value=ctx.author.mention, inline=False)
    await ctx.send(embed=embed)

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Sila mention pengguna. Contoh: `!kick @user spamming`')

# Warn command - Warn a user
@bot.command(name='warn')
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason=None):
    """Berikan amaran kepada pengguna"""
    if member == ctx.author:
        await ctx.send('❌ Anda tidak boleh amar diri sendiri!')
        return
    
    if member.top_role >= ctx.author.top_role:
        await ctx.send('❌ Anda tidak boleh amar pengguna dengan role yang lebih tinggi!')
        return
    
    reason = reason or "Tiada sebab diberikan"
    
    # Add warning to storage
    warn_count = add_warning(ctx.guild.id, member.id, reason, ctx.author.id)
    
    # Add to modlogs
    add_modlog(ctx.guild.id, 'WARN', member.id, member.name, ctx.author.id, ctx.author.name, reason)
    
    embed = discord.Embed(
        title='⚠️ Amaran Diberikan',
        description=f'{member.mention} telah diberi amaran',
        color=discord.Color.yellow()
    )
    embed.add_field(name='Sebab', value=reason, inline=False)
    embed.add_field(name='Amaran ke', value=f'{warn_count}', inline=True)
    embed.add_field(name='Diberi oleh', value=ctx.author.mention, inline=True)
    
    # Auto-action if warnings reach threshold
    if warn_count >= 5:
        embed.add_field(name='⚠️ Notis', value='Pengguna ini telah mencapai 5 amaran!', inline=False)
    
    await ctx.send(embed=embed)
    
    # Try to DM the user
    try:
        user_embed = discord.Embed(
            title=f'⚠️ Anda telah diberi amaran di {ctx.guild.name}',
            description=f'Sebab: {reason}',
            color=discord.Color.yellow()
        )
        user_embed.add_field(name='Jumlah Amaran', value=f'{warn_count}', inline=False)
        await member.send(embed=user_embed)
    except:
        pass  # User might have DMs disabled

@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Sila mention pengguna. Contoh: `!warn @user spamming`')

# Warns command - List user warnings
@bot.command(name='warns')
async def warns(ctx, member: discord.Member = None):
    """Semak amaran pengguna (default: diri sendiri)"""
    member = member or ctx.author
    
    warnings = get_warnings(ctx.guild.id, member.id)
    
    if not warnings:
        await ctx.send(f'✅ {member.mention} tidak mempunyai sebarang amaran.')
        return
    
    embed = discord.Embed(
        title=f'⚠️ Senarai Amaran - {member.display_name}',
        description=f'Jumlah amaran: **{len(warnings)}**',
        color=discord.Color.yellow()
    )
    
    for i, warning in enumerate(warnings, 1):
        moderator = ctx.guild.get_member(warning['moderator_id'])
        mod_name = moderator.mention if moderator else 'Unknown'
        timestamp = datetime.fromisoformat(warning['timestamp']).strftime('%Y-%m-%d %H:%M')
        
        embed.add_field(
            name=f'Amaran #{i} - {timestamp}',
            value=f'Sebab: {warning["reason"]}\nOleh: {mod_name}',
            inline=False
        )
    
    await ctx.send(embed=embed)

# Clearwarns command - Clear user warnings
@bot.command(name='clearwarns')
@commands.has_permissions(moderate_members=True)
async def clearwarns(ctx, member: discord.Member):
    """Padam semua amaran pengguna"""
    if clear_user_warnings(ctx.guild.id, member.id):
        # Add to modlogs
        add_modlog(ctx.guild.id, 'CLEARWARNS', member.id, member.name, ctx.author.id, ctx.author.name, 'All warnings cleared')
        
        embed = discord.Embed(
            title='✅ Amaran Dipadam',
            description=f'Semua amaran untuk {member.mention} telah dipadam',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(f'❌ {member.mention} tidak mempunyai sebarang amaran untuk dipadam.')

@clearwarns.error
async def clearwarns_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Sila mention pengguna. Contoh: `!clearwarns @user`')

# Userinfo command - Show user information
@bot.command(name='userinfo')
async def userinfo(ctx, member: discord.Member = None):
    """Papar maklumat pengguna"""
    member = member or ctx.author
    
    # Get warning count
    warnings = get_warnings(ctx.guild.id, member.id)
    
    embed = discord.Embed(
        title=f'👤 Maklumat Pengguna - {member.display_name}',
        color=member.color
    )
    
    embed.add_field(name='Nama Penuh', value=member.name, inline=True)
    embed.add_field(name='ID', value=member.id, inline=True)
    embed.add_field(name='Status', value=str(member.status).title(), inline=True)
    embed.add_field(name='Role Tertinggi', value=member.top_role.mention, inline=True)
    embed.add_field(name='Sertai Server', value=member.joined_at.strftime('%Y-%m-%d'), inline=True)
    embed.add_field(name='Akaun Dibuat', value=member.created_at.strftime('%Y-%m-%d'), inline=True)
    embed.add_field(name='Amaran', value=f'{len(warnings)} amaran', inline=True)
    
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    
    await ctx.send(embed=embed)

# Serverinfo command - Show server information
@bot.command(name='serverinfo')
async def serverinfo(ctx):
    """Papar maklumat server"""
    guild = ctx.guild
    
    embed = discord.Embed(
        title=f'🏠 Maklumat Server - {guild.name}',
        color=discord.Color.blue()
    )
    
    embed.add_field(name='ID', value=guild.id, inline=True)
    embed.add_field(name='Pemilik', value=guild.owner.mention, inline=True)
    embed.add_field(name='Dibuat Pada', value=guild.created_at.strftime('%Y-%m-%d'), inline=True)
    embed.add_field(name='Jumlah Ahli', value=guild.member_count, inline=True)
    embed.add_field(name='Jumlah Channel', value=len(guild.channels), inline=True)
    embed.add_field(name='Jumlah Role', value=len(guild.roles), inline=True)
    embed.add_field(name='Jumlah Emoji', value=len(guild.emojis), inline=True)
    embed.add_field(name='Level Verification', value=guild.verification_level, inline=True)
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    await ctx.send(embed=embed)

# Slowmode command - Set channel slowmode
@bot.command(name='slowmode')
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, seconds: int = 0):
    """
    Set slow mode untuk channel (dalam saat)
    0 = disable, max 21600 (6 jam)
    """
    if seconds < 0 or seconds > 21600:
        await ctx.send('❌ Durasi mestilah antara 0 hingga 21600 saat (6 jam).')
        return
    
    await ctx.channel.edit(slowmode_delay=seconds)
    
    if seconds == 0:
        await ctx.send('✅ Slow mode telah **dinyahaktifkan**.')
    else:
        await ctx.send(f'✅ Slow mode telah disetkan ke **{seconds} saat**.')

@slowmode.error
async def slowmode_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')
    elif isinstance(error, commands.BadArgument):
        await ctx.send('❌ Sila masukkan nombor. Contoh: `!slowmode 5`')

# ───────────────────────────────────────────────
# MINIGAMES
# ───────────────────────────────────────────────

# Roll command - Roll dice
@bot.command(name='roll')
async def roll(ctx, sides: int = 6):
    """Roll dadu (default: 6 sisi)"""
    if sides < 2 or sides > 100:
        await ctx.send('❌ Bilangan sisi mestilah antara 2 hingga 100.')
        return
    
    result = random.randint(1, sides)
    
    embed = discord.Embed(
        title='[ ROLL DADU ]',
        description=f'🎲 Anda roll **{result}**! (1-{sides})',
        color=0x6366f1
    )
    embed.set_footer(text=f'Diminta oleh {ctx.author.display_name}')
    await ctx.send(embed=embed)

@roll.error
async def roll_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send('❌ Sila masukkan nombor. Contoh: `!roll 20`')

# Coinflip command - Flip a coin
@bot.command(name='coinflip')
async def coinflip(ctx):
    """Flip syiling (Heads atau Tails)"""
    result = random.choice(['Heads', 'Tails'])
    emoji = '👑' if result == 'Heads' else '🪙'
    
    embed = discord.Embed(
        title='[ FLIP SYILING ]',
        description=f'{emoji} Keputusan: **{result}**!',
        color=0xf59e0b
    )
    embed.set_footer(text=f'Diminta oleh {ctx.author.display_name}')
    await ctx.send(embed=embed)

# 8ball command - Magic 8-ball
@bot.command(name='8ball')
async def eight_ball(ctx, *, question=None):
    """Tanya soalan, dapat jawapan rawak"""
    if not question:
        await ctx.send('❌ Sila tanya soalan. Contoh: `!8ball Adakah saya hebat?`')
        return
    
    responses = [
        '✅ Ya, pasti!',
        '✅ Tanpa syak!',
        '✅ Sangat mungkin.',
        '✅ Ya.',
        '🔮 Nampaknya begitu.',
        '🤔 Cuba tanya lagi.',
        '⏳ Lebih baik jangan beritahu sekarang.',
        '😶 Tidak dapat jangka sekarang.',
        '❌ Jangan bergantung padanya.',
        '❌ Tidak.',
        '❌ Sangat meragukan.',
        '❌ Tidak akan berlaku.',
    ]
    
    result = random.choice(responses)
    
    embed = discord.Embed(
        title='[ MAGIC 8-BALL ]',
        color=0x8b5cf6
    )
    embed.add_field(name='Soalan', value=f'```{question}```', inline=False)
    embed.add_field(name='Jawapan', value=f'**{result}**', inline=False)
    embed.set_footer(text=f'Diminta oleh {ctx.author.display_name}')
    await ctx.send(embed=embed)

# ───────────────────────────────────────────────
# TIC TAC TOE GAME (2 PLAYER)
# ───────────────────────────────────────────────

# Store active games
active_ttt_games = {}  # {channel_id: TicTacToeGame}

class TicTacToeGame:
    def __init__(self, player1, player2, channel_id):
        self.player1 = player1  # X
        self.player2 = player2  # O
        self.channel_id = channel_id
        self.board = [' ' for _ in range(9)]  # 3x3 grid
        self.current_player = player1
        self.current_symbol = 'X'
        self.moves_count = 0
        self.game_over = False
        self.winner = None
    
    def make_move(self, position):
        if self.board[position] == ' ' and not self.game_over:
            self.board[position] = self.current_symbol
            self.moves_count += 1
            
            # Check win
            if self.check_win(self.current_symbol):
                self.game_over = True
                self.winner = self.current_player
                return True
            
            # Check draw
            if self.moves_count == 9:
                self.game_over = True
                return True
            
            # Switch turn
            self.current_player = self.player2 if self.current_player == self.player1 else self.player1
            self.current_symbol = 'O' if self.current_symbol == 'X' else 'X'
            return True
        return False
    
    def check_win(self, symbol):
        win_conditions = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]              # Diagonals
        ]
        for condition in win_conditions:
            if all(self.board[i] == symbol for i in condition):
                return True
        return False
    
    def get_board_display(self):
        b = self.board
        return f"""
```
 {b[0]} │ {b[1]} │ {b[2]} 
───┼───┼───
 {b[3]} │ {b[4]} │ {b[5]} 
───┼───┼───
 {b[6]} │ {b[7]} │ {b[8]} 
```
"""
    
    def get_status(self):
        if self.game_over:
            if self.winner:
                return f"🏆 **{self.winner.display_name}** Menang!"
            else:
                return "🤝 Seri!"
        return f"🎮 Giliran: **{self.current_player.display_name}** ({self.current_symbol})"

class TicTacToeView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=300)  # 5 minute timeout
        self.game = game
        self.update_buttons()
    
    def update_buttons(self):
        self.clear_items()
        symbols = {'X': '❌', 'O': '⭕', ' ': '⬜'}
        
        for i in range(9):
            btn = discord.ui.Button(
                label=symbols[self.game.board[i]],
                style=discord.ButtonStyle.secondary if self.game.board[i] == ' ' else 
                      (discord.ButtonStyle.danger if self.game.board[i] == 'X' else discord.ButtonStyle.success),
                row=i // 3,
                custom_id=f"ttt_{i}"
            )
            btn.disabled = self.game.board[i] != ' ' or self.game.game_over
            btn.callback = self.make_callback(i)
            self.add_item(btn)
    
    def make_callback(self, position):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.game.current_player.id:
                await interaction.response.send_message(
                    "❌ Bukan giliran anda!", ephemeral=True
                )
                return
            
            if self.game.make_move(position):
                self.update_buttons()
                
                embed = discord.Embed(
                    title='🎮 Tic Tac Toe',
                    description=self.game.get_board_display(),
                    color=0x6366f1
                )
                embed.add_field(name='Status', value=self.game.get_status(), inline=False)
                embed.add_field(
                    name='Pemain',
                    value=f"❌ {self.game.player1.mention} vs ⭕ {self.game.player2.mention}",
                    inline=False
                )
                
                if self.game.game_over:
                    if self.game.winner:
                        embed.color = discord.Color.green()
                    else:
                        embed.color = discord.Color.greyple()
                    
                    # Remove from active games
                    if self.game.channel_id in active_ttt_games:
                        del active_ttt_games[self.game.channel_id]
                    
                    # Disable all buttons
                    for child in self.children:
                        child.disabled = True
                
                await interaction.response.edit_message(embed=embed, view=self)
        return callback

# TicTacToe command - Start a new game
@bot.command(name='tictactoe')
async def tictactoe(ctx, opponent: discord.Member = None):
    """Mula game Tic Tac Toe dengan player lain"""
    if opponent is None:
        await ctx.send('❌ Sila mention lawan. Contoh: `!tictactoe @user`')
        return
    
    if opponent.id == ctx.author.id:
        await ctx.send('❌ Anda tidak boleh lawan diri sendiri!')
        return
    
    if opponent.bot:
        await ctx.send('❌ Anda tidak boleh lawan bot!')
        return
    
    # Check if game already exists in this channel
    if ctx.channel.id in active_ttt_games:
        await ctx.send('❌ Sudah ada game Tic Tac Toe berjalan di channel ini!')
        return
    
    # Create new game
    game = TicTacToeGame(ctx.author, opponent, ctx.channel.id)
    active_ttt_games[ctx.channel.id] = game
    
    embed = discord.Embed(
        title='🎮 Tic Tac Toe',
        description=game.get_board_display(),
        color=0x6366f1
    )
    embed.add_field(name='Status', value=game.get_status(), inline=False)
    embed.add_field(
        name='Pemain',
        value=f"❌ {ctx.author.mention} vs ⭕ {opponent.mention}",
        inline=False
    )
    embed.add_field(
        name='Cara Main',
        value='Tekan butang untuk letak simbol anda (X atau O).\n3 dalam baris = Menang!',
        inline=False
    )
    
    view = TicTacToeView(game)
    await ctx.send(embed=embed, view=view)

@tictactoe.error
async def tictactoe_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Sila mention lawan. Contoh: `!tictactoe @user`')

# ───────────────────────────────────────────────
# TIKTOK LIVE NOTIFICATIONS
# ───────────────────────────────────────────────

# Configuration
TIKTOK_CHANNEL_ID = 1490618780911538267  # Channel for live notifications
tiktok_username = None  # Will be set via command
tiktok_live_status = False  # Track if currently live
tiktok_check_task = None  # Background task

# TikTok Live Embed Design - Returns both embed and image URL for top placement
def create_tiktok_live_embed(username, stream_title=None, viewers=None, duration=None, profile_pic=None, thumbnail=None):
    """Create premium embed for TikTok live announcement - returns embed and image URL"""
    
    # Determine the image URL to show at top
    image_url = thumbnail if thumbnail else 'https://p16-sign-va.tiktokcdn.com/obj/tiktok-obj/tiktok_live_placeholder.png'
    
    embed = discord.Embed(
        title='[  LIVE NOW - TikTok  ]',
        description=f'**@{username}** sedang live di TikTok!\n\n'
                   f'Jom tonton dan support live stream! 🎥✨',
        color=0xFE2C55,  # TikTok red/pink color
        timestamp=datetime.now()
    )
    
    # Stream title in code block
    if stream_title:
        embed.add_field(name='📱 Tajuk', value=f'```{stream_title}```', inline=False)
    
    # Viewers and duration side by side
    if viewers:
        embed.add_field(name='👥 Penonton', value=f'**{viewers}**', inline=True)
    if duration:
        embed.add_field(name='⏱ Masa', value=f'**{duration} minit**', inline=True)
    
    # Watch link
    embed.add_field(
        name='🔗 Tonton Live',
        value=f'[https://www.tiktok.com/@{username}/live](https://www.tiktok.com/@{username}/live)',
        inline=False
    )
    
    # Set author with profile info
    embed.set_author(
        name=f'{username} - Sedang Live!',
        icon_url=profile_pic if profile_pic else 'https://p16-sign-va.tiktokcdn.com/obj/tiktok-obj/tiktok_logo.png'
    )
    
    # Footer with ByteWolf branding
    embed.set_footer(
        text='Dijana oleh ByteWolf LiveBot',
        icon_url='https://cdn.discordapp.com/embed/avatars/0.png'
    )
    
    return embed, image_url

# Command to set TikTok username
@bot.command(name='settiktok')
@commands.has_permissions(administrator=True)
async def set_tiktok(ctx, username: str):
    """Set TikTok username untuk live notification"""
    global tiktok_username, tiktok_check_task
    
    # Remove @ if included
    tiktok_username = username.lstrip('@')
    
    # Start background checker if not already running
    if tiktok_check_task is None or tiktok_check_task.done():
        tiktok_check_task = bot.loop.create_task(tiktok_live_checker())
    
    embed = discord.Embed(
        title='✅ TikTok Username Diset',
        description=f'Username: **@{tiktok_username}**\n\n'
                   f'Bot akan check setiap **5 minit** dan hantar notifikasi '
                   f'ke channel <#{TIKTOK_CHANNEL_ID}> apabila anda live.',
        color=0xFE2C55
    )
    await ctx.send(embed=embed)

@set_tiktok.error
async def set_tiktok_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda perlu kebenaran Administrator untuk set TikTok username!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Sila masukkan username TikTok. Contoh: `!settiktok dikowolf_official`')

# Command to test TikTok embed (manual trigger)
@bot.command(name='testtiktok')
@commands.has_permissions(administrator=True)
async def test_tiktok(ctx, username: str = None):
    """Test TikTok live embed (manual)"""
    global tiktok_username
    
    test_user = username or tiktok_username or 'dikowolf_official'
    
    embed, image_url = create_tiktok_live_embed(
        username=test_user,
        stream_title='Test Stream - Live Gaming & Chat',
        viewers='1.2K',
        duration='15'
    )
    
    # Send image URL first (will unfurl at top), then embed
    await ctx.send(content=f'{image_url}', embed=embed)

# Background task to check TikTok live status
async def tiktok_live_checker():
    """Check TikTok live status every 5 minutes"""
    global tiktok_username, tiktok_live_status
    
    await bot.wait_until_ready()
    
    while not bot.is_closed():
        if tiktok_username:
            try:
                # Check if live (simulation - replace with actual API call)
                is_live = await check_tiktok_live_status(tiktok_username)
                
                # If just went live
                if is_live and not tiktok_live_status:
                    tiktok_live_status = True
                    
                    # Get notification channel
                    channel = bot.get_channel(TIKTOK_CHANNEL_ID)
                    if channel:
                        embed, image_url = create_tiktok_live_embed(tiktok_username)
                        # Send image URL first (unfurls at top), then embed
                        await channel.send(content=f'{image_url}', embed=embed)
                        print(f'[TIKTOK] Live notification sent for @{tiktok_username}')
                
                # If stream ended
                elif not is_live and tiktok_live_status:
                    tiktok_live_status = False
                    print(f'[TIKTOK] Stream ended for @{tiktok_username}')
                    
            except Exception as e:
                print(f'[TIKTOK ERROR] {e}')
        
        # Check every 5 minutes
        await asyncio.sleep(300)

async def check_tiktok_live_status(username):
    """Check if TikTok user is live (placeholder - needs actual implementation)"""
    # TODO: Implement actual TikTok live checking
    # Options: Web scraping, third-party API, or manual trigger
    # For now, return False (not live)
    return False

# ───────────────────────────────────────────────
# AUTO-MODERATION ADMIN COMMANDS
# ───────────────────────────────────────────────

# Check violations command
@bot.command(name='violations')
@commands.has_permissions(moderate_members=True)
async def violations(ctx, member: discord.Member = None):
    """Check auto-moderation violations for a user"""
    member = member or ctx.author
    
    if member.id not in user_violations:
        await ctx.send(f'✅ {member.mention} tidak mempunyai sebarang pelanggaran.')
        return
    
    v = user_violations[member.id]
    embed = discord.Embed(
        title=f'⚠️ Pelanggaran - {member.display_name}',
        color=0xf59e0b
    )
    embed.add_field(name='Spam', value=f'{v.get("spam", 0)}/3', inline=True)
    embed.add_field(name='Kata Kesat', value=f'{v.get("profanity", 0)}/3', inline=True)
    embed.set_footer(text='Mencapai 3 = Timeout automatik 10 minit')
    await ctx.send(embed=embed)

@violations.error
async def violations_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')

# Clear violations command
@bot.command(name='clearviolations')
@commands.has_permissions(moderate_members=True)
async def clear_violations(ctx, member: discord.Member):
    """Clear all auto-moderation violations for a user"""
    if member.id in user_violations:
        del user_violations[member.id]
        await ctx.send(f'✅ Pelanggaran untuk {member.mention} telah dipadam.')
    else:
        await ctx.send(f'❌ {member.mention} tidak mempunyai pelanggaran.')

@clear_violations.error
async def clear_violations_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('❌ Sila mention pengguna. Contoh: `!clearviolations @user`')

# Test auto-mod command
@bot.command(name='testspam')
@commands.has_permissions(administrator=True)
async def test_spam(ctx):
    """Test spam detection (admin only)"""
    embed = discord.Embed(
        title='🧪 Ujian Spam Detection',
        description='Hantar 5 mesej dalam 5 saat untuk trigger peringatan.',
        color=0x6366f1
    )
    await ctx.send(embed=embed)

# Test join embed command
@bot.command(name='testjoin')
@commands.has_permissions(administrator=True)
async def test_join(ctx, member: discord.Member = None):
    """Test welcome join embed (admin only)"""
    member = member or ctx.author
    
    WELCOME_CHANNEL_ID = 1490320988766867548
    print(f'[TESTJOIN] Looking for channel: {WELCOME_CHANNEL_ID}')
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    
    if not channel:
        print(f'[TESTJOIN ERROR] Channel not found!')
        await ctx.send('❌ Channel welcome tidak dijumpai!')
        return
    
    print(f'[TESTJOIN] Channel found: {channel.name}')
    
    embed = discord.Embed(
        title='ByteWolf Studio',
        description=f'{member.mention} **Selamat datang ke ByteWolf Studio!** 🎉\n\n'
                   f'Kami sangat gembira **Awak** ada di sini! Semoga seronok dan jangan segan-segan untuk tanya apa-apa. 😊',
        color=0x10b981,
        timestamp=datetime.now()
    )
    
    # Calculate account age
    try:
        account_age = (datetime.now() - member.created_at).days
        created_str = f'```{member.created_at.strftime("%d/%m/%Y")}\n({account_age} hari)```'
    except:
        created_str = '```Unknown```'
    
    # Safe values
    member_name = member.name if member.name else 'Unknown'
    member_id = str(member.id) if member.id else 'Unknown'
    member_count = str(ctx.guild.member_count) if ctx.guild.member_count else 'Unknown'
    join_date = f'```{datetime.now().strftime("%d/%m/%Y")}\n(Today)```'
    
    # List format (single column)
    embed.add_field(name='Nama:', value=f'```{member_name}```', inline=False)
    embed.add_field(name='ID:', value=f'```{member_id}```', inline=False)
    embed.add_field(name='Ahli:', value=f'```{member_count}```', inline=False)
    embed.add_field(name='Join Server:', value=join_date, inline=False)
    embed.add_field(name='Akaun Dibuat:', value=created_str, inline=False)
    embed.add_field(name='Invite By:', value='```Unknown```', inline=False)
    
    # Safe thumbnail
    try:
        if member.avatar and member.avatar.url:
            embed.set_thumbnail(url=member.avatar.url)
    except:
        pass
    
    # Safe footer
    try:
        guild_name = ctx.guild.name if ctx.guild.name else 'Server'
        if ctx.guild.icon and ctx.guild.icon.url:
            embed.set_footer(text=f'Server: {guild_name}', icon_url=ctx.guild.icon.url)
        else:
            embed.set_footer(text=f'Server: {guild_name}')
    except:
        embed.set_footer(text='ByteWolf Studio')
    
    try:
        await channel.send(embed=embed)
        await ctx.send(f'✅ Embed join telah dihantar ke <#{WELCOME_CHANNEL_ID}>')
        print(f'[TESTJOIN] Embed sent successfully to {channel.name}')
    except Exception as e:
        await ctx.send(f'❌ Error: {e}')
        print(f'[TESTJOIN ERROR] {e}')

@test_join.error
async def test_join_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')

# Test leave embed command
@bot.command(name='testleave')
@commands.has_permissions(administrator=True)
async def test_leave(ctx, member: discord.Member = None):
    """Test leave embed (admin only)"""
    member = member or ctx.author
    
    WELCOME_CHANNEL_ID = 1490320988766867548
    print(f'[TESTLEAVE] Looking for channel: {WELCOME_CHANNEL_ID}')
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    
    if not channel:
        print(f'[TESTLEAVE ERROR] Channel not found!')
        await ctx.send('❌ Channel welcome tidak dijumpai!')
        return
    
    print(f'[TESTLEAVE] Channel found: {channel.name}')
    
    embed = discord.Embed(
        title='ByteWolf Studio',
        description=f'{member.mention} **Terima kasih kerana bersama kami di ByteWolf Studio!**\n\n'
                   f'Semoga berjumpa lagi di lain waktu. Jaga diri dan datanglah lagi bila-bila masa! 😊',
        color=0xef4444,
        timestamp=datetime.now()
    )
    
    # Calculate account age for leave embed too
    try:
        account_age = (datetime.now() - member.created_at).days
        account_created = f'```{member.created_at.strftime("%d/%m/%Y")}\n({account_age} hari)```'
    except:
        account_created = '```Unknown```'
    
    # Calculate days stayed
    try:
        if member.joined_at:
            days_stayed = (datetime.now() - member.joined_at).days
            join_date = member.joined_at.strftime('%d/%m/%Y')
        else:
            days_stayed = 'Unknown'
            join_date = 'Unknown'
    except:
        days_stayed = 'Unknown'
        join_date = 'Unknown'
    
    leave_date = datetime.now().strftime('%d/%m/%Y')
    
    # Safe values
    member_name = member.name if member.name else 'Unknown'
    member_id = str(member.id) if member.id else 'Unknown'
    member_count = str(ctx.guild.member_count) if ctx.guild.member_count else 'Unknown'
    
    # List format (single column)
    embed.add_field(name='Nama:', value=f'```{member_name}```', inline=False)
    embed.add_field(name='ID:', value=f'```{member_id}```', inline=False)
    embed.add_field(name='Ahli:', value=f'```{member_count}```', inline=False)
    embed.add_field(name='Akaun Dibuat:', value=account_created, inline=False)
    embed.add_field(name='Ahli Sejak:', value=f'```{join_date}```', inline=False)
    embed.add_field(name='Keluar Server:', value=f'```{leave_date}```', inline=False)
    embed.add_field(name='Total Stay:', value=f'```{days_stayed} hari```', inline=False)
    
    # Safe thumbnail
    try:
        if member.avatar and member.avatar.url:
            embed.set_thumbnail(url=member.avatar.url)
    except:
        pass
    
    # Safe footer
    try:
        guild_name = ctx.guild.name if ctx.guild.name else 'Server'
        if ctx.guild.icon and ctx.guild.icon.url:
            embed.set_footer(text=f'Server: {guild_name}', icon_url=ctx.guild.icon.url)
        else:
            embed.set_footer(text=f'Server: {guild_name}')
    except:
        embed.set_footer(text='ByteWolf Studio')
    
    try:
        await channel.send(embed=embed)
        await ctx.send(f'✅ Embed leave telah dihantar ke <#{WELCOME_CHANNEL_ID}>')
        print(f'[TESTLEAVE] Embed sent successfully to {channel.name}')
    except Exception as e:
        await ctx.send(f'❌ Error: {e}')
        print(f'[TESTLEAVE ERROR] {e}')

@test_leave.error
async def test_leave_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')

# Restart bot command
@bot.command(name='restart')
@commands.has_permissions(administrator=True)
async def restart_bot(ctx):
    """Restart the bot (admin only)"""
    embed = discord.Embed(
        title='🔄 Restarting Bot',
        description='Bot sedang di-restart...\nSila tunggu sebentar.',
        color=0xf59e0b,
        timestamp=datetime.now()
    )
    embed.set_footer(text=f'Dilakukan oleh: {ctx.author.name}')
    await ctx.send(embed=embed)
    
    print(f'[RESTART] Bot di-restart oleh {ctx.author.name}')
    
    # Restart the bot process
    await bot.close()
    os.execl(sys.executable, sys.executable, *sys.argv)

@restart_bot.error
async def restart_bot_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')

# ───────────────────────────────────────────────
# MODERATION LOGS VIEWER
# ───────────────────────────────────────────────

# Premium Logs View with Pagination
class LogsView(discord.ui.View):
    def __init__(self, ctx, logs, user_filter=None):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.logs = logs
        self.user_filter = user_filter
        self.current_page = 0
        self.per_page = 5
        self.total_pages = max(1, (len(logs) + self.per_page - 1) // self.per_page)
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "[Hanya pemohon boleh guna button ini]", ephemeral=True
            )
            return False
        return True
    
    def get_page_embed(self, page_num: int) -> discord.Embed:
        start_idx = page_num * self.per_page
        end_idx = start_idx + self.per_page
        page_logs = self.logs[start_idx:end_idx]
        
        if self.user_filter:
            title = f"[ LOGS MODERASI - {self.user_filter.display_name} ]"
            desc = f"Semua tindakan moderator terhadap {self.user_filter.mention}"
        else:
            title = "[ BUKU LOGS MODERASI ]"
            desc = "Rekod semua tindakan moderator dalam server"
        
        embed = discord.Embed(
            title=title,
            description=desc,
            color=0x6366f1,
            timestamp=datetime.now()
        )
        
        if not page_logs:
            embed.add_field(
                name="📭 Tiada Logs",
                value="Tiada rekod tindakan moderator lagi.",
                inline=False
            )
        else:
            for log in page_logs:
                action_emoji = {
                    'BAN': '🔨', 'UNBAN': '🔓', 'KICK': '👢',
                    'MUTE': '🔇', 'UNMUTE': '🔊', 'WARN': '⚠️',
                    'CLEARWARNS': '🗑️'
                }.get(log['action'], '📋')
                
                timestamp = datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M')
                
                value = f"```asciidoc\n"
                value += f"User    :: {log['target_name']}\n"
                value += f"Action  :: {log['action']}\n"
                value += f"Reason  :: {log['reason'][:50]}{'...' if len(log['reason']) > 50 else ''}\n"
                if log.get('duration'):
                    value += f"Masa    :: {log['duration']}\n"
                value += f"Oleh    :: {log['moderator_name']}\n"
                value += f"```"
                
                embed.add_field(
                    name=f"{action_emoji} #{log['id']} - {timestamp}",
                    value=value,
                    inline=False
                )
        
        embed.set_footer(
            text=f"Halaman {page_num + 1}/{self.total_pages} | Total: {len(self.logs)} logs",
            icon_url=self.ctx.author.avatar.url if self.ctx.author.avatar else None
        )
        return embed
    
    @discord.ui.button(label="<<", style=discord.ButtonStyle.secondary, custom_id="logs_first")
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        await self.update_message(interaction)
    
    @discord.ui.button(label="<", style=discord.ButtonStyle.primary, custom_id="logs_prev")
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        await self.update_message(interaction)
    
    @discord.ui.button(label="Halaman", style=discord.ButtonStyle.secondary, custom_id="logs_page", disabled=True)
    async def page_indicator(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass
    
    @discord.ui.button(label=">", style=discord.ButtonStyle.primary, custom_id="logs_next")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(self.total_pages - 1, self.current_page + 1)
        await self.update_message(interaction)
    
    @discord.ui.button(label=">>", style=discord.ButtonStyle.secondary, custom_id="logs_last")
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.total_pages - 1
        await self.update_message(interaction)
    
    async def update_message(self, interaction: discord.Interaction):
        for item in self.children:
            if isinstance(item, discord.ui.Button) and item.custom_id == "logs_page":
                item.label = f"Halaman {self.current_page + 1}/{self.total_pages}"
        
        embed = self.get_page_embed(self.current_page)
        await interaction.response.edit_message(embed=embed, view=self)

# Logs command - View all moderation logs
@bot.command(name='logs')
@commands.has_permissions(moderate_members=True)
async def view_logs(ctx, member: discord.Member = None):
    """View moderation logs (book-style) - filter by user optional"""
    logs = get_modlogs(ctx.guild.id, member.id if member else None, limit=50)
    
    if not logs and member:
        await ctx.send(f'✅ Tiada logs untuk {member.mention}.')
        return
    elif not logs:
        await ctx.send('✅ Tiada logs moderator lagi.')
        return
    
    view = LogsView(ctx, logs, member)
    embed = view.get_page_embed(0)
    
    for item in view.children:
        if isinstance(item, discord.ui.Button) and item.custom_id == "logs_page":
            item.label = f"Halaman 1/{view.total_pages}"
    
    await ctx.send(embed=embed, view=view)

@view_logs.error
async def view_logs_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')

# Userlogs command - Quick user mod summary
@bot.command(name='userlogs')
@commands.has_permissions(moderate_members=True)
async def user_logs(ctx, member: discord.Member = None):
    """Quick summary of user's moderation history"""
    member = member or ctx.author
    
    counts, total = get_user_modlog_count(ctx.guild.id, member.id)
    logs = get_modlogs(ctx.guild.id, member.id, limit=5)
    
    embed = discord.Embed(
        title=f'📋 Sejarah Moderasi - {member.display_name}',
        description=f'Total tindakan: **{total}**',
        color=0x6366f1,
        timestamp=datetime.now()
    )
    
    # Action counts
    if counts:
        stats = " | ".join([f"{action}: {count}" for action, count in counts.items()])
        embed.add_field(name='📊 Statistik', value=f'`{stats}`', inline=False)
    else:
        embed.add_field(name='📊 Statistik', value='`Tiada rekod`', inline=False)
    
    # Recent logs
    if logs:
        recent = ""
        for log in logs[:3]:
            date = datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d')
            recent += f"• {log['action']} - {date}\n"
        embed.add_field(name='📅 Terkini', value=f'```\n{recent}```', inline=False)
    
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    embed.set_footer(text=f'ID: {member.id}')
    await ctx.send(embed=embed)

@user_logs.error
async def user_logs_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('❌ Anda tidak mempunyai kebenaran untuk menggunakan perintah ini!')

# ───────────────────────────────────────────────
# RUN THE BOT
# ───────────────────────────────────────────────
if __name__ == '__main__':
    if not TOKEN:
        print('[ERROR] Token Discord tidak dijumpai!')
        print('Sila pastikan anda telah menetapkan DISCORD_TOKEN dalam fail .env')
        exit(1)
    
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print('[ERROR] Token tidak sah!')
    except Exception as e:
        print(f'[ERROR] {e}')
