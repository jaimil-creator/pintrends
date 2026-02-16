import asyncio
from playwright.async_api import async_playwright
import sys

async def generate_auth():
    async with async_playwright() as p:
        print("\n--- Pinterest Login Helper ---")
        print("This script will open a browser window for you to log in to Pinterest.")
        print("Once you are logged in, come back here and press ENTER.\n")
        
        # Launch visible browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Go to Pinterest login
        await page.goto("https://www.pinterest.com/login/")
        
        # Wait for user to press enter in terminal
        input("Log in to Pinterest in the browser, then press ENTER here to save the session...")
        
        # Save state
        await context.storage_state(path="auth.json")
        print("\nSuccess! 'auth.json' has been generated.")
        print("You can now upload this file to your VPS root directory.")
        
        await browser.close()

if __name__ == "__main__":
    try:
        asyncio.run(generate_auth())
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"\nError: {e}")
