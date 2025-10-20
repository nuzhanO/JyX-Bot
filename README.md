# JyX Clan Bot v1.0.2

A friendly Discord bot for clan management, made by Tury.

## Features

- Team management system
- Ticket system with custom categories
- Giveaway system
- Warning and moderation tools
- Voice state logging
- Partner system
- Custom nickname management with clan prefix
- Auto-thread and smart slowmode
- Member counter
- HTML Control Panel for config management and script viewing
- Auto voice channel creation
- Voice region changer
- Server backup and restore
- Blacklist word filter
- Ticket spam protection

## Setup

1. Install dependencies:
```bash
pip install discord.py pytz aiohttp
```

2. Add your bot token:
   - Copy `bot_token.example.txt` to `bot_token.txt`
   - Paste your Discord bot token inside
   - (Optional) Add checker bot token to `checker_token.txt`

3. Run the bot:
```bash
python bot.py
```
The bot and panel will start automatically on http://localhost:8080

4. Configure everything from the panel:
   - Open http://localhost:8080 in your browser
   - Set your clan name
   - Right-click on channels/roles/members to assign them
   - Click "Save & Reload" - no restart needed!

## Config

**Everything is configured from the web panel!** No need to edit JSON files manually.

The panel lets you:
- **Set clan name**: Changes JyX to your clan name everywhere
- **Assign channels**: Right-click any channel → set as welcome, log, ticket panel, etc.
- **Assign roles**: Right-click any role → set as team, mute, partner, etc.
- **Add admins**: Right-click any member → add to admin users
- **Save & Reload**: Instantly apply changes without restarting the bot
- Configuration is stored in `panel_config.json` (auto-generated)

## Control Panel

Open http://localhost:8080 after running the bot for an amazing web interface with:
- **Live server data**: See all channels, roles, and members from your Discord server
- **Right-click to assign**: Right-click on any channel/role/member to set it in config
- **Save & Reload**: Save config changes without restarting the bot!
- **Search**: Quickly find channels, roles, or members with built-in search
- **View scripts**: Access saved scripts by ID using `/savescript` command
- **View tickets**: View and export closed ticket transcripts by ID
- **Beautiful theme**: Clean black/white design with 3D background
- **No more HTML files** cluttering your directory!

## Script System

Use `/savescript` in Discord to save scripts with unique IDs, then view them in the panel:
```
/savescript content: Your script here
```
The bot will give you a unique ID like `SCR-AB12CD34` that you can use in the panel to view the script.

## Ticket System

When you close a ticket, the bot automatically:
- Generates a unique Ticket ID (e.g., `TKT-AB12CD34`)
- Saves the full transcript to database
- Sends the ID to the transcript channel
- You can view/export the ticket anytime from the panel

No more HTML files in your folder!

## New in v1.0.2

### Ticket Spam Protection
The bot now automatically detects and prevents ticket spam:
- **Detection**: 15 tickets in 1 hour OR 6-7 tickets in 30 minutes triggers timeout
- **Progressive timeout**: 12h, 24h, 48h, 96h... (doubles each time)
- **Auto pin**: First message in tickets is automatically pinned

### Auto Voice Channels
Set a voice channel in config that creates temporary channels:
- Join the configured channel → bot creates a private channel for you
- You get full control (manage, move members)
- Channel auto-deletes when empty
- Configure via panel: `qol_features.auto_voice_channel_id`

### Voice Region Command
Change voice channel region on the fly:
```
/region region:singapore
```
Supported regions: auto, us-west, us-east, us-central, us-south, singapore, brazil, hongkong, russia, japan, rotterdam, southafrica, sydney, india

### Server Backup & Restore
Secret admin commands for server backup:
```
=savesv
=loadsv server_backup_123456.json
```
Backs up all channels, roles, and categories. Use with caution!

### Blacklist System
Add blacklisted words in config (`blacklist_words` array):
- Automatically deletes messages containing blacklisted words
- Sends warning to user
- Logs to log channel

## Notes

- **Token security**: Bot token is in `bot_token.txt` (never committed to git)
- **Config management**: Everything done through web panel (no manual JSON editing)
- **Auto-reload**: Config changes apply instantly without bot restart
- The main bot uses `/` and `=` as command prefixes
- Checker bot is separate and uses `!checker_` prefix - it won't sync slash commands in servers where it's added
- All data is stored in JSON files (partners.json, giveaways.json, points.json, scripts.json, tickets_db.json, panel_config.json)
- Web panel runs automatically when you start the bot on port 8080

Made with love by Tury
