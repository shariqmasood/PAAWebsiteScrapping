"""
Project Overview:
-----------------
Title: PAA Tenders Scraper

Objective:
    This script automates the extraction of tender notices from the Pakistan Airports Authority (PAA)
    website (https://paa.gov.pk/allTender) and saves the results into a CSV file for further analysis.

Key Features:
    1. Uses Playwright (async API) to control a headless Chromium browser.
    2. Navigates to the PAA tenders page and waits for the tender listings to load.
    3. Extracts structured data (serial number, title, location, advertising date, closing date) from each row.
    4. Handles timeouts and takes a screenshot on failure to aid debugging.
    5. Aggregates the data into a pandas DataFrame and exports it as a UTF-8-encoded CSV.

Dependencies:
    - Python 3.7+
    - playwright (pip install playwright)
    - pandas (pip install pandas)
    - asyncio (built-in)
    - Ensure you have run `playwright install` after installing the playwright package.

Usage:
    1. Install dependencies:
         pip install playwright pandas
         playwright install
    2. Run the script:
         python main.py
    3. On success, a file named 'paa_tenders_playwright.csv' will be created in the working directory.

Source:
    Original code file: main.py :contentReference[oaicite:0]{index=0}&#8203;:contentReference[oaicite:1]{index=1}
"""

import asyncio
from playwright.async_api import async_playwright
import pandas as pd

async def scrape_tenders():
    """
    Main scraping coroutine:
    - Launches browser
    - Navigates to the PAA tenders page
    - Waits for the tender listings to appear
    - Parses each tender row into a Python dict
    - Saves all tenders to a CSV file
    """
    # Start Playwright in async context
    async with async_playwright() as p:
        # Launch Chromium browser; headless=False shows the browser window (set to True for headless mode)
        browser = await p.chromium.launch(headless=False)
        # Create a new browser context (isolated session, cookies, cache, etc.)
        context = await browser.new_context()
        # Open a new page/tab in the context
        page = await context.new_page()

        # Inform the user that navigation is starting
        print("✅ Loading page...")
        # Go to the PAA tenders URL; wait up to 60 seconds for the page to load
        await page.goto("https://paa.gov.pk/allTender", timeout=60000)

        # Wait for the main tender heading to appear to ensure content has loaded
        print("✅ Page loaded... waiting for tender content")
        try:
            # Look for the static text "INVITATION TO BID" as an anchor for page readiness
            await page.wait_for_selector("text=INVITATION TO BID", timeout=60000)
        except:
            # On timeout or error, capture a screenshot for debugging and exit
            await page.screenshot(path="error_screenshot.png", full_page=True)
            print("❌ Could not detect tender content. Screenshot saved.")
            return

        # Now wait for the row elements that contain the tender details
        print("✅ Waiting for div-based tender rows...")
        try:
            await page.wait_for_selector('div[role="row"]', timeout=60000)
        except:
            await page.screenshot(path="error_screenshot.png", full_page=True)
            print("❌ Rows not found. Screenshot saved.")
            return

        # Locate all rows representing tenders
        row_locator = page.locator('div[role="row"]')
        row_count = await row_locator.count()
        print(f"✅ Found {row_count} rows.")

        tenders = []  # List to accumulate tender data dicts

        # Iterate over each row and extract the columns (cells)
        for i in range(row_count):
            row = row_locator.nth(i)
            cells = row.locator('div[role="cell"]')
            # Only process rows that have at least 5 cells (to skip headers or malformed rows)
            if await cells.count() >= 5:
                # Build a dict for each tender
                tenders.append({
                    "Sr": (await cells.nth(0).inner_text()).strip(),
                    "Title": (await cells.nth(1).inner_text()).strip(),
                    "Location": (await cells.nth(2).inner_text()).strip(),
                    "Advertising Date": (await cells.nth(3).inner_text()).strip(),
                    "Closing Date": (await cells.nth(4).inner_text()).strip()
                })

        # Close the browser once scraping is done
        await browser.close()

        # Convert the list of dicts into a pandas DataFrame
        df = pd.DataFrame(tenders)
        # Export DataFrame to CSV with UTF-8 BOM to preserve character encoding
        df.to_csv("paa_tenders_playwright.csv", index=False, encoding='utf-8-sig')
        print(f"✅ Done. Saved {len(tenders)} tenders to 'paa_tenders_playwright.csv'.")

# Entry point for script execution
if __name__ == "__main__":
    # Run the async scraping function
    asyncio.run(scrape_tenders())
