# JyX Clan Bot

# version 1.0.1
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

## Setup

1. Install dependencies:
```bash
pip install discord.py pytz
```

2. Create your config file:
   - Copy `config.example.json` to `config.json`
   - Add your bot tokens
   - Set your `clan_name` (default is JyX, you can change it to anything like Night, etc.)
   - Configure channel IDs, role IDs, and admin users
   - Customize ticket options

3. Run the bot:
```bash
python bot.py
```

## Config

The bot uses `config.json` for all settings. You can customize:
- **clan_name**: Change your clan name (replaces JyX everywhere in embeds and messages)
- Channel IDs for welcome, logs, tickets, etc.
- Role IDs for team, staff, testers, etc.
- Admin user IDs
- Ticket categories
- QoL features like auto-thread channels

## Notes

- The main bot uses `/` and `=` as command prefixes
- Checker bot is separate and uses `!checker_` prefix - it won't sync slash commands in servers where it's added
- All data is stored in JSON files (partners.json, giveaways.json, points.json, etc.)

Made with love by Tury
