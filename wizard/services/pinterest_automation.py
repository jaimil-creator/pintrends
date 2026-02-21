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
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                response = requests.get(image_url, headers=headers, timeout=60)
                response.raise_for_status()
                
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
        
        email_input = page.locator('input[name="id"], input[type="email"], #email')
        email_input.fill(self.email)
        time.sleep(0.5)
        
        pwd_input = page.locator('input[name="password"], input[type="password"], #password')
        pwd_input.fill(self.password)
        time.sleep(0.5)
        
        login_btn = page.locator('button[type="submit"], div[data-test-id="registerFormSubmitButton"]')
        login_btn.click()
        
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(3)
        
        if "login" in page.url.lower():
            raise Exception("Login failed. Please check your credentials or try manual login.")
        
        print("✅ Pinterest login successful!")
        self._save_state(context)
    
    def post_pin(self, image_url: str, title: str, description: str, link: str = '', board_name: str = '', schedule_date: str = '', schedule_time: str = '', tags: str = '') -> str:
        """
        Post a pin to Pinterest.
        
        Flow: image -> title/desc -> link -> board -> tags -> schedule toggle -> date -> time -> click Schedule
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
                browser = p.chromium.launch(headless=False)
                
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
                
                try:
                    page.wait_for_selector('div[data-test-id="pin-builder"]', timeout=15000)
                except:
                    pass
                
                # ===== 1. UPLOAD IMAGE =====
                try:
                    file_input = page.locator('input[type="file"]')
                    file_input.wait_for(state="attached", timeout=10000)
                    file_input.set_input_files(image_path)
                    time.sleep(10)
                except Exception as e:
                    print(f"❌ Image upload failed: {e}")
                    page.screenshot(path="debug_upload_error.png")
                    raise Exception(f"Image upload failed: {e}")
                
                print(f"Current URL: {page.url}")
                
                # ===== 2. FILL TITLE =====
                try:
                    title_selector = 'input[id*="title"], textarea[id*="title"], [data-test-id*="title"] textarea, [data-test-id*="title"] input, [aria-label*="Title"], [aria-label*="title"]'
                    page.wait_for_selector(title_selector, timeout=15000)
                    title_input = page.locator(title_selector).first
                    title_input.click(force=True)
                    title_input.fill(title[:100])
                    time.sleep(0.5)
                except Exception as e:
                    print(f"⚠️ Could not fill title: {e}")

                # ===== 3. FILL DESCRIPTION =====
                try:
                    desc_selector = 'div[data-test-id*="description"] div[contenteditable="true"], textarea[id*="description"], [aria-label*="Description"], [aria-label*="description"]'
                    page.wait_for_selector(desc_selector, timeout=5000)
                    desc_input = page.locator(desc_selector).first
                    desc_input.click(force=True)
                    desc_input.fill(description[:500])
                    time.sleep(0.5)
                except Exception as e:
                    try:
                        desc_container = page.locator('div[data-test-id*="description"], [aria-label*="Description"], [aria-label*="description"]').first
                        if desc_container.count() > 0:
                            desc_container.click(force=True)
                            time.sleep(0.5)
                            page.locator(desc_selector).first.fill(description[:500])
                    except:
                        print(f"⚠️ Could not fill description: {e}")
                
                # ===== 4. FILL LINK =====
                if link:
                    try:
                        link_input = page.locator('input[placeholder*="link"], input[placeholder*="url"], input[data-test-id="pin-draft-link"]')
                        if link_input.count() > 0:
                            link_input.first.fill(link)
                            time.sleep(0.5)
                    except:
                        pass
                
                # ===== 5. SELECT BOARD =====
                target_board = board_name or self.board_name
                if target_board:
                    print(f"📋 Selecting board: {target_board}")
                    try:
                        board_selector = page.locator('[data-test-id="board-dropdown-select-button"], [aria-label*="board"], button[data-test-id*="board"]')
                        if board_selector.count() > 0:
                            board_selector.first.click()
                            time.sleep(2)
                            
                            search_input = page.locator('[data-test-id="board-dropdown-search-input"], input[aria-label="Search"], input[placeholder*="Search"]')
                            if search_input.count() > 0:
                                search_input.first.fill(target_board)
                                time.sleep(1)
                            
                            board_option = page.locator(f'div[title="{target_board}"], div[aria-label="{target_board}"], div[data-test-id="board-row-{target_board}"]')
                            if board_option.count() > 0:
                                board_option.first.click()
                                time.sleep(1)
                            else:
                                print(f"⚠️ Board '{target_board}' not found in dropdown")
                    except Exception as e:
                        print(f"⚠️ Board selection skipped: {e}")
                
                # ===== 6. ADD TAGS (before scheduling per Pinterest UI flow) =====
                if tags:
                    print(f"🏷️ Adding tags: {tags}")
                    try:
                        tag_list = [t.strip() for t in tags.split(',')] if isinstance(tags, str) else tags
                        tag_input = page.locator('input[placeholder*="Search for a tag"]')
                        
                        if tag_input.count() > 0:
                            tag_input_el = tag_input.first
                            tag_input_el.click()
                            time.sleep(0.5)
                            
                            for tag in tag_list:
                                if not tag: continue
                                try:
                                    print(f"   - Typing tag: {tag}")
                                    tag_input_el.fill(tag)
                                    time.sleep(2.0)
                                    tag_input_el.press('Enter')
                                    time.sleep(1.0)
                                except Exception as e:
                                    print(f"   - Error adding tag '{tag}': {e}")
                            
                            time.sleep(1)
                        else:
                            print("⚠️ Tagged topics input not found")
                    except Exception as e:
                        print(f"⚠️ Tagging failed: {e}")

                # ===== 7. SCHEDULING (toggle + date + time) =====
                scheduling_active = False
                if schedule_date and schedule_time:
                    # TIME BUMPER
                    try:
                        from datetime import datetime, timedelta
                        dt_str = f"{schedule_date} {schedule_time}"
                        target_dt = datetime.strptime(dt_str, "%Y-%m-%d %I:%M %p")
                        now = datetime.now()
                        if target_dt < now + timedelta(minutes=20):
                            print(f"⚠️ Time too close/past. Bumping...")
                            safe_start = now + timedelta(minutes=25)
                            next_slot = safe_start + (datetime.min - safe_start) % timedelta(minutes=30)
                            if next_slot < safe_start:
                                next_slot += timedelta(minutes=30)
                            schedule_date = next_slot.strftime("%Y-%m-%d")
                            schedule_time = next_slot.strftime("%I:%M %p").lstrip("0")
                            print(f"🔄 Adjusted to: {schedule_date} at {schedule_time}")
                    except Exception as e:
                        print(f"⚠️ Time adjustment failed: {e}")
                    
                    if schedule_time:
                        schedule_time = schedule_time.lstrip("0")

                    print(f"📅 Scheduling for {schedule_date} at {schedule_time}")
                    try:
                        # STEP 7a: Scroll down and click the "Publish at a later date" toggle
                        print("   1️⃣ Clicking scheduling toggle...")
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        time.sleep(1)
                        
                        # Verified selector: div[data-test-id="pin-draft-switch-group"] with checkbox inside
                        toggle_clicked = False
                        toggle_container = page.locator('[data-test-id="pin-draft-switch-group"]')
                        if toggle_container.count() > 0:
                            print("   - Found toggle via data-test-id='pin-draft-switch-group'")
                            checkbox = toggle_container.locator('input[type="checkbox"]')
                            if checkbox.count() > 0:
                                checkbox.first.click(force=True)
                                toggle_clicked = True
                            else:
                                toggle_container.first.click()
                                toggle_clicked = True
                        
                        if not toggle_clicked:
                            # Fallback: click by text
                            txt_el = page.locator('text="Publish at a later date"')
                            if txt_el.count() > 0:
                                txt_el.first.click()
                                toggle_clicked = True
                        
                        if not toggle_clicked:
                            page.screenshot(path="debug_no_toggle.png")
                            raise Exception("Could not find scheduling toggle")
                        
                        time.sleep(3)
                        page.screenshot(path="debug_after_toggle.png")
                        
                        # STEP 7b: Verify date input appeared
                        # Pinterest changes placeholder format (MM/DD/YYYY or DD/MM/YYYY etc)
                        date_input = page.locator('input[placeholder="MM/DD/YYYY"], input[placeholder="DD/MM/YYYY"], input[placeholder="YYYY-MM-DD"], input[id*="date-field"], input[id*="schedule-date"], [data-test-id*="date"] input')
                        if date_input.count() == 0:
                            # Last resort: find any new input that appeared after toggle
                            date_input = page.locator('input[type="text"]').filter(has_text="")
                            # Check for any input near the toggle area
                            all_inputs = page.locator('[data-test-id="pin-draft-switch-group"] ~ * input, [data-test-id="pin-draft-switch-group"] + * input')
                            if all_inputs.count() > 0:
                                date_input = all_inputs
                        
                        if date_input.count() == 0:
                            page.screenshot(path="debug_no_date_input.png")
                            raise Exception("Date input not found after toggle. Scheduling did not activate.")
                        
                        # Detect the placeholder format
                        date_placeholder = date_input.first.get_attribute('placeholder') or ''
                        print(f"   - Date input placeholder: '{date_placeholder}'")
                        
                        scheduling_active = True
                        print("   ✅ Scheduling mode active! Date input found.")
                        
                        # STEP 7c: Fill Date
                        print("   2️⃣ Setting date...")
                        from datetime import datetime
                        dt = datetime.strptime(schedule_date, "%Y-%m-%d")
                        
                        # Format date based on detected placeholder
                        if 'DD/MM' in date_placeholder:
                            formatted_date = dt.strftime("%d/%m/%Y")  # DD/MM/YYYY
                        elif 'YYYY' in date_placeholder and '-' in date_placeholder:
                            formatted_date = dt.strftime("%Y-%m-%d")  # YYYY-MM-DD
                        else:
                            formatted_date = dt.strftime("%m/%d/%Y")  # MM/DD/YYYY (default)
                        
                        print(f"   - Formatted date: {formatted_date} (for placeholder '{date_placeholder}')")
                        
                        date_input.first.click()
                        time.sleep(0.5)
                        
                        # Try calendar picker first
                        cal_ok = False
                        try:
                            month_name = dt.strftime("%B")
                            day_num = dt.day
                            if 11 <= (day_num % 100) <= 13:
                                suf = 'th'
                            else:
                                suf = {1: 'st', 2: 'nd', 3: 'rd'}.get(day_num % 10, 'th')
                            
                            day_option = page.locator(f'div.react-datepicker__day[aria-label*="{month_name} {day_num}{suf}"]')
                            if day_option.count() > 0 and day_option.first.is_visible():
                                print(f"   - Calendar: clicking {month_name} {day_num}{suf}")
                                day_option.first.click(force=True)
                                cal_ok = True
                                time.sleep(1)
                        except:
                            pass
                        
                        if not cal_ok:
                            print(f"   - Typing date: {formatted_date}")
                            date_input.first.click()
                            time.sleep(0.3)
                            date_input.first.press("Control+a")
                            date_input.first.press("Backspace")
                            date_input.first.type(formatted_date, delay=100)
                            date_input.first.press("Tab")
                            time.sleep(1)
                        
                        try:
                            print(f"   - Date value: '{date_input.first.input_value()}'")
                        except:
                            pass
                        
                        # STEP 7d: Fill Time
                        # Verified selector: input[placeholder="Time"]
                        print("   3️⃣ Setting time...")
                        time_field = page.locator('input[placeholder="Time"]')
                        if time_field.count() > 0:
                            time_field.first.click()
                            time.sleep(1)
                            
                            # Build time variants, prioritizing Pinterest's 0-padded hour (e.g. 02:30 AM)
                            time_variants = []
                            parts = schedule_time.split(':')
                            if len(parts) == 2:
                                hr = parts[0].lstrip('0')  # ensure no leading zeros to start
                                m_ampm = parts[1]
                                # 1. Try zero-padded first: "02:30 AM" or "12:30 AM"
                                time_variants.append(f"{hr.zfill(2)}:{m_ampm}")
                                # 2. Try unpadded fallback: "2:30 AM"
                                time_variants.append(f"{hr}:{m_ampm}")
                            else:
                                time_variants.append(schedule_time)
                            
                            time_ok = False
                            for t in time_variants:
                                try:
                                    # Use :text-is for exact match to prevent '12:30 AM' matching '2:30 AM'
                                    # Fallback to the specific div structure provided by user: [id*="time-field-dropdown-item-"] div
                                    opt_selector = f'[role="menuitem"]:text-is("{t}"), [role="option"]:text-is("{t}"), [id*="time-field-dropdown-item-"] div:text-is("{t}")'
                                    opt = page.locator(opt_selector)
                                    
                                    # If not in DOM yet, we might need to scroll the menu container
                                    if opt.count() == 0 or not opt.first.is_visible():
                                        menu = page.locator('[role="menu"], [role="listbox"]').last
                                        if menu.count() > 0 and menu.is_visible():
                                            print(f"   - Scrolling dropdown to find '{t}'...")
                                            for _ in range(25):  # scroll max 25 times
                                                menu.evaluate("el => el.scrollBy(0, 150)")
                                                time.sleep(0.5)  # Give React time to render virtualized items
                                                if opt.count() > 0 and opt.first.is_visible():
                                                    break
                                            
                                    if opt.count() > 0 and opt.first.is_visible():
                                        print(f"   - Dropdown: clicking '{t}'")
                                        opt.first.scroll_into_view_if_needed()
                                        opt.first.click(force=True)
                                        time_ok = True
                                        time.sleep(1)
                                        break
                                except Exception as e:
                                    print(f"   - Dropdown error for '{t}': {e}")
                            
                            if not time_ok:
                                print(f"   - Typing time: {schedule_time}")
                                time_field.first.click()
                                time.sleep(0.3)
                                time_field.first.press("Control+a")
                                time_field.first.press("Backspace")
                                time_field.first.type(schedule_time, delay=100)
                                time_field.first.press("Tab")
                                time.sleep(1)
                            
                            try:
                                print(f"   - Time value: '{time_field.first.input_value()}'")
                            except:
                                pass
                        else:
                            print("⚠️ Time input (placeholder='Time') not found")
                        
                        page.screenshot(path="debug_schedule_filled.png")
                        print("   ✅ Schedule date/time filled.")
                        
                    except Exception as e:
                        print(f"❌ Scheduling failed: {e}")
                        print("🛑 ABORTING to prevent immediate post.")
                        page.screenshot(path="debug_scheduling_abort.png")
                        raise Exception(f"Scheduling failed, aborting: {e}")

                # ===== 8. CLICK THE ACTION BUTTON (Schedule or Publish) =====
                # Scroll back to top where the button is
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(1)
                
                target_text = "Schedule" if scheduling_active else "Publish"
                print(f"🔍 Looking for '{target_text}' button...")
                
                # Iterate ALL <button> elements to find exact text match
                action_btn = None
                all_buttons = page.locator('button')
                btn_count = all_buttons.count()
                
                for i in range(btn_count):
                    try:
                        btn = all_buttons.nth(i)
                        txt = (btn.text_content() or '').strip()
                        if btn.is_visible() and txt == target_text:
                            action_btn = btn
                            print(f"   ✅ Found '{target_text}' button (index {i})")
                            break
                    except:
                        pass
                
                # If exact match not found, try partial match
                if action_btn is None:
                    for i in range(btn_count):
                        try:
                            btn = all_buttons.nth(i)
                            txt = (btn.text_content() or '').strip()
                            if btn.is_visible() and target_text.lower() in txt.lower():
                                action_btn = btn
                                print(f"   ⚠️ Partial match: button[{i}] = '{txt}'")
                                break
                        except:
                            pass
                
                if action_btn is None:
                    # Dump all visible buttons for debugging
                    print(f"❌ '{target_text}' button NOT FOUND! All visible buttons:")
                    for i in range(btn_count):
                        try:
                            btn = all_buttons.nth(i)
                            txt = (btn.text_content() or '').strip()
                            if btn.is_visible() and txt:
                                print(f"   [{i}] '{txt}'")
                        except:
                            pass
                    page.screenshot(path="debug_no_action_btn.png")
                    raise Exception(f"'{target_text}' button not found on page")
                
                # Safety: don't click Publish when we meant Schedule
                final_text = (action_btn.text_content() or '').strip()
                if scheduling_active and final_text.lower() == 'publish':
                    print(f"❌ SAFETY: Found 'Publish' but expected 'Schedule'. Aborting.")
                    page.screenshot(path="debug_safety_abort.png")
                    raise Exception("Safety abort: Button says 'Publish' not 'Schedule'")
                
                page.screenshot(path="debug_before_click.png")
                print(f"   🔘 Clicking '{final_text}'...")
                action_btn.click()
                
                # ===== 9. POST-CLICK VERIFICATION =====
                if scheduling_active:
                    print("🔔 Verifying scheduling...")
                    try:
                        for _ in range(15):
                            time.sleep(1)
                            # Check for success
                            if page.locator('text="Scheduled for"').is_visible():
                                print("✅ 'Scheduled for' confirmed!")
                                break
                            # Check for confirmation dialog
                            cnf = page.locator('div[role="dialog"] button:has-text("Schedule")')
                            if cnf.count() > 0 and cnf.first.is_visible():
                                print("🔔 Confirmation popup, clicking Schedule...")
                                cnf.first.click()
                                time.sleep(5)  # Wait for Pinterest to process
                    except Exception as e:
                        print(f"ℹ️ Confirmation check error: {e}")
                    
                    time.sleep(40)  # Give Pinterest time to finalize
                    page.screenshot(path="debug_after_schedule.png")
                    print("✅ Pin scheduled!")
                else:
                    print("⏳ Waiting for publish confirmation...")
                    try:
                        page.wait_for_selector('text="Saved to"', timeout=15000)
                        print("✅ Published!")
                        time.sleep(2)
                    except:
                        print("⚠️ 'Saved to' not detected.")
                
                print("✅ Pin operation complete!")
                
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
