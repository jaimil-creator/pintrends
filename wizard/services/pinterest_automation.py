"""
Pinterest Automation Service using Playwright.
Posts pins to Pinterest by automating a real browser session.
No official API required.
"""

import os
import time
import json
import tempfile
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load env from root
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Path to store Pinterest cookies/session
AUTH_FILE = Path(__file__).resolve().parent.parent.parent / 'auth.json'


class PinterestAutomationService:
    """
    Automates Pinterest pin posting using Playwright browser automation.
    
    Setup:
    1. Set PINTEREST_EMAIL and PINTEREST_PASSWORD in .env
    2. OR Ensure 'auth.json' exists with valid session (from previous login or scraper)
    
    Usage:
        service = PinterestAutomationService()
        url = service.post_pin(image_url="...", title="...", description="...")
    """
    
    def __init__(self):
        self.email = os.getenv('PINTEREST_EMAIL', '')
        self.password = os.getenv('PINTEREST_PASSWORD', '')
        self.board_name = os.getenv('PINTEREST_BOARD', '')
    
    def _download_image(self, image_url: str) -> str:
        """Download image from URL to a temp file and return the path."""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Determine extension
            content_type = response.headers.get('content-type', 'image/png')
            ext = '.png'
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'webp' in content_type:
                ext = '.webp'
            
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
            tmp.write(response.content)
            tmp.close()
            return tmp.name
        except Exception as e:
            raise Exception(f"Failed to download image: {e}")
    
    def _save_state(self, context):
        """Save browser state (cookies, storage) for future sessions."""
        context.storage_state(path=AUTH_FILE)
        print(f"✅ Pinterest session saved to {AUTH_FILE}")
    
    def _login(self, page, context):
        """Login to Pinterest using email/password."""
        if not self.email or not self.password:
            raise Exception(
                "Pinterest credentials not configured and no valid session found. "
                "Please set PINTEREST_EMAIL and PINTEREST_PASSWORD in your .env file."
            )
        
        print("🔐 Logging into Pinterest...")
        page.goto("https://www.pinterest.com/login/", wait_until="networkidle")
        time.sleep(2)
        
        # Fill email
        email_input = page.locator('input[name="id"], input[type="email"], #email')
        email_input.fill(self.email)
        time.sleep(0.5)
        
        # Fill password
        pwd_input = page.locator('input[name="password"], input[type="password"], #password')
        pwd_input.fill(self.password)
        time.sleep(0.5)
        
        # Click login button
        login_btn = page.locator('button[type="submit"], div[data-test-id="registerFormSubmitButton"]')
        login_btn.click()
        
        # Wait for navigation
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(3)
        
        # Check if login was successful
        if "login" in page.url.lower():
            raise Exception("Login failed. Please check your credentials or try manual login.")
        
        print("✅ Pinterest login successful!")
        self._save_state(context)
    
    def post_pin(self, image_url: str, title: str, description: str, link: str = '') -> str:
        """
        Post a pin to Pinterest.
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise Exception(
                "Playwright is not installed. Run: pip install playwright && playwright install chromium"
            )
        
        # Download image to temp file
        image_path = self._download_image(image_url)
        
        try:
            with sync_playwright() as p:
                # Launch browser
                has_auth = AUTH_FILE.exists()
                browser = p.chromium.launch(headless=False) # Headed mode for better reliability initially
                
                # Context with storage state if available
                if has_auth:
                    print(f"📂 Loading session from {AUTH_FILE}...")
                    context = browser.new_context(
                        storage_state=AUTH_FILE,
                        viewport={"width": 1280, "height": 900},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                else:
                    context = browser.new_context(
                        viewport={"width": 1280, "height": 900},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                
                page = context.new_page()
                
                # Navigate to check auth
                try:
                    page.goto("https://www.pinterest.com/", wait_until="domcontentloaded")
                    time.sleep(4)
                except Exception as e:
                    print(f"Navigation error: {e}")
                
                # Check login status
                is_logged_in = False
                if "login" not in page.url.lower() and page.locator('div[data-test-id="header-profile"]').count() > 0:
                     is_logged_in = True
                
                if not is_logged_in:
                    print("⚠️ Session expired or invalid, logging in...")
                    self._login(page, context)
                
                # Navigate to pin creation
                print("📌 Creating new pin...")
                page.goto("https://www.pinterest.com/pin-creation-tool/", wait_until="domcontentloaded")
                
                # Wait for the UI to settle
                try:
                    page.wait_for_selector('div[data-test-id="pin-builder"]', timeout=15000)
                except:
                    pass
                
                # Upload image
                try:
                    file_input = page.locator('input[type="file"]')
                    file_input.wait_for(state="attached", timeout=10000)
                    file_input.set_input_files(image_path)
                    time.sleep(10)  # Extended wait for slower connections/processing
                except Exception as e:
                    print(f"❌ Image upload failed: {e}")
                    page.screenshot(path="debug_upload_error.png")
                    raise Exception(f"Image upload failed: {e}")
                
                print(f"Current URL: {page.url}")
                
                # Fill title
                try:
                    # Broad selectors for title to handle localization/variations
                    title_selector = 'input[id*="title"], textarea[id*="title"], [data-test-id*="title"] textarea, [data-test-id*="title"] input, [aria-label*="Title"], [aria-label*="title"]'
                    page.wait_for_selector(title_selector, timeout=15000)
                    title_input = page.locator(title_selector).first
                    title_input.click(force=True)
                    title_input.fill(title[:100])
                    time.sleep(0.5)
                except Exception as e:
                    print(f"⚠️ Could not fill title: {e}")

                # Fill description
                try:
                    desc_selector = 'div[data-test-id*="description"] div[contenteditable="true"], textarea[id*="description"], [aria-label*="Description"], [aria-label*="description"]'
                    page.wait_for_selector(desc_selector, timeout=5000) # Short timeout as container might be clicked
                    desc_input = page.locator(desc_selector).first
                    desc_input.click(force=True)
                    desc_input.fill(description[:500])
                    time.sleep(0.5)
                except Exception as e:
                     # Attempt container click fallback
                    try:
                        desc_container = page.locator('div[data-test-id*="description"], [aria-label*="Description"], [aria-label*="description"]').first
                        if desc_container.count() > 0:
                            desc_container.click(force=True)
                            time.sleep(0.5)
                            # Retry input
                            page.locator(desc_selector).first.fill(description[:500])
                    except:
                        print(f"⚠️ Could not fill description: {e}")
                
                # Fill link (if provided)
                if link:
                    try:
                        link_input = page.locator('input[placeholder*="link"], input[placeholder*="url"], input[data-test-id="pin-draft-link"]')
                        if link_input.count() > 0:
                            link_input.first.fill(link)
                            time.sleep(0.5)
                    except:
                        pass
                
                # Select board (if configured)
                if self.board_name:
                    print(f"📋 Selecting board: {self.board_name}")
                    try:
                        # Open dropdown
                        board_selector = page.locator('[data-test-id="board-dropdown-select-button"], [aria-label*="board"], button[data-test-id*="board"]')
                        if board_selector.count() > 0:
                            board_selector.first.click()
                            time.sleep(2)
                            
                            # Type into search if available (makes selection robust)
                            search_input = page.locator('[data-test-id="board-dropdown-search-input"], input[aria-label="Search"], input[placeholder*="Search"]')
                            if search_input.count() > 0:
                                search_input.first.fill(self.board_name)
                                time.sleep(1)
                            
                            # Click the board
                            board_option = page.locator(f'div[title="{self.board_name}"], div[aria-label="{self.board_name}"], div[data-test-id="board-row-{self.board_name}"]')
                            if board_option.count() > 0:
                                board_option.first.click()
                                time.sleep(1)
                            else:
                                print(f"⚠️ Board '{self.board_name}' not found in dropdown")
                    except Exception as e:
                        print(f"⚠️ Board selection skipped: {e}")
                
                # Click Publish
                publish_btn = page.locator('[data-test-id="board-dropdown-save-button"], button:has-text("Publish"), button:has-text("Save")')
                if publish_btn.count() > 0:
                    publish_btn.first.click()
                    time.sleep(5)
                    print("✅ Pin published successfully!")
                else:
                    print("⚠️ Could not find Publish button")
                
                # Try to get the pin URL
                pin_url = page.url if 'pin/' in page.url else ''
                
                # Save state for next time
                self._save_state(context)
                
                browser.close()
                
                return pin_url
        finally:
            # Clean up temp file
            try:
                os.unlink(image_path)
            except:
                pass
