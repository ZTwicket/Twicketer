# Twicket Bot

⚠️ **DISCLAIMER** ⚠️  
This bot is provided for educational purposes only. Users are responsible for ensuring compliance with Twickets' Terms of Service and all applicable laws. The authors assume no liability for misuse of this software. Always respect ticket purchase limits and fair use policies.

---

Automated ticket monitoring for Twickets. This bot **cannot** buy tickets automatically, it will only open a direct buy link to the tickets.

## Features

- 🎫 Automated ticket monitoring for events
- 🔄 Real-time availability checking
- 🌐 Browser automation for ticket purchasing
- 🔔 Discord webhook notifications
- ⚙️ Configurable filters (price, seats, delivery method)
- 📊 Rich console UI with status updates

## Prerequisites

- Python 3.8 or higher
- Chrome/Chromium browser
- Twickets account
- Discord webhook URL (optional, for notifications)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ZTwicket/Twicketer.git
   cd bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

## Configuration

1. **Copy the configuration template:**
   ```bash
   cp config.json.template config.json
   ```

2. **Edit `config.json` with your settings:**
   ```json
   {
     "user": "your-email@example.com",
     "password": "your-password",
     "event_id": "event-id-from-twickets-url",
     "api_key": "your-twickets-api-key",
     "discord_webhook_url": "optional-discord-webhook-url",
     "time_delay": 2.0,
     "headless": true,
     "user_agent": "your user agent",
     "min_seats": 1,
     "max_seats": 4,
     "max_price": 150,
     "skip_meetup_delivery": true
   }
   ```

### Configuration Options

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user` | string | ✅ | Your Twickets account email |
| `password` | string | ✅ | Your Twickets account password |
| `event_id` | string | ✅ | Event ID from Twickets URL (e.g., `1234567890` from `twickets.live/event/1234567890`) |
| `api_key` | string | ✅ | Twickets API key |
| `discord_webhook_url` | string | ❌ | Discord webhook URL for notifications |
| `time_delay` | float | ❌ | Delay between checks in seconds (default: 2.0) |
| `headless` | boolean | ❌ | Run browser in headless mode (default: true) |
| `user_agent` | string | ❌ | Browser user agent string |
| `min_seats` | integer | ❌ | Minimum number of seats (default: 1) |
| `max_seats` | integer | ❌ | Maximum number of seats (default: 4) |
| `max_price` | float | ❌ | Maximum price per ticket (optional) |
| `skip_meetup_delivery` | boolean | ❌ | Skip tickets with meetup delivery (default: true) |

### Setting Up Discord Notifications (Optional)

1. Create a Discord webhook in your server:
   - Go to Server Settings → Integrations → Webhooks
   - Click "New Webhook"
   - Copy the webhook URL
2. Add the webhook URL to your `config.json`

## Usage

### Basic Usage

Run the bot with default configuration:
```bash
python main.py
```

### What Happens When Running

1. The bot will log in to your Twickets account
2. Start monitoring the specified event for available tickets
3. When tickets matching your criteria are found:
   - Send a Discord notification (if configured)
   - Automatically open up a web page when a ticket becomes available so you can purchase straight away
4. The bot will display real-time status in the console

## Troubleshooting

### Common Issues

1. **Login fails:**
   - Double-check your email and password in `config.json`
   - Ensure your account is not locked or requires 2FA

2. **API errors:**
   - Verify your API key is correct
   - Check if the event ID exists

3. **Browser not found:**
   - Run `playwright install chromium` again

### Logs

Detailed logs are saved in the `logs/` directory:
- `twicket_bot.log` - Main application logs
- Check these for detailed error messages and debugging information

## Security Notes

- **Never share your `config.json` file** - it contains sensitive credentials
- The `config.json` file is already in `.gitignore` to prevent accidental commits

## License

This project is provided as-is for educational purposes. See LICENSE file for details.

## Support

For issues or questions:
- Check the logs in `logs/` directory first
- Review the troubleshooting section
- Open an issue with detailed error messages and logs (remove sensitive data)

---

⚠️ **Remember:** Use this bot responsibly and in accordance with Twickets' Terms of Service.