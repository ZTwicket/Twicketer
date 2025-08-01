from dataclasses import dataclass
from typing import Optional
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class TwicketConfig:
    """Configuration for Twicket bot."""
    
    # Required fields (no defaults)
    user: str
    password: str
    event_id: str
    api_key: str
    
    # Optional fields (with defaults)
    time_delay: float = 2.0
    discord_webhook_url: Optional[str] = None
    
    # Browser settings
    headless: bool = True
    user_agent: str = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0'
    
    # Ticket preferences
    min_seats: int = 1
    max_seats: int = 4
    max_price: Optional[float] = None
    skip_meetup_delivery: bool = True
    
    @classmethod
    def from_json(cls, config_path: str = None) -> 'TwicketConfig':
        """Create config from JSON file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / 'config.json'
        else:
            config_path = Path(config_path)
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        return cls(
            user=data.get('user', ''),
            password=data.get('password', ''),
            event_id=data.get('event_id', ''),
            api_key=data.get('api_key', ''),
            discord_webhook_url=data.get('discord_webhook_url'),
            time_delay=data.get('time_delay', 2.0),
            headless=data.get('headless', True),
            user_agent=data.get('user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0'),
            min_seats=data.get('min_seats', 1),
            max_seats=data.get('max_seats', 4),
            max_price=data.get('max_price'),
            skip_meetup_delivery=data.get('skip_meetup_delivery', True)
        )
    
    @property
    def cookies(self) -> list[dict[str, str]]:
        """Browser cookies for Twickets."""
        return [
            {'name': 'clientId', 'value': 'cf6de4c4-cca6-4425-b252-4c1360309a1c', 'domain': '.twickets.live', 'path': '/'},
            {'name': 'territory', 'value': 'GB', 'domain': '.twickets.live', 'path': '/'},
            {'name': 'locale', 'value': 'en_GB', 'domain': '.twickets.live', 'path': '/'}
        ]