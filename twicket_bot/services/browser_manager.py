import logging
from typing import Optional
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, Page

from ..core.config import TwicketConfig


class BrowserManager:
    """Manages Playwright browser instance and page context."""
    
    def __init__(self, config: TwicketConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    def initialize(self) -> Page:
        """Initialize browser and return page instance."""
        self.logger.info("Browser    : Initializing Playwright...")
        self.playwright = sync_playwright().start()
        
        self.logger.info("Browser    : Launching Chromium browser (headless mode)")
        self.browser = self.playwright.chromium.launch(headless=self.config.headless)
        
        self.logger.info("Browser    : Creating browser context with cookies and user agent")
        self.context = self.browser.new_context(user_agent=self.config.user_agent)
        
        # Add required cookies
        self.context.add_cookies(self.config.cookies)
        
        self.page = self.context.new_page()
        self.logger.info("Browser    : Navigating to Twickets homepage to establish session")
        self.page.goto('https://www.twickets.live')
        self.logger.info("Browser    : Browser initialization complete")
        
        return self.page
    
    def cleanup(self) -> None:
        """Clean up browser resources."""
        self.logger.info("Browser    : Cleaning up browser resources...")
        
        if self.page:
            self.page.close()
            self.page = None
            
        if self.context:
            self.context.close()
            self.context = None
            
        if self.browser:
            self.browser.close()
            self.browser = None
            
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
            
        self.logger.info("Browser    : Browser cleanup complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self.initialize()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()