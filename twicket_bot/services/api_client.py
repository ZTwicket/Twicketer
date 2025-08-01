import logging
from typing import Optional, List, Dict, Any
from playwright.sync_api import Page

from ..models.ticket import (
    TicketListing, TicketAvailability,
    LoginResponse, APIResponse,
    DeliveryPlan, TicketBlock
)
from ..core.config import TwicketConfig


class TwicketAPIClient:
    """Client for interacting with Twickets API."""
    
    def __init__(self, config: TwicketConfig, page: Page):
        self.config = config
        self.page = page
        self.logger = logging.getLogger(__name__)
    
    def login(self, username: str, password: str) -> Optional[str]:
        """Authenticate with Twickets and return auth token."""
        self.logger.info(f"Login      : Starting login process for user: {username}")
        
        url = f'https://www.twickets.live/services/auth/login?api_key={self.config.api_key}'
        
        headers = {
            'User-Agent': self.config.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': 'https://www.twickets.live',
            'Referer': 'https://www.twickets.live/app/login?target=https:%2F%2Fwww.twickets.live%2Fen%2Fuk'
        }
        
        data = {
            "login": username,
            "password": password,
            "accountType": "U"
        }
        
        self.logger.info("Login      : Sending login request to Twickets API")
        
        result = self.page.evaluate("""
            async ({url, headers, data}) => {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: headers,
                    body: JSON.stringify(data)
                });
                const text = await response.text();
                let json;
                try {
                    json = JSON.parse(text);
                } catch (e) {
                    json = null;
                }
                return {
                    json: json,
                    status: response.status,
                    headers: Object.fromEntries(response.headers.entries()),
                    text: text
                };
            }
        """, {"url": url, "headers": headers, "data": data})
        
        try:
            json_result = result['json']
            self.logger.info(f"Login      : Received response from Twickets API (Status: {result['status']})")
        except Exception as e:
            self.logger.error(f"Login      : Failed to decode JSON: {e}")
            self.logger.error(f"Login      : Status code: {result['status']}")
            self.logger.error(f"Login      : Response headers: {result['headers']}")
            self.logger.error(f"Login      : Response text: {result['text']}")
            return None
        
        if json_result and json_result.get("responseData"):
            auth_token = json_result["responseData"]
            self.logger.info(f"Login      : Login successful! Auth token received: {str(auth_token)[:20]}...")
            return auth_token
        else:
            self.logger.error(f"Login      : Login failed. Response: {json_result}")
            return None
    
    def get_ticket_availability(self, inventory_id: str, seats: str) -> Optional[TicketAvailability]:
        """Check if specific ticket is available."""
        url = f'https://www.twickets.live/services/inventory/{inventory_id}?api_key={self.config.api_key}&qty={seats}'
        self.logger.debug(f"API Call   : Checking ticket availability for inventory ID: {inventory_id} (seats: {seats})")
        
        result = self.page.evaluate("""
            async (url) => {
                const response = await fetch(url, {
                    headers: {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:101.0) Gecko/20100101 Firefox/101.0'
                    }
                });
                return await response.json();
            }
        """, url)
        
        if result:
            available = result.get('available', False)
            self.logger.debug(f"API Call   : Ticket is available: {available}")
            
            if available and result.get('block'):
                delivery_plan = [
                    DeliveryPlan(
                        delivery_method=plan.get('deliveryMethod', 0),
                        title=plan.get('title', '')
                    ) for plan in result.get('deliveryPlan', [])
                ]
                
                block = TicketBlock(block_id=result['block']['blockId'])
                
                return TicketAvailability(
                    available=True,
                    block=block,
                    delivery_plan=delivery_plan
                )
            else:
                # Return a TicketAvailability object with available=False
                return TicketAvailability(
                    available=False,
                    block=None,
                    delivery_plan=[]
                )
        
        return None
    
    def check_event_availability(self, event_id: str) -> Optional[List[TicketListing]]:
        """Get all available ticket listings for an event."""
        url = f'https://www.twickets.live/services/g2/inventory/listings/{event_id}?api_key={self.config.api_key}'
        self.logger.debug(f"API Call   : Checking event availability for event ID: {event_id}")
        
        results = self.page.evaluate("""
            async (url) => {
                const response = await fetch(url);
                return await response.json();
            }
        """, url)
        
        if not results.get('responseData'):
            return None
        
        self.logger.debug(f"API Call   : Found {len(results['responseData'])} ticket listings")
        
        listings = []
        for result in results['responseData']:
            listing = TicketListing(
                id=str(result['id']).split('@')[1],
                seats=str(result['splits'][0]),
                type=result['type'],
                area=result['area'],
                section=result['section'],
                row=result['row'],
                price=result['pricing']['prices'][0]['netSellingPrice'] / 100
            )
            listings.append(listing)
        
        return listings