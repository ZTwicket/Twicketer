"""Utility functions for the Twicket Bot."""

from typing import List
from ..models.ticket import TicketListing


def sort_listings_by_section(listings: List[TicketListing]) -> List[TicketListing]:
    """Sort ticket listings by section."""
    return sorted(listings, key=lambda x: x.section)


def format_ticket_info(listing: TicketListing) -> str:
    """Format ticket information for logging."""
    return f"Section: {listing.section}, Row: {listing.row}, Seats: {listing.seats}, Price: £{listing.price}"


def is_valid_seat_count(seats: str, max_seats: int) -> bool:
    """Check if seat count is within acceptable limits."""
    try:
        seat_count = int(seats)
        return 1 <= seat_count < max_seats
    except ValueError:
        return False