import asyncio
import random
from playwright.async_api import async_playwright, Page, BrowserContext

class PinterestBrowser:
    def __init__(self, headless: bool = False, auth_file: str = "auth.json"):
        self.headless = headless
        self.auth_file = auth_file
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def start(self):
        """Initializes the Playwright browser instance."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"] # Basic evasion
        )
        # Load auth state if exists
        try:
            self.context = await self.browser.new_context(
                storage_state=self.auth_file,
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            print(f"Loaded auth state from {self.auth_file}")
        except Exception:
            print("No auth file found or invalid, starting fresh.")
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        
        # Add basic stealth scripts if needed, for now just standard
        self.page = await self.context.new_page()

    async def save_state(self):
        """Saves the current browser state (cookies, local storage) to file."""
        if self.context:
            await self.context.storage_state(path=self.auth_file)
            print(f"Auth state saved to {self.auth_file}")

    async def close(self):
        """Closes the browser resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def navigate(self, url: str):
        """Navigates to a URL with random delays to mimic human behavior."""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        await self.page.goto(url, wait_until="domcontentloaded")
        await self.random_delay(2, 4)

    async def scroll_to_bottom(self, times: int = 3):
        """Scrolls the page to load more content."""
        if not self.page:
            return

        for _ in range(times):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.random_delay(2, 4)

    async def random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Waits for a random amount of time."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)

    async def get_content(self) -> str:
        if not self.page:
            return ""
        return await self.page.content()
