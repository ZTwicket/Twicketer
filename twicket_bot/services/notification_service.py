import logging
import requests
import json

from ..core.config import TwicketConfig
from ..models.ticket import TicketListing


class NotificationService:
    """Handles notifications via Prowl and Discord webhooks."""
    
    def __init__(self, config: TwicketConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        if config.discord_webhook_url:
            self.logger.info("Notification: Discord webhook notifications enabled")
    
    
    def _send_discord_webhook(self, title: str, description: str, color: int = 0x00ff00, url: str = None) -> None:
        """Send a Discord webhook notification."""
        if not self.config.discord_webhook_url:
            return
        
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": None
        }
        
        if url:
            embed["url"] = url
        
        payload = {
            "embeds": [embed]
        }
        
        try:
            response = requests.post(
                self.config.discord_webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
        except Exception as e:
            self.logger.error(f"Notification: Failed to send Discord webhook: {e}")
    
    
    def notify_bot_started(self) -> None:
        """Send notification when bot starts monitoring."""
        description = "Bot has started monitoring for tickets!"
        
        self._send_discord_webhook("🚀 Twicket Bot Started", description, 0x0099ff, f"https://www.twickets.live/event/{self.config.event_id}")
    
    def notify_ticket_found(self, listing: TicketListing, block_id: str, ticket_url: str) -> None:
        """Send notification when a ticket is found and opened in browser."""
        description = f"Found available ticket and opened in browser!\n**Section:** {listing.section}\n**Row:** {listing.row}\n**Seats:** {listing.seats}\n**Price:** £{listing.price}"
        
        self._send_discord_webhook("🎯 Ticket Found & Opened!", description, 0x00ff00, ticket_url)
    
    @property
    def is_enabled(self) -> bool:
        """Check if notifications are enabled."""
        return self.config.discord_webhook_url is not None