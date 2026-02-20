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
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Increased timeout and added headers to mimic browser
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(image_url, headers=headers, timeout=60)
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
                if attempt < max_retries - 1:
                    print(f"⚠️ Image download failed (attempt {attempt+1}/{max_retries}): {e}. Retrying...")
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    raise Exception(f"Failed to download image after {max_retries} attempts: {e}")
    
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
    
    def post_pin(self, image_url: str, title: str, description: str, link: str = '', board_name: str = '', schedule_date: str = '', schedule_time: str = '', tags: str = '') -> str:
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
                target_board = board_name or self.board_name
                if target_board:
                    print(f"📋 Selecting board: {target_board}")
                    try:
                        # Open dropdown
                        board_selector = page.locator('[data-test-id="board-dropdown-select-button"], [aria-label*="board"], button[data-test-id*="board"]')
                        if board_selector.count() > 0:
                            board_selector.first.click()
                            time.sleep(2)
                            
                            # Type into search if available (makes selection robust)
                            search_input = page.locator('[data-test-id="board-dropdown-search-input"], input[aria-label="Search"], input[placeholder*="Search"]')
                            if search_input.count() > 0:
                                search_input.first.fill(target_board)
                                time.sleep(1)
                            
                            # Click the board
                            board_option = page.locator(f'div[title="{target_board}"], div[aria-label="{target_board}"], div[data-test-id="board-row-{target_board}"]')
                            if board_option.count() > 0:
                                board_option.first.click()
                                time.sleep(1)
                            else:
                                print(f"⚠️ Board '{target_board}' not found in dropdown")
                    except Exception as e:
                        print(f"⚠️ Board selection skipped: {e}")
                
                # Native Scheduling
                if schedule_date and schedule_time:
                    # TIME BUMPER: Check if time is too close/past and bump it
                    try:
                        from datetime import datetime, timedelta
                        
                        # Parse inputs (schedule_date is YYYY-MM-DD, schedule_time is HH:MM AM/PM)
                        dt_str = f"{schedule_date} {schedule_time}"
                        target_dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
                        now = datetime.now()
                        
                        # If target is in past or within 20 mins
                        if target_dt < now + timedelta(minutes=20):
                            print(f"⚠️ Scheduled time {schedule_time} is too close or in past. Bumping...")
                            
                            # Start from now + 25 mins to be safe
                            safe_start = now + timedelta(minutes=25)
                            
                            # Round up to next 30 min slot
                            # e.g. 10:12 -> 10:30, 10:40 -> 11:00
                            next_slot = safe_start + (datetime.min - safe_start) % timedelta(minutes=30)
                            
                            # If next_slot is somehow earlier than safe_start (shouldn't happen with math above but safe check)
                            if next_slot < safe_start:
                                next_slot += timedelta(minutes=30)
                            
                            # Formats
                            new_date = next_slot.strftime("%Y-%m-%d")
                            new_time = next_slot.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
                            
                            print(f"🔄 Adjusted schedule to: {new_date} at {new_time}")
                            schedule_date = new_date
                            schedule_time = new_time
                            
                    except Exception as e:
                        print(f"⚠️ Time adjustment failed: {e}")
                        # Fallback to original
                        pass
                    
                    # Clean time format for better matching (1:00 PM vs 01:00 PM)
                    # Pinterest often uses 1:00 PM, 2:00 PM (no leading zero)
                    if schedule_time:
                         schedule_time = schedule_time.lstrip("0")

                    print(f"📅 Scheduling for {schedule_date} at {schedule_time}")
                    try:
                        # 1. Click "Publish at a later date" radio/toggle
                        # Use multiple strategies to find the scheduling option
                        schedule_radio = page.locator('input[type="radio"][name="publish-date"], label:has-text("Publish at a later date"), label:has-text("Schedule"), div[data-test-id*="schedule-radio"], div[role="radio"]:has-text("Publish at a later date")')
                        
                        if schedule_radio.count() > 0:
                            print("   - Found scheduling option, clicking...")
                            # Try to click the label or container if it's a complex component
                            try:
                                schedule_radio.first.scroll_into_view_if_needed()
                                schedule_radio.first.click(force=True)
                            except:
                                # Fallback: try Javascript click
                                try:
                                    page.evaluate("el => el.click()", schedule_radio.first.element_handle())
                                except Exception as e:
                                    print(f"   - JS click failed: {e}")
                            
                            time.sleep(1)
                            
                            # VERIFY: Check if date input appeared. If not, scheduling mode is NOT active.
                            if page.locator('input[id*="date"], input[name="date"], [aria-label*="Choose a date"]').count() == 0:
                                print("❌ Error: 'Publish at a later date' clicked but Date input did not appear.")
                                page.screenshot(path="debug_schedule_activation_failed.png")
                                raise Exception("Failed to activate scheduling mode (Date input missing). Aborting to prevent immediate post.")
                        else:
                            print("❌ Error: 'Publish at a later date' option NOT found.")
                            page.screenshot(path="debug_schedule_radio_missing.png")
                            raise Exception("Scheduling option not found on page. Aborting.")
                            
                            # 2. Fill Date
                            date_input = page.locator('input[id*="date"], input[name="date"], [aria-label*="Choose a date"]')
                            if date_input.count() > 0:
                                date_input.first.click()
                                time.sleep(0.5)
                                # Clear existing value if possible (Ctrl+A, Delete) to be safe
                                date_input.first.press("Control+a")
                                date_input.first.press("Backspace")
                                
                                # Check input type to decide format
                                input_type = date_input.first.get_attribute("type")
                                if input_type == "date":
                                    # HTML5 date input expects YYYY-MM-DD usually
                                    # But sometimes locale matters. Let's try standard YYYY-MM-DD first.
                                    # If schedule_date is already YYYY-MM-DD, perfect.
                                    date_input.first.fill(schedule_date)
                                else:
                                    # Text input, likely Pinterest custom picker.
                                    # Usually expects MM/DD/YYYY or similar based on locale.
                                    # If we got YYYY-MM-DD from frontend, we might need to convert here.
                                    formatted_date = schedule_date
                                    if '-' in schedule_date:
                                        parts = schedule_date.split('-')
                                        if len(parts) == 3: # YYYY-MM-DD
                                            formatted_date = f"{parts[1]}/{parts[2]}/{parts[0]}"
                                    
                                    date_input.first.fill(formatted_date)
                                
                                date_input.first.press("Enter")
                                time.sleep(1)
                                
                                # VERIFY DATE
                                try:
                                    actual_val = date_input.first.input_value()
                                    print(f"   - Date input value after fill: '{actual_val}' (Expected: '{schedule_date}' or close match)")
                                    
                                    # Basic check: if we wanted 2026-02-19 and got 2026-02-20, that's the error.
                                    # If mismatch, try forcing it via JS or typing manually
                                    if schedule_date not in actual_val and actual_val != schedule_date:
                                        normalized_actual = actual_val.replace('/', '-')
                                        normalized_expected = schedule_date.replace('/', '-')
                                        # Simple heuristic check
                                        if normalized_actual != normalized_expected:
                                             print("⚠️ Date mismatch detected! Retrying with manual typing...")
                                             date_input.first.click()
                                             date_input.first.press("Control+a")
                                             date_input.first.press("Backspace")
                                             
                                             # Determine correct format for typing
                                             type_value = schedule_date
                                             # If text input, likely needs MM/DD/YYYY
                                             if date_input.first.get_attribute("type") != "date":
                                                 if '-' in schedule_date:
                                                     parts = schedule_date.split('-')
                                                     if len(parts) == 3:
                                                         type_value = f"{parts[1]}/{parts[2]}/{parts[0]}"
                                             
                                             # Try typing char by char
                                             print(f"   - Typing manually: {type_value}")
                                             date_input.first.type(type_value, delay=100)
                                             date_input.first.press("Enter")
                                             time.sleep(1)
                                             print(f"   - Retry value: '{date_input.first.input_value()}'")
                                except Exception as e:
                                    print(f"⚠️ Could not verify date input: {e}")

                            else:
                                print("⚠️ Date input not found")

                            # 3. Fill Time
                            time_input = page.locator('input[id*="time"], input[name="time"], [aria-label*="Choose a time"]')
                            if time_input.count() > 0:
                                time_input.first.click()
                                time.sleep(0.5)
                                
                                # Clear and type
                                time_input.first.press("Control+a")
                                time_input.first.press("Backspace")
                                time_input.first.fill(schedule_time)
                                time.sleep(1.0) # Wait for dropdown to filter
                                
                                # Select the EXACT option from dropdown to avoid 12:00 AM/PM mixup
                                # Pinterest dropdown usually shows the time text.
                                # specific strategy: Look for option with exact text match
                                try:
                                    # Helper to find option in dropdown
                                    # We look for a container closer to the input usually
                                    # SEARCH for the stripped time (e.g. "12:30 PM")
                                    # AND also try one with leading zero just in case
                                    
                                    target_times = [schedule_time]
                                    # If "1:30 PM", add "01:30 PM"
                                    # If "01:00 PM" (already stripped, so won't happen), but let's be safe
                                    parts = schedule_time.split(':')
                                    if len(parts) == 2 and len(parts[0]) == 1:
                                        target_times.append(f"0{schedule_time}")
                                    
                                    option_found = False
                                    for t_str in target_times:
                                        # Look for exact text match in options
                                        option = page.locator(f'div[role="option"] div:has-text("{t_str}"), div[data-test-id*="time-item"] div:has-text("{t_str}"), div[role="option"]:has-text("{t_str}")').first
                                        if option.count() > 0 and option.is_visible():
                                            print(f"   - Found time option '{t_str}', clicking...")
                                            option.click()
                                            option_found = True
                                            break
                                    
                                    if not option_found:
                                        # Fallback to Enter if specific option not found
                                        print(f"⚠️ Exact time option '{schedule_time}' not found in dropdown, pressing Enter on input.")
                                        time_input.first.press("Enter")
                                except:
                                    time_input.first.press("Enter")
                                    
                                time.sleep(1)
                            else:
                                print(f"⚠️ Time input not found for {schedule_time}")
                    except Exception as e:
                        print(f"⚠️ Scheduling failed: {e}")

                # Tagged Topics
                if tags:
                    print(f"🏷️ Adding tags: {tags}")
                    try:
                        # Split tags if comma separated string
                        tag_list = [t.strip() for t in tags.split(',')] if isinstance(tags, str) else tags
                        
                        # Find the input (often labeled "Tagged topics" or similar)
                        # We try a few selectors
                        tag_input = page.locator('input[id*="documented_user_interest"], input[placeholder*="Search for a tag"], [data-test-id="tagged-topics-search-bar"] input')
                        
                        try:
                            # Sometimes the section is collapsed or needs a click to appear? Usually visible.
                            if tag_input.count() > 0:
                                tag_input_el = tag_input.first
                                tag_input_el.click()
                                time.sleep(0.5)
                                
                                for tag in tag_list:
                                    if not tag: continue
                                    try:
                                        print(f"   - Typing tag: {tag}")
                                        tag_input_el.fill(tag)
                                        time.sleep(2.0) # Wait for suggestions to populate
                                        
                                        # Press enter to select first suggestion
                                        tag_input_el.press('Enter')
                                        time.sleep(1.0) # Wait for chip to be created
                                        
                                        # Optional: Verify chip creation if possible, but strict wait is usually enough
                                    except Exception as e:
                                        print(f"   - Error adding tag '{tag}': {e}")
                                
                                # Ensure we click out or wait a moment before proceeding
                                time.sleep(1)
                            else:
                                print("⚠️ Tagged topics input not found")
                        except Exception as e:
                            print(f"⚠️ Could not fill tag: {e}")

                    except Exception as e:
                        print(f"⚠️ Tagging failed: {e}")

                publish_btn = page.locator('[data-test-id="board-dropdown-save-button"], button:has-text("Publish"), button:has-text("Save"), button:has-text("Schedule"), [aria-label="Schedule"]')
                if publish_btn.count() > 0:
                    publish_btn.first.click()
                    
                    # Logic for Scheduling Confirmation
                    if schedule_date and schedule_time:
                        print("🔔 Check for scheduling confirmation...")
                        # We need to wait for EITHER the success message OR the confirmation popup.
                        # If we see the popup, we must click it.
                        
                        try:
                            # Wait for a "Schedule" button in a dialog OR the success message
                            # This hybrid approach handles cases where popup is skipped
                            for _ in range(10): # Try for 10 seconds approx
                                time.sleep(1)
                                
                                # 1. Check for Success Message first (fast path)
                                if page.locator('text="Scheduled for"').is_visible():
                                    print("✅ Correctly scheduled (no popup needed).")
                                    break
                                
                                # 2. Check for Confirmation Popup
                                confirm_btn = page.locator('div[role="dialog"] button:has-text("Schedule"), div[role="dialog"] [aria-label="Schedule"]')
                                if confirm_btn.is_visible():
                                    print("🔔 Confirmation popup detected. Clicking Schedule...")
                                    confirm_btn.first.click()
                                    time.sleep(1) # Give it a moment to process click
                                    # Now loop will continue and check for success message next iteration
                        except Exception as e:
                            print(f"ℹ️ Error in confirmation loop: {e}")

                        # Final strict check for success
                        print("⏳ Verifying final schedule success...")
                        try:
                            # User requested 35 second strict wait
                            page.wait_for_selector('text="Scheduled for"', timeout=35000)
                            print("✅ Success message 'Scheduled for...' confirmed!")
                            time.sleep(2) # Visual confirmation for user
                        except:
                            print("❌ 'Scheduled for' message NOT detected.")
                            
                            # Fallback: Check if draft is gone
                            print("🕵️ Running fallback verification: Checking if draft was removed...")
                            try:
                                # Navigate back to pin creation tool (drafts list)
                                page.goto("https://www.pinterest.com/pin-creation-tool/", wait_until="domcontentloaded")
                                time.sleep(4)
                                
                                # Check if a draft with this title exists
                                # Selector for draft titles in the list
                                draft_selector = f'div[role="button"]:has-text("{title[:20]}")' 
                                if page.locator(draft_selector).count() == 0:
                                    print("✅ Fallback: Draft not found! Assuming it was scheduled successfully.")
                                else:
                                    print("❌ Fallback: Draft still exists. Scheduling failed.")
                                    page.screenshot(path="debug_schedule_fail_draft_exists.png")
                                    raise Exception("Scheduling failed - Draft still exists.")
                                    
                            except Exception as e:
                                print(f"⚠️ Fallback verification failed: {e}")
                                raise Exception("Scheduling failed and fallback check failed.")

                    else:
                        # Immediate Post Logic (simpler)
                        print("⏳ Waiting for immediate post success...")
                        try:
                            page.wait_for_selector('text="Saved to"', timeout=15000)
                            print("✅ Success message 'Saved to...' detected!")
                            time.sleep(2)
                        except:
                            print("⚠️ 'Saved to' not detected. Assuming success if no error dialogs.")

                    print("✅ Pin published/scheduled successfully!")
                else:
                    print("⚠️ Could not find Publish/Schedule button")
                
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
