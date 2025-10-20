import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import Select, View, Button
import json
import asyncio
from datetime import datetime, timedelta
import pytz
import random
import time
import uuid
from collections import defaultdict
from aiohttp import web
import threading
import os

# Read bot tokens from separate files
try:
    with open('bot_token.txt', 'r', encoding='utf-8') as f:
        BOT_TOKEN = f.read().strip()
except:
    BOT_TOKEN = ""

try:
    with open('checker_token.txt', 'r', encoding='utf-8') as f:
        CHECKER_TOKEN = f.read().strip()
except:
    CHECKER_TOKEN = ""

# Load or create config from panel database
def load_config():
    try:
        with open('panel_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        # Default config
        return {
            'clan_name': 'JyX',
            'admin_users': [],
            'channels': {},
            'roles': {},
            'ticket_options': [
                ['Team Tester Apply', 'Apply to be a team tester', '👤'],
                ['JyX Team', 'Apply for JyX Team', '✨'],
                ['Support', 'Get technical support', '🌐']
            ],
            'settings': {
                'claims_for_rankup': 2000
            },
            'qol_features': {
                'auto_thread_channels': [],
                'smart_slowmode_channels': [],
                'smart_slowmode_threshold': 12,
                'smart_slowmode_timeframe': 8,
                'smart_slowmode_duration': 60
            }
        }

def save_config(cfg):
    with open('panel_config.json', 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

config = load_config()
CLAN_NAME = config.get('clan_name', 'JyX')

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=['/', '='], intents=intents)
tree = bot.tree



checker_intents = discord.Intents.default()
checker_intents.guilds = True
checker_intents.members = True
checker_bot = commands.Bot(command_prefix='!checker_', intents=checker_intents)

@checker_bot.event
async def on_ready():
    print(f'✅ Checker Bot is online: {checker_bot.user}')
    print(f'📊 Checker Bot is in {len(checker_bot.guilds)} servers')
    for guild in checker_bot.guilds:
        print(f'   - {guild.name} (ID: {guild.id})')


EMBED_COLOR = 0xd4b2f6
IRAN_TZ = pytz.timezone('Asia/Tehran')

partners = []
giveaways = {}
points_data = {}
user_nicknames = {}
claimed_tickets = {}
decline_counts = defaultdict(int)
accept_counts = defaultdict(int)
cooldowns = {}
closed_channels = set()
ticket_creators = {}
claim_counts = defaultdict(int)
user_permissions = defaultdict(set)
pending_prizes = {}
scripts_data = {}
ticket_abuse = defaultdict(lambda: {'count': 0, 'last_reset': time.time(), 'timeout_until': 0, 'timeout_level': 0})

channel_message_history = defaultdict(list)
thread_creation_cooldowns = {}
active_slowmodes = {} 

ADMIN_USERS = [1143130719426719855, 483361985170505739, 825049695532482640, 1020597337153875980]

try:
    with open('partners.json', 'r', encoding='utf-8') as f:
        partners = json.load(f)
except:
    partners = []

try:
    with open('giveaways.json', 'r', encoding='utf-8') as f:
        giveaways = json.load(f)
except:
    giveaways = {}

try:
    with open('points.json', 'r', encoding='utf-8') as f:
        points_data = json.load(f)
except:
    points_data = {}

try:
    with open('nicknames.json', 'r', encoding='utf-8') as f:
        user_nicknames = json.load(f)
except:
    user_nicknames = {}

try:
    with open('tickets.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        claimed_tickets.update({int(k): int(v) for k, v in data.get('claimed', {}).items()})
        decline_counts.update(defaultdict(int, {int(k): int(v) for k, v in data.get('declines', {}).items()}))
        accept_counts.update(defaultdict(int, {int(k): int(v) for k, v in data.get('accepts', {}).items()}))
        cooldowns.update({int(k): float(v) for k, v in data.get('cooldowns', {}).items()})
        ticket_creators.update({int(k): int(v) for k, v in data.get('creators', {}).items()})
        claim_counts.update(defaultdict(int, {int(k): int(v) for k, v in data.get('claim_counts', {}).items()}))
        user_permissions.update(defaultdict(set, {int(k): set(v) for k, v in data.get('permissions', {}).items()}))
except:
    pass

warnings_data = {}
try:
    with open('warnings.json', 'r', encoding='utf-8') as f:
        warnings_data = json.load(f)

        warnings_data = {int(k): v for k, v in warnings_data.items()}
except:
    warnings_data = {}

try:
    with open('scripts.json', 'r', encoding='utf-8') as f:
        scripts_data = json.load(f)
except:
    scripts_data = {}

def save_partners():
    with open('partners.json', 'w', encoding='utf-8') as f:
        json.dump(partners, f, indent=4, ensure_ascii=False)

def save_giveaways():
    with open('giveaways.json', 'w', encoding='utf-8') as f:
        json.dump(giveaways, f, indent=4, ensure_ascii=False)

def save_points():
    with open('points.json', 'w', encoding='utf-8') as f:
        json.dump(points_data, f, indent=4, ensure_ascii=False)

def save_nicknames():
    with open('nicknames.json', 'w', encoding='utf-8') as f:
        json.dump(user_nicknames, f, indent=4, ensure_ascii=False)

def save_tickets():
    with open('tickets.json', 'w', encoding='utf-8') as f:
        data = {
            'claimed': {str(k): str(v) for k, v in claimed_tickets.items()},
            'declines': {str(k): decline_counts[k] for k in decline_counts if decline_counts[k] > 0},
            'accepts': {str(k): accept_counts[k] for k in accept_counts if accept_counts[k] > 0},
            'cooldowns': {str(k): str(v) for k, v in cooldowns.items()},
            'creators': {str(k): str(v) for k, v in ticket_creators.items()},
            'claim_counts': {str(k): claim_counts[k] for k in claim_counts if claim_counts[k] > 0},
            'permissions': {str(k): list(v) for k, v in user_permissions.items()}
        }
        json.dump(data, f, indent=4, ensure_ascii=False)

def save_warnings():
    with open('warnings.json', 'w', encoding='utf-8') as f:

        json.dump({str(k): v for k, v in warnings_data.items()}, f, indent=4, ensure_ascii=False)

def save_scripts():
    with open('scripts.json', 'w', encoding='utf-8') as f:
        json.dump(scripts_data, f, indent=4, ensure_ascii=False)

def generate_script_id():
    return f"SCR-{str(uuid.uuid4())[:8].upper()}"

def create_error_embed(error_message):
    embed = discord.Embed(
        title="Error Occurred",
        description=f"```diff\n- {error_message}\n```",
        color=EMBED_COLOR,
        timestamp=datetime.now(IRAN_TZ)
    )
    embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    return embed

def create_success_embed(title, description):
    embed = discord.Embed(
        title=f"{title}",
        description=description,
        color=EMBED_COLOR,
        timestamp=datetime.now(IRAN_TZ)
    )
    embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    return embed

async def auto_delete_message(interaction, delay=30):
    """Auto-delete ephemeral messages after a delay (default 30 seconds)"""
    try:
        await asyncio.sleep(delay)
        if interaction.response.is_done():
            try:
                await interaction.delete_original_response()
            except:
                pass
    except:
        pass

def has_permission(user_id, command_name, user_roles=None):
    if user_id in ADMIN_USERS:
        return True

    if user_id in user_permissions and command_name in user_permissions[user_id]:
        return True

    if user_roles:
        for role in user_roles:
            role_id = role.id
            if role_id in user_permissions and command_name in user_permissions[role_id]:
                return True

    return False

async def send_transcript(channel, closed_by, ticket_type):
    try:
        transcript_channel_id = None
        if 'channels' in config and 'transcript' in config['channels']:
            transcript_list = config['channels']['transcript']
            if transcript_list and len(transcript_list) > 0:
                transcript_channel_id = transcript_list[0]

        if not transcript_channel_id:
            transcript_channel_id = config.get('transcript_channel_id')

        if not transcript_channel_id or transcript_channel_id == 0:
            print(f"Transcript channel ID not set in config")
            return

        log_channel = bot.get_channel(transcript_channel_id)
        if not log_channel:
            print(f"Transcript channel not found: {transcript_channel_id}")
            return

        # Generate unique ticket ID
        ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"

        # Collect messages
        messages_data = []
        messages_html = ""
        async for message in channel.history(limit=500, oldest_first=True):
            timestamp = message.created_at.astimezone(IRAN_TZ).strftime("%Y-%m-%d %H:%M:%S")
            avatar_url = message.author.display_avatar.url if message.author.display_avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
            username = message.author.display_name
            user_id = message.author.id
            content = message.content.replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br>') if message.content else '<em>No text content</em>'

            # Store message data for database
            messages_data.append({
                'timestamp': timestamp,
                'avatar_url': avatar_url,
                'username': username,
                'user_id': user_id,
                'content': content,
                'attachments': [{'url': att.url, 'filename': att.filename, 'is_image': att.content_type and att.content_type.startswith('image')} for att in message.attachments] if message.attachments else []
            })

            attachments_html = ""
            if message.attachments:
                for att in message.attachments:
                    if att.content_type and att.content_type.startswith('image'):
                        attachments_html += f'<div class="attachment"><img src="{att.url}" alt="{att.filename}" style="max-width: 400px; border-radius: 8px; margin-top: 8px;"></div>'
                    else:
                        attachments_html += f'<div class="attachment"><a href="{att.url}" target="_blank">📎 {att.filename}</a></div>'

            embeds_html = ""
            if message.embeds:
                for emb in message.embeds:
                    embed_color = f"#{emb.color.value:06x}" if emb.color else "#d4b2f6"
                    embeds_html += f'<div class="embed" style="border-left: 4px solid {embed_color};">'
                    if emb.author.name:
                        embeds_html += f'<div class="embed-author">{emb.author.name}</div>'
                    if emb.title:
                        embeds_html += f'<div class="embed-title">{emb.title}</div>'
                    if emb.description:
                        embeds_html += f'<div class="embed-description">{emb.description[:500]}</div>'
                    if emb.fields:
                        for field in emb.fields[:5]:
                            embeds_html += f'<div class="embed-field"><strong>{field.name}</strong><br>{field.value}</div>'
                    embeds_html += '</div>'

            messages_html += f'''
            <div class="message">
                <img class="avatar" src="{avatar_url}" alt="{username}">
                <div class="message-content">
                    <div class="message-header">
                        <span class="username">{username}</span>
                        <span class="user-id">ID: {user_id}</span>
                        <span class="timestamp">{timestamp}</span>
                    </div>
                    <div class="message-text">{content}</div>
                    {attachments_html}
                    {embeds_html}
                </div>
            </div>
            '''

        html_content = f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticket Transcript - {channel.name}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #36393f;
            color: #dcddde;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #2f3136;
            border-radius: 8px;
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #d4b2f6 0%, #9b7bb5 100%);
            padding: 30px;
            color: white;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header-info {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .messages {{
            padding: 20px;
        }}
        .message {{
            display: flex;
            margin-bottom: 20px;
            padding: 10px;
            border-radius: 4px;
            transition: background 0.2s;
        }}
        .message:hover {{
            background: #32353b;
        }}
        .avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 15px;
            flex-shrink: 0;
        }}
        .message-content {{
            flex: 1;
        }}
        .message-header {{
            margin-bottom: 5px;
        }}
        .username {{
            font-weight: 600;
            color: #ffffff;
            margin-right: 8px;
        }}
        .user-id {{
            font-size: 11px;
            color: #72767d;
            margin-right: 8px;
        }}
        .timestamp {{
            font-size: 12px;
            color: #72767d;
        }}
        .message-text {{
            color: #dcddde;
            line-height: 1.5;
            word-wrap: break-word;
        }}
        .attachment {{
            margin-top: 8px;
        }}
        .attachment a {{
            color: #00b0f4;
            text-decoration: none;
        }}
        .attachment a:hover {{
            text-decoration: underline;
        }}
        .embed {{
            background: #2f3136;
            border-radius: 4px;
            padding: 12px;
            margin-top: 8px;
            max-width: 520px;
        }}
        .embed-author {{
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 4px;
        }}
        .embed-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #ffffff;
        }}
        .embed-description {{
            font-size: 14px;
            margin-bottom: 8px;
            color: #dcddde;
        }}
        .embed-field {{
            margin-top: 8px;
            font-size: 14px;
        }}
        .footer {{
            background: #202225;
            padding: 20px;
            text-align: center;
            color: #72767d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Ticket Transcript - {channel.name}</h1>
            <div class="header-info">
                <strong>Ticket Type:</strong> {ticket_type} |
                <strong>Closed By:</strong> {closed_by.display_name} (ID: {closed_by.id}) |
                <strong>Closed At:</strong> {datetime.now(IRAN_TZ).strftime('%Y-%m-%d %H:%M:%S')} (Iran Time)
            </div>
        </div>
        <div class="messages">
            {messages_html if messages_html else '<p style="text-align: center; color: #72767d;">No messages found</p>'}
        </div>
        <div class="footer">
            Generated by {CLAN_NAME} System | Discord Bot Transcript
        </div>
    </div>
</body>
</html>
        '''

       
        if 'tickets' not in globals():
            tickets_db = {}
        else:
            try:
                with open('tickets_db.json', 'r', encoding='utf-8') as f:
                    tickets_db = json.load(f)
            except:
                tickets_db = {}

        tickets_db[ticket_id] = {
            'ticket_name': channel.name,
            'ticket_type': ticket_type,
            'closed_by': closed_by.display_name,
            'closed_by_id': str(closed_by.id),
            'closed_at': datetime.now(IRAN_TZ).strftime('%Y-%m-%d %H:%M:%S'),
            'messages': messages_data,
            'html_content': html_content
        }

        with open('tickets_db.json', 'w', encoding='utf-8') as f:
            json.dump(tickets_db, f, indent=4, ensure_ascii=False)

        embed = discord.Embed(
            title="📋 Ticket Transcript Saved",
            description=f"**Ticket ID:** `{ticket_id}`\n**Ticket:** {channel.name}\n**Type:** {ticket_type}\n**Closed By:** {closed_by.mention}\n**Time:** {datetime.now(IRAN_TZ).strftime('%Y-%m-%d %H:%M:%S')}\n\nView this ticket in the panel using the Ticket ID.",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.add_field(name="Panel Access", value="Open `panel.html` → Export Ticket tab", inline=False)
        embed.set_footer(text=f"{CLAN_NAME} System")

        await log_channel.send(embed=embed)

    except Exception as e:
        print(f"Failed to send transcript: {e}")

def build_nickname(member, suffix=None):
    user_id = str(member.id)
    base_name = member.display_name

    if base_name.startswith('['):
        if ']' in base_name:
            base_name = base_name.split(']', 1)[1].strip()

    if ' | ' in base_name:
        base_name = base_name.split(' | ')[0].strip()

    if not base_name:
        base_name = member.nick if member.nick else member.name
        if base_name.startswith('['):
            if ']' in base_name:
                base_name = base_name.split(']', 1)[1].strip()
        if ' | ' in base_name:
            base_name = base_name.split(' | ')[0].strip()

    points = points_data.get(user_id, 0)

    if suffix is None:
        suffix = user_nicknames.get(user_id, "")

    parts = []
    if points > 0:
        parts.append(f"[{points}]")
    parts.append(base_name)

    nickname = " ".join(parts)

    if suffix:
        nickname += f" | {suffix}"

    return nickname

async def update_user_nickname(member):
    try:
        user_id = str(member.id)
        if user_id in user_nicknames or user_id in points_data:
            new_nickname = build_nickname(member)
            if member.display_name != new_nickname:
                try:
                    await member.edit(nick=new_nickname)
                except:
                    pass
    except Exception as e:
        print(f'Update user nickname error: {e}')

async def check_auto_rankup(user_id, guild):
    try:
        claims = claim_counts.get(user_id, 0)

        team_tester_role_id = config.get('roles', {}).get('team_tester')
        team_tester_manager_role_id = config.get('roles', {}).get('tester_manager')
        claims_for_rankup = config.get('settings', {}).get('claims_for_rankup', 2000)

        member = guild.get_member(user_id)
        if not member:
            return

        team_tester_role = guild.get_role(team_tester_role_id) if team_tester_role_id else None
        team_tester_manager_role = guild.get_role(team_tester_manager_role_id) if team_tester_manager_role_id else None

        if claims >= claims_for_rankup and team_tester_role and team_tester_manager_role:
            if team_tester_role in member.roles and team_tester_manager_role not in member.roles:
                await member.add_roles(team_tester_manager_role)

                
                rankup_channel_id = config.get('channels', {}).get('rankup')

                if rankup_channel_id:
                    channel = bot.get_channel(rankup_channel_id)
                    if channel:
                        embed = discord.Embed(
                            title="Player Ranked Up",
                            description=f"{member.mention} has been promoted to **Team Tester Manager**",
                            color=EMBED_COLOR,
                            timestamp=datetime.now(IRAN_TZ)
                        )
                        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                        embed.add_field(name="New Role", value=team_tester_manager_role.mention, inline=True)
                        embed.add_field(name="Total Claims", value=str(claims), inline=True)
                        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
                        await channel.send(embed=embed)

                claim_counts[user_id] = 0
                save_tickets()
    except Exception as e:
        print(f'Auto rankup error: {e}')

@bot.event
async def on_ready():
    print(f'{bot.user} is online')
    print(f'Bot ID: {bot.user.id}')

    try:
        synced = await tree.sync()
        print(f'Synced {len(synced)} commands')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

    
    cleaned_channels = []
    for guild in bot.guilds:
        for ch_id in list(ticket_creators.keys()):
            channel = guild.get_channel(ch_id)
            if not channel:
                cleaned_channels.append(ch_id)
                del ticket_creators[ch_id]
                if ch_id in claimed_tickets:
                    del claimed_tickets[ch_id]

    if cleaned_channels:
        save_tickets()
        print(f'Cleaned up {len(cleaned_channels)} invalid ticket channels on startup')

    status_rotation.start()
    member_counter.start()
    check_giveaways.start()
    check_participant_membership.start()
    check_prize_deadlines.start()
    update_nicknames.start()

    bot.add_view(TicketSelect())
    bot.add_view(TicketManagementView())
    bot.add_view(PrizeTicketView())

    
    for giveaway_id, giveaway_data in giveaways.items():
        if giveaway_data.get('ended') and giveaway_data.get('selected_winners'):
            winners = giveaway_data['selected_winners']
            bot.add_view(PrizeAcceptView(winners, giveaway_id))

    ticket_panel_channel_id = config.get('channels', {}).get('ticket_panel')
    if ticket_panel_channel_id:
        channel = bot.get_channel(ticket_panel_channel_id)
        if channel:
            panel_exists = False
            async for message in channel.history(limit=50):
                if message.author.id == bot.user.id and message.embeds:
                    if f"{CLAN_NAME} Team Tickets" in message.embeds[0].title:
                        panel_exists = True
                        print(f'Ticket panel already exists in channel {channel.name}')
                        break

            if not panel_exists:
                embed = discord.Embed(
                    title=f"{CLAN_NAME} Team Tickets",
                    description="Select an option below to create a ticket.",
                    color=EMBED_COLOR,
                    timestamp=datetime.now(IRAN_TZ)
                )
                embed.set_footer(text=f"{CLAN_NAME} System")
                try:
                    await channel.send(embed=embed, view=TicketSelect())
                    print(f'Ticket panel sent to channel {channel.name}')
                except Exception as e:
                    print(f'Failed to send ticket panel: {e}')

    for message_id_str, giveaway_data in giveaways.items():
        if not giveaway_data.get('ended', False):
            try:
                channel_id = giveaway_data.get('channel_id')
                if channel_id:
                    channel = bot.get_channel(channel_id)
                    if channel:
                        try:
                            message = await channel.fetch_message(int(message_id_str))
                            required_role_id = giveaway_data.get('required_role_id')
                            view = GiveawayView(int(message_id_str), required_role_id)
                            await message.edit(view=view)
                            print(f'Restored giveaway view for message {message_id_str}')
                        except:
                            pass
            except Exception as e:
                print(f'Failed to restore giveaway {message_id_str}: {e}')

@bot.event
async def on_member_join(member):
    try:
        welcome_channel_id = config.get('welcome_channel_id')
        if not welcome_channel_id:
            return

        channel = bot.get_channel(welcome_channel_id)
        if not channel:
            return

        embed = discord.Embed(
            title=f"Welcome to {CLAN_NAME} Clan",
            description=f"**{member.mention}** just joined the server\n\nPlease use `/rules` to read our rules.",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await channel.send(embed=embed)
    except Exception as e:
        print(f'Welcome error: {e}')



@bot.event
async def on_message_delete(message):
    try:
       
        if message.author.bot:
            return

        log_channel_id = config.get('channels', {}).get('log_channel_id')
        if not log_channel_id or log_channel_id == 0:
            return

        log_channel = bot.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="Message Deleted",
            description=f"**Author:** {message.author.mention} ({message.author.id})\n**Channel:** {message.channel.mention}",
            color=0xff4747,
            timestamp=datetime.now(IRAN_TZ)
        )

        content = message.content if message.content else "*[No text content]*"
        if len(content) > 1024:
            content = content[:1021] + "..."
        embed.add_field(name="Content", value=content, inline=False)

        if message.attachments:
            attachments_text = "\n".join([f"[{att.filename}]({att.url})" for att in message.attachments])
            embed.add_field(name="Attachments", value=attachments_text, inline=False)

        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await log_channel.send(embed=embed)
    except Exception as e:
        print(f'Message delete logging error: {e}')

@bot.event
async def on_message_edit(before, after):
    try:
       
        if before.author.bot or before.content == after.content:
            return

        log_channel_id = config.get('channels', {}).get('log_channel_id')
        if not log_channel_id or log_channel_id == 0:
            return

        log_channel = bot.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="Message Edited",
            description=f"**Author:** {before.author.mention} ({before.author.id})\n**Channel:** {before.channel.mention}\n**Jump:** [Go to Message]({after.jump_url})",
            color=0xffea00,
            timestamp=datetime.now(IRAN_TZ)
        )

        before_content = before.content if before.content else "*[No text content]*"
        after_content = after.content if after.content else "*[No text content]*"

        if len(before_content) > 1024:
            before_content = before_content[:1021] + "..."
        if len(after_content) > 1024:
            after_content = after_content[:1021] + "..."

        embed.add_field(name="Before", value=before_content, inline=False)
        embed.add_field(name="After", value=after_content, inline=False)

        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await log_channel.send(embed=embed)
    except Exception as e:
        print(f'Message edit logging error: {e}')

@bot.event
async def on_member_update(before, after):
    try:
       
        if before.bot:
            return

        log_channel_id = config.get('channels', {}).get('log_channel_id')
        if not log_channel_id or log_channel_id == 0:
            return

        log_channel = bot.get_channel(log_channel_id)
        if not log_channel:
            return


        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            if added_roles or removed_roles:
                embed = discord.Embed(
                    title="Member Roles Updated",
                    description=f"**Member:** {after.mention} ({after.id})",
                    color=0x5865F2,
                    timestamp=datetime.now(IRAN_TZ)
                )

                if added_roles:
                    roles_text = ", ".join([role.mention for role in added_roles])
                    embed.add_field(name="Roles Added", value=roles_text, inline=False)

                if removed_roles:
                    roles_text = ", ".join([role.mention for role in removed_roles])
                    embed.add_field(name="Roles Removed", value=roles_text, inline=False)

                embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

                await log_channel.send(embed=embed)


        if before.nick != after.nick:
            embed = discord.Embed(
                title="Member Nickname Updated",
                description=f"**Member:** {after.mention} ({after.id})",
                color=0x5865F2,
                timestamp=datetime.now(IRAN_TZ)
            )

            old_nick = before.nick if before.nick else "*[No nickname]*"
            new_nick = after.nick if after.nick else "*[No nickname]*"

            embed.add_field(name="Old Nickname", value=old_nick, inline=True)
            embed.add_field(name="New Nickname", value=new_nick, inline=True)

            embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

            await log_channel.send(embed=embed)

    except Exception as e:
        print(f'Member update logging error: {e}')

@bot.event
async def on_voice_state_update(member, before, after):
    try:

        if member.bot:
            return

        log_channel_id = config.get('channels', {}).get('log_channel_id')
        if not log_channel_id or log_channel_id == 0:
            return

        log_channel = bot.get_channel(log_channel_id)
        if not log_channel:
            return

        embed = discord.Embed(
            title="Voice State Update",
            description=f"**Member:** {member.mention} ({member.id})",
            color=0x57F287,
            timestamp=datetime.now(IRAN_TZ)
        )


        if before.channel is None and after.channel is not None:
            embed.add_field(name="Action", value="Joined Voice Channel", inline=False)
            embed.add_field(name="Channel", value=after.channel.mention, inline=False)


        elif before.channel is not None and after.channel is None:
            embed.add_field(name="Action", value="Left Voice Channel", inline=False)
            embed.add_field(name="Channel", value=before.channel.mention, inline=False)


        elif before.channel != after.channel:
            embed.add_field(name="Action", value="Moved Between Channels", inline=False)
            embed.add_field(name="From", value=before.channel.mention, inline=True)
            embed.add_field(name="To", value=after.channel.mention, inline=True)

        else:
            # (mute, deafen, etc.) - we can skip logging these
            return

        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await log_channel.send(embed=embed)

    except Exception as e:
        print(f'Voice state logging error: {e}')

    try:
        auto_voice_id = config.get('qol_features', {}).get('auto_voice_channel_id')
        if auto_voice_id and after.channel and after.channel.id == auto_voice_id:
            guild = member.guild
            category = after.channel.category

            channel_name = f"{member.display_name}'s Channel"
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=True, view_channel=True),
                member: discord.PermissionOverwrite(connect=True, manage_channels=True, move_members=True),
                guild.me: discord.PermissionOverwrite(connect=True, manage_channels=True)
            }

            new_channel = await guild.create_voice_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )

            await member.move_to(new_channel)

            await new_channel.edit(user_limit=after.channel.user_limit if after.channel.user_limit else 0)
    except Exception as e:
        print(f'Auto voice channel error: {e}')

    try:
        if before.channel and len(before.channel.members) == 0:
            if before.channel.category:
                auto_voice_id = config.get('qol_features', {}).get('auto_voice_channel_id')
                if auto_voice_id:
                    parent_channel = member.guild.get_channel(auto_voice_id)
                    if parent_channel and parent_channel.category == before.channel.category and before.channel.id != auto_voice_id:
                        await before.channel.delete()
    except Exception as e:
        print(f'Auto voice channel deletion error: {e}')





@bot.event
async def on_message(message):

    if message.author.bot:
        await bot.process_commands(message)
        return

    if not message.guild:
        return

    channel_id = message.channel.id
    guild = message.guild


    current_time = time.time()
    channel_message_history[channel_id].append({
        'author_id': message.author.id,
        'timestamp': current_time,
        'message_id': message.id
    })


    channel_message_history[channel_id] = [
        msg for msg in channel_message_history[channel_id]
        if current_time - msg['timestamp'] < 120
    ]


    auto_thread_channels = config.get('qol_features', {}).get('auto_thread_channels', [])

    if channel_id in auto_thread_channels:

        if channel_id in thread_creation_cooldowns:
            if current_time - thread_creation_cooldowns[channel_id] < 300:  
                pass  
            else:
                del thread_creation_cooldowns[channel_id] 

        if channel_id not in thread_creation_cooldowns:
            
            recent_msgs = channel_message_history[channel_id][-7:]

            if len(recent_msgs) >= 7:
                
                unique_authors = set(msg['author_id'] for msg in recent_msgs)

                
                if 2 <= len(unique_authors) <= 3:
                   
                    author_counts = {}
                    for msg in recent_msgs:
                        author_id = msg['author_id']
                        author_counts[author_id] = author_counts.get(author_id, 0) + 1

                   
                    total_from_group = sum(author_counts.values())
                    if total_from_group >= 5:
                        try:
                            
                            thread_msg = await message.channel.send(
                                "Looks like a detailed discussion is happening! 💬 I've created a thread for you to continue."
                            )

                            thread = await message.create_thread(
                                name=f"Discussion - {datetime.now(IRAN_TZ).strftime('%H:%M')}",
                                auto_archive_duration=60
                            )

                         
                            thread_creation_cooldowns[channel_id] = current_time
                            print(f"Auto-thread created in channel {channel_id}")

                        except Exception as e:
                            print(f"Failed to create auto-thread: {e}")

    
    smart_slowmode_channels = config.get('qol_features', {}).get('smart_slowmode_channels', [])

    if channel_id in smart_slowmode_channels:
        threshold = config.get('qol_features', {}).get('smart_slowmode_threshold', 12)
        timeframe = config.get('qol_features', {}).get('smart_slowmode_timeframe', 8)
        duration = config.get('qol_features', {}).get('smart_slowmode_duration', 60)

       
        recent_msgs = [
            msg for msg in channel_message_history[channel_id]
            if current_time - msg['timestamp'] <= timeframe
        ]

        if len(recent_msgs) >= threshold:
          
            if channel_id not in active_slowmodes:
                
                if message.channel.permissions_for(guild.me).manage_channels:
                   
                    if message.channel.slowmode_delay == 0:
                        try:
                            
                            await message.channel.edit(slowmode_delay=5)

                            await message.channel.send(
                                f"High activity detected! 🚦 Slowmode has been temporarily enabled for {duration} seconds."
                            )

                            
                            async def disable_slowmode_after(ch, dur, ch_id):
                                await asyncio.sleep(dur)
                                try:
                                    await ch.edit(slowmode_delay=0)
                                    if ch_id in active_slowmodes:
                                        del active_slowmodes[ch_id]
                                    print(f"Slowmode disabled in channel {ch_id}")
                                except Exception as e:
                                    print(f"Failed to disable slowmode: {e}")

                            active_slowmodes[channel_id] = True
                            asyncio.create_task(disable_slowmode_after(message.channel, duration, channel_id))

                        except Exception as e:
                            print(f"Failed to enable slowmode: {e}")

    blacklist_words = config.get('blacklist_words', [])
    if blacklist_words:
        message_content_lower = message.content.lower()
        for word in blacklist_words:
            if word.lower() in message_content_lower:
                try:
                    await message.delete()
                    warn_embed = discord.Embed(
                        title="Message Deleted",
                        description=f"{message.author.mention}, your message contained a blacklisted word and has been removed.",
                        color=0xFF0000,
                        timestamp=datetime.now(IRAN_TZ)
                    )
                    warn_embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
                    await message.channel.send(embed=warn_embed, delete_after=5)

                    log_channel_id = config.get('channels', {}).get('log_channel_id')
                    if log_channel_id:
                        log_channel = bot.get_channel(log_channel_id)
                        if log_channel:
                            log_embed = discord.Embed(
                                title="Blacklist Word Detected",
                                description=f"**User:** {message.author.mention} ({message.author.id})\n**Channel:** {message.channel.mention}\n**Word:** `{word}`",
                                color=0xFF0000,
                                timestamp=datetime.now(IRAN_TZ)
                            )
                            log_embed.add_field(name="Message Content", value=message.content[:1000], inline=False)
                            log_embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
                            await log_channel.send(embed=log_embed)
                    return
                except Exception as e:
                    print(f"Blacklist error: {e}")


    await bot.process_commands(message)



status_messages = [
    f"Felafeled By {CLAN_NAME} Team",
    "by Tury",
    "i See you",
    "bypassed by NotSallam..."
]
current_status_index = 0

@tasks.loop(seconds=3)
async def status_rotation():
    global current_status_index
    try:
        await bot.change_presence(
            activity=discord.Streaming(
                name=status_messages[current_status_index],
                url="https://www.twitch.tv/jyx_team"
            ),
            status=discord.Status.online
        )
        current_status_index = (current_status_index + 1) % len(status_messages)
    except Exception as e:
        print(f'Status rotation error: {e}')

@tasks.loop(seconds=5)
async def member_counter():
    try:
        
        member_counter_channel_id = config.get('channels', {}).get('member_counter')
        if member_counter_channel_id:
            channel = bot.get_channel(member_counter_channel_id)
            if channel:
                try:
                    guild = channel.guild
                    member_count = sum(1 for m in guild.members if not m.bot)
                    await channel.edit(name=f"🤷‍♂️| Members: {member_count}")
                except discord.errors.Forbidden:
                    print(f"Missing permissions to edit member counter channel")
                except Exception as e:
                    print(f"Error updating member counter: {e}")

        
        team_counter_channel_id = config.get('channels', {}).get('team_counter')
        if team_counter_channel_id:
            channel = bot.get_channel(team_counter_channel_id)
            if channel:
                try:
                    guild = channel.guild
                    team_role_id = config.get('roles', {}).get('team')
                    if team_role_id:
                        team_role = guild.get_role(team_role_id)
                        if team_role:
                            team_count = sum(1 for m in team_role.members if not m.bot)
                            await channel.edit(name=f"💎 | Team: {team_count}")
                except discord.errors.Forbidden:
                    print(f"Missing permissions to edit team counter channel")
                except Exception as e:
                    print(f"Error updating team counter: {e}")
    except Exception as e:
        print(f'Member counter general error: {e}')

@tree.command(name="addp", description="Grant permission to a user or role (Admin only)")
@app_commands.describe(target="User or Role to grant permission", command="Command name (e.g., ban, kick, mute)")
async def addp(interaction: discord.Interaction, target: str, command: str):
    try:
        if interaction.user.id not in ADMIN_USERS:
            return await interaction.response.send_message(
                embed=create_error_embed("Only admins can grant permissions"),
                ephemeral=True
            )

        target_id = None
        target_name = None
        is_role = False

        if target.startswith('<@&') and target.endswith('>'):
            role_id = int(target[3:-1])
            role = interaction.guild.get_role(role_id)
            if role:
                target_id = role_id
                target_name = role.name
                is_role = True
        elif target.startswith('<@') and target.endswith('>'):
            user_id = int(target.replace('<@!', '').replace('<@', '').replace('>', ''))
            user = interaction.guild.get_member(user_id)
            if user:
                target_id = user_id
                target_name = user.display_name
        else:
            return await interaction.response.send_message(
                embed=create_error_embed("Please mention a valid user or role"),
                ephemeral=True
            )

        if not target_id:
            return await interaction.response.send_message(
                embed=create_error_embed("Could not find the specified user or role"),
                ephemeral=True
            )

        if target_id not in user_permissions:
            user_permissions[target_id] = set()

        user_permissions[target_id].add(command)
        save_tickets()

        success_embed = create_success_embed(
            "Permission Granted",
            f"{'Role' if is_role else 'User'} **{target_name}** can now use `/{command}`"
        )
        await interaction.response.send_message(embed=success_embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="removep", description="Remove permission from a user or role (Admin only)")
@app_commands.describe(target="User or Role to remove permission", command="Command name")
async def removep(interaction: discord.Interaction, target: str, command: str):
    try:
        if interaction.user.id not in ADMIN_USERS:
            return await interaction.response.send_message(
                embed=create_error_embed("Only admins can remove permissions"),
                ephemeral=True
            )

        target_id = None
        target_name = None
        is_role = False

        if target.startswith('<@&') and target.endswith('>'):
            role_id = int(target[3:-1])
            role = interaction.guild.get_role(role_id)
            if role:
                target_id = role_id
                target_name = role.name
                is_role = True
        elif target.startswith('<@') and target.endswith('>'):
            user_id = int(target.replace('<@!', '').replace('<@', '').replace('>', ''))
            user = interaction.guild.get_member(user_id)
            if user:
                target_id = user_id
                target_name = user.display_name
        else:
            return await interaction.response.send_message(
                embed=create_error_embed("Please mention a valid user or role"),
                ephemeral=True
            )

        if not target_id:
            return await interaction.response.send_message(
                embed=create_error_embed("Could not find the specified user or role"),
                ephemeral=True
            )

        if target_id in user_permissions and command in user_permissions[target_id]:
            user_permissions[target_id].remove(command)
            if not user_permissions[target_id]:
                del user_permissions[target_id]
            save_tickets()

            success_embed = create_success_embed(
                "Permission Removed",
                f"{'Role' if is_role else 'User'} **{target_name}** can no longer use `/{command}`"
            )
            await interaction.response.send_message(embed=success_embed)
        else:
            await interaction.response.send_message(
                embed=create_error_embed(f"{'Role' if is_role else 'User'} **{target_name}** doesn't have permission for `/{command}`"),
                ephemeral=True
            )

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="listperms", description="List all permissions (Admin only)")
async def listperms(interaction: discord.Interaction):
    try:
        if interaction.user.id not in ADMIN_USERS:
            return await interaction.response.send_message(
                embed=create_error_embed("Only admins can view permissions"),
                ephemeral=True
            )

        if not user_permissions:
            return await interaction.response.send_message(
                embed=create_error_embed("No permissions have been granted yet"),
                ephemeral=True
            )

        embed = discord.Embed(
            title="Permission List",
            description="All granted permissions:",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )

        for target_id, commands in user_permissions.items():
            role = interaction.guild.get_role(target_id)
            if role:
                target_name = f"Role: {role.name}"
            else:
                member = interaction.guild.get_member(target_id)
                target_name = f"User: {member.display_name if member else 'Unknown'}"

            commands_list = ', '.join([f"`{cmd}`" for cmd in commands])
            embed.add_field(name=target_name, value=commands_list, inline=False)

        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="ban", description="Ban a user from the server")
@app_commands.describe(user="The user to ban", reason="Reason for the ban")
async def ban(interaction: discord.Interaction, user: discord.Member, reason: str):
    try:
        if not has_permission(interaction.user.id, "ban", interaction.user.roles):
            await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )
            asyncio.create_task(auto_delete_message(interaction))
            return

        log_channel_id = config.get('channels', {}).get('mod_log')
        if log_channel_id:
            log_channel = bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="User Banned",
                    color=EMBED_COLOR,
                    timestamp=datetime.now(IRAN_TZ)
                )
                log_embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
                log_embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                log_embed.add_field(name="Reason", value=f"```{reason}```", inline=False)
                log_embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
                await log_channel.send(embed=log_embed)

        await user.ban(reason=reason)

        success_embed = create_success_embed(
            "User Banned",
            f"**{user.mention}** has been banned\n\n**Reason:** ```{reason}```"
        )
        await interaction.response.send_message(embed=success_embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="mute", description="Mute a user in the server")
@app_commands.describe(user="The user to mute", reason="Reason for the mute")
async def mute(interaction: discord.Interaction, user: discord.Member, reason: str):
    try:
        if not has_permission(interaction.user.id, "mute", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        mute_role_id = config.get('mute_role_id')
        if not mute_role_id:
            return await interaction.response.send_message(
                embed=create_error_embed("Mute role not configured"),
                ephemeral=True
            )

        mute_role = interaction.guild.get_role(mute_role_id)
        if not mute_role:
            return await interaction.response.send_message(
                embed=create_error_embed("Mute role not found"),
                ephemeral=True
            )

        await user.add_roles(mute_role)

        log_channel_id = config.get('mod_log_channel_id')
        if log_channel_id:
            log_channel = bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="User Muted",
                    color=EMBED_COLOR,
                    timestamp=datetime.now(IRAN_TZ)
                )
                log_embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
                log_embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                log_embed.add_field(name="Reason", value=f"```{reason}```", inline=False)
                log_embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
                await log_channel.send(embed=log_embed)

        success_embed = create_success_embed(
            "User Muted",
            f"**{user.mention}** has been muted\n\n**Reason:** ```{reason}```"
        )
        await interaction.response.send_message(embed=success_embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="kick", description="Kick a user from the server")
@app_commands.describe(user="The user to kick", reason="Reason for the kick")
async def kick(interaction: discord.Interaction, user: discord.Member, reason: str):
    try:
        if not has_permission(interaction.user.id, "kick", interaction.user.roles):
            await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )
            asyncio.create_task(auto_delete_message(interaction))
            return

        log_channel_id = config.get('channels', {}).get('mod_log')
        if log_channel_id:
            log_channel = bot.get_channel(log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="User Kicked",
                    color=EMBED_COLOR,
                    timestamp=datetime.now(IRAN_TZ)
                )
                log_embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=False)
                log_embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
                log_embed.add_field(name="Reason", value=f"```{reason}```", inline=False)
                log_embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
                await log_channel.send(embed=log_embed)

        await user.kick(reason=reason)

        success_embed = create_success_embed(
            "User Kicked",
            f"**{user.mention}** has been kicked\n\n**Reason:** ```{reason}```"
        )
        await interaction.response.send_message(embed=success_embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )



async def check_auto_moderation(user: discord.Member, guild: discord.Guild, channel: discord.TextChannel):
    """Check and apply auto-moderation rules based on warning count."""
    try:
        user_id = user.id
        warnings = warnings_data.get(user_id, [])
        warn_count = len(warnings)

        
        if warn_count == 3:
            mute_role_id = config.get('roles', {}).get('mute')
            if mute_role_id:
                mute_role = guild.get_role(mute_role_id)
                if mute_role:
                    await user.add_roles(mute_role)

                    auto_embed = discord.Embed(
                        title="Auto-Moderation: User Muted",
                        description=f"{user.mention} has been automatically muted for 24 hours",
                        color=0xff9900,
                        timestamp=datetime.now(IRAN_TZ)
                    )
                    auto_embed.add_field(name="Reason", value="Reached 3 warnings", inline=False)
                    auto_embed.set_footer(text=f"{CLAN_NAME} System - Auto-Mod", icon_url=guild.me.avatar.url if guild.me.avatar else None)

                    await channel.send(embed=auto_embed)

                    
                    print(f"Auto-muted {user.display_name} for 24 hours (3 warnings)")

       
        elif warn_count >= 5:
            try:
                auto_embed = discord.Embed(
                    title="Auto-Moderation: User Kicked",
                    description=f"{user.mention} has been automatically kicked from the server",
                    color=0xff0000,
                    timestamp=datetime.now(IRAN_TZ)
                )
                auto_embed.add_field(name="Reason", value="Reached 5 warnings", inline=False)
                auto_embed.set_footer(text=f"{CLAN_NAME} System - Auto-Mod", icon_url=guild.me.avatar.url if guild.me.avatar else None)

                await channel.send(embed=auto_embed)
                await user.kick(reason="Auto-moderation: Reached 5 warnings")

            except discord.Forbidden:
                error_embed = create_error_embed("Failed to kick user - Bot lacks permission")
                await channel.send(embed=error_embed)

    except Exception as e:
        print(f"Auto-moderation error: {e}")

@tree.command(name="warn", description="Warn a user")
@app_commands.describe(user="The user to warn", reason="Reason for the warning")
async def warn(interaction: discord.Interaction, user: discord.Member, reason: str):
    try:
        if not has_permission(interaction.user.id, "kick", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        
        warn_id = str(int(time.time() * 1000))  
        warning = {
            'warn_id': warn_id,
            'moderator_id': interaction.user.id,
            'reason': reason,
            'timestamp': datetime.now(IRAN_TZ).isoformat()
        }

        
        user_id = user.id
        if user_id not in warnings_data:
            warnings_data[user_id] = []

        warnings_data[user_id].append(warning)
        save_warnings()

        success_embed = create_success_embed(
            "User Warned",
            f"**{user.mention}** has been warned\n\n**Reason:** ```{reason}```\n**Warning ID:** `{warn_id}`\n**Total Warnings:** {len(warnings_data[user_id])}"
        )
        await interaction.response.send_message(embed=success_embed)

        
        try:
            dm_embed = discord.Embed(
                title="You have been warned",
                description=f"You received a warning in **{interaction.guild.name}**",
                color=EMBED_COLOR,
                timestamp=datetime.now(IRAN_TZ)
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.add_field(name="Moderator", value=interaction.user.mention, inline=False)
            dm_embed.add_field(name="Total Warnings", value=str(len(warnings_data[user_id])), inline=False)
            dm_embed.set_footer(text=f"{CLAN_NAME} System", icon_url=interaction.guild.me.avatar.url if interaction.guild.me.avatar else None)

            await user.send(embed=dm_embed)
        except:
            pass  

      
        await check_auto_moderation(user, interaction.guild, interaction.channel)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="warnings", description="View all warnings for a user")
@app_commands.describe(user="The user to check warnings for")
async def warnings_command(interaction: discord.Interaction, user: discord.Member):
    try:
        if not has_permission(interaction.user.id, "kick", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        user_id = user.id
        warnings = warnings_data.get(user_id, [])

        if not warnings:
            return await interaction.response.send_message(
                embed=create_success_embed("No Warnings", f"{user.mention} has no warnings"),
                ephemeral=True
            )

        embed = discord.Embed(
            title=f"Warnings for {user.display_name}",
            description=f"**User:** {user.mention}\n**Total Warnings:** {len(warnings)}",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)

        for i, warning in enumerate(warnings[:10], 1):  
            moderator_id = warning.get('moderator_id')
            moderator = interaction.guild.get_member(moderator_id)
            moderator_text = moderator.mention if moderator else f"<@{moderator_id}>"

            warn_time = warning.get('timestamp', 'Unknown')
            try:
                warn_dt = datetime.fromisoformat(warn_time)
                warn_time_display = warn_dt.strftime('%Y-%m-%d %H:%M')
            except:
                warn_time_display = warn_time

            field_value = f"**Reason:** {warning.get('reason', 'No reason')}\n**Moderator:** {moderator_text}\n**Date:** {warn_time_display}\n**ID:** `{warning.get('warn_id', 'N/A')}`"
            embed.add_field(name=f"Warning #{i}", value=field_value, inline=False)

        if len(warnings) > 10:
            embed.set_footer(text=f"Showing 10 of {len(warnings)} warnings • {CLAN_NAME} System")
        else:
            embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="removewarn", description="Remove a specific warning from a user")
@app_commands.describe(user="The user to remove warning from", warn_id="The warning ID to remove")
async def removewarn(interaction: discord.Interaction, user: discord.Member, warn_id: str):
    try:
        if not has_permission(interaction.user.id, "ban", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        user_id = user.id
        warnings = warnings_data.get(user_id, [])

       
        warning_found = False
        for i, warning in enumerate(warnings):
            if warning.get('warn_id') == warn_id:
                removed_warning = warnings.pop(i)
                warning_found = True
                break

        if not warning_found:
            return await interaction.response.send_message(
                embed=create_error_embed(f"Warning ID `{warn_id}` not found for {user.mention}"),
                ephemeral=True
            )

        
        if len(warnings) == 0:
            del warnings_data[user_id]
        else:
            warnings_data[user_id] = warnings

        save_warnings()

        success_embed = create_success_embed(
            "Warning Removed",
            f"Removed warning `{warn_id}` from {user.mention}\n\n**Remaining Warnings:** {len(warnings)}"
        )
        await interaction.response.send_message(embed=success_embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )



@bot.command(name='npn')
async def add_partner(ctx, user: discord.Member, server_name: str, *, message: str):
    try:
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send(
                embed=create_error_embed("You don't have permission to add partners")
            )

        partner_role_id = config.get('partner_role_id')
        if partner_role_id:
            partner_role = ctx.guild.get_role(partner_role_id)
            if partner_role:
                await user.add_roles(partner_role)

        partner_data = {
            'user_id': user.id,
            'server_name': server_name,
            'message': message,
            'added_by': ctx.author.id,
            'added_at': datetime.now(IRAN_TZ).isoformat()
        }
        partners.append(partner_data)
        save_partners()

        success_embed = create_success_embed(
            "Partner Added",
            f"**{user.mention}** has been added as a partner\n\n**Server:** `{server_name}`"
        )
        await ctx.send(embed=success_embed)

    except Exception as e:
        await ctx.send(
            embed=create_error_embed(f"An error occurred: {str(e)}")
        )

@bot.command(name='savesv')
async def save_server(ctx):
    try:
        if not has_permission(ctx.author.id, "savesv", ctx.author.roles):
            return await ctx.send(embed=create_error_embed("You don't have permission to use this command"))

        guild = ctx.guild

        backup_data = {
            'guild_id': guild.id,
            'guild_name': guild.name,
            'timestamp': datetime.now(IRAN_TZ).isoformat(),
            'channels': [],
            'roles': [],
            'categories': []
        }

        for category in guild.categories:
            backup_data['categories'].append({
                'id': category.id,
                'name': category.name,
                'position': category.position
            })

        for channel in guild.channels:
            channel_data = {
                'id': channel.id,
                'name': channel.name,
                'type': str(channel.type),
                'position': channel.position,
                'category_id': channel.category.id if channel.category else None
            }
            backup_data['channels'].append(channel_data)

        for role in guild.roles:
            if role.name != "@everyone":
                role_data = {
                    'id': role.id,
                    'name': role.name,
                    'color': role.color.value,
                    'permissions': role.permissions.value,
                    'position': role.position,
                    'hoist': role.hoist,
                    'mentionable': role.mentionable
                }
                backup_data['roles'].append(role_data)

        backup_file = f'server_backup_{guild.id}.json'
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

        embed = discord.Embed(
            title="Server Backup Saved",
            description=f"Backup saved to `{backup_file}`\n\n**Categories:** {len(backup_data['categories'])}\n**Channels:** {len(backup_data['channels'])}\n**Roles:** {len(backup_data['roles'])}",
            color=0x57F287,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(embed=create_error_embed(f"An error occurred: {str(e)}"))

@bot.command(name='loadsv')
async def load_server(ctx, filename: str):
    try:
        if not has_permission(ctx.author.id, "loadsv", ctx.author.roles):
            return await ctx.send(embed=create_error_embed("You don't have permission to use this command"))

        if not filename.endswith('.json'):
            filename += '.json'

        if not os.path.exists(filename):
            return await ctx.send(embed=create_error_embed(f"Backup file `{filename}` not found"))

        with open(filename, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)

        guild = ctx.guild

        await ctx.send(embed=create_success_embed("Loading Backup", "Starting server restoration..."))

        for category_data in backup_data['categories']:
            existing_cat = discord.utils.get(guild.categories, name=category_data['name'])
            if not existing_cat:
                await guild.create_category(name=category_data['name'])

        for role_data in backup_data['roles']:
            existing_role = discord.utils.get(guild.roles, name=role_data['name'])
            if not existing_role:
                await guild.create_role(
                    name=role_data['name'],
                    color=discord.Color(role_data['color']),
                    permissions=discord.Permissions(role_data['permissions']),
                    hoist=role_data['hoist'],
                    mentionable=role_data['mentionable']
                )

        for channel_data in backup_data['channels']:
            existing_channel = discord.utils.get(guild.channels, name=channel_data['name'])
            if not existing_channel:
                category = None
                if channel_data['category_id']:
                    for cat_data in backup_data['categories']:
                        if cat_data['id'] == channel_data['category_id']:
                            category = discord.utils.get(guild.categories, name=cat_data['name'])
                            break

                if 'text' in channel_data['type']:
                    await guild.create_text_channel(name=channel_data['name'], category=category)
                elif 'voice' in channel_data['type']:
                    await guild.create_voice_channel(name=channel_data['name'], category=category)

        embed = discord.Embed(
            title="Server Backup Loaded",
            description=f"Server restored from `{filename}`\n\n**Categories:** {len(backup_data['categories'])}\n**Channels:** {len(backup_data['channels'])}\n**Roles:** {len(backup_data['roles'])}",
            color=0x57F287,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(embed=create_error_embed(f"An error occurred: {str(e)}"))

class PartnerView(discord.ui.View):
    def __init__(self, partners_list):
        super().__init__(timeout=None)
        self.partners_list = partners_list

        options = []
        for i, partner in enumerate(partners_list[:25]):
            options.append(
                discord.SelectOption(
                    label=partner['server_name'][:100],
                    value=str(i),
                    description=partner['message'][:100] if len(partner['message']) <= 100 else partner['message'][:97] + "..."
                )
            )

        select = Select(
            custom_id="partner_select",
            placeholder="Select a partner to view details",
            options=options,
            min_values=1,
            max_values=1
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        try:
            selected_index = int(interaction.data['values'][0])
            partner = self.partners_list[selected_index]

            embed = discord.Embed(
                title=f"{partner['server_name']}",
                description=partner['message'],
                color=EMBED_COLOR,
                timestamp=datetime.now(IRAN_TZ)
            )
            user = interaction.guild.get_member(partner['user_id'])
            if user:
                embed.set_author(name=user.name, icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
            embed.set_footer(text=f"{CLAN_NAME} System", icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                embed=create_error_embed(f"An error occurred: {str(e)}"),
                ephemeral=True
            )

@tree.command(name="partner", description="View all server partners")
async def partner(interaction: discord.Interaction):
    try:
        if not partners:
            return await interaction.response.send_message(
                embed=create_error_embed("No partners added yet"),
                ephemeral=True
            )

        embed = discord.Embed(
            title=f"{CLAN_NAME} Partners",
            description="Select a partner from the menu below to view their message",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        view = PartnerView(partners)
        await interaction.response.send_message(embed=embed, view=view)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="dpartner", description="Delete a partner (Admin only)")
@app_commands.describe(user="The partner user to remove")
async def dpartner(interaction: discord.Interaction, user: discord.Member):
    try:
        if interaction.user.id not in ADMIN_USERS:
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to delete partners"),
                ephemeral=True
            )

        global partners
        partner_found = False
        for i, partner in enumerate(partners):
            if partner['user_id'] == user.id:
                removed_partner = partners.pop(i)
                partner_found = True
                save_partners()

                partner_role_id = config.get('partner_role_id')
                if partner_role_id:
                    partner_role = interaction.guild.get_role(partner_role_id)
                    if partner_role and partner_role in user.roles:
                        await user.remove_roles(partner_role)

                success_embed = create_success_embed(
                    "Partner Removed",
                    f"**{user.mention}** has been removed from partners\n\n**Server:** `{removed_partner['server_name']}`"
                )
                await interaction.response.send_message(embed=success_embed)
                break

        if not partner_found:
            await interaction.response.send_message(
                embed=create_error_embed(f"{user.mention} is not a partner"),
                ephemeral=True
            )

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

def parse_duration(duration_str):
    amount = int(duration_str[:-1])
    unit = duration_str[-1]

    if unit == 'h':
        return timedelta(hours=amount)
    elif unit == 'd':
        return timedelta(days=amount)
    elif unit == 'M':
        return timedelta(days=amount * 30)
    elif unit == 'm':
        return timedelta(minutes=amount)
    elif unit == 's':
        return timedelta(seconds=amount)
    else:
        raise ValueError("Invalid duration format")

async def extract_guild_id_from_invite(invite_link):
    """Extract guild ID from Discord invite link."""
    try:
        
        if 'discord.gg/' in invite_link:
            invite_code = invite_link.split('discord.gg/')[-1].split('?')[0]
        elif 'discord.com/invite/' in invite_link:
            invite_code = invite_link.split('invite/')[-1].split('?')[0]
        else:
            return None

        
        invite = await bot.fetch_invite(invite_code)
        return invite.guild.id if invite.guild else None
    except:
        return None

class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id, required_role_id=None):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
        self.required_role_id = required_role_id

    @discord.ui.button(label="Join Giveaway", style=discord.ButtonStyle.green, custom_id="join_giveaway")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            actual_giveaway_id = str(interaction.message.id)
            giveaway_data = giveaways.get(actual_giveaway_id)
            if not giveaway_data:
                return await interaction.response.send_message(
                    embed=create_error_embed("This giveaway no longer exists"),
                    ephemeral=True
                )

            if giveaway_data.get('ended', False):
                return await interaction.response.send_message(
                    embed=create_error_embed("This giveaway has already ended"),
                    ephemeral=True
                )

            
            if giveaway_data.get('require_server_join', False):
                server_link = giveaway_data.get('server_link')
                if server_link:
                    target_guild_id = await extract_guild_id_from_invite(server_link)

                    if target_guild_id:
                        
                        target_guild = checker_bot.get_guild(target_guild_id)

                        if target_guild:
                           
                            target_member = target_guild.get_member(interaction.user.id)

                            if not target_member:
                                return await interaction.response.send_message(
                                    embed=create_error_embed(f"To enter this giveaway, you must first join the partner server: {server_link}"),
                                    ephemeral=True
                                )
                        else:
                            
                            return await interaction.response.send_message(
                                embed=create_error_embed(f"Verification failed: Checker Bot must be invited to the partner server first.\n\nInvite link: {server_link}"),
                                ephemeral=True
                            )

            if self.required_role_id:
                member = interaction.guild.get_member(interaction.user.id)
                if not any(role.id == self.required_role_id for role in member.roles):
                    return await interaction.response.send_message(
                        embed=create_error_embed("You don't have the required role to join this giveaway"),
                        ephemeral=True
                    )

          
            required_invites = giveaway_data.get('required_invites', 0)
            if required_invites > 0:
                try:
                    
                    invites = await interaction.guild.invites()
                    user_invites = sum(invite.uses for invite in invites if invite.inviter and invite.inviter.id == interaction.user.id)

                    if user_invites < required_invites:
                        return await interaction.response.send_message(
                            embed=create_error_embed(
                                f"You need at least **{required_invites}** invites to join this giveaway.\n\n"
                                f"Your current invites: **{user_invites}**"
                            ),
                            ephemeral=True
                        )
                except discord.Forbidden:
                    
                    return await interaction.response.send_message(
                        embed=create_error_embed("Bot doesn't have permission to check invites. Please contact an administrator."),
                        ephemeral=True
                    )

            if 'participants' not in giveaway_data:
                giveaway_data['participants'] = []

            if interaction.user.id in giveaway_data['participants']:
                return await interaction.response.send_message(
                    embed=create_error_embed("You're already in this giveaway"),
                    ephemeral=True
                )

            giveaway_data['participants'].append(interaction.user.id)
            giveaways[actual_giveaway_id] = giveaway_data
            save_giveaways()

            giveaway_role_id = config.get('giveaway_role_id')
            if giveaway_role_id:
                giveaway_role = interaction.guild.get_role(giveaway_role_id)
                if giveaway_role:
                    member = interaction.guild.get_member(interaction.user.id)
                    await member.add_roles(giveaway_role)

            success_embed = create_success_embed(
                "Joined Giveaway",
                f"You've successfully joined the giveaway\n\n**Total participants:** `{len(giveaway_data['participants'])}`"
            )
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            asyncio.create_task(auto_delete_message(interaction))

            await update_giveaway_message(interaction.message, giveaway_data)

        except Exception as e:
            await interaction.response.send_message(
                embed=create_error_embed(f"An error occurred: {str(e)}"),
                ephemeral=True
            )

async def update_giveaway_message(message, giveaway_data):
    try:
        iran_time = datetime.fromtimestamp(giveaway_data['end_time'], IRAN_TZ)

        description = f"**Prize:** {giveaway_data['prize']}\n**Winners:** {giveaway_data['winners']}\n**Participants:** {len(giveaway_data.get('participants', []))}\n\n**Ends:** <t:{int(giveaway_data['end_time'])}:R>\n**Iran Time:** {iran_time.strftime('%Y/%m/%d - %H:%M')}"

        if giveaway_data.get('required_role_id'):
            role = message.guild.get_role(giveaway_data['required_role_id'])
            if role:
                description += f"\n\n**Only {role.mention} can join this giveaway**"

        if giveaway_data.get('required_invites', 0) > 0:
            description += f"\n\n**📨 Required Invites:** {giveaway_data['required_invites']}+"

        embed = discord.Embed(
            title="GIVEAWAY",
            description=description,
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )

        if giveaway_data.get('server_link'):
            embed.add_field(name="Server Link", value=giveaway_data['server_link'], inline=False)

        embed.set_footer(text=f"{CLAN_NAME} System - Click the button to join", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await message.edit(embed=embed)
    except:
        pass

@tree.command(name="giveaway", description="Create a giveaway")
@app_commands.describe(
    winners="Number of winners",
    duration="Duration (e.g., 30s, 5m, 1h, 1d, 1M)",
    prize="Prize for the giveaway",
    channel="Channel to send the giveaway",
    server_link="Server link (optional)",
    role="Required role to join (optional)",
    require_server_join="Require users to be in partner server (default: False)",
    required_invites="Minimum number of invites required to join (optional, default: 0)"
)
async def giveaway(
    interaction: discord.Interaction,
    winners: int,
    duration: str,
    prize: str,
    channel: discord.TextChannel,
    server_link: str = None,
    role: discord.Role = None,
    require_server_join: bool = False,
    required_invites: int = 0
):
    try:
        if not has_permission(interaction.user.id, "giveaway", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        
        if require_server_join and not server_link:
            return await interaction.response.send_message(
                embed=create_error_embed("Server link is required when 'require_server_join' is True"),
                ephemeral=True
            )

      
        if require_server_join and server_link:
            target_guild_id = await extract_guild_id_from_invite(server_link)
            if target_guild_id:
                target_guild = checker_bot.get_guild(target_guild_id)
                if not target_guild:
                    return await interaction.response.send_message(
                        embed=create_error_embed(
                            f"Checker Bot is not in the target server!\n\n"
                            f"Please invite Checker Bot to {server_link} first to enable server join verification.\n\n"
                            f"**Checker Bot Invite:** https://discord.com/api/oauth2/authorize?client_id={checker_bot.user.id}&permissions=0&scope=bot"
                        ),
                        ephemeral=True
                    )
            else:
                return await interaction.response.send_message(
                    embed=create_error_embed("Invalid server link format"),
                    ephemeral=True
                )

        try:
            duration_delta = parse_duration(duration)
        except:
            return await interaction.response.send_message(
                embed=create_error_embed("Invalid duration format! Use format like: 30s, 5m, 1h, 1d, 1M"),
                ephemeral=True
            )

        end_time = datetime.now(IRAN_TZ) + duration_delta
        iran_time_str = end_time.strftime('%Y/%m/%d - %H:%M')

        description = f"**Prize:** {prize}\n**Winners:** {winners}\n**Participants:** 0\n\n**Ends:** <t:{int(end_time.timestamp())}:R>\n**Iran Time:** {iran_time_str}"

        if role:
            description += f"\n\n**Only {role.mention} can join this giveaway**"

        if required_invites > 0:
            description += f"\n\n**📨 Required Invites:** {required_invites}+"

        embed = discord.Embed(
            title="GIVEAWAY",
            description=description,
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )

        if server_link:
            embed.add_field(name="Server Link", value=server_link, inline=False)

        embed.set_footer(text=f"{CLAN_NAME} System - Click the button to join", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        view = GiveawayView(0, role.id if role else None)

        giveaway_role_id = config.get('giveaway_role_id')
        giveaway_role = None
        if giveaway_role_id:
            giveaway_role = interaction.guild.get_role(giveaway_role_id)

        if giveaway_role:
            giveaway_msg = await channel.send(content=f"{giveaway_role.mention}", embed=embed, view=view)
        else:
            giveaway_msg = await channel.send(embed=embed, view=view)

        giveaway_data = {
            'message_id': giveaway_msg.id,
            'channel_id': channel.id,
            'guild_id': interaction.guild.id,
            'prize': prize,
            'winners': winners,
            'end_time': end_time.timestamp(),
            'server_link': server_link,
            'required_role_id': role.id if role else None,
            'require_server_join': require_server_join,
            'required_invites': required_invites,
            'participants': [],
            'ended': False,
            'created_by': interaction.user.id
        }

        giveaways[str(giveaway_msg.id)] = giveaway_data
        save_giveaways()

        success_embed = create_success_embed(
            "Giveaway Created",
            f"Giveaway has been created in {channel.mention}\n\n**Prize:** {prize}\n**Duration:** {duration}"
        )
        await interaction.response.send_message(embed=success_embed, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="giveawayend", description="End a giveaway manually")
@app_commands.describe(message_id="ID of the giveaway message")
async def giveaway_end(interaction: discord.Interaction, message_id: str):
    try:
        if not has_permission(interaction.user.id, "giveawayend", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        giveaway_data = giveaways.get(message_id)
        if not giveaway_data:
            return await interaction.response.send_message(
                embed=create_error_embed("Giveaway not found"),
                ephemeral=True
            )

        await interaction.response.send_message(
            embed=create_success_embed("Ending Giveaway", "Processing..."),
            ephemeral=True
        )

        await end_giveaway(message_id, giveaway_data)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="rwgiveaway", description="Reroll giveaway winner instantly")
@app_commands.describe(message_id="ID of the giveaway message")
async def reroll_giveaway(interaction: discord.Interaction, message_id: str):
    """Reroll/select new winners for an ended giveaway"""
    try:
        if not has_permission(interaction.user.id, "giveawayend", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        giveaway_data = giveaways.get(message_id)
        if not giveaway_data:
            return await interaction.response.send_message(
                embed=create_error_embed("Giveaway not found"),
                ephemeral=True
            )

        if not giveaway_data.get('ended', False):
            return await interaction.response.send_message(
                embed=create_error_embed("This giveaway hasn't ended yet. Use /giveawayend to end it first."),
                ephemeral=True
            )

        participants = giveaway_data.get('participants', [])
        if not participants:
            return await interaction.response.send_message(
                embed=create_error_embed("No participants in this giveaway"),
                ephemeral=True
            )

        
        previous_winners = giveaway_data.get('selected_winners', [])

        
        available = [p for p in participants if p not in previous_winners]
        if not available:
            available = participants  

        num_winners = min(giveaway_data['winners'], len(available))
        new_winners = random.sample(available, num_winners)

        
        giveaway_data['selected_winners'] = new_winners
        save_giveaways()

        
        for old_winner in previous_winners:
            if old_winner in pending_prizes and pending_prizes[old_winner]['giveaway_id'] == message_id:
                del pending_prizes[old_winner]

       
        for winner_id in new_winners:
            pending_prizes[winner_id] = {
                'giveaway_id': message_id,
                'prize': giveaway_data['prize'],
                'deadline': time.time() + 43200,  
                'accepted': False
            }

        
        channel = bot.get_channel(giveaway_data['channel_id'])
        if not channel:
            return await interaction.response.send_message(
                embed=create_error_embed("Giveaway channel not found"),
                ephemeral=True
            )

        try:
            message = await channel.fetch_message(int(message_id))
        except:
            return await interaction.response.send_message(
                embed=create_error_embed("Giveaway message not found"),
                ephemeral=True
            )

        
        winner_mentions = []
        for winner_id in new_winners:
            user = await bot.fetch_user(winner_id)
            if user:
                winner_mentions.append(user.mention)

       
        embed = discord.Embed(
            title="🎁 GIVEAWAY ENDED (REROLLED)",
            description=f"**Prize:** {giveaway_data['prize']}\n\n**New Winners:**\n" + "\n".join(winner_mentions) + f"\n\n⏰ Winners have **12 hours** to accept their prize by clicking the button below!",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_footer(text=f"{CLAN_NAME} System • Winners: Click 'Accept Prize' below", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await message.edit(embed=embed, view=PrizeAcceptView(new_winners, message_id))

        
        winner_pings = " ".join(winner_mentions)
        await channel.send(
            content=winner_pings,
            embed=create_success_embed(
                "🔄 Giveaway Rerolled!",
                f"**New Winners:**\n{winner_pings}\n\nYou won **{giveaway_data['prize']}**!\n\nClick the **Accept Prize** button above within 12 hours to claim your prize."
            )
        )

        await interaction.response.send_message(
            embed=create_success_embed(
                "Giveaway Rerolled",
                f"New winners have been selected:\n{winner_pings}"
            ),
            ephemeral=True
        )

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

class PrizeAcceptView(discord.ui.View):
    """View for accepting prize directly in giveaway channel"""
    def __init__(self, winner_ids, giveaway_id):
        super().__init__(timeout=None)
        self.winner_ids = winner_ids  
        self.giveaway_id = giveaway_id

    @discord.ui.button(label="🎁 Accept Prize", style=discord.ButtonStyle.green, custom_id="accept_prize")
    async def accept_prize_button(self, interaction: discord.Interaction, button: discord.ui.Button):
       
        giveaway_data = giveaways.get(self.giveaway_id)
        if not giveaway_data:
            return await interaction.response.send_message(
                embed=create_error_embed("Giveaway data not found"),
                ephemeral=True
            )

        
        current_winners = giveaway_data.get('selected_winners', [])
        if interaction.user.id not in current_winners:
            return await interaction.response.send_message(
                embed=create_error_embed("You are not a current winner of this giveaway. The giveaway may have been rerolled."),
                ephemeral=True
            )

        
        if interaction.user.id in pending_prizes and pending_prizes[interaction.user.id].get('accepted'):
            return await interaction.response.send_message(
                embed=create_error_embed("You have already accepted your prize"),
                ephemeral=True
            )

      
        pending_prizes[interaction.user.id] = {
            'giveaway_id': self.giveaway_id,
            'prize': giveaway_data['prize'],
            'deadline': time.time() + 43200, 
            'accepted': True
        }

        guild = interaction.guild
        member = interaction.user

       
        prize_category = None

        
        for category in guild.categories:
            if category.name == "Prize Tickets":
                prize_category = category
                break

        
        if not prize_category:
            prize_category_id = config.get('prize_category_id')
            if prize_category_id:
                prize_category = discord.utils.get(guild.categories, id=prize_category_id)

        
        if not prize_category:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }
            prize_category = await guild.create_category("Prize Tickets", overwrites=overwrites)

       
        ticket_channel_name = f"prize-{member.name.lower().replace('#', '')}"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        prize_role_id = config.get('prize_role_id')
        if prize_role_id:
            prize_role = guild.get_role(prize_role_id)
            if prize_role:
                overwrites[prize_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        ticket_channel = await guild.create_text_channel(
            ticket_channel_name,
            category=prize_category,
            overwrites=overwrites,
            topic=f"PRIZE • {member.display_name} • {interaction.channel.id}"
        )

        prize_embed = discord.Embed(
            title="🎁 Prize Ticket",
            description=f"Congratulations {member.mention}!\n\nYou won **{giveaway_data['prize']}** in the giveaway.\n\nPlease wait for staff to process your prize.",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        prize_embed.set_footer(text=f"{CLAN_NAME} System")

        mention_text = ""
        if prize_role_id:
            prize_role = guild.get_role(prize_role_id)
            if prize_role:
                mention_text = prize_role.mention

        await ticket_channel.send(content=mention_text, embed=prize_embed, view=PrizeTicketView())

     
        await interaction.response.send_message(
            embed=create_success_embed(
                "Prize Accepted",
                f"Your prize ticket has been created: {ticket_channel.mention}"
            ),
            ephemeral=True
        )

        
        await interaction.channel.send(
            embed=create_success_embed(
                "Prize Accepted",
                f"{member.mention} has accepted their prize! 🎉"
            )
        )

class PrizeTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        done_button = Button(label="Done", style=discord.ButtonStyle.success, custom_id="prize_done")
        done_button.callback = self.done_callback
        self.add_item(done_button)

    async def done_callback(self, interaction: discord.Interaction):
        prize_role_id = config.get('prize_role_id')
        if prize_role_id and not any(role.id == prize_role_id for role in interaction.user.roles):
            return await interaction.response.send_message("You don't have permission to use this button", ephemeral=True)

        topic_parts = interaction.channel.topic.split(" • ") if interaction.channel.topic else []
        if len(topic_parts) < 3:
            return await interaction.response.send_message("Could not find giveaway info", ephemeral=True)

        
        winner_name = topic_parts[1] if len(topic_parts) > 1 else "Unknown"

        giveaway_channel_id = int(topic_parts[2])
        giveaway_channel = bot.get_channel(giveaway_channel_id)

        if giveaway_channel:
            embed = discord.Embed(
                title="Prize Claimed ✅",
                description=f"**{winner_name}** has successfully claimed their prize!",
                color=EMBED_COLOR,
                timestamp=datetime.now(IRAN_TZ)
            )
            embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
            await giveaway_channel.send(embed=embed)

        await interaction.channel.delete()

async def end_giveaway(message_id, giveaway_data):
    """End giveaway and select winners - NO DM, only in-channel accept button"""
    try:
        channel = bot.get_channel(giveaway_data['channel_id'])
        if not channel:
            return

        try:
            message = await channel.fetch_message(int(message_id))
        except:
            return

        participants = giveaway_data.get('participants', [])

        if not participants:
            embed = discord.Embed(
                title="🎁 GIVEAWAY ENDED",
                description=f"**Prize:** {giveaway_data['prize']}\n\n**No one participated in this giveaway**",
                color=EMBED_COLOR,
                timestamp=datetime.now(IRAN_TZ)
            )
            embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
            await message.edit(embed=embed, view=None)
            giveaway_data['ended'] = True
            save_giveaways()
            return

        num_winners = min(giveaway_data['winners'], len(participants))
        winners = random.sample(participants, num_winners)

        
        giveaway_data['selected_winners'] = winners
        giveaway_data['ended'] = True
        save_giveaways()

        
        for winner_id in winners:
            pending_prizes[winner_id] = {
                'giveaway_id': message_id,
                'prize': giveaway_data['prize'],
                'deadline': time.time() + 43200,  
                'accepted': False
            }

        winner_mentions = []
        for winner_id in winners:
            user = await bot.fetch_user(winner_id)
            if user:
                winner_mentions.append(user.mention)

        embed = discord.Embed(
            title="🎁 GIVEAWAY ENDED",
            description=f"**Prize:** {giveaway_data['prize']}\n\n**Winners:**\n" + "\n".join(winner_mentions) + f"\n\n⏰ Winners have **12 hours** to accept their prize by clicking the button below!",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_footer(text=f"{CLAN_NAME} System • Winners: Click 'Accept Prize' below", icon_url=bot.user.avatar.url if bot.user.avatar else None)

       
        await message.edit(embed=embed, view=PrizeAcceptView(winners, message_id))

       
        winner_pings = " ".join(winner_mentions)
        try:
            announcement = await channel.send(
                content=winner_pings,
                embed=create_success_embed(
                    "🎉 Congratulations!",
                    f"{winner_pings}\n\nYou won **{giveaway_data['prize']}**!\n\nClick the **Accept Prize** button above within 12 hours to claim your prize."
                )
            )
            print(f"✅ Giveaway {message_id} ended successfully. Announcement sent: {announcement.id}")
        except Exception as announce_error:
            print(f"⚠️ Failed to send giveaway announcement: {announce_error}")

    except Exception as e:
        print(f'End giveaway error: {e}')
        import traceback
        traceback.print_exc()

@tasks.loop(seconds=30)
async def check_giveaways():
    try:
        current_time = datetime.now(IRAN_TZ).timestamp()

        for message_id, giveaway_data in list(giveaways.items()):
            if giveaway_data.get('ended', False):
                continue

            if current_time >= giveaway_data['end_time']:
                await end_giveaway(message_id, giveaway_data)
    except Exception as e:
        print(f'Check giveaways error: {e}')

@tasks.loop(minutes=10)
async def check_participant_membership():
    """Check every 10 minutes if giveaway participants are still in partner servers"""
    try:
        for message_id, giveaway_data in list(giveaways.items()):
          
            if giveaway_data.get('ended', False):
                continue

           
            if not giveaway_data.get('require_server_join', False):
                continue

            server_link = giveaway_data.get('server_link')
            if not server_link:
                continue

           
            target_guild_id = await extract_guild_id_from_invite(server_link)
            if not target_guild_id:
                continue

            target_guild = checker_bot.get_guild(target_guild_id)
            if not target_guild:
                print(f"Checker Bot not in guild {target_guild_id} for giveaway {message_id}")
                continue

         
            participants = giveaway_data.get('participants', [])
            removed_users = []

            for user_id in participants:
                target_member = target_guild.get_member(user_id)
                if not target_member:
                    
                    removed_users.append(user_id)

            
            if removed_users:
                giveaway_data['participants'] = [uid for uid in participants if uid not in removed_users]
                giveaways[message_id] = giveaway_data
                save_giveaways()

                
                try:
                    guild = bot.get_guild(giveaway_data['guild_id'])
                    if guild:
                        channel = guild.get_channel(giveaway_data['channel_id'])
                        if channel:
                            message = await channel.fetch_message(int(message_id))
                            if message:
                                await update_giveaway_message(message, giveaway_data)
                except Exception as e:
                    print(f"Error updating giveaway message {message_id}: {e}")

                print(f"Removed {len(removed_users)} users from giveaway {message_id} (left partner server)")

    except Exception as e:
        print(f'Check participant membership error: {e}')

@tasks.loop(minutes=10)
async def check_prize_deadlines():
    """Check every 10 minutes if any winner's 12-hour deadline has passed"""
    try:
        current_time = time.time()
        expired_winners = []

        
        for user_id, prize_data in list(pending_prizes.items()):
            if prize_data['accepted']:
                continue  

            if current_time >= prize_data['deadline']:
                expired_winners.append((user_id, prize_data))

        
        for user_id, prize_data in expired_winners:
            giveaway_id = prize_data['giveaway_id']
            giveaway_data = giveaways.get(giveaway_id)

            if not giveaway_data:
                del pending_prizes[user_id]
                continue

            
            channel = bot.get_channel(giveaway_data['channel_id'])
            if not channel:
                del pending_prizes[user_id]
                continue

           
            try:
                expired_user = await bot.fetch_user(user_id)
            except:
                expired_user = None

            
            del pending_prizes[user_id]

            
            participants = giveaway_data.get('participants', [])
            current_winners = giveaway_data.get('selected_winners', [])
            available = [p for p in participants if p not in current_winners]

            if not available:
                
                await channel.send(
                    embed=create_error_embed(
                        "⏰ Prize Expired",
                        f"{expired_user.mention if expired_user else 'Winner'} didn't accept the prize within 12 hours. No more participants available for reroll."
                    )
                )
                continue

            
            new_winner_id = random.choice(available)
            new_winner = await bot.fetch_user(new_winner_id)

            
            giveaway_data['selected_winners'].remove(user_id)
            giveaway_data['selected_winners'].append(new_winner_id)
            save_giveaways()

            
            pending_prizes[new_winner_id] = {
                'giveaway_id': giveaway_id,
                'prize': giveaway_data['prize'],
                'deadline': time.time() + 43200,  
                'accepted': False
            }

           
            try:
                message = await channel.fetch_message(int(giveaway_id))

                
                all_winners = giveaway_data.get('selected_winners', [])
                winner_mentions = []
                for winner_id in all_winners:
                    user = await bot.fetch_user(winner_id)
                    if user:
                        winner_mentions.append(user.mention)

                embed = discord.Embed(
                    title="🎁 GIVEAWAY ENDED",
                    description=f"**Prize:** {giveaway_data['prize']}\n\n**Winners:**\n" + "\n".join(winner_mentions) + f"\n\n⏰ Winners have **12 hours** to accept their prize by clicking the button below!",
                    color=EMBED_COLOR,
                    timestamp=datetime.now(IRAN_TZ)
                )
                embed.set_footer(text=f"{CLAN_NAME} System • Winners: Click 'Accept Prize' below", icon_url=bot.user.avatar.url if bot.user.avatar else None)

                await message.edit(embed=embed, view=PrizeAcceptView(all_winners, giveaway_id))
            except Exception as e:
                print(f"Error updating giveaway message after reroll: {e}")

            
            await channel.send(
                content=new_winner.mention,
                embed=create_success_embed(
                    "⏰ Automatic Reroll",
                    f"{expired_user.mention if expired_user else 'Previous winner'} didn't accept within 12 hours.\n\n**New Winner:** {new_winner.mention}\n\nClick the **Accept Prize** button above within 12 hours!"
                )
            )

            print(f"Auto-rerolled giveaway {giveaway_id}: {user_id} -> {new_winner_id}")

    except Exception as e:
        print(f'Check prize deadlines error: {e}')

@tree.command(name="nick", description=f"Set or remove your nickname with {CLAN_NAME} prefix")
@app_commands.describe(nickname="Your new nickname (max 15 characters, leave empty to remove)")
async def nick(interaction: discord.Interaction, nickname: str = None):
    try:
        member = interaction.user
        user_id = str(member.id)

       
        if not nickname or nickname.strip() == "":
            if user_id in user_nicknames:
                del user_nicknames[user_id]
                save_nicknames()

                
                new_nickname = build_nickname(member, "")

                try:
                    await member.edit(nick=new_nickname if new_nickname.strip() else None)

                    success_embed = create_success_embed(
                        "Nickname Removed",
                        f"Your custom nickname has been removed.\nYour display name is now: **{member.display_name}**"
                    )
                    await interaction.response.send_message(embed=success_embed, ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message(
                        embed=create_error_embed("I don't have permission to change your nickname"),
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message(
                    embed=create_error_embed("You don't have a custom nickname set"),
                    ephemeral=True
                )
            return

        
        if len(nickname) > 15:
            return await interaction.response.send_message(
                embed=create_error_embed("Nickname must be 15 characters or less"),
                ephemeral=True
            )

       
        user_nicknames[user_id] = nickname
        save_nicknames()

        new_nickname = build_nickname(member, nickname)

        try:
            await member.edit(nick=new_nickname)

            success_embed = create_success_embed(
                "Nickname Changed",
                f"Your nickname has been set to: **{new_nickname}**"
            )
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=create_error_embed("I don't have permission to change your nickname"),
                ephemeral=True
            )

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tasks.loop(seconds=10)
async def update_nicknames():
    try:
        for guild in bot.guilds:
            for user_id, suffix in user_nicknames.items():
                try:
                    member = guild.get_member(int(user_id))
                    if member and not member.bot:
                        new_nickname = build_nickname(member, suffix)
                        if member.display_name != new_nickname:
                            try:
                                await member.edit(nick=new_nickname)
                            except:
                                pass
                except:
                    continue
    except Exception as e:
        print(f'Update nicknames error: {e}')

@tree.command(name="jaccept", description=f"Add a user to {CLAN_NAME} team")
@app_commands.describe(user="The user to add to the team")
async def jaccept(interaction: discord.Interaction, user: discord.Member):
    try:
        if not has_permission(interaction.user.id, "jaccept", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        if "jyx-team" not in interaction.channel.name.lower() and "ticket" not in interaction.channel.name.lower():
            return await interaction.response.send_message(
                embed=create_error_embed(f"This command can only be used in a {CLAN_NAME} Team ticket channel"),
                ephemeral=True
            )

        team_role_id = config.get('roles', {}).get('team')
        if not team_role_id:
            return await interaction.response.send_message(
                embed=create_error_embed("Team role not configured in config.json under roles->team"),
                ephemeral=True
            )

        team_role = interaction.guild.get_role(team_role_id)
        if not team_role:
            return await interaction.response.send_message(
                embed=create_error_embed("Team role not found"),
                ephemeral=True
            )

        await user.add_roles(team_role)

        accept_counts[user.id] += 1
        ch_id = interaction.channel.id
        if ch_id in claimed_tickets:
            claimer_id = claimed_tickets[ch_id]
            claim_counts[claimer_id] += 1
            save_tickets()
            await check_auto_rankup(claimer_id, interaction.guild)

        success_embed = create_success_embed(
            "Team Member Added",
            f"**{user.mention}** has been added to the {CLAN_NAME} team"
        )
        await interaction.response.send_message(embed=success_embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="jdecline", description=f"Decline a Join{CLAN_NAME}Team application with cooldown")
async def jdecline(interaction: discord.Interaction):
    try:
        if not has_permission(interaction.user.id, "jdecline", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        if "jyx-team" not in interaction.channel.name.lower() and "ticket" not in interaction.channel.name.lower():
            return await interaction.response.send_message(
                embed=create_error_embed(f"This command can only be used in a {CLAN_NAME} Team ticket channel"),
                ephemeral=True
            )

        topic_parts = interaction.channel.topic.split(" • ") if interaction.channel.topic else []
        if len(topic_parts) < 2:
            return await interaction.response.send_message(
                embed=create_error_embed("Could not identify ticket creator"),
                ephemeral=True
            )
        creator_name = topic_parts[1]
        creator = discord.utils.get(interaction.guild.members, display_name=creator_name) if creator_name else None
        if not creator:
            return await interaction.response.send_message(
                embed=create_error_embed("Could not identify the ticket creator"),
                ephemeral=True
            )

        user_id = creator.id
        decline_counts[user_id] += 1
        cooldown_days = {1: 3, 2: 7, 3: 14}.get(decline_counts[user_id], 14)
        cooldown_end = time.time() + (cooldown_days * 86400)
        cooldowns[user_id] = cooldown_end

        ch_id = interaction.channel.id
        if ch_id in claimed_tickets:
            claimer_id = claimed_tickets[ch_id]
            claim_counts[claimer_id] += 1
            save_tickets()
            await check_auto_rankup(claimer_id, interaction.guild)

        save_tickets()

        embed = discord.Embed(
            title="Application Declined",
            description=f"{creator.mention}'s {CLAN_NAME} Team application declined by {interaction.user.mention}\n\n**Cooldown:** {cooldown_days} days",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="team", description=f"View all {CLAN_NAME} team members")
async def team(interaction: discord.Interaction):
    try:
        team_role_id = config.get('roles', {}).get('team')
        if not team_role_id:
            return await interaction.response.send_message(
                embed=create_error_embed("Team role not configured in config.json under roles->team"),
                ephemeral=True
            )

        team_role = interaction.guild.get_role(team_role_id)
        if not team_role:
            return await interaction.response.send_message(
                embed=create_error_embed("Team role not found"),
                ephemeral=True
            )

        team_members = [m for m in team_role.members if not m.bot]

        team_tester_role_id = config.get('roles', {}).get('team_tester')
        team_tester_manager_role_id = config.get('roles', {}).get('tester_manager')
        senior_tester_role_id = config.get('roles', {}).get('senior_tester')
        jr_tester_role_id = config.get('roles', {}).get('jr_tester')

        managers = []
        senior_testers = []
        team_testers = []
        jr_testers = []
        regular = []

        for m in team_members:
            if team_tester_manager_role_id and any(r.id == team_tester_manager_role_id for r in m.roles):
                managers.append(m)
            elif senior_tester_role_id and any(r.id == senior_tester_role_id for r in m.roles):
                senior_testers.append(m)
            elif team_tester_role_id and any(r.id == team_tester_role_id for r in m.roles):
                team_testers.append(m)
            elif jr_tester_role_id and any(r.id == jr_tester_role_id for r in m.roles):
                jr_testers.append(m)
            else:
                regular.append(m)

        if not team_members:
            return await interaction.response.send_message(
                embed=create_error_embed("No team members found"),
                ephemeral=True
            )

        embed = discord.Embed(
            title=f"{CLAN_NAME} Team Members",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )

        if managers:
            embed.add_field(name="<:SeniorTester:1423135937747091516> Tester Managers", value="\n".join([m.mention for m in managers]), inline=False)
        if senior_testers:
            embed.add_field(name="<:SeniorTester2:1423135961059164284> Senior Testers", value="\n".join([m.mention for m in senior_testers]), inline=False)
        if team_testers:
            embed.add_field(name="<:Tester:1423135883946754140> Team Testers", value="\n".join([m.mention for m in team_testers]), inline=False)
        if jr_testers:
            embed.add_field(name="<:JrTester:1429006645891174431> Jr Testers", value="\n".join([m.mention for m in jr_testers]), inline=False)
        if regular:
            embed.add_field(name="<:JyXManager:1429007421023457370> Team Members", value="\n".join([m.mention for m in regular]), inline=False)

        embed.set_footer(text=f"Total: {len(team_members)} members - {CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="addpoints", description="Add points to a user")
@app_commands.describe(user="The user to add points to", amount="Amount of points to add")
async def addpoints(interaction: discord.Interaction, user: discord.Member, amount: int):
    try:
        if not has_permission(interaction.user.id, "addpoints", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        if amount <= 0:
            return await interaction.response.send_message(
                embed=create_error_embed("Amount must be greater than 0"),
                ephemeral=True
            )

        user_id = str(user.id)
        if user_id not in points_data:
            points_data[user_id] = 0

        points_data[user_id] += amount
        save_points()

        await update_user_nickname(user)

        success_embed = create_success_embed(
            "Points Added",
            f"Added **{amount}** points to {user.mention}\n\n**New balance:** {points_data[user_id]} points"
        )
        await interaction.response.send_message(embed=success_embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="removepoints", description="Remove points from a user")
@app_commands.describe(user="The user to remove points from", amount="Amount of points to remove")
async def removepoints(interaction: discord.Interaction, user: discord.Member, amount: int):
    try:
        if not has_permission(interaction.user.id, "removepoints", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        if amount <= 0:
            return await interaction.response.send_message(
                embed=create_error_embed("Amount must be greater than 0"),
                ephemeral=True
            )

        user_id = str(user.id)
        if user_id not in points_data:
            points_data[user_id] = 0

        points_data[user_id] = max(0, points_data[user_id] - amount)
        save_points()

        await update_user_nickname(user)

        success_embed = create_success_embed(
            "Points Removed",
            f"Removed **{amount}** points from {user.mention}\n\n**New balance:** {points_data[user_id]} points"
        )
        await interaction.response.send_message(embed=success_embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="modifypoints", description="Set a user's points to a specific amount")
@app_commands.describe(user="The user to modify points for", amount="New amount of points")
async def modifypoints(interaction: discord.Interaction, user: discord.Member, amount: int):
    try:
        if not has_permission(interaction.user.id, "modifypoints", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        if amount < 0:
            return await interaction.response.send_message(
                embed=create_error_embed("Amount cannot be negative"),
                ephemeral=True
            )

        user_id = str(user.id)
        old_amount = points_data.get(user_id, 0)
        points_data[user_id] = amount
        save_points()

        await update_user_nickname(user)

        success_embed = create_success_embed(
            "Points Modified",
            f"Set {user.mention}'s points to **{amount}**\n\n**Old balance:** {old_amount} points\n**New balance:** {amount} points"
        )
        await interaction.response.send_message(embed=success_embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="clearpoints", description="Clear all points from a user")
@app_commands.describe(user="The user to clear points from")
async def clearpoints(interaction: discord.Interaction, user: discord.Member):
    try:
        if not has_permission(interaction.user.id, "clearpoints", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        user_id = str(user.id)
        old_amount = points_data.get(user_id, 0)
        points_data[user_id] = 0
        save_points()

        await update_user_nickname(user)

        success_embed = create_success_embed(
            "Points Cleared",
            f"Cleared all points from {user.mention}\n\n**Previous balance:** {old_amount} points"
        )
        await interaction.response.send_message(embed=success_embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="leaderboard", description="View the points leaderboard")
async def leaderboard(interaction: discord.Interaction):
    try:
        if not points_data:
            return await interaction.response.send_message(
                embed=create_error_embed("No one has any points yet"),
                ephemeral=True
            )

        sorted_users = sorted(points_data.items(), key=lambda x: x[1], reverse=True)[:10]

        embed = discord.Embed(
            title="Points Leaderboard",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )

        leaderboard_text = ""
        for i, (user_id, points) in enumerate(sorted_users, 1):
            try:
                user = await bot.fetch_user(int(user_id))
                medal = "" if i == 1 else "" if i == 2 else "" if i == 3 else f"**{i}.**"
                leaderboard_text += f"{medal} {user.mention} - **{points}** points\n"
            except:
                continue

        embed.description = leaderboard_text
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="rules", description="View server rules")
async def rules(interaction: discord.Interaction):
    try:
        embed = discord.Embed(
            title=f"{CLAN_NAME} Server Rules",
            description="Please Read the following rules :",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )

        persian_rules = """1 - این تیم یک تیم دوستانه است پس با تمام ممبر ها با احترام برخورد کنید
2 - با تیم استف سرور دیسکورد جیکس با احترام برخورد کنید
3 - به هیچ عنوان هیچ توهینی به اعضای خانواده ی هیچ یک از ممبر های سرور دیسکورد جیکس نکنید
4 - از تگ دادن بی دلیل خودداری کنید
5 - از اسپم دادن گیف/مسیج/ویدیو/عکس خودداری کنید
6 - از انتشار هر گونه محتوای پورنوگرافی خودداری کنید"""

        english_rules = f"""1 - This team is a friendly team, so treat all members with respect.
2 - Treat the {CLAN_NAME} Discord server staff team with respect.
3 - Under no circumstances insult the family members of any {CLAN_NAME} Discord server's member.
4 - Avoid tagging without reason.
5 - Avoid spamming gifs/messages/videos/pictures.
6 - Do not share any kind of pornographic content."""

        embed.add_field(name="Persian", value=persian_rules, inline=False)
        embed.add_field(name="English", value=english_rules, inline=False)
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="info", description=f"Information on how to join {CLAN_NAME} team")
async def info(interaction: discord.Interaction):
    try:
        embed = discord.Embed(
            title=f"Join {CLAN_NAME} Team",
            description="Information on how to join our team",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )

        persian_info = """جهت عضویت در تیم جیکس شما باید از طریق باز کردن تیکت برای عضویت اپلای بدید.
وقتی که یک تستر تیکت شمارو کلیم کرد با هماهمنگی یک تایم مناسب جهت تست گرفتن از شما انتخای میکنید.
حالا شما باید در 2 مچ آنرنکد در دو مود ساید و تاپ اسکیل خودتون رو به تستر ما نشون بدید.
این 2 مچ به صورتی برگذار میشه که هرکسی زودتر به 5 کیل برسه برنده میشه.
توجه داشته باشید که همه چیز به کیل نیست و شما باید در این تست اسکیل خودتون رو به تستر ما نشون بدید به طوری که حتی اگر تستر مارو 5-0 بردید باز هم درصورتی که تستر تشخیص بده که اسکیل کافی رو ندارید میتونه شمارو دیکلاین کنه.
درصورتی که تست رو دیکلاین شدید میتونید درخواست کنید که یک ووت برای شما برگزار بشه به صورتی که یک ووت در چنلی که فقط افرادی که در جیکس عضو هستند به آن دسترسی دارند برگزار خواهد شد و اگر اکثریت افراد ووت بدن که شما باید وارد تیم بشید شما اکسپت خواهید شد.
اما درصورتی که اکثریت افراد ووت بدن که شما نباید وارد تیم بشید شما دیکلاین خواهید شد.
درصورتی که شما دیکلاین بشید تا 3 روز توانایی تست مجدد نخواهید داشت.
درصورتی که شما برای بار دوم دیکلاین بشید تا 7 روز توانایی تست مجدد نخواهید داشت.
درصورتی که شما برای بار سوم دیکلاین بشید تا 14 روز توانایی تست مجدد نخواهید داشت.
مهم ترین چیز در این تست اینه که شما لجیت باشید و از هیچ گونه (ModifiedClient/HackClient) ای استفاده نکنید. درصورتی که تستر به شما مشکوک بشه که دارید از هرگونه ابزار غیر مجاز مانند اتوکلیکر استفاده میکنید شما توسط اسکرین شیرر های ما اس اس خواهید شد. و درصورتی که تیم ما چیت یا هرگونه ابزار غیرمجاز از شما پیدا کنه شما به مدت زمان مشخصی بلک لیست خواهید شد"""

        english_info = f"""To apply for membership in the {CLAN_NAME} team you must apply by opening a ticket.
When a tester accepts your ticket they will coordinate and pick a suitable time with you to run the test.
You must then show your skills to our tester in two unranked matches (Top and Side).
These two matches are played so that whoever reaches 5 kills first wins.

Please note that it's not all about kills you must demonstrate your skill during this test. Even if you beat our tester 5-0, if the tester determines you do not have sufficient skill they can decline you.

If the tester declines the test you may request a vote. The vote will be held in a channel that only people who are members of {CLAN_NAME} can access, and if the majority vote that you should join the team you will be accepted.
If your vote is also declined you will have a 3-day cooldown before you can test again.
If you are declined on the second test the cooldown will be 7 days.
If you are declined on the third test the cooldown will be 14 days.

The most important thing in this test is that you are legit and do not use any Modified Client or Hack Client. If the tester suspects you of using any sort of cheats, our ssers will ss you. If our staff find evidence that you cheated, you will be completely blacklisted for a specified period of time."""

        embed.add_field(name="Persian", value=persian_info[:1024], inline=False)
        if len(persian_info) > 1024:
            embed.add_field(name="", value=persian_info[1024:], inline=False)
        embed.add_field(name="English", value=english_info[:1024], inline=False)
        if len(english_info) > 1024:
            embed.add_field(name="", value=english_info[1024:], inline=False)
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="trules", description="View tester rules (Testers only)")
async def trules(interaction: discord.Interaction):
    try:
        tester_role_id = config.get('tester_role_id')
        if not tester_role_id:
            return await interaction.response.send_message(
                embed=create_error_embed("Tester role not configured"),
                ephemeral=True
            )

        if not any(role.id == tester_role_id for role in interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("This command is only for testers"),
                ephemeral=True
            )

        embed = discord.Embed(
            title="Tester Rules",
            description="Please read the following rules :",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )

        persian_rules = """1- اولین و مهم ترین قانون اینه که باید با فردی که درحال تست دادن هست با احترام رفتار کنید اگر دیدید هر راش داره شمارو میزنه بجای اینکه توی چت بهش بی احترامی کنید بدون گفتن هیچ چیزه دیگه ای بنویسید Dont Log {UserName}

2- حتما ریزالت هر تست رو توی چنل مربوطه بنویسید درصورتی که تستی بگیرید و ریزالت رو در چنل ریزالت ننویسید وارن دریافت خواهید کرد و با گرفتن 3 وارن دیموت خواهید شد

3- به هیچ عنوان تیکت تست رو بعد از کلوز دادن دیلیت نکنید

4- اگر تستر منیجری آنلاین بود حتما قبل از اکسپت کردن کسی با تستر منیجر هماهنگ کنید

5- وقتی یک تستر به تیکتی جواب میده به این معناست که اون فرد اون تیکت رو اکسپت کرده و بعد از اون هیچ تستری جز تستر منیجر حق صحبت در اون چنل رو نداره مگر تستری که تیکت رو اکسپت کرده به دلایلی نتونه تست رو بگیره و تیکت رو بسپره به تستر دیگری

6- قبل از تست گرفتن حتما چنل guide رو بخونید"""

        english_rules = """1- The first and most important rule is that you must treat the person taking the test with respect.
If you see that the person keeps rushing and defeating you, instead of being disrespectful in chat, simply type:
Dont Log {UserName} and say nothing else.

2- You must post the results of every test in the results channel.
If you conduct a test but fail to post the result there, you will receive a warn, and after three warns, you will be demoted.

3- Never delete a ticket after closing it.

4- If a Tester Manager is online, you must coordinate with them before accepting anyone.

5- When a tester responds to a ticket, it means that they have accepted that ticket.
After that, no other tester is allowed to speak in that channel except the Tester Manager,
unless the tester who accepted the ticket cannot take the test and hands it over to another tester.

6- Before conducting any test, make sure to read the guide channel."""

        embed.add_field(name="Persian", value=persian_rules[:1024], inline=False)
        if len(persian_rules) > 1024:
            embed.add_field(name="", value=persian_rules[1024:], inline=False)
        embed.add_field(name="English", value=english_rules[:1024], inline=False)
        if len(english_rules) > 1024:
            embed.add_field(name="", value=english_rules[1024:], inline=False)
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="tguide", description="View tester guide (Testers only)")
async def tguide(interaction: discord.Interaction):
    try:
        tester_role_ids = config.get('roles', {}).get('tester', [])
        if not tester_role_ids:
            await interaction.response.send_message(
                embed=create_error_embed("Tester role not configured"),
                ephemeral=True
            )
            asyncio.create_task(auto_delete_message(interaction))
            return

        
        user_role_ids = [role.id for role in interaction.user.roles]
        has_tester_role = any(role_id in user_role_ids for role_id in tester_role_ids)

        if not has_tester_role:
            await interaction.response.send_message(
                embed=create_error_embed("This command is only for testers"),
                ephemeral=True
            )
            asyncio.create_task(auto_delete_message(interaction))
            return

        embed = discord.Embed(
            title="Tester Guide",
            description="Simple guide for testers on how to test new players",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )

        persian_guide = """اول از همه باید بدونید که مهم ترین چیز توی تست ها اینه که اسکیل فرد رو درنظر بگیرید و صرفا به تعداد کیل ها اهمیت ندید
حتی اگر 5-0 ازشون باختید و یا برعکس باز هم تصمیم شماست که آیا اسکیل کافی رو دارند یا نه
تست در دو مود ساید و تاپ انجام میشه :
ساید - مپ ترجیها اینویژن - فرست تو 5
تاپ - مپ ترجیها آرچوی - فرست تو 5
درصورتی که بنظرتون هنوز نتونستید سطح پلی فرد رو بسنجید یک گیم دیگه هم باهاشون برید :
لومید - مپ ترجیها پالادین/آرتمیس - فرست تو 5"""

        english_guide = """First of all, you should know that the most important thing in the tests is to consider the player's skill level, not just the number of kills.
Even if you lose 0-5 or win 5-0, it's still your decision whether the player has enough skill or not.

The test is done in two modes: Side and Top

Side - Preferred map: Invasion - First to 5

Top - Preferred map: Archway - First to 5

If you feel that you still haven't been able to properly evaluate the player's skill level, play one more game with them:

Lowmid - Preferred map: Paladin/Artemis - First to 5"""

        embed.add_field(name="Persian", value=persian_guide, inline=False)
        embed.add_field(name="English", value=english_guide, inline=False)
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )
        asyncio.create_task(auto_delete_message(interaction))

class TicketSelect(View):
    def __init__(self):
        super().__init__(timeout=None)
        options = [
            discord.SelectOption(label="Team Tester Apply", description="Apply to be a team tester", emoji="👤"),
            discord.SelectOption(label=f"{CLAN_NAME} Team", description=f"Apply for {CLAN_NAME} Team", emoji="✨"),
            discord.SelectOption(label="Support", description="Get technical support", emoji="🌐")
        ]
        select = Select(custom_id="ticket_select", placeholder="Make a selection", options=options, min_values=1, max_values=1)
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.response.is_done():
            return

        
        await interaction.response.defer(ephemeral=True)

        selected_option = interaction.data['values'][0]
        emoji_map = {"Team Tester Apply": "👤", f"{CLAN_NAME} Team": "✨", "Support": "🌐"}

        
        user_ticket_channels = [
            ch_id for ch_id in ticket_creators
            if ticket_creators.get(ch_id) == interaction.user.id
        ]

        
        user_has_valid_ticket = False
        for ch_id in user_ticket_channels:
            channel = interaction.guild.get_channel(ch_id)
            if channel:
                user_has_valid_ticket = True
                break
            else:
                
                del ticket_creators[ch_id]
                if ch_id in claimed_tickets:
                    del claimed_tickets[ch_id]
                save_tickets()

        if user_has_valid_ticket:
            await interaction.followup.send(
                embed=create_error_embed("You already have an open ticket Please close it before opening a new one"),
                ephemeral=True
            )
            asyncio.create_task(auto_delete_message(interaction))
            return

        if selected_option == f"{CLAN_NAME} Team" and interaction.user.id in cooldowns:
            remaining = cooldowns[interaction.user.id] - time.time()
            if remaining > 0:
                days = int(remaining // 86400)
                hours = int((remaining % 86400) // 3600)
                minutes = int((remaining % 3600) // 60)

                embed = discord.Embed(
                    title="Cooldown Active",
                    description=f"You must wait before opening another {CLAN_NAME} Team ticket",
                    color=EMBED_COLOR,
                    timestamp=datetime.now(IRAN_TZ)
                )
                embed.add_field(name="Remaining Time", value=f"{days} days, {hours} hours, {minutes} minutes", inline=False)
                embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

                await interaction.followup.send(embed=embed, ephemeral=True)
                asyncio.create_task(auto_delete_message(interaction))
                return

        for attempt in range(3):
            try:
               
                await create_ticket_deferred(interaction, selected_option, emoji_map.get(selected_option, ""), interaction.user.display_name, "")
                return
            except discord.errors.NotFound as e:
                if attempt < 2:
                    await asyncio.sleep(1)
                continue
            except Exception as e:
                print(f"Failed to create ticket: {e}")
                import traceback
                traceback.print_exc()
                await interaction.followup.send(embed=create_error_embed(f"Failed to create ticket: {str(e)}"), ephemeral=True)
                asyncio.create_task(auto_delete_message(interaction))
                return
        await interaction.followup.send(embed=create_error_embed("Interaction expired Please try again"), ephemeral=True)
        asyncio.create_task(auto_delete_message(interaction))

class TicketManagementView(View):
    def __init__(self, ticket_channel=None):
        super().__init__(timeout=None)
        self.ticket_channel = ticket_channel
        self.claim_button = Button(label="Claim", style=discord.ButtonStyle.success, custom_id="claim_ticket")
        self.release_button = Button(label="Release", style=discord.ButtonStyle.secondary, custom_id="release_ticket", disabled=True)
        self.close_button = Button(label="Close", style=discord.ButtonStyle.danger, custom_id="close_ticket")

        self.claim_button.callback = self.claim_callback
        self.release_button.callback = self.release_callback
        self.close_button.callback = self.close_callback

        self.add_item(self.claim_button)
        self.add_item(self.release_button)
        self.add_item(self.close_button)

        if ticket_channel and ticket_channel.id in claimed_tickets:
            self.update_claim_buttons(disabled_claim=True, disabled_release=False)

    def update_claim_buttons(self, disabled_claim=True, disabled_release=True):
        self.claim_button.disabled = disabled_claim
        self.release_button.disabled = disabled_release

    async def claim_callback(self, interaction: discord.Interaction):
        
        await interaction.response.defer()

        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.followup.send(embed=create_error_embed("Bot lacks permission to manage channels"), ephemeral=True)
            asyncio.create_task(auto_delete_message(interaction))
            return

        ch_id = interaction.channel.id

        creator_id = ticket_creators.get(ch_id)
        if creator_id and creator_id == interaction.user.id:
            await interaction.followup.send(embed=create_error_embed("You cannot claim your own ticket"), ephemeral=True)
            asyncio.create_task(auto_delete_message(interaction))
            return

        if ch_id in claimed_tickets:
            claimer = bot.get_user(claimed_tickets[ch_id])
            await interaction.followup.send(embed=create_error_embed(f"This ticket is already claimed by {claimer.mention if claimer else 'someone'}"), ephemeral=True)
            asyncio.create_task(auto_delete_message(interaction))
            return

        claimed_tickets[ch_id] = interaction.user.id
        self.update_claim_buttons(disabled_claim=True, disabled_release=False)

        overwrites = interaction.channel.overwrites.copy()
        
        overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(read_messages=False, send_messages=False, view_channel=False)

       
        overwrites[interaction.guild.me] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True, manage_channels=True)

        
        if creator_id:
            creator = interaction.guild.get_member(creator_id)
            if creator:
                overwrites[creator] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)

        
        overwrites[interaction.user] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)

        try:
            await interaction.channel.edit(overwrites=overwrites)
        except discord.errors.Forbidden:
            await interaction.followup.send(embed=create_error_embed("Bot lacks permission to edit channel permissions"), ephemeral=True)
            asyncio.create_task(auto_delete_message(interaction))
            del claimed_tickets[ch_id]
            save_tickets()
            return

        cmd_hint = ""
        if "jyx-team" in interaction.channel.name.lower():
            if has_permission(interaction.user.id, 'jaccept', interaction.user.roles) and has_permission(interaction.user.id, 'jdecline', interaction.user.roles):
                cmd_hint = "\n\nUse `/add <user>`, `/jaccept <user>`, or `/jdecline` to manage this ticket."
            elif has_permission(interaction.user.id, 'jaccept', interaction.user.roles):
                cmd_hint = "\n\nUse `/add <user>` or `/jaccept <user>` to manage this ticket."
            else:
                cmd_hint = "\n\nUse `/add <user>` to add more users to this ticket."
        else:
            cmd_hint = "\n\nUse `/add <user>` to add more users to this ticket."

        embed = discord.Embed(
            title="Ticket Claimed",
            description=f"Ticket claimed by {interaction.user.mention}. Only the claimer can chat now.{cmd_hint}",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        claim_msg = await interaction.followup.send(embed=embed, wait=True)

        
        async def delete_claim_msg():
            try:
                await asyncio.sleep(30)
                await claim_msg.delete()
            except:
                pass
        asyncio.create_task(delete_claim_msg())

        try:
            original_message = await interaction.channel.fetch_message(interaction.message.id)
            await original_message.edit(view=self)
        except Exception as e:
            print(f"Failed to edit original message in claim: {e}")
        save_tickets()

    async def release_callback(self, interaction: discord.Interaction):
        
        await interaction.response.defer()

        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.followup.send(embed=create_error_embed("Bot lacks permission to manage channels"), ephemeral=True)
            asyncio.create_task(auto_delete_message(interaction))
            return

        ch_id = interaction.channel.id
        if ch_id not in claimed_tickets or claimed_tickets[ch_id] != interaction.user.id:
            await interaction.followup.send(embed=create_error_embed("You can only release tickets you have claimed"), ephemeral=True)
            asyncio.create_task(auto_delete_message(interaction))
            return

        del claimed_tickets[ch_id]
        self.update_claim_buttons(disabled_claim=False, disabled_release=True)

        overwrites = interaction.channel.overwrites.copy()
        creator_id = ticket_creators.get(ch_id)
        creator = interaction.guild.get_member(creator_id) if creator_id else None

        overwrites[interaction.guild.default_role] = discord.PermissionOverwrite(read_messages=False, send_messages=False)
        if creator:
            overwrites[creator] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        try:
            await interaction.channel.edit(overwrites=overwrites)
        except discord.errors.Forbidden:
            await interaction.followup.send(embed=create_error_embed("Bot lacks permission to edit channel permissions"), ephemeral=True)
            asyncio.create_task(auto_delete_message(interaction))
            claimed_tickets[ch_id] = interaction.user.id
            save_tickets()
            return

        embed = discord.Embed(
            title="Ticket Released",
            description=f"Ticket released by {interaction.user.mention}. This ticket is now available for others.",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        release_msg = await interaction.followup.send(embed=embed, wait=True)

        
        async def delete_release_msg():
            try:
                await asyncio.sleep(30)
                await release_msg.delete()
            except:
                pass
        asyncio.create_task(delete_release_msg())

        try:
            original_message = await interaction.channel.fetch_message(interaction.message.id)
            await original_message.edit(view=self)
        except Exception as e:
            print(f"Failed to edit original message in release: {e}")
        save_tickets()

    async def close_callback(self, interaction: discord.Interaction):
        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(embed=create_error_embed("Bot lacks permission to manage channels"), ephemeral=True)
            return

        ch_id = interaction.channel.id
        if ch_id in closed_channels:
            await interaction.response.send_message(embed=create_error_embed("This ticket is already being closed"), ephemeral=True)
            return

        creator_id = ticket_creators.get(ch_id)
        is_creator = creator_id and creator_id == interaction.user.id

        claimer_id = claimed_tickets.get(ch_id)
        is_claimer = claimer_id and claimer_id == interaction.user.id

        is_admin = interaction.user.id in ADMIN_USERS

        if not is_creator and not is_claimer and not is_admin:
            await interaction.response.send_message(embed=create_error_embed("You do not have permission to close this ticket"), ephemeral=True)
            return

        
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.confirmed = None

            @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
            async def confirm_button(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != interaction.user.id:
                    return
                self.confirmed = True
                self.stop()
                await btn_interaction.response.defer()

            @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
            async def cancel_button(self, btn_interaction: discord.Interaction, button: discord.ui.Button):
                if btn_interaction.user.id != interaction.user.id:
                    return
                self.confirmed = False
                self.stop()
                await btn_interaction.response.defer()

        confirm_embed = discord.Embed(
            title="Close Ticket",
            description="Are you sure you want to close this ticket?\nThe ticket will be deleted.",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        confirm_embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        view = ConfirmView()
        await interaction.response.send_message(embed=confirm_embed, view=view, ephemeral=True)
        await view.wait()

        if not view.confirmed:
            return

        
        if ch_id in ticket_creators:
            del ticket_creators[ch_id]
        save_tickets()

       
        closed_channels.add(ch_id)
        embed = discord.Embed(
            title="Ticket Closed",
            description=f"Ticket closed by {interaction.user.mention}. This channel will be deleted soon.",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        await interaction.channel.send(embed=embed)

        channel = bot.get_channel(ch_id)
        if channel:
            ticket_type = channel.topic.split(" • ")[-1] if channel.topic else "Unknown"
            await send_transcript(channel, interaction.user, ticket_type)

        await asyncio.sleep(3)

        try:
            if channel:
                await channel.delete()
        except Exception as e:
            print(f'Failed to delete channel: {e}')
        finally:
            if ch_id in closed_channels:
                closed_channels.remove(ch_id)
            if ch_id in claimed_tickets:
                del claimed_tickets[ch_id]
            save_tickets()

@tree.command(name="add", description="Add a user to the ticket")
@app_commands.describe(user="The user to add")
async def add_user(interaction: discord.Interaction, user: discord.User):
    if not interaction.guild.me.guild_permissions.manage_channels:
        await interaction.response.send_message(embed=create_error_embed("Bot lacks permission to manage channels"), ephemeral=True)
        return

    ch_id = interaction.channel.id
    if ch_id not in claimed_tickets or claimed_tickets[ch_id] != interaction.user.id:
        await interaction.response.send_message(embed=create_error_embed("You can only add users to tickets you have claimed"), ephemeral=True)
        return

    overwrites = interaction.channel.overwrites.copy()
    overwrites[user] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    try:
        await interaction.channel.edit(overwrites=overwrites)
        embed = discord.Embed(
            title="User Added",
            description=f"{user.mention} added by {interaction.user.mention}.",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        await interaction.response.send_message(embed=embed)
    except discord.errors.Forbidden:
        await interaction.response.send_message(embed=create_error_embed("Bot lacks permission to edit channel permissions"), ephemeral=True)

async def create_ticket(interaction: discord.Interaction, category: str, emoji: str, name: str, details: str):
    if not interaction.guild:
        await interaction.response.send_message(embed=create_error_embed("This command can only be used in a server"), ephemeral=True)
        asyncio.create_task(auto_delete_message(interaction))
        return

    user_id = interaction.user.id
    abuse_data = ticket_abuse[user_id]
    current_time = time.time()

    if current_time < abuse_data['timeout_until']:
        remaining = int(abuse_data['timeout_until'] - current_time)
        hours = remaining // 3600
        await interaction.response.send_message(embed=create_error_embed(f"You are timed out from creating tickets for {hours} more hours"), ephemeral=True)
        return

    if current_time - abuse_data['last_reset'] > 3600:
        abuse_data['count'] = 0
        abuse_data['last_reset'] = current_time

    abuse_data['count'] += 1

    if abuse_data['count'] >= 15:
        abuse_data['timeout_level'] += 1
        timeout_hours = 12 * (2 ** (abuse_data['timeout_level'] - 1))
        abuse_data['timeout_until'] = current_time + (timeout_hours * 3600)
        abuse_data['count'] = 0
        await interaction.response.send_message(embed=create_error_embed(f"Ticket spam detected! You are timed out for {timeout_hours} hours"), ephemeral=True)
        return
    elif abuse_data['count'] >= 6:
        if current_time - abuse_data['last_reset'] < 1800:
            abuse_data['timeout_level'] += 1
            timeout_hours = 12 * (2 ** (abuse_data['timeout_level'] - 1))
            abuse_data['timeout_until'] = current_time + (timeout_hours * 3600)
            abuse_data['count'] = 0
            await interaction.response.send_message(embed=create_error_embed(f"Ticket spam detected! You are timed out for {timeout_hours} hours"), ephemeral=True)
            return

    if not interaction.guild.me.guild_permissions.manage_channels:
        await interaction.response.send_message(embed=create_error_embed("Bot lacks permission to manage channels"), ephemeral=True)
        asyncio.create_task(auto_delete_message(interaction))
        return

    guild = interaction.guild
    category_name = f"{category} Tickets"
    ticket_category = discord.utils.get(guild.categories, name=category_name)
    if not ticket_category:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        try:
            ticket_category = await guild.create_category(category_name, overwrites=overwrites)
        except discord.errors.Forbidden:
            await interaction.response.send_message(embed=create_error_embed("Bot lacks permission to create a category"), ephemeral=True)
            asyncio.create_task(auto_delete_message(interaction))
            return

    ticket_id = f"TICK-{int(time.time()) % 10000:04d}"
    ticket_channel_name = f"{category.lower().replace(' ', '-')}-{interaction.user.name.lower().replace('#', '')}"
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
    }

    
    if category == "Support":
        
        support_role_1 = guild.get_role(1417899701176369162)
        support_role_2 = guild.get_role(1416444850030641324)
        support_role_3 = guild.get_role(1426945220360274051)
        if support_role_1:
            overwrites[support_role_1] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if support_role_2:
            overwrites[support_role_2] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if support_role_3:
            overwrites[support_role_3] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    elif category == f"{CLAN_NAME} Team":
        
        jyx_role_1 = guild.get_role(1426595756630085742)  
        jyx_role_2 = guild.get_role(1426595891099467887)  
        jyx_role_3 = guild.get_role(1423136141036752937)  
        if jyx_role_1:
            overwrites[jyx_role_1] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if jyx_role_2:
            overwrites[jyx_role_2] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if jyx_role_3:
            overwrites[jyx_role_3] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    elif category == "Team Tester Apply":
        
        tester_manager_role = guild.get_role(1423136141036752937)
        if tester_manager_role:
            overwrites[tester_manager_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    try:
        ticket_channel = await guild.create_text_channel(
            ticket_channel_name, category=ticket_category, overwrites=overwrites, topic=f"{ticket_id} • {interaction.user.display_name} • {category}"
        )
    except discord.errors.Forbidden:
        await interaction.response.send_message(embed=create_error_embed("Bot lacks permission to create a ticket channel"), ephemeral=True)
        asyncio.create_task(auto_delete_message(interaction))
        return

    ticket_creators[ticket_channel.id] = interaction.user.id
    save_tickets()

    embed = discord.Embed(
        title=f"{category} Ticket - {ticket_id}",
        description=f"Hello {interaction.user.mention}\nYour ticket has been created. {details if details else 'Please provide details below.'}\n\n**Response Time:** 2-5 minutes",
        color=EMBED_COLOR,
        timestamp=datetime.now(IRAN_TZ)
    )
    embed.add_field(name="Category", value=f"{emoji} {category}", inline=True)
    embed.add_field(name="Name", value=name, inline=True)
    embed.set_footer(text=f"{CLAN_NAME} System")

    
    mention_text = ""
    staff_roles_to_check = []

    if category == f"{CLAN_NAME} Team":
     
        staff_roles_to_check = [1426595756630085742, 1426595891099467887, 1423136141036752937]
    elif category == "Team Tester Apply":
     
        staff_roles_to_check = [1423136141036752937]
    elif category == "Support":
       
        staff_roles_to_check = [1417899701176369162, 1416444850030641324, 1426945220360274051]

  
    available_staff = []
    for role_id in staff_roles_to_check:
        role = guild.get_role(role_id)
        if role:
            for member in role.members:
                if member.status in [discord.Status.online, discord.Status.idle] and member not in available_staff:
                    available_staff.append(member)

    
    if available_staff:
        mention_text = " ".join([member.mention for member in available_staff])
    else:
   
        if staff_roles_to_check:
            fallback_role = guild.get_role(staff_roles_to_check[0])
            if fallback_role:
                mention_text = fallback_role.mention

    try:
        msg = await ticket_channel.send(content=mention_text if mention_text else None, embed=embed, view=TicketManagementView(ticket_channel))
        await msg.pin()
        await interaction.response.send_message(embed=create_success_embed("Ticket Created", f"Ticket created: {ticket_channel.mention}"), ephemeral=True)
    except discord.errors.Forbidden:
        await interaction.response.send_message(embed=create_error_embed("Bot lacks permission to send messages in the ticket channel"), ephemeral=True)
        asyncio.create_task(auto_delete_message(interaction))
        return

async def create_ticket_deferred(interaction: discord.Interaction, category: str, emoji: str, name: str, details: str):
    """Version of create_ticket for deferred interactions (uses followup instead of response)"""
    if not interaction.guild:
        await interaction.followup.send(embed=create_error_embed("This command can only be used in a server"), ephemeral=True)
        asyncio.create_task(auto_delete_message(interaction))
        return

    if not interaction.guild.me.guild_permissions.manage_channels:
        await interaction.followup.send(embed=create_error_embed("Bot lacks permission to manage channels"), ephemeral=True)
        asyncio.create_task(auto_delete_message(interaction))
        return

    guild = interaction.guild
    category_name = f"{category} Tickets"
    ticket_category = discord.utils.get(guild.categories, name=category_name)
    if not ticket_category:
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        try:
            ticket_category = await guild.create_category(category_name, overwrites=overwrites)
        except discord.errors.Forbidden:
            await interaction.followup.send(embed=create_error_embed("Bot lacks permission to create a category"), ephemeral=True)
            asyncio.create_task(auto_delete_message(interaction))
            return

    ticket_id = f"TICK-{int(time.time()) % 10000:04d}"
    ticket_channel_name = f"{category.lower().replace(' ', '-')}-{interaction.user.name.lower().replace('#', '')}"
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
    }

   
    if category == "Support":
        support_role_1 = guild.get_role(1417899701176369162)
        support_role_2 = guild.get_role(1416444850030641324)
        support_role_3 = guild.get_role(1426945220360274051)
        if support_role_1:
            overwrites[support_role_1] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if support_role_2:
            overwrites[support_role_2] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if support_role_3:
            overwrites[support_role_3] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    elif category == f"{CLAN_NAME} Team":
        jyx_role_1 = guild.get_role(1426595756630085742)
        jyx_role_2 = guild.get_role(1426595891099467887)
        jyx_role_3 = guild.get_role(1423136141036752937)
        if jyx_role_1:
            overwrites[jyx_role_1] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if jyx_role_2:
            overwrites[jyx_role_2] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        if jyx_role_3:
            overwrites[jyx_role_3] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

    elif category == "Team Tester Apply":
        tester_manager_role = guild.get_role(1423136141036752937)
        if tester_manager_role:
            overwrites[tester_manager_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
    try:
        ticket_channel = await guild.create_text_channel(
            ticket_channel_name, category=ticket_category, overwrites=overwrites, topic=f"{ticket_id} • {interaction.user.display_name} • {category}"
        )
    except discord.errors.Forbidden:
        await interaction.followup.send(embed=create_error_embed("Bot lacks permission to create a ticket channel"), ephemeral=True)
        asyncio.create_task(auto_delete_message(interaction))
        return

    ticket_creators[ticket_channel.id] = interaction.user.id
    save_tickets()

    embed = discord.Embed(
        title=f"{category} Ticket - {ticket_id}",
        description=f"Hello {interaction.user.mention}\nYour ticket has been created. {details if details else 'Please provide details below.'}\n\n**Response Time:** 2-5 minutes",
        color=EMBED_COLOR,
        timestamp=datetime.now(IRAN_TZ)
    )
    embed.add_field(name="Category", value=f"{emoji} {category}", inline=True)
    embed.add_field(name="Name", value=name, inline=True)
    embed.set_footer(text=f"{CLAN_NAME} System")

    
    mention_text = ""
    staff_roles_to_check = []

    if category == f"{CLAN_NAME} Team":
        staff_roles_to_check = [1426595756630085742, 1426595891099467887, 1423136141036752937]
    elif category == "Team Tester Apply":
        staff_roles_to_check = [1423136141036752937]
    elif category == "Support":
        staff_roles_to_check = [1417899701176369162, 1416444850030641324, 1426945220360274051]

    available_staff = []
    for role_id in staff_roles_to_check:
        role = guild.get_role(role_id)
        if role:
            for member in role.members:
                if member.status in [discord.Status.online, discord.Status.idle] and member not in available_staff:
                    available_staff.append(member)

    if available_staff:
        mention_text = " ".join([member.mention for member in available_staff])
    else:
        if staff_roles_to_check:
            fallback_role = guild.get_role(staff_roles_to_check[0])
            if fallback_role:
                mention_text = fallback_role.mention

    try:
        msg = await ticket_channel.send(content=mention_text if mention_text else None, embed=embed, view=TicketManagementView(ticket_channel))
        await msg.pin()
        await interaction.followup.send(embed=create_success_embed("Ticket Created", f"Ticket created: {ticket_channel.mention}"), ephemeral=True)
    except discord.errors.Forbidden:
        await interaction.followup.send(embed=create_error_embed("Bot lacks permission to send messages in the ticket channel"), ephemeral=True)
        asyncio.create_task(auto_delete_message(interaction))
        return

class JHistoryView(discord.ui.View):
    def __init__(self, user, pages):
        super().__init__(timeout=60)
        self.user = user
        self.pages = pages
        self.current_page = 0

        if len(pages) <= 1:
            self.previous_button.disabled = True
            self.next_button.disabled = True

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

@tree.command(name="jhistory", description=f"View user's {CLAN_NAME} team application history")
@app_commands.describe(user="The user to check history for")
async def jhistory(interaction: discord.Interaction, user: discord.Member):
    try:
        user_id = user.id

        declines = decline_counts.get(user_id, 0)
        accepts = accept_counts.get(user_id, 0)

        cooldown_text = "No active cooldown"
        if user_id in cooldowns:
            remaining = cooldowns[user_id] - time.time()
            if remaining > 0:
                days = int(remaining // 86400)
                hours = int((remaining % 86400) // 3600)
                minutes = int((remaining % 3600) // 60)
                cooldown_text = f"{days} days, {hours} hours, {minutes} minutes remaining"

        embed = discord.Embed(
            title=f"{CLAN_NAME} History - {user.display_name}",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
        embed.add_field(name="Accepts", value=str(accepts), inline=True)
        embed.add_field(name="Declines", value=str(declines), inline=True)
        embed.add_field(name="Cooldown", value=cooldown_text, inline=False)
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )



@tree.command(name="profile", description="View detailed profile of a user")
@app_commands.describe(user="The user to view profile for (defaults to yourself)")
async def profile(interaction: discord.Interaction, user: discord.Member = None):
    try:
 
        if user is None:
            user = interaction.user

        user_id = user.id


        embed = discord.Embed(
            title=f"{CLAN_NAME} Profile - {user.display_name}",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)


        general_info = f"**User:** {user.mention}\n**ID:** `{user.id}`\n"

 
        if isinstance(user, discord.Member):
            if user.joined_at:
                join_timestamp = int(user.joined_at.timestamp())
                general_info += f"**Joined Server:** <t:{join_timestamp}:D> (<t:{join_timestamp}:R>)\n"

    
        creation_timestamp = int(user.created_at.timestamp())
        general_info += f"**Account Created:** <t:{creation_timestamp}:D> (<t:{creation_timestamp}:R>)"

        embed.add_field(name="📋 General Info", value=general_info, inline=False)


        points = points_data.get(str(user_id), 0)


        jyx_rank = "Member"
        if isinstance(user, discord.Member):

            role_hierarchy = [
                (config.get('roles', {}).get('tester_manager'), "TesterManager"),
                (config.get('roles', {}).get('senior_tester'), "SeniorTester"),
                (config.get('roles', {}).get('team_tester'), "TeamTester"),
                (config.get('roles', {}).get('jr_tester'), "JrTester"),
                (config.get('roles', {}).get('team'), "Team Member"),
            ]

            for role_id, rank_name in role_hierarchy:
                if role_id and any(r.id == role_id for r in user.roles):
                    jyx_rank = rank_name
                    break

   
        accepts = accept_counts.get(user_id, 0)
        declines = decline_counts.get(user_id, 0)

        
        cooldown_status = "No active cooldown"
        if user_id in cooldowns:
            remaining = cooldowns[user_id] - time.time()
            if remaining > 0:
                days = int(remaining // 86400)
                hours = int((remaining % 86400) // 3600)
                minutes = int((remaining % 3600) // 60)
                cooldown_status = f"{days}d {hours}h {minutes}m remaining"
            else:
                cooldown_status = "No active cooldown"

        jyx_stats = f"**Points:** {points}\n"
        jyx_stats += f"**Rank:** {jyx_rank}\n"
        jyx_stats += f"**Applications:** {accepts} Accepted / {declines} Declined\n"
        jyx_stats += f"**Cooldown:** {cooldown_status}"

        embed.add_field(name=f"⭐ {CLAN_NAME} Stats", value=jyx_stats, inline=False)

        
        warnings = warnings_data.get(user_id, [])
        total_warnings = len(warnings)

        warnings_text = f"**Total Warnings:** {total_warnings}"

       
        if total_warnings > 0:
            last_warning = warnings[-1]
            warn_time = last_warning.get('timestamp', 'Unknown')
            try:
                warn_dt = datetime.fromisoformat(warn_time)
                warn_timestamp = int(warn_dt.timestamp())
                warnings_text += f"\n**Last Warning:** <t:{warn_timestamp}:R>"
            except:
                pass

        embed.add_field(name="⚠️ Warnings", value=warnings_text, inline=False)

       
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )



@tree.command(name="jcooldown", description=f"Set a cooldown for a user's {CLAN_NAME} Team tickets")
@app_commands.describe(user="The user to set cooldown for", duration="Duration (e.g., 1h, 1d, 1M, 1y)")
async def jcooldown(interaction: discord.Interaction, user: discord.Member, duration: str):
    try:
        if not has_permission(interaction.user.id, 'jdecline', interaction.user.roles) and interaction.user.id not in ADMIN_USERS:
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        try:
            amount = int(duration[:-1])
            unit = duration[-1].lower()

            if unit == 's':
                cooldown_seconds = amount
            elif unit == 'h':
                cooldown_seconds = amount * 3600
            elif unit == 'd':
                cooldown_seconds = amount * 86400
            elif unit == 'm':
                cooldown_seconds = amount * 86400 * 30
            elif unit == 'y':
                cooldown_seconds = amount * 86400 * 365
            else:
                raise ValueError("Invalid duration format")

            cooldown_end = time.time() + cooldown_seconds
            cooldowns[user.id] = cooldown_end
            save_tickets()

            days = int(cooldown_seconds // 86400)
            hours = int((cooldown_seconds % 86400) // 3600)
            minutes = int((cooldown_seconds % 3600) // 60)

            success_embed = create_success_embed(
                "Cooldown Set",
                f"Set cooldown for {user.mention}\n\n**Duration:** {days} days, {hours} hours, {minutes} minutes"
            )
            await interaction.response.send_message(embed=success_embed)

        except (ValueError, IndexError):
            await interaction.response.send_message(
                embed=create_error_embed("Invalid duration format Use: 1s, 1h, 1d, 1m (month), 1y"),
                ephemeral=True
            )

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="rankup", description="Promote a user to the next rank")
@app_commands.describe(
    user="The user to rank up",
    reason="Reason for the promotion"
)
async def rankup(interaction: discord.Interaction, user: discord.Member, reason: str = "Great performance and dedication"):
    try:
        if not has_permission(interaction.user.id, "rankup", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        

        team_role_id = config.get('team_role_id', 0)

        JRTESTER_ID = 1416444856972083215
        TEAMTESTER_ID = 1426595756630085742
        SENIORTESTER_ID = 1426595891099467887
        TESTERMANAGER_ID = 1423136141036752937

        
        jrtester_role = interaction.guild.get_role(JRTESTER_ID)
        teamtester_role = interaction.guild.get_role(TEAMTESTER_ID)
        seniortester_role = interaction.guild.get_role(SENIORTESTER_ID)
        testermanager_role = interaction.guild.get_role(TESTERMANAGER_ID)
        team_role = interaction.guild.get_role(team_role_id) if team_role_id else None


        jyx_role = None
        for role in interaction.guild.roles:
            if role.name.lower() == "jyx":
                jyx_role = role
                break

       
        current_role = None
        next_role = None
        current_rank_name = None

        if testermanager_role and testermanager_role in user.roles:
            return await interaction.response.send_message(
                embed=create_error_embed("User is already at max rank (TesterManager)"),
                ephemeral=True
            )
        elif seniortester_role and seniortester_role in user.roles:
            current_role = seniortester_role
            next_role = testermanager_role
            current_rank_name = "SeniorTester"
        elif teamtester_role and teamtester_role in user.roles:
            current_role = teamtester_role
            next_role = seniortester_role
            current_rank_name = "TeamTester"
        elif jrtester_role and jrtester_role in user.roles:
            current_role = jrtester_role
            next_role = teamtester_role
            current_rank_name = "JrTester"
        elif (team_role and team_role in user.roles) or (jyx_role and jyx_role in user.roles):
            if team_role and team_role in user.roles:
                current_role = team_role
                current_rank_name = "Team"
            elif jyx_role and jyx_role in user.roles:
                current_role = jyx_role
                current_rank_name = CLAN_NAME
            next_role = jrtester_role
        else:
            return await interaction.response.send_message(
                embed=create_error_embed(f"User doesn't have any rankable role ({CLAN_NAME}, Team, JrTester, TeamTester, SeniorTester)"),
                ephemeral=True
            )

        if not next_role:
            return await interaction.response.send_message(
                embed=create_error_embed("Next rank role not found on the server"),
                ephemeral=True
            )

        
        if current_role:
            await user.remove_roles(current_role)
        await user.add_roles(next_role)

       
        rankup_channel_id = None
        if 'channels' in config and 'rankup' in config['channels']:
            rankup_list = config['channels']['rankup']
            if rankup_list and len(rankup_list) > 0:
                rankup_channel_id = rankup_list[0]

        
        if not rankup_channel_id:
            rankup_channel_id = config.get('rankup_channel_id')

        if rankup_channel_id:
            channel = bot.get_channel(rankup_channel_id)
            if channel:
                embed = discord.Embed(
                    title="🎉 Rank Promotion",
                    description=f"Congratulations {user.mention} on your promotion!",
                    color=EMBED_COLOR,
                    timestamp=datetime.now(IRAN_TZ)
                )
                embed.set_author(name=user.display_name, icon_url=user.avatar.url if user.avatar else user.default_avatar.url)
                embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
                embed.add_field(name="📊 Previous Rank", value=f"`{current_rank_name}`", inline=True)
                embed.add_field(name="⬆️ New Rank", value=next_role.mention, inline=True)
                embed.add_field(name="👤 Promoted By", value=interaction.user.mention, inline=True)
                embed.add_field(name="📝 Reason", value=reason, inline=False)
                embed.set_footer(text=f"{CLAN_NAME} System • Rank Management", icon_url=bot.user.avatar.url if bot.user.avatar else None)
                await channel.send(embed=embed)

        
        success_embed = create_success_embed(
            "User Ranked Up",
            f"{user.mention} has been promoted from **{current_rank_name}** to {next_role.mention}"
        )
        await interaction.response.send_message(embed=success_embed)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="savescript", description="Save a script/text with a unique ID for panel access")
@app_commands.describe(content="The script or text content to save")
async def savescript(interaction: discord.Interaction, content: str):
    try:
        if not has_permission(interaction.user.id, "savescript", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        script_id = generate_script_id()
        scripts_data[script_id] = {
            'content': content,
            'timestamp': datetime.now(IRAN_TZ).strftime('%Y-%m-%d %H:%M:%S'),
            'channelId': str(interaction.channel_id),
            'userId': str(interaction.user.id),
            'username': str(interaction.user)
        }
        save_scripts()

        embed = discord.Embed(
            title="Script Saved",
            description=f"Your script has been saved successfully!\n\n**Script ID:** `{script_id}`\n\nYou can view this script in the panel using this ID.",
            color=0x5cb85c,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.add_field(name="Panel Access", value="Open `panel.html` in your browser and use the Script Viewer tab", inline=False)
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="panel", description="Get the control panel link")
async def panel_command(interaction: discord.Interaction):
    try:
        if not has_permission(interaction.user.id, "panel", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        embed = discord.Embed(
            title="🎛️ Bot Control Panel",
            description="Access the web panel to manage your bot configuration",
            color=0x5865F2,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.add_field(name="Panel URL", value="[http://localhost:8080](http://localhost:8080)", inline=False)
        embed.add_field(
            name="Features",
            value="• Set channels, roles, and admins with right-click\n• Manage permissions\n• View scripts and tickets\n• Save & Reload config without restart",
            inline=False
        )
        embed.set_footer(text=f"{CLAN_NAME} System | Click 'Done' in panel when finished", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="region", description="Change voice channel region")
@app_commands.describe(region="The region to set (auto, us-west, us-east, us-central, us-south, singapore, brazil, hongkong, russia, japan, rotterdam, southafrica, sydney, india)")
async def region_command(interaction: discord.Interaction, region: str):
    try:
        if not has_permission(interaction.user.id, "region", interaction.user.roles):
            return await interaction.response.send_message(
                embed=create_error_embed("You don't have permission to use this command"),
                ephemeral=True
            )

        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message(
                embed=create_error_embed("You must be in a voice channel to use this command"),
                ephemeral=True
            )

        voice_channel = interaction.user.voice.channel

        valid_regions = {
            'auto': None,
            'us-west': discord.VoiceRegion.us_west,
            'us-east': discord.VoiceRegion.us_east,
            'us-central': discord.VoiceRegion.us_central,
            'us-south': discord.VoiceRegion.us_south,
            'singapore': discord.VoiceRegion.singapore,
            'brazil': discord.VoiceRegion.brazil,
            'hongkong': discord.VoiceRegion.hongkong,
            'russia': discord.VoiceRegion.russia,
            'japan': discord.VoiceRegion.japan,
            'rotterdam': discord.VoiceRegion.rotterdam,
            'southafrica': discord.VoiceRegion.south_africa,
            'sydney': discord.VoiceRegion.sydney,
            'india': discord.VoiceRegion.india
        }

        region_lower = region.lower()
        if region_lower not in valid_regions:
            return await interaction.response.send_message(
                embed=create_error_embed(f"Invalid region. Valid regions: {', '.join(valid_regions.keys())}"),
                ephemeral=True
            )

        await voice_channel.edit(rtc_region=valid_regions[region_lower])

        embed = discord.Embed(
            title="Voice Region Changed",
            description=f"Region for {voice_channel.mention} changed to **{region}**",
            color=0x57F287,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )

@tree.command(name="viewscript", description="View a saved script by ID")
@app_commands.describe(script_id="The script ID to view")
async def viewscript(interaction: discord.Interaction, script_id: str):
    try:
        if script_id not in scripts_data:
            return await interaction.response.send_message(
                embed=create_error_embed(f"Script not found with ID: {script_id}"),
                ephemeral=True
            )

        script = scripts_data[script_id]
        embed = discord.Embed(
            title="Script Details",
            description=f"**ID:** `{script_id}`\n**Created:** {script.get('timestamp', 'Unknown')}\n**By:** {script.get('username', 'Unknown')}",
            color=EMBED_COLOR,
            timestamp=datetime.now(IRAN_TZ)
        )
        embed.add_field(name="Content", value=f"```\n{script['content'][:1000]}\n```", inline=False)
        embed.set_footer(text=f"{CLAN_NAME} System", icon_url=bot.user.avatar.url if bot.user.avatar else None)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            embed=create_error_embed(f"An error occurred: {str(e)}"),
            ephemeral=True
        )


app = web.Application()
routes = web.RouteTableDef()

@routes.get('/api/server-data')
async def get_server_data(request):
    """Get all server channels, roles, and members"""
    try:
        guild_id = request.query.get('guild_id')
        if not guild_id:
            
            guilds = bot.guilds
            if not guilds:
                return web.json_response({'error': 'Bot not in any servers'}, status=400)
            guild = guilds[0]
        else:
            guild = bot.get_guild(int(guild_id))

        if not guild:
            return web.json_response({'error': 'Guild not found'}, status=404)

        data = {
            'guild': {
                'id': str(guild.id),
                'name': guild.name,
                'icon': str(guild.icon.url) if guild.icon else None
            },
            'channels': [
                {
                    'id': str(ch.id),
                    'name': ch.name,
                    'type': str(ch.type),
                    'category': ch.category.name if ch.category else None
                }
                for ch in guild.channels if isinstance(ch, (discord.TextChannel, discord.VoiceChannel))
            ],
            'roles': [
                {
                    'id': str(role.id),
                    'name': role.name,
                    'color': str(role.color),
                    'position': role.position
                }
                for role in guild.roles
            ],
            'members': [
                {
                    'id': str(member.id),
                    'name': member.name,
                    'display_name': member.display_name,
                    'avatar': str(member.display_avatar.url),
                    'roles': [str(r.id) for r in member.roles]
                }
                for member in guild.members
            ]
        }
        return web.json_response(data)
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

@routes.get('/api/tickets')
async def get_tickets(request):
    try:
        with open('tickets_db.json', 'r', encoding='utf-8') as f:
            tickets = json.load(f)
        return web.json_response(tickets)
    except:
        return web.json_response({})

@routes.get('/api/scripts')
async def get_scripts(request):
    try:
        with open('scripts.json', 'r', encoding='utf-8') as f:
            scripts = json.load(f)
        return web.json_response(scripts)
    except:
        return web.json_response({})

@routes.get('/api/config')
async def get_config_api(request):
    global config
    return web.json_response(config)

@routes.post('/api/config')
async def save_config_api(request):
    global config, CLAN_NAME
    try:
        new_config = await request.json()
        save_config(new_config)

        
        config = new_config
        CLAN_NAME = config.get('clan_name', 'JyX')

        return web.json_response({'success': True, 'message': 'Config saved and reloaded successfully!'})
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

@routes.post('/api/panel/done')
async def panel_done(request):
    """Called when user clicks Done button - reload all configs and notify channels"""
    global config, CLAN_NAME
    try:
        
        config = load_config()
        CLAN_NAME = config.get('clan_name', 'JyX')

        
        return web.json_response({
            'success': True,
            'message': 'Panel closed, config reloaded!'
        })
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)

@routes.get('/{path:.*}')
async def serve_file(request):
    path = request.match_info['path']
    if not path:
        path = 'panel.html'
    try:
        with open(path, 'rb') as f:
            content = f.read()

        content_type = 'text/html'
        if path.endswith('.js'):
            content_type = 'application/javascript'
        elif path.endswith('.css'):
            content_type = 'text/css'
        elif path.endswith('.json'):
            content_type = 'application/json'

        return web.Response(body=content, content_type=content_type)
    except FileNotFoundError:
        return web.Response(text='File not found', status=404)

app.add_routes(routes)

async def start_web_server():
    """Start the web panel server"""
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    print(f'🌐 Panel Server running at http://localhost:8080')
    print(f'📊 Open http://localhost:8080 in your browser')

async def start_bots():
    """Start both main bot and checker bot concurrently with web server"""
    
    await start_web_server()

    if not BOT_TOKEN:
        print("❌ Bot token not found! Please add your token to bot_token.txt")
        return

    async with bot:
        if CHECKER_TOKEN:
            async with checker_bot:
                await asyncio.gather(
                    bot.start(BOT_TOKEN),
                    checker_bot.start(CHECKER_TOKEN)
                )
        else:
            print("⚠️  Checker bot token not found, running main bot only")
            await bot.start(BOT_TOKEN)

if __name__ == "__main__":
    import sys
    import io

    
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    try:
        print("🚀 Starting JyX Bot...")
        print(f"📁 Config file: panel_config.json")
        print(f"🔑 Token file: bot_token.txt")
        asyncio.run(start_bots())
    except KeyboardInterrupt:
        print("\n👋 Bots stopped by user")
    except Exception as e:
        print(f"❌ Failed to start bots: {e}")
