import os
import time
import datetime
from datetime import date, timedelta
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, StaleElementReferenceException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import gspread
from google.oauth2.service_account import Credentials
import json
from typing import List, Dict, Optional, Tuple, Any
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# -----------------------------
# Credentials Loading Functions
# -----------------------------

REQUIRED_SA_FIELDS = {
    "type",
    "project_id",
    "private_key_id",
    "private_key",
    "client_email",
    "client_id",
    "auth_uri",
    "token_uri",
    "auth_provider_x509_cert_url",
    "client_x509_cert_url",
}

def _normalize_private_key(info: dict) -> dict:
    """
    Google private_key often arrives with literal '\\n'. Convert to real newlines.
    """
    pk = info.get("private_key")
    if isinstance(pk, str) and "\\n" in pk:
        info["private_key"] = pk.replace("\\n", "\n")
    return info

def _validate_service_account_info(info: dict):
    missing = [k for k in REQUIRED_SA_FIELDS if k not in info or not info.get(k)]
    if missing:
        raise ValueError(f"Service account JSON missing fields: {', '.join(missing)}")

def load_service_account_info() -> dict:
    """
    Load service account JSON from:
    1) GOOGLE_CREDENTIALS_FILE (path to JSON)
    2) GOOGLE_CREDENTIALS (raw JSON string or path)
    """
    file_env = os.environ.get("GOOGLE_CREDENTIALS_FILE")
    logger.info(f"GOOGLE_CREDENTIALS_FILE env: {file_env!r}")

    if file_env:
        if os.path.exists(file_env):
            logger.info("Loading service account from GOOGLE_CREDENTIALS_FILE path.")
            with open(file_env, "r", encoding="utf-8") as fh:
                info = json.load(fh)
            info = _normalize_private_key(info)
            _validate_service_account_info(info)
            return info
        raise ValueError(f"GOOGLE_CREDENTIALS_FILE set but not found: {file_env}")

    creds_raw = os.environ.get("GOOGLE_CREDENTIALS")
    logger.info(f"GOOGLE_CREDENTIALS env present: {bool(creds_raw)}")
    if not creds_raw:
        raise ValueError("GOOGLE_CREDENTIALS or GOOGLE_CREDENTIALS_FILE is required.")

    txt = creds_raw.strip()
    # If it's JSON
    if txt.startswith("{"):
        logger.info("Attempting to load credentials from JSON string in env.")
        try:
            info = json.loads(txt)
        except json.JSONDecodeError as e:
            raise ValueError(f"GOOGLE_CREDENTIALS is not valid JSON: {e}") from e
        info = _normalize_private_key(info)
        _validate_service_account_info(info)
        return info

    # If it's a filesystem path
    if os.path.exists(txt):
        logger.info("Attempting to load credentials from file path in GOOGLE_CREDENTIALS.")
        with open(txt, "r", encoding="utf-8") as fh:
            info = json.load(fh)
        info = _normalize_private_key(info)
        _validate_service_account_info(info)
        return info

    raise ValueError("GOOGLE_CREDENTIALS is neither valid JSON nor an existing file path.")

# -----------------------------
# Scraper
# -----------------------------

class MontgomeryCountyScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Initialize the Chrome driver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        # Optional: set Chrome binary for CI environments
        if os.path.exists("/usr/bin/google-chrome"):
            chrome_options.binary_location = "/usr/bin/google-chrome"

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
    def retry_action(self, action, max_attempts=3, delay=2):
        """Retry a specific action with delays between attempts"""
        for attempt in range(max_attempts):
            try:
                return action()
            except (TimeoutException, StaleElementReferenceException, ElementClickInterceptedException) as e:
                if attempt == max_attempts - 1:
                    raise e
                logging.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
                time.sleep(delay)
                
    def wait_for_element(self, by, value, timeout=15):
        """Wait for an element to be present"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        
    def wait_for_element_clickable(self, by, value, timeout=15):
        """Wait for an element to be clickable"""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )
        
    def navigate_to_search_page(self):
        """Navigate to the case search page"""
        try:
            self.driver.get("https://courtsapp.montcopa.org/psi3/v/search/case")
            self.wait_for_element(By.TAG_NAME, "body")
            time.sleep(3)
            return True
        except Exception as e:
            logging.error(f"Failed to navigate to search page: {e}")
            return False
            
    def perform_search(self, start_date="01/01/2025", end_date=None):
        """Perform the search with the given date range"""
        if end_date is None:
            end_date = date.today().strftime("%m/%d/%Y")
            
        try:
            search_box = self.wait_for_element(By.ID, "Q")
            search_box.clear()
            search_box.send_keys("probate")
            time.sleep(2)
            
            from_date = self.wait_for_element(By.ID, "FilingDateFrom")
            from_date.clear()
            from_date.send_keys(start_date)
            time.sleep(2)
            
            to_date = self.wait_for_element(By.ID, "FilingDateTo")
            to_date.clear()
            to_date.send_keys(end_date)
            time.sleep(2)
            
            search_button = self.wait_for_element_clickable(
                By.XPATH, "//button[contains(@class, 'btn-primary') and contains(., 'Search')]"
            )
            search_button.click()
            time.sleep(5)
            
            try:
                self.wait_for_element(By.ID, "gridViewResults", timeout=10)
                return True
            except TimeoutException:
                try:
                    no_results = self.driver.find_element(By.XPATH, "//div[contains(text(), 'No results')]")
                    if no_results:
                        logging.info("No results found for the search criteria")
                        return True
                except Exception:
                    logging.error("Search results did not load properly")
                    return False
                
        except Exception as e:
            logging.error(f"Error performing search: {e}")
            return False
            
    def extract_case_details(self, case_url):
        """Extract case details from the detail page"""
        self.driver.get(case_url)
        time.sleep(3)
        
        case_data = {
            "case_number": "",
            "last_filing_date": "",
            "personal_representatives": [],
            "case_foundation_parties_address": "",
            "case_details_url": case_url,
            "scrape_timestamp": datetime.datetime.now().isoformat()
        }
        
        try:
            try:
                case_number_element = self.wait_for_element(
                    By.XPATH, "//td[contains(., 'Case Number')]/following-sibling::td"
                )
                case_data["case_number"] = case_number_element.text.strip()
            except Exception:
                try:
                    case_number_element = self.driver.find_element(
                        By.XPATH, "//th[contains(., 'Case Number')]/following-sibling::td"
                    )
                    case_data["case_number"] = case_number_element.text.strip()
                except Exception:
                    logging.warning("Could not find case number")
                
            try:
                last_filing_element = self.driver.find_element(
                    By.XPATH, "//td[contains(., 'Last Filing Date') or contains(., 'Filing Date')]/following-sibling::td"
                )
                date_text = last_filing_element.text.strip()
                parsed = None
                for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%Y/%m/%d"):
                    try:
                        parsed = datetime.datetime.strptime(date_text, fmt)
                        break
                    except ValueError:
                        continue
                case_data["last_filing_date"] = parsed.strftime("%Y-%m-%d") if parsed else date_text
            except Exception:
                logging.warning("Could not find last filing date")
                
            try:
                reps_tables = self.driver.find_elements(
                    By.XPATH, "//table[contains(@id, 'PersonalRepresentatives') or contains(., 'Personal Representative')]"
                )
                for table in reps_tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")[1:]
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:
                            rep = {
                                "name": cells[0].text.strip() if cells[0].text.strip() else "",
                                "role": cells[1].text.strip() if len(cells) > 1 else "",
                                "address": cells[2].text.strip().replace("\n", ", ") if len(cells) > 2 else ""
                            }
                            if rep["name"]:
                                case_data["personal_representatives"].append(rep)
            except Exception as e:
                logging.warning(f"Could not extract personal representatives: {e}")
                
            try:
                parties_tables = self.driver.find_elements(
                    By.XPATH, "//table[contains(@id, 'CaseFoundationParties') or contains(., 'Parties')]"
                )
                for table in parties_tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")[1:]
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 5:
                            address = cells[4].text.strip().replace("\n", ", ")
                            if address and not case_data["case_foundation_parties_address"]:
                                case_data["case_foundation_parties_address"] = address
            except Exception as e:
                logging.warning(f"Could not extract case foundation parties address: {e}")
                
        except Exception as e:
            logging.error(f"Error extracting case details: {e}")
            
        return case_data
        
    def get_search_results(self):
        """Get all search results from the current page"""
        results = []
        try:
            try:
                table = self.wait_for_element(By.ID, "gridViewResults", timeout=10)
                rows = table.find_elements(By.TAG_NAME, "tr")[1:]
            except Exception:
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                rows = []
                for table in tables:
                    if "probate" in table.text.lower():
                        rows = table.find_elements(By.TAG_NAME, "tr")[1:]
                        break
                if not rows:
                    logging.info("No results table found")
                    return results
            
            for row in rows:
                try:
                    select_link = row.find_element(By.TAG_NAME, "a")
                    case_url = select_link.get_attribute("href")
                    if case_url and "case" in case_url:
                        results.append(case_url)
                except Exception:
                    continue
                    
        except Exception as e:
            logging.error(f"Error getting search results: {e}")
            
        return results
        
    def has_next_page(self):
        """Check if there's a next page of results"""
        try:
            next_buttons = self.driver.find_elements(
                By.XPATH, "//a[contains(@href, 'Skip') or contains(@href, 'next') or contains(text(), 'Next')]"
            )
            for button in next_buttons:
                if button.is_enabled() and button.is_displayed():
                    return True
            return False
        except Exception:
            return False
            
    def go_to_next_page(self):
        """Navigate to the next page of results"""
        try:
            next_buttons = self.driver.find_elements(
                By.XPATH, "//a[contains(@href, 'Skip') or contains(@href, 'next') or contains(text(), 'Next')]"
            )
            for button in next_buttons:
                if button.is_enabled() and button.is_displayed():
                    button.click()
                    time.sleep(3)
                    self.wait_for_element(By.TAG_NAME, "body")
                    return True
            return False
        except Exception as e:
            logging.error(f"Error going to next page: {e}")
            return False
            
    def scrape_cases(self, start_date="01/01/2025", end_date=None):
        """Main method to scrape all cases"""
        if end_date is None:
            end_date = date.today().strftime("%m/%d/%Y")
            
        if not self.navigate_to_search_page():
            return []
        
        if not self.perform_search(start_date, end_date):
            logging.error("Search failed")
            return []
            
        all_case_data = []
        page = 1
        max_pages = 50  # Safety limit
        
        while page <= max_pages:
            logging.info(f"Scraping page {page}")
            case_urls = self.get_search_results()
            
            if not case_urls:
                logging.info("No case URLs found on this page")
                break
                
            logging.info(f"Found {len(case_urls)} cases on page {page}")
            
            for i, case_url in enumerate(case_urls):
                logging.info(f"Scraping case {i+1}/{len(case_urls)}: {case_url}")
                case_data = self.extract_case_details(case_url)
                
                if case_data["case_number"] or case_data["personal_representatives"]:
                    all_case_data.append(case_data)
                else:
                    logging.warning(f"Skipping case with no data: {case_url}")
                
                self.driver.back()
                time.sleep(3)
                try:
                    self.wait_for_element(By.TAG_NAME, "body")
                    self.wait_for_element(By.ID, "gridViewResults", timeout=5)
                except Exception:
                    if not self.navigate_to_search_page() or not self.perform_search(start_date, end_date):
                        logging.error("Failed to return to search results")
                        return all_case_data
                
            if not self.has_next_page():
                break
                
            if not self.go_to_next_page():
                break
                
            page += 1
            time.sleep(2)
            
        return all_case_data
        
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

# -----------------------------
# Google Sheets Handler (gspread)
# -----------------------------

class GoogleSheetsHandler:
    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None
        self.setup_client()
        
    def setup_client(self):
        try:
            service_account_info = load_service_account_info()
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            credentials = Credentials.from_service_account_info(
                service_account_info, scopes=scopes
            )
            self.client = gspread.authorize(credentials)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            sa_email = service_account_info.get("client_email", "<unknown-service-account>")
            logging.info(f"Successfully connected to Google Sheets. Service account: {sa_email}")
            logging.info("Ensure this email has Editor access to your spreadsheet.")
        except Exception as e:
            logging.error(f"Error setting up Google Sheets client: {e}")
            raise
            
    def get_or_create_sheet(self, sheet_name):
        """Get or create a sheet with the given name"""
        try:
            worksheet = self.spreadsheet.worksheet(sheet_name)
            logging.info(f"Found existing sheet: {sheet_name}")
        except gspread.exceptions.WorksheetNotFound:
            logging.info(f"Creating new sheet: {sheet_name}")
            worksheet = self.spreadsheet.add_worksheet(
                title=sheet_name, rows=1000, cols=20
            )
            headers = [
                "Case Number", 
                "Last Filing Date", 
                "Representative Name", 
                "Role", 
                "Address", 
                "Case Foundation Parties Address",
                "Case Details URL",
                "Scrape Timestamp"
            ]
            worksheet.update("A1:H1", [headers])
            worksheet.format("A1:H1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
            })
            worksheet.freeze(rows=1)
        return worksheet
        
    def get_last_scraped_date(self, sheet_name):
        """Get the last scraped date from the specified sheet"""
        try:
            worksheet = self.get_or_create_sheet(sheet_name)
            dates = worksheet.col_values(2)
            if len(dates) > 1:
                date_objects = []
                for date_str in dates[1:]:
                    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"):
                        try:
                            date_obj = datetime.datetime.strptime(date_str, fmt).date()
                            date_objects.append(date_obj)
                            break
                        except ValueError:
                            continue
                if date_objects:
                    latest_date = max(date_objects)
                    return latest_date.strftime("%m/%d/%Y")
            return None
        except Exception as e:
            logging.error(f"Error getting last scraped date: {e}")
            return None
            
    def get_all_case_numbers(self, sheet_name):
        """Get all case numbers from the specified sheet"""
        try:
            worksheet = self.get_or_create_sheet(sheet_name)
            case_numbers = worksheet.col_values(1)
            return set(case_numbers[1:]) if len(case_numbers) > 1 else set()
        except Exception as e:
            logging.error(f"Error getting all case numbers: {e}")
            return set()
        
    def update_sheet(self, sheet_name, case_data, existing_case_numbers):
        """Update the sheet with the given case data, skipping existing cases"""
        worksheet = self.get_or_create_sheet(sheet_name)
        rows = []
        for case in case_data:
            if case["case_number"] in existing_case_numbers:
                logging.info(f"Skipping existing case: {case['case_number']}")
                continue
            if not case["case_number"] and not case["personal_representatives"]:
                logging.warning(f"Skipping invalid case with no data: {case['case_details_url']}")
                continue
            if case["personal_representatives"]:
                for rep in case["personal_representatives"]:
                    row = [
                        case["case_number"],
                        case["last_filing_date"],
                        rep.get("name", ""),
                        rep.get("role", ""),
                        rep.get("address", ""),
                        case["case_foundation_parties_address"],
                        case["case_details_url"],
                        case["scrape_timestamp"]
                    ]
                    rows.append(row)
            else:
                # No reps; still record the case
                row = [
                    case["case_number"],
                    case["last_filing_date"],
                    "",
                    "",
                    "",
                    case["case_foundation_parties_address"],
                    case["case_details_url"],
                    case["scrape_timestamp"]
                ]
                rows.append(row)
                
        if rows:
            worksheet.append_rows(rows)
            logging.info(f"Added {len(rows)} new rows to sheet {sheet_name}")
            try:
                worksheet.columns_auto_resize(0, 8)
            except Exception:
                logging.warning("Could not auto-resize columns")
        else:
            logging.info(f"No new data to add to sheet {sheet_name}")

# -----------------------------
# Helpers
# -----------------------------

def get_monthly_date_ranges(start_date_str=None):
    """Generate date ranges for each month from start_date to current date"""
    if start_date_str:
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%m/%d/%Y").date()
        except ValueError:
            logging.error(f"Invalid start date format: {start_date_str}. Using default.")
            start_date = datetime.date(2025, 1, 1)
    else:
        start_date = datetime.date(2025, 1, 1)
    
    end_date = datetime.date.today()
    date_ranges = []
    current = start_date
    
    while current <= end_date:
        first_day = current.replace(day=1)
        if current.month == 12:
            next_month = current.replace(year=current.year+1, month=1, day=1)
        else:
            next_month = current.replace(month=current.month+1, day=1)
        last_day = next_month - datetime.timedelta(days=1)
        if last_day > end_date:
            last_day = end_date
        if first_day <= last_day:
            date_ranges.append((
                first_day.strftime("%m/%d/%Y"),
                last_day.strftime("%m/%d/%Y"),
                first_day.strftime("%b %Y")
            ))
        current = next_month
    
    return date_ranges

# -----------------------------
# Main
# -----------------------------

def main():
    HEADLESS = True
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    
    if not spreadsheet_id:
        logging.error("Error: SPREADSHEET_ID environment variable is required")
        return
        
    try:
        sheets_handler = GoogleSheetsHandler(spreadsheet_id)
    except Exception as e:
        logging.error(f"Failed to initialize Google Sheets handler: {e}")
        return
        
    scraper = MontgomeryCountyScraper(headless=HEADLESS)
    
    try:
        current_month = datetime.datetime.now().strftime("%b %Y")
        last_scraped_date = sheets_handler.get_last_scraped_date(current_month)
        if not last_scraped_date:
            prev_month = (datetime.datetime.now() - datetime.timedelta(days=31)).strftime("%b %Y")
            last_scraped_date = sheets_handler.get_last_scraped_date(prev_month)
        
        date_ranges = get_monthly_date_ranges(last_scraped_date)
        
        if not date_ranges:
            logging.info("No date ranges to process. Data is up to date.")
            return
            
        logging.info(f"Processing {len(date_ranges)} month(s) of data")
        
        for start_date, end_date, sheet_name in date_ranges:
            logging.info(f"Processing {sheet_name}: {start_date} to {end_date}")
            existing_case_numbers = sheets_handler.get_all_case_numbers(sheet_name)
            logging.info(f"Found {len(existing_case_numbers)} existing cases in {sheet_name}")
            case_data = scraper.scrape_cases(start_date=start_date, end_date=end_date)
            if case_data:
                logging.info(f"Successfully scraped {len(case_data)} cases for {sheet_name}")
                sheets_handler.update_sheet(sheet_name, case_data, existing_case_numbers)
                logging.info(f"Processed cases for {sheet_name}")
            else:
                logging.info(f"No new cases found for {sheet_name}")
            time.sleep(2)
            
    except Exception as e:
        logging.error(f"Error during scraping: {e}")
        
    finally:
        scraper.close()
        logging.info("Scraping completed")

if __name__ == "__main__":
    main()