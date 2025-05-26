import asyncio
import csv
import os
from playwright.async_api import async_playwright

# URL of the NOTAMs page to scrape
URL = "https://paa.gov.pk/aeronautical-information/notice-to-airmen"

# Output CSV file where scraped data will be saved
CSV_FILE = "paa_notams_detailed.csv"

async def scrape_notams():
    # Initialize Playwright and launch Chromium browser (non-headless for debugging)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        # Create a new browser context to isolate session data (cookies/cache)
        context = await browser.new_context()
        # Open a new tab/page in the browser context
        page = await context.new_page()

        print("✅ Page loaded. Starting...")
        # Navigate to the NOTAMs URL
        await page.goto(URL)
        # Wait for 3 seconds to ensure dynamic content is fully loaded
        await page.wait_for_timeout(3000)

        # Check if output CSV already exists to decide if header needs writing
        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
            # Define CSV writer with desired columns
            writer = csv.DictWriter(file, fieldnames=["Location", "NOTAM", "Start Date", "End Date", "Status", "Text", "Details"])
            if not file_exists:
                # Write header row if file is new
                writer.writeheader()

            page_number = 1
            total_rows_processed = 0

            # Main scraping loop to paginate through all NOTAM pages
            while True:
                print(f"🔁 Processing Page {page_number}...")
                try:
                    # Wait for table rows to appear on the page (max 10 seconds)
                    await page.wait_for_selector(".rdt_TableRow", timeout=10000)
                except:
                    # No rows found means no more pages or error
                    print("❌ No more rows found or timeout.")
                    break

                # Select all rows containing NOTAM entries on current page
                rows = await page.query_selector_all(".rdt_TableRow")
                print(f"✅ Found {len(rows)} NOTAMs on Page {page_number}.")

                # Process each row to extract column data
                for index, row in enumerate(rows):
                    cols = await row.query_selector_all(".rdt_TableCell")
                    if len(cols) >= 6:
                        try:
                            # Extract visible text from each relevant cell
                            location = await cols[0].inner_text()
                            notam_no = await cols[1].inner_text()
                            start_date = await cols[2].inner_text()
                            end_date = await cols[3].inner_text()
                            status = await cols[4].inner_text()
                            summary = await cols[5].inner_text()
                        except:
                            # Fallback in case of reading errors
                            location = notam_no = start_date = end_date = status = summary = "[Error reading cell]"

                        detail_text = ""
                        try:
                            # Attempt to find anchor (<a>) tag linking to detailed NOTAM info
                            anchor = await row.query_selector("a")
                            if anchor:
                                href = await anchor.get_attribute("href")
                                # If href points to a blob URL, open it in a new page
                                if href and href.startswith("blob:"):
                                    detail_page = await context.new_page()
                                    await detail_page.goto(href)
                                    await detail_page.wait_for_selector("pre", timeout=10000)
                                    await detail_page.wait_for_timeout(3000)
                                    pre = await detail_page.query_selector("pre")
                                    if pre:
                                        # Extract detailed text content from <pre> tag
                                        all_lines = await pre.inner_text()
                                        # Fallback to text_content if inner_text too short
                                        if len(all_lines.strip().splitlines()) < 2:
                                            all_lines = await pre.text_content()
                                        detail_text = all_lines.strip()
                                        print(f"\n📄 Extracted Blob Text from row {index+1} on page {page_number}\n")
                                    else:
                                        detail_text = "[No <pre> found]"
                                    await detail_page.close()
                                else:
                                    # If blob href not found, attempt forced clicks to open detail page
                                    print(f"⚠️ Blob href not found for row {index+1}, trying forced clicks...")
                                    detail_page = None
                                    for attempt in range(4):
                                        try:
                                            async with context.expect_page() as new_page_info:
                                                await anchor.click(force=True)
                                            detail_page = await new_page_info.value
                                            await detail_page.wait_for_selector("pre", timeout=10000)
                                            break
                                        except Exception as e:
                                            print(f"⏳ Retry {attempt+1}: {e}")
                                            await asyncio.sleep(1)
                                    if detail_page:
                                        pre = await detail_page.query_selector("pre")
                                        if pre:
                                            all_lines = await pre.inner_text()
                                            if len(all_lines.strip().splitlines()) < 2:
                                                all_lines = await pre.text_content()
                                            detail_text = all_lines.strip()
                                            print(f"\n📄 Extracted Click-Based Text from row {index+1} on page {page_number}\n")
                                        else:
                                            detail_text = "[No <pre> found]"
                                        await detail_page.close()
                                    else:
                                        detail_text = "[Failed to open detail page after retries]"
                            else:
                                detail_text = "[Anchor tag not found]"
                        except Exception as e:
                            detail_text = f"[Error navigating to blob or opening view: {e}]"

                        # Write the extracted row data to CSV
                        writer.writerow({
                            "Location": location,
                            "NOTAM": notam_no,
                            "Start Date": start_date,
                            "End Date": end_date,
                            "Status": status,
                            "Text": summary,
                            "Details": detail_text
                        })
                        total_rows_processed += 1

                        print(f"✅ Extracted NOTAM {notam_no}")

                # Periodically flush and sync file to ensure data is saved during long runs
                if total_rows_processed % 100 == 0:
                    file.flush()
                    os.fsync(file.fileno())
                    print(f"💾 Saved progress at {total_rows_processed} records.")

                try:
                    # Attempt to find and click the 'Next' pagination button to continue scraping
                    next_button = await page.query_selector("#pagination-next-page")
                    if next_button:
                        is_disabled = await next_button.get_attribute("aria-disabled")
                        if is_disabled == "true":
                            print("🛑 Reached last page.")
                            break
                        await next_button.click()
                        # Wait for page to load new data after clicking next
                        await page.wait_for_timeout(3000)
                        page_number += 1
                    else:
                        print("❌ Next button not found by ID.")
                        break
                except Exception as e:
                    print(f"❌ Error handling next button: {e}")
                    break

        print(f"✅ Data saved to '{CSV_FILE}'.")
        # Close the browser cleanly after scraping is complete
        await browser.close()

# Script entry point - run the asynchronous scraper
if __name__ == '__main__':
    asyncio.run(scrape_notams())
