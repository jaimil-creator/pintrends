import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scraper.browser import PinterestBrowser

async def setup_auth():
    print("--- Pinterest Auth Setup ---")
    print("1. Browser will open.")
    print("2. Log in manually to Pinterest.")
    print("3. Return here and press ENTER to save your session.")
    
    # Force headful for interaction
    browser = PinterestBrowser(headless=False, auth_file="auth.json")
    await browser.start()
    
    try:
        await browser.navigate("https://www.pinterest.com/login/")
        
        # portable input for async? currently running in terminal
        # simple blocking input is fine here for a setup script
        input("\nPress ENTER after you have successfully logged in...")
        
        await browser.save_state()
        print("Session saved successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser.close()

if __name__ == "__main__":
    asyncio.run(setup_auth())
