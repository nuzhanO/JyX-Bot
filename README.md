# JyX Clan Bot v1.0.1

A friendly Discord bot for clan management, made by Tury.

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
## Notes

- **Token security**: Bot token is in `bot_token.txt` (never committed to git)
- **Config management**: Everything done through web panel (no manual JSON editing)
- **Auto-reload**: Config changes apply instantly without bot restart
- The main bot uses `/` and `=` as command prefixes
- Checker bot is separate and uses `!checker_` prefix - it won't sync slash commands in servers where it's added
- All data is stored in JSON files (partners.json, giveaways.json, points.json, scripts.json, tickets_db.json, panel_config.json)
- Web panel runs automatically when you start the bot on port 8080

Made with love by Tury

