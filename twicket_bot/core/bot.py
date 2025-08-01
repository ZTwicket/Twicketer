import logging
import random
import sys
import webbrowser
from time import sleep
from typing import Optional, List, Set
from datetime import datetime

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

from ..core.config import TwicketConfig
from ..services.browser_manager import BrowserManager
from ..services.api_client import TwicketAPIClient
from ..services.notification_service import NotificationService
from ..models.ticket import TicketListing


class TwicketBot:
    """Main bot orchestrator for ticket monitoring and purchasing."""
    
    def __init__(self, config: TwicketConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.browser_manager = BrowserManager(config)
        self.notification_service = NotificationService(config)
        self.api_client: Optional[TwicketAPIClient] = None
        self.auth_token: Optional[str] = None
        
        self.console = Console()
        self.status_messages = []
        self.found_tickets = {}
        self.opened_tickets: Set[str] = set() 
        self.monitoring_start_time = None
        self.tickets_processed = 0
        self.tickets_opened = 0
    
    def _get_random_sleep_time(self, base_time: float) -> float:
        """Get a random sleep time between base_time and base_time * 1.5 seconds."""
        return random.uniform(base_time, base_time * 1.5)

    def _add_status_message(self, message: str, style: str = ""):
        """Add a status message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_messages.append((timestamp, message, style))
        # Keep only last 10 messages
        if len(self.status_messages) > 10:
            self.status_messages.pop(0)
        
        self.logger.info(f"Status     : {message}")
    
    def _create_display_layout(self) -> Layout:
        """Create the display layout for the terminal UI."""
        layout = Layout()
        
        # Create status panel
        status_content = ""
        for timestamp, message, style in self.status_messages:
            status_content += f"[dim]{timestamp}[/dim] {message}\n"
        
        status_panel = Panel(
            status_content.strip() or "Waiting for status updates...",
            title="Status Log",
            border_style="cyan"
        )
        
        # Create recent activity content
        activity_content = ""
        
        if not self.found_tickets:
            activity_content = "[dim italic]No tickets found yet...[/dim italic]"
        else:
            # Get unique tickets, sorted by timestamp (most recent first)
            unique_tickets = list(self.found_tickets.values())
            # Sort by timestamp descending
            unique_tickets.sort(key=lambda x: x.get('timestamp', datetime.now()), reverse=True)
            # Take only the most recent 8 tickets
            recent_tickets = unique_tickets[:8]
            
            # Display in reverse chronological order (newest first)
            for ticket in recent_tickets:
                # Determine status style and icon
                status = ticket.get('status', '')
                status_style = "dim"
                status_icon = "⏳"
                if status == 'Opened in Browser':
                    status_style = "green bold"
                    status_icon = "🎯"
                elif status == 'Already Opened':
                    status_style = "dim green"
                    status_icon = "✅"
                elif status == 'Failed to Open':
                    status_style = "red"
                    status_icon = "❌"
                elif status == 'Checking...':
                    status_style = "yellow"
                    status_icon = "🔍"
                elif status == 'Skipped':
                    status_style = "dim yellow"
                    status_icon = "⏭️"
                elif status == 'No Longer Available':
                    status_style = "dim red"
                    status_icon = "🚫"
                elif status == 'No Block Info':
                    status_style = "red"
                    status_icon = "⚠️"
                
                # Format timestamp
                timestamp = ticket.get('timestamp', '')
                if timestamp:
                    timestamp = timestamp.strftime("%H:%M:%S")
                
                # Build ticket line with padded numbers, replacing empty/None values with '?'
                section = str(ticket.get('section') or '?').rjust(3)  # Right-pad section numbers
                row = str(ticket.get('row') or '?').rjust(3)          # Right-pad row numbers  
                seats = str(ticket.get('seats') or '?').rjust(2)      # Right-pad seat count
                price = str(ticket.get('price') or '?').rjust(6)      # Right-pad price
                
                # Create formatted line with single spaces
                activity_content += f"[dim]{timestamp}[/dim] "
                activity_content += f"[cyan][{section}][/cyan] "
                activity_content += f"[green][Row {row}][/green] "
                activity_content += f"[{seats} {'seat' if seats == '1' else 'seats'}] "
                activity_content += f"[yellow]£{price}[/yellow] "
                activity_content += f"[{status_style}][{status}][/{status_style}] "
                
                # Add link to listing if ticket has an ID
                if 'id' in ticket:
                    activity_content += f"[blue underline]https://www.twickets.live/app/block/{ticket['id']},{ticket['seats']}[/blue underline]"
                
                activity_content += "\n"
        
        # Create stats panel
        runtime = "00:00:00"
        if self.monitoring_start_time:
            elapsed = datetime.now() - self.monitoring_start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            runtime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        stats_text = f"""Runtime: {runtime}
Tickets Processed: {self.tickets_processed}
Tickets Opened: {self.tickets_opened}
Event ID: {self.config.event_id}
Min Seats: {self.config.min_seats} | Max Seats: {self.config.max_seats}
Max Price: £{self.config.max_price if self.config.max_price else 'No limit'}"""
        
        stats_panel = Panel(
            stats_text,
            title="Statistics",
            border_style="green"
        )
        
        # Create recent activity panel
        activity_panel = Panel(
            activity_content.strip() or "[dim italic]No tickets found yet...[/dim italic]",
            title="Recent Activity",
            border_style="cyan"
        )
        
        # Arrange layout without header
        layout.split_column(
            Layout(name="top_row", ratio=1),
            Layout(name="bottom_row", ratio=1)
        )
        
        layout["top_row"].split_row(
            Layout(status_panel, name="status", ratio=2),
            Layout(stats_panel, name="stats", ratio=1)
        )
        
        layout["bottom_row"].split_row(
            Layout(activity_panel, name="activity")
        )
        
        return layout
    
    def initialize(self) -> bool:
        """Initialize bot components."""
        try:
            self._add_status_message("Starting browser...", "yellow")
            page = self.browser_manager.initialize()
            
            self.api_client = TwicketAPIClient(self.config, page)
            
            self._add_status_message("Logging in...", "yellow")
            self.auth_token = self.api_client.login(self.config.user, self.config.password)
            
            if not self.auth_token:
                self._add_status_message("Authentication failed!", "red")
                return False
            
            self._add_status_message("Authentication successful ✓", "green")
            
            self.notification_service.notify_bot_started()
            self.monitoring_start_time = datetime.now()
            
            return True
            
        except Exception as e:
            self._add_status_message(f"Initialization failed: {e}", "red")
            return False
    
    def cleanup(self) -> None:
        """Clean up bot resources."""
        if self.browser_manager:
            self.browser_manager.cleanup()
    
    def _should_skip_listing(self, listing: TicketListing, ticket_availability) -> bool:
        """Check if listing should be skipped based on criteria."""
        # Skip if too few seats
        if int(listing.seats) < self.config.min_seats:
            self._add_status_message(f"Skipping - too few seats ({listing.seats})", "dim yellow")
            return True
        
        # Skip if too many seats
        if int(listing.seats) >= self.config.max_seats:
            self._add_status_message(f"Skipping - too many seats ({listing.seats})", "dim yellow")
            return True
        
        # Skip if price exceeds maximum
        if self.config.max_price is not None and float(listing.price) > self.config.max_price:
            self._add_status_message(f"Skipping - price too high (£{listing.price})", "dim yellow")
            return True
        
        # Skip if not available
        if not ticket_availability or not ticket_availability.available:
            self._add_status_message(f"Ticket unavailable", "dim red")
            # Mark as no longer available in the recent activity
            ticket_key = f"{listing.section}-{listing.row}-{listing.seats}"
            if ticket_key in self.found_tickets:
                self.found_tickets[ticket_key]['status'] = 'No Longer Available'
            return True
        
        # Skip meetup delivery if configured
        if self.config.skip_meetup_delivery and ticket_availability.delivery_plan:
            for plan in ticket_availability.delivery_plan:
                if plan.delivery_method == 1:
                    self._add_status_message(f"Skipping - meetup delivery", "dim yellow")
                    return True
        
        return False
    
    def _process_listing(self, listing: TicketListing) -> bool:
        """Process a single ticket listing. Returns True if ticket was successfully processed."""
        if not self.api_client or not self.auth_token:
            return False
        
        self.tickets_processed += 1
        
        # Create unique key for the ticket
        ticket_key = f"{listing.section}-{listing.row}-{listing.seats}-{listing.id}"
        
        # Add or update ticket info
        if ticket_key not in self.found_tickets:
            self.found_tickets[ticket_key] = {
                'id': listing.id,
                'section': listing.section,
                'row': listing.row,
                'seats': listing.seats,
                'price': listing.price,
                'status': 'Checking...',
                'timestamp': datetime.now()
            }
        else:
            # Update existing ticket
            self.found_tickets[ticket_key]['id'] = listing.id
            self.found_tickets[ticket_key]['status'] = 'Checking...'
            self.found_tickets[ticket_key]['timestamp'] = datetime.now()
        
        ticket_info = self.found_tickets[ticket_key]
        
        # Check availability
        ticket_availability = self.api_client.get_ticket_availability(listing.id, listing.seats)
        
        if self._should_skip_listing(listing, ticket_availability):
            ticket_info['status'] = 'Skipped'
            return False
        
        # Check if we've already opened this ticket
        if listing.id in self.opened_tickets:
            ticket_info['status'] = 'Already Opened'
            self._add_status_message(f"Already opened ticket in {listing.section} Row {listing.row}", "dim yellow")
            return False
        
        # Get block ID for URL construction
        if not ticket_availability.block:
            ticket_info['status'] = 'No Block Info'
            self._add_status_message(f"No block information available for ticket in {listing.section}", "red")
            return False
            
        block_id = ticket_availability.block.block_id
        
        # Open the ticket URL in browser
        ticket_url = f"https://www.twickets.live/app/block/{block_id},{listing.seats}"
        self._add_status_message(f"Opening ticket in browser: {listing.section} Row {listing.row}", "cyan bold")
        
        try:
            webbrowser.open(ticket_url)
            self.opened_tickets.add(listing.id)
            self.tickets_opened += 1
            ticket_info['status'] = 'Opened in Browser'
            self._add_status_message(f"✓ Opened ticket page for {listing.section} Row {listing.row}!", "green bold")
            
            # Send Discord notification
            self.notification_service.notify_ticket_found(listing, block_id, ticket_url)
            self.logger.info(f"Main loop   : Opened ticket: {ticket_url} (£{listing.price})")
            
            return True
            
        except Exception as e:
            ticket_info['status'] = 'Failed to Open'
            self._add_status_message(f"✗ Failed to open browser: {e}", "red bold")
            self.logger.error(f"Main loop   : Failed to open ticket: {ticket_url} - {e}")
            return False
    
    def run_monitoring_loop(self) -> None:
        """Run the main ticket monitoring loop."""
        # Set up file logging to prevent console output during live display
        import os
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"twicket_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        # Configure file handler for all loggers
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(levelname)s %(asctime)s: %(message)s", datefmt="%H:%M:%S"))
        
        # Get root logger and all module loggers
        root_logger = logging.getLogger()
        
        # Store original handlers and replace with file handler
        original_handlers = root_logger.handlers[:]
        root_logger.handlers = [file_handler]
        
        # Redirect stderr to suppress any print statements
        original_stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
        
        try:
            with Live(self._create_display_layout(), refresh_per_second=2, console=self.console, screen=True) as live:
                if not self.initialize():
                    sys.exit(1)
                
                try:
                    self._add_status_message("Entering main monitoring loop", "cyan")
                    self._add_status_message(f"Logs are being written to: {log_file}", "dim")
                    
                    while True:
                        try:
                            options = self.api_client.check_event_availability(self.config.event_id)
                            
                            if not options:
                                self._add_status_message("No tickets found", "dim")
                            else:
                                self._add_status_message(f"{len(options)} tickets found!", "cyan bold")
                                
                                # Sort by section and process
                                options.sort(key=lambda x: x.section)
                                
                                for listing in options:
                                    self.logger.info(f"Main loop  : Found ticket - Section: {listing.section}, Row: {listing.row}, Seats: {listing.seats}, Price: £{listing.price}")
                                    if self._process_listing(listing):
                                        # Successfully processed a ticket, could break here if needed
                                        pass
                            
                            # Update the live display
                            live.update(self._create_display_layout())
                            
                        except Exception as e:
                            self._add_status_message(f"Error: {e}", "red")
                        
                        sleep(self._get_random_sleep_time(self.config.time_delay))
                        
                except KeyboardInterrupt:
                    self._add_status_message("Shutting down...", "yellow")
                    live.stop()
                    # Restore stderr before printing
                    sys.stderr.close()
                    sys.stderr = original_stderr
                    print("\nExiting by user request.\n", file=sys.stderr)
                    
        finally:
            # Restore original logging configuration
            root_logger.handlers = original_handlers
            if sys.stderr != original_stderr:
                sys.stderr.close()
                sys.stderr = original_stderr
            self.cleanup()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()