# import os
# import time
# import datetime
# from datetime import date, timedelta
# import re
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import (
#     TimeoutException, NoSuchElementException, StaleElementReferenceException
# )
# from selenium.webdriver.chrome.options import Options
# import gspread
# from google.oauth2.service_account import Credentials
# import json
# from typing import List, Dict, Optional, Tuple

# class MontgomeryCountyScraper:
#     def __init__(self, headless=True):
#         self.headless = headless
#         self.driver = None
#         self.setup_driver()
        
#     def setup_driver(self):
#         """Initialize the Chrome driver with appropriate options"""
#         chrome_options = Options()
#         if self.headless:
#             chrome_options.add_argument("--headless")
#         chrome_options.add_argument("--no-sandbox")
#         chrome_options.add_argument("--disable-dev-shm-usage")
#         chrome_options.add_argument("--disable-gpu")
#         chrome_options.add_argument("--window-size=1920,1080")
#         chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
#         self.driver = webdriver.Chrome(options=chrome_options)
#         self.driver.implicitly_wait(2)
        
#     def retry_action(self, action, max_attempts=3, delay=2):
#         """Retry a specific action with delays between attempts"""
#         for attempt in range(max_attempts):
#             try:
#                 return action()
#             except (TimeoutException, StaleElementReferenceException) as e:
#                 if attempt == max_attempts - 1:
#                     raise e
#                 time.sleep(delay)
                
#     def wait_for_element(self, by, value, timeout=10):
#         """Wait for an element to be present"""
#         return WebDriverWait(self.driver, timeout).until(
#             EC.presence_of_element_located((by, value))
#         )
        
#     def wait_for_element_clickable(self, by, value, timeout=10):
#         """Wait for an element to be clickable"""
#         return WebDriverWait(self.driver, timeout).until(
#             EC.element_to_be_clickable((by, value))
#         )
        
#     def navigate_to_search_page(self):
#         """Navigate to the case search page"""
#         self.driver.get("https://courtsapp.montcopa.org/psi3/v/search/case")
#         time.sleep(3)  # Initial page load
        
#     def perform_search(self, start_date="01/01/2025", end_date=None):
#         """Perform the search with the given date range"""
#         if end_date is None:
#             end_date = date.today().strftime("%m/%d/%Y")
            
#         try:
#             # Wait for search box and enter search term
#             search_box = self.wait_for_element(By.ID, "Q")
#             search_box.clear()
#             search_box.send_keys("probate")
#             time.sleep(2)
            
#             # Set filing date from
#             from_date = self.wait_for_element(By.ID, "FilingDateFrom")
#             from_date.clear()
#             from_date.send_keys(start_date)
#             time.sleep(2)
            
#             # Set filing date to
#             to_date = self.wait_for_element(By.ID, "FilingDateTo")
#             to_date.clear()
#             to_date.send_keys(end_date)
#             time.sleep(2)
            
#             # Click search button
#             search_button = self.wait_for_element_clickable(
#                 By.XPATH, "//button[contains(@class, 'fa-search') and contains(text(), 'Search')]"
#             )
#             search_button.click()
#             time.sleep(3)
            
#             # Wait for results table
#             self.wait_for_element(By.ID, "gridViewResults")
#             return True
            
#         except Exception as e:
#             print(f"Error performing search: {e}")
#             return False
            
#     def extract_case_details(self, case_url):
#         """Extract case details from the detail page"""
#         self.driver.get(case_url)
#         time.sleep(3)
        
#         case_data = {
#             "case_number": "",
#             "last_filing_date": "",
#             "personal_representatives": [],
#             "case_foundation_parties_address": ""
#         }
        
#         try:
#             # Extract case number
#             try:
#                 case_number_element = self.wait_for_element(
#                     By.XPATH, "//*[@id='page-content-wrapper']/div/div[1]/div[1]/div[1]/table/tbody/tr[1]/td"
#                 )
#                 case_data["case_number"] = case_number_element.text.strip()
#             except:
#                 pass
                
#             # Extract last filing date
#             try:
#                 last_filing_element = self.wait_for_element(
#                     By.XPATH, "//*[@id='page-content-wrapper']/div/div[1]/div[1]/div[1]/table/tbody/tr[3]/td"
#                 )
#                 case_data["last_filing_date"] = last_filing_element.text.strip()
#             except:
#                 pass
                
#             # Extract personal representatives
#             try:
#                 reps_table = self.wait_for_element(By.ID, "table_PersonalRepresentatives")
#                 rows = reps_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
                
#                 for row in rows:
#                     cells = row.find_elements(By.TAG_NAME, "td")
#                     if len(cells) >= 4:  # Ensure we have enough cells
#                         rep = {
#                             "name": cells[1].text.strip() if len(cells) > 1 else "",
#                             "role": cells[2].text.strip() if len(cells) > 2 else "",
#                             "address": cells[3].text.strip().replace("\n", ", ") if len(cells) > 3 else ""
#                         }
#                         case_data["personal_representatives"].append(rep)
#             except:
#                 pass
                
#             # Extract case foundation parties address
#             try:
#                 parties_table = self.wait_for_element(By.ID, "table_CaseFoundationParties")
#                 rows = parties_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
                
#                 if rows:
#                     first_party_cells = rows[0].find_elements(By.TAG_NAME, "td")
#                     if len(first_party_cells) >= 5:  # Address is in the 5th column
#                         case_data["case_foundation_parties_address"] = first_party_cells[4].text.strip().replace("\n", ", ")
#             except:
#                 pass
                
#         except Exception as e:
#             print(f"Error extracting case details: {e}")
            
#         return case_data
        
#     def get_search_results(self):
#         """Get all search results from the current page"""
#         results = []
#         try:
#             table = self.wait_for_element(By.ID, "gridViewResults")
#             rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header if exists
            
#             for row in rows:
#                 try:
#                     select_link = row.find_element(By.TAG_NAME, "a")
#                     case_url = select_link.get_attribute("href")
#                     results.append(case_url)
#                 except:
#                     continue
                    
#         except Exception as e:
#             print(f"Error getting search results: {e}")
            
#         return results
        
#     def has_next_page(self):
#         """Check if there's a next page of results"""
#         try:
#             next_button = self.driver.find_element(
#                 By.XPATH, "//a[contains(@href, 'Skip=') and contains(text(), 'Next')]"
#             )
#             return True
#         except:
#             return False
            
#     def go_to_next_page(self):
#         """Navigate to the next page of results"""
#         try:
#             next_button = self.wait_for_element_clickable(
#                 By.XPATH, "//a[contains(@href, 'Skip=') and contains(text(), 'Next')]"
#             )
#             next_button.click()
#             time.sleep(3)
#             self.wait_for_element(By.ID, "gridViewResults")
#             return True
#         except Exception as e:
#             print(f"Error going to next page: {e}")
#             return False
            
#     def scrape_cases(self, start_date="01/01/2025", end_date=None):
#         """Main method to scrape all cases"""
#         if end_date is None:
#             end_date = date.today().strftime("%m/%d/%Y")
            
#         self.navigate_to_search_page()
        
#         if not self.perform_search(start_date, end_date):
#             print("Search failed")
#             return []
            
#         all_case_data = []
#         page = 1
        
#         while True:
#             print(f"Scraping page {page}")
#             case_urls = self.get_search_results()
            
#             for case_url in case_urls:
#                 case_data = self.extract_case_details(case_url)
                
#                 # Only include cases with personal representatives
#                 if case_data["personal_representatives"]:
#                     all_case_data.append(case_data)
                
#                 # Go back to search results
#                 self.driver.back()
#                 time.sleep(3)
#                 self.wait_for_element(By.ID, "gridViewResults")
                
#             # Check for next page
#             if not self.has_next_page():
#                 break
                
#             if not self.go_to_next_page():
#                 break
                
#             page += 1
            
#         return all_case_data
        
#     def close(self):
#         """Close the browser"""
#         if self.driver:
#             self.driver.quit()


# class GoogleSheetsHandler:
#     def __init__(self, credentials_json, spreadsheet_id):
#         self.credentials_json = credentials_json
#         self.spreadsheet_id = spreadsheet_id
#         self.client = None
#         self.spreadsheet = None
#         self.setup_client()
        
#     def setup_client(self):
#         """Set up the Google Sheets client"""
#         try:
#             scopes = [
#                 "https://www.googleapis.com/auth/spreadsheets",
#                 "https://www.googleapis.com/auth/drive"
#             ]
#             credentials = Credentials.from_service_account_info(
#                 json.loads(self.credentials_json), scopes=scopes
#             )
#             self.client = gspread.authorize(credentials)
#             self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
#         except Exception as e:
#             print(f"Error setting up Google Sheets client: {e}")
#             raise
            
#     def get_or_create_sheet(self, sheet_name):
#         """Get or create a sheet with the given name"""
#         try:
#             worksheet = self.spreadsheet.worksheet(sheet_name)
#             print(f"Found existing sheet: {sheet_name}")
#         except gspread.exceptions.WorksheetNotFound:
#             print(f"Creating new sheet: {sheet_name}")
#             worksheet = self.spreadsheet.add_worksheet(
#                 title=sheet_name, rows=1000, cols=20
#             )
            
#             # Set up headers
#             headers = [
#                 "Case Number", 
#                 "Last Filing Date", 
#                 "Representative Name", 
#                 "Role", 
#                 "Address", 
#                 "Case Foundation Parties Address"
#             ]
#             worksheet.update("A1:F1", [headers])
            
#             # Format headers
#             worksheet.format("A1:F1", {
#                 "textFormat": {"bold": True},
#                 "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
#             })
            
#             # Freeze header row
#             worksheet.freeze(rows=1)
            
#         return worksheet
        
#     def update_sheet(self, sheet_name, case_data):
#         """Update the sheet with the given case data"""
#         worksheet = self.get_or_create_sheet(sheet_name)
        
#         # Prepare data for writing
#         rows = []
#         for case in case_data:
#             for rep in case["personal_representatives"]:
#                 row = [
#                     case["case_number"],
#                     case["last_filing_date"],
#                     rep["name"],
#                     rep["role"],
#                     rep["address"],
#                     case["case_foundation_parties_address"]
#                 ]
#                 rows.append(row)
                
#         if rows:
#             # Clear existing data (except headers)
#             worksheet.batch_clear(["A2:F1000"])
            
#             # Write new data
#             worksheet.update(f"A2:F{len(rows)+1}", rows)
            
#             # Auto-resize columns
#             worksheet.columns_auto_resize(0, 5)  # Columns A to F
            
#         print(f"Updated sheet {sheet_name} with {len(rows)} rows")
        
#     def get_last_scraped_date(self, sheet_name):
#         """Get the last date that was scraped from a sheet"""
#         try:
#             worksheet = self.spreadsheet.worksheet(sheet_name)
#             dates = worksheet.col_values(2)  # Column B has filing dates
#             if len(dates) > 1:  # Skip header
#                 # Return the latest date
#                 return max(
#                     [self.parse_date(date_str) for date_str in dates[1:] if date_str],
#                     default=None
#                 )
#         except:
#             pass
#         return None
        
#     def parse_date(self, date_str):
#         """Parse a date string into a date object"""
#         try:
#             # Handle various date formats
#             for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
#                 try:
#                     return datetime.datetime.strptime(date_str, fmt).date()
#                 except ValueError:
#                     continue
#         except:
#             pass
#         return None


# def main():
#     # Configuration
#     HEADLESS = True
#     START_DATE = "01/01/2025"
    
#     # Get credentials from environment
#     google_credentials = os.environ.get("GOOGLE_CREDENTIALS")
#     spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    
#     if not google_credentials or not spreadsheet_id:
#         print("Error: GOOGLE_CREDENTIALS and SPREADSHEET_ID environment variables are required")
#         return
        
#     # Initialize Google Sheets handler
#     sheets_handler = GoogleSheetsHandler(google_credentials, spreadsheet_id)
    
#     # Determine the current month for the sheet name
#     current_month = date.today().strftime("%Y-%m")
    
#     # Check if we have a previous scrape for this month
#     last_date = sheets_handler.get_last_scraped_date(current_month)
    
#     # If we have a previous scrape, start from the day after the last date
#     if last_date:
#         start_date = (last_date + timedelta(days=1)).strftime("%m/%d/%Y")
#     else:
#         start_date = START_DATE
        
#     # Initialize scraper
#     scraper = MontgomeryCountyScraper(headless=HEADLESS)
    
#     try:
#         # Scrape cases
#         case_data = scraper.scrape_cases(start_date=start_date)
        
#         if case_data:
#             # Update Google Sheet
#             sheets_handler.update_sheet(current_month, case_data)
#             print(f"Successfully processed {len(case_data)} cases")
#         else:
#             print("No cases found or no new cases since last scrape")
            
#     except Exception as e:
#         print(f"Error during scraping: {e}")
        
#     finally:
#         scraper.close()


# if __name__ == "__main__":
#     main()




#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import logging
import datetime
from typing import Any, Dict, List, Optional, Tuple
import time
import re
import requests
from bs4 import BeautifulSoup
import backoff
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Logging
logging.basicConfig(
    filename="montgomery_scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# -----------------------------
# Credentials Loading
# -----------------------------
def load_service_account_info() -> Dict[str, Any]:
    file_env = os.environ.get("GOOGLE_CREDENTIALS_FILE")
    if file_env and os.path.exists(file_env):
        with open(file_env, "r", encoding="utf-8") as fh:
            return json.load(fh)

    creds_raw = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_raw:
        raise ValueError("Missing GOOGLE_CREDENTIALS or GOOGLE_CREDENTIALS_FILE")

    txt = creds_raw.strip()
    if txt.startswith("{"):
        return json.loads(txt)
    if os.path.exists(txt):
        with open(txt, "r", encoding="utf-8") as fh:
            return json.load(fh)
    raise ValueError("Invalid GOOGLE_CREDENTIALS data")

# -----------------------------
# Driverless Scraper (Requests + BeautifulSoup)
# -----------------------------
class MontgomeryCountyScraperDriverless:
    BASE_URL = "https://courtsapp.montcopa.org/psi3/v/search/case"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"
        })

    def make_search(self, start_date: str, end_date: str) -> Optional[str]:
        """
        Submit search form.
        This may need to be adapted if the site uses hidden tokens.
        """
        logging.info(f"Submitting search from {start_date} to {end_date}")
        params = {
            "Q": "probate",
            "FilingDateFrom": start_date,
            "FilingDateTo": end_date
        }
        r = self.session.get(self.BASE_URL, params=params, timeout=30)
        if r.status_code != 200:
            logging.error(f"Search failed: {r.status_code}")
            return None
        return r.text

    def parse_results(self, html: str) -> List[str]:
        """Extract case detail URLs from results table"""
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.select("#gridViewResults a[href*='case']"):
            href = a.get("href")
            if href and "case" in href:
                if href.startswith("/"):
                    href = "https://courtsapp.montcopa.org" + href
                links.append(href)
        logging.info(f"Found {len(links)} case links")
        return links

    def fetch_case(self, url: str) -> Dict[str, Any]:
        logging.info(f"Fetching case: {url}")
        r = self.session.get(url, timeout=30)
        if r.status_code != 200:
            logging.error(f"Case request failed: {r.status_code}")
            return {}

        soup = BeautifulSoup(r.text, "html.parser")
        case_data = {
            "case_number": "",
            "last_filing_date": "",
            "personal_representatives": [],
            "case_foundation_parties_address": "",
            "case_details_url": url,
            "scrape_timestamp": datetime.datetime.now().isoformat(),
        }

        # Try case number
        num_el = soup.find(lambda t: t.name in ["td", "th"] and "Case Number" in t.text)
        if num_el:
            next_td = num_el.find_next("td")
            if next_td:
                case_data["case_number"] = next_td.get_text(strip=True)

        # Try last filing date
        date_el = soup.find(lambda t: t.name == "td" and "Filing Date" in t.text)
        if date_el:
            next_td = date_el.find_next("td")
            if next_td:
                case_data["last_filing_date"] = next_td.get_text(strip=True)

        # Representatives
        reps = []
        tables = soup.find_all("table")
        for table in tables:
            if "Representative" in table.get_text():
                for row in table.find_all("tr")[1:]:
                    cells = row.find_all("td")
                    if len(cells) >= 3:
                        reps.append({
                            "name": cells[0].get_text(strip=True),
                            "role": cells[1].get_text(strip=True),
                            "address": cells[2].get_text(strip=True).replace("\n", ", ")
                        })
        case_data["personal_representatives"] = reps

        return case_data

    def scrape_cases(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        html = self.make_search(start_date, end_date)
        if not html:
            return []
        urls = self.parse_results(html)
        all_cases = []
        for url in urls:
            c = self.fetch_case(url)
            if c and (c["case_number"] or c["personal_representatives"]):
                all_cases.append(c)
            time.sleep(1)
        return all_cases

# -----------------------------
# Google Sheets Handler (Direct API - No gspread)
# -----------------------------
class GoogleSheetsHandler:
    def __init__(self, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id
        sa_info = load_service_account_info()
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(sa_info, scopes=scopes)
        self.service = build('sheets', 'v4', credentials=creds)
        self.sheets = self.service.spreadsheets()

    def get_or_create_sheet(self, sheet_name: str):
        """Get sheet info or create if it doesn't exist"""
        try:
            # Get spreadsheet metadata
            spreadsheet = self.sheets.get(spreadsheetId=self.spreadsheet_id).execute()
            sheets = spreadsheet.get('sheets', [])
            
            # Check if sheet exists
            for sheet in sheets:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            
            # Sheet doesn't exist, create it
            requests_body = {
                'requests': [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name,
                            'gridProperties': {
                                'rowCount': 1000,
                                'columnCount': 10
                            }
                        }
                    }
                }]
            }
            
            response = self.sheets.batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=requests_body
            ).execute()
            
            sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']
            
            # Add headers
            headers = [
                "Case Number", "Last Filing Date",
                "Representative Name", "Role",
                "Address", "Case Foundation Parties Address"
            ]
            
            self.sheets.values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A1:F1",
                valueInputOption='RAW',
                body={'values': [headers]}
            ).execute()
            
            return sheet_id
            
        except HttpError as e:
            logging.error(f"Error managing sheet {sheet_name}: {e}")
            raise

    def get_all_case_numbers(self, sheet_name: str) -> set:
        """Get all existing case numbers from the sheet"""
        self.get_or_create_sheet(sheet_name)
        
        try:
            result = self.sheets.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A2:A"  # Skip header row
            ).execute()
            
            values = result.get('values', [])
            return set(row[0] for row in values if row)
            
        except HttpError as e:
            logging.error(f"Error reading case numbers from {sheet_name}: {e}")
            return set()

    def update_sheet(self, sheet_name: str, cases: List[Dict[str, Any]], existing: set):
        """Update sheet with new cases"""
        self.get_or_create_sheet(sheet_name)
        
        rows = []
        for c in cases:
            if c["case_number"] in existing:
                continue
            for rep in c["personal_representatives"]:
                rows.append([
                    c["case_number"],
                    c["last_filing_date"],
                    rep.get("name", ""),
                    rep.get("role", ""),
                    rep.get("address", ""),
                    c.get("case_foundation_parties_address", "")
                ])
        
        if rows:
            try:
                # Find the next empty row
                result = self.sheets.values().get(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{sheet_name}!A:A"
                ).execute()
                
                existing_rows = len(result.get('values', []))
                start_row = existing_rows + 1
                
                range_name = f"{sheet_name}!A{start_row}:F{start_row + len(rows) - 1}"
                
                self.sheets.values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_name,
                    valueInputOption='RAW',
                    body={'values': rows}
                ).execute()
                
                logging.info(f"Inserted {len(rows)} rows in {sheet_name}")
                
            except HttpError as e:
                logging.error(f"Error updating sheet {sheet_name}: {e}")
                raise

# -----------------------------
# Date Ranges
# -----------------------------
def get_monthly_date_ranges(start_date_str=None):
    if start_date_str:
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%m/%d/%Y").date()
        except Exception:
            start_date = datetime.date(2025,1,1)
    else:
        start_date = datetime.date(2025,1,1)
    end_date = datetime.date.today()

    ranges=[]
    cm = start_date.replace(day=1)
    while cm <= end_date:
        if cm.month==12:
            nm = cm.replace(year=cm.year+1, month=1, day=1)
        else:
            nm = cm.replace(month=cm.month+1, day=1)
        last_day = nm - datetime.timedelta(days=1)
        if last_day>end_date:
            last_day=end_date
        ranges.append((cm.strftime("%m/%d/%Y"), last_day.strftime("%m/%d/%Y"), cm.strftime("%b %Y")))
        cm = nm
    return ranges

# -----------------------------
# Main
# -----------------------------
def main():
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    if not spreadsheet_id:
        logging.error("Missing SPREADSHEET_ID")
        return

    gs = GoogleSheetsHandler(spreadsheet_id)
    scraper = MontgomeryCountyScraperDriverless()

    drs = get_monthly_date_ranges()
    for start_date,end_date,sheet_name in drs:
        existing = gs.get_all_case_numbers(sheet_name)
        cases = scraper.scrape_cases(start_date,end_date)
        gs.update_sheet(sheet_name,cases,existing)
        time.sleep(2)

if __name__=="__main__":
    main()