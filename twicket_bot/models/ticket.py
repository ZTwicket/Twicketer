from dataclasses import dataclass
from typing import Optional, Any, Dict, List


@dataclass
class TicketListing:
    """Represents a ticket listing from the API."""
    id: str
    seats: str
    type: str
    area: str
    section: str
    row: str
    price: float


@dataclass
class DeliveryPlan:
    """Delivery plan information for tickets."""
    delivery_method: int
    title: str


@dataclass
class TicketBlock:
    """Ticket block information."""
    block_id: str


@dataclass
class TicketAvailability:
    """Ticket availability response."""
    available: bool
    block: Optional[TicketBlock]
    delivery_plan: List[DeliveryPlan]


@dataclass
class LoginResponse:
    """Login API response."""
    response_data: Optional[str] = None
    status_code: int = 0
    
    @property
    def is_successful(self) -> bool:
        return self.response_data is not None


@dataclass
class APIResponse:
    """Generic API response wrapper."""
    json_data: Optional[Dict[str, Any]]
    status: int
    headers: Dict[str, str]
    text: str
    
    @property
    def is_successful(self) -> bool:
        return 200 <= self.status < 300