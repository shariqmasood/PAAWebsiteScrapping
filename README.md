# Pakistan Airports Authority (PAA) Web Scraper

## Overview

This project contains two Python web scraping scripts designed to extract critical aviation-related data from the Pakistan Airports Authority (PAA) official website:

- **NOTAMs Scraper (`notam.py`)**  
  Scrapes detailed Notice to Airmen (NOTAM) data from  
  [https://paa.gov.pk/aeronautical-information/notice-to-airmen](https://paa.gov.pk/aeronautical-information/notice-to-airmen).

- **Tenders Scraper (`tender.py`)**  
  Extracts tender notices and details from  
  [https://paa.gov.pk/allTender](https://paa.gov.pk/allTender).

Both scrapers leverage Playwright’s async Python API to control a headless Chromium browser for rendering dynamic content and handling JavaScript-heavy pages.

---

## Features

- Asynchronous scraping using `asyncio` for high performance and efficiency.
- Robust handling of dynamic content and pagination.
- Extraction of structured tabular data with detailed fields.
- Incremental data saving to CSV files to prevent data loss on long runs.
- Error handling with retries and debug aids (e.g., screenshots for tender scraper).
- Modular and maintainable Python code for easy extension and reuse.

---

## Requirements

- Python 3.7 or higher
- [Playwright](https://playwright.dev/python/)  
  Install via pip:
  ```bash
  pip install playwright pandas
  playwright install
