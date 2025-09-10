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
#     TimeoutException, NoSuchElementException, StaleElementReferenceException,
#     ElementClickInterceptedException
# )
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.keys import Keys
# import gspread
# from google.oauth2.service_account import Credentials
# import json
# from typing import List, Dict, Optional, Tuple, Any
# import logging

# # Set up logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler("scraper.log"),
#         logging.StreamHandler()
#     ]
# )

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
#         chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
#         self.driver = webdriver.Chrome(options=chrome_options)
#         self.driver.implicitly_wait(5)
        
#     def retry_action(self, action, max_attempts=3, delay=2):
#         """Retry a specific action with delays between attempts"""
#         for attempt in range(max_attempts):
#             try:
#                 return action()
#             except (TimeoutException, StaleElementReferenceException, ElementClickInterceptedException) as e:
#                 if attempt == max_attempts - 1:
#                     raise e
#                 logging.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
#                 time.sleep(delay)
                
#     def wait_for_element(self, by, value, timeout=15):
#         """Wait for an element to be present"""
#         return WebDriverWait(self.driver, timeout).until(
#             EC.presence_of_element_located((by, value))
#         )
        
#     def wait_for_element_clickable(self, by, value, timeout=15):
#         """Wait for an element to be clickable"""
#         return WebDriverWait(self.driver, timeout).until(
#             EC.element_to_be_clickable((by, value))
#         )
        
#     def navigate_to_search_page(self):
#         """Navigate to the case search page"""
#         try:
#             self.driver.get("https://courtsapp.montcopa.org/psi3/v/search/case")
#             # Wait for page to load
#             self.wait_for_element(By.TAG_NAME, "body")
#             time.sleep(3)  # Initial page load
#             return True
#         except Exception as e:
#             logging.error(f"Failed to navigate to search page: {e}")
#             return False
            
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
#                 By.XPATH, "//button[contains(@class, 'btn-primary') and contains(., 'Search')]"
#             )
#             search_button.click()
#             time.sleep(5)
            
#             # Wait for results table or no results message
#             try:
#                 self.wait_for_element(By.ID, "gridViewResults", timeout=10)
#                 return True
#             except TimeoutException:
#                 # Check if no results message appears
#                 try:
#                     no_results = self.driver.find_element(By.XPATH, "//div[contains(text(), 'No results')]")
#                     if no_results:
#                         logging.info("No results found for the search criteria")
#                         return True
#                 except:
#                     logging.error("Search results did not load properly")
#                     return False
                
#         except Exception as e:
#             logging.error(f"Error performing search: {e}")
#             return False
            
#     def extract_case_details(self, case_url):
#         """Extract case details from the detail page"""
#         self.driver.get(case_url)
#         time.sleep(3)
        
#         case_data = {
#             "case_number": "",
#             "last_filing_date": "",
#             "personal_representatives": [],
#             "case_foundation_parties_address": "",
#             "case_details_url": case_url,
#             "scrape_timestamp": datetime.datetime.now().isoformat()
#         }
        
#         try:
#             # Extract case number - try multiple possible selectors
#             try:
#                 case_number_element = self.wait_for_element(
#                     By.XPATH, "//td[contains(., 'Case Number')]/following-sibling::td"
#                 )
#                 case_data["case_number"] = case_number_element.text.strip()
#             except:
#                 try:
#                     case_number_element = self.driver.find_element(
#                         By.XPATH, "//th[contains(., 'Case Number')]/following-sibling::td"
#                     )
#                     case_data["case_number"] = case_number_element.text.strip()
#                 except:
#                     logging.warning("Could not find case number")
                
#             # Extract last filing date
#             try:
#                 last_filing_element = self.driver.find_element(
#                     By.XPATH, "//td[contains(., 'Last Filing Date') or contains(., 'Filing Date')]/following-sibling::td"
#                 )
#                 case_data["last_filing_date"] = last_filing_element.text.strip()
#             except:
#                 logging.warning("Could not find last filing date")
                
#             # Extract personal representatives
#             try:
#                 reps_tables = self.driver.find_elements(
#                     By.XPATH, "//table[contains(@id, 'PersonalRepresentatives') or contains(., 'Personal Representative')]"
#                 )
                
#                 for table in reps_tables:
#                     rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
                    
#                     for row in rows:
#                         cells = row.find_elements(By.TAG_NAME, "td")
#                         if len(cells) >= 3:  # Ensure we have enough cells
#                             rep = {
#                                 "name": cells[0].text.strip() if cells[0].text.strip() else "",
#                                 "role": cells[1].text.strip() if len(cells) > 1 else "",
#                                 "address": cells[2].text.strip().replace("\n", ", ") if len(cells) > 2 else ""
#                             }
#                             if rep["name"]:  # Only add if we have a name
#                                 case_data["personal_representatives"].append(rep)
#             except Exception as e:
#                 logging.warning(f"Could not extract personal representatives: {e}")
                
#             # Extract case foundation parties address
#             try:
#                 parties_tables = self.driver.find_elements(
#                     By.XPATH, "//table[contains(@id, 'CaseFoundationParties') or contains(., 'Parties')]"
#                 )
                
#                 for table in parties_tables:
#                     rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
                    
#                     if rows:
#                         for row in rows:
#                             cells = row.find_elements(By.TAG_NAME, "td")
#                             if len(cells) >= 5:  # Address is often in the 5th column
#                                 address = cells[4].text.strip().replace("\n", ", ")
#                                 if address and not case_data["case_foundation_parties_address"]:
#                                     case_data["case_foundation_parties_address"] = address
#             except Exception as e:
#                 logging.warning(f"Could not extract case foundation parties address: {e}")
                
#         except Exception as e:
#             logging.error(f"Error extracting case details: {e}")
            
#         return case_data
        
#     def get_search_results(self):
#         """Get all search results from the current page"""
#         results = []
#         try:
#             # Try to find results table
#             try:
#                 table = self.wait_for_element(By.ID, "gridViewResults", timeout=10)
#                 rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header if exists
#             except:
#                 # Check if there's a different table structure
#                 tables = self.driver.find_elements(By.TAG_NAME, "table")
#                 for table in tables:
#                     if "probate" in table.text.lower():
#                         rows = table.find_elements(By.TAG_NAME, "tr")[1:]
#                         break
#                 else:
#                     logging.info("No results table found")
#                     return results
            
#             for row in rows:
#                 try:
#                     select_link = row.find_element(By.TAG_NAME, "a")
#                     case_url = select_link.get_attribute("href")
#                     if case_url and "case" in case_url:
#                         results.append(case_url)
#                 except:
#                     continue
                    
#         except Exception as e:
#             logging.error(f"Error getting search results: {e}")
            
#         return results
        
#     def has_next_page(self):
#         """Check if there's a next page of results"""
#         try:
#             next_buttons = self.driver.find_elements(
#                 By.XPATH, "//a[contains(@href, 'Skip') or contains(@href, 'next') or contains(text(), 'Next')]"
#             )
#             for button in next_buttons:
#                 if button.is_enabled() and button.is_displayed():
#                     return True
#             return False
#         except:
#             return False
            
#     def go_to_next_page(self):
#         """Navigate to the next page of results"""
#         try:
#             next_buttons = self.driver.find_elements(
#                 By.XPATH, "//a[contains(@href, 'Skip') or contains(@href, 'next') or contains(text(), 'Next')]"
#             )
#             for button in next_buttons:
#                 if button.is_enabled() and button.is_displayed():
#                     button.click()
#                     time.sleep(3)
#                     self.wait_for_element(By.TAG_NAME, "body")
#                     return True
#             return False
#         except Exception as e:
#             logging.error(f"Error going to next page: {e}")
#             return False
            
#     def scrape_cases(self, start_date="01/01/2025", end_date=None):
#         """Main method to scrape all cases"""
#         if end_date is None:
#             end_date = date.today().strftime("%m/%d/%Y")
            
#         if not self.navigate_to_search_page():
#             return []
        
#         if not self.perform_search(start_date, end_date):
#             logging.error("Search failed")
#             return []
            
#         all_case_data = []
#         page = 1
        
#         while True:
#             logging.info(f"Scraping page {page}")
#             case_urls = self.get_search_results()
            
#             if not case_urls:
#                 logging.info("No case URLs found on this page")
#                 break
                
#             logging.info(f"Found {len(case_urls)} cases on page {page}")
            
#             for i, case_url in enumerate(case_urls):
#                 logging.info(f"Scraping case {i+1}/{len(case_urls)}: {case_url}")
#                 case_data = self.extract_case_details(case_url)
                
#                 # Only include cases with personal representatives or valid data
#                 if case_data["case_number"] or case_data["personal_representatives"]:
#                     all_case_data.append(case_data)
#                 else:
#                     logging.warning(f"Skipping case with no data: {case_url}")
                
#                 # Go back to search results
#                 self.driver.back()
#                 time.sleep(3)
#                 # Wait for results to load
#                 try:
#                     self.wait_for_element(By.TAG_NAME, "body")
#                     self.wait_for_element(By.ID, "gridViewResults", timeout=5)
#                 except:
#                     pass
                
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
#             logging.info("Successfully connected to Google Sheets")
#         except Exception as e:
#             logging.error(f"Error setting up Google Sheets client: {e}")
#             raise
            
#     def get_or_create_sheet(self, sheet_name):
#         """Get or create a sheet with the given name"""
#         try:
#             worksheet = self.spreadsheet.worksheet(sheet_name)
#             logging.info(f"Found existing sheet: {sheet_name}")
#         except gspread.exceptions.WorksheetNotFound:
#             logging.info(f"Creating new sheet: {sheet_name}")
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
#                 "Case Foundation Parties Address",
#                 "Case Details URL",
#                 "Scrape Timestamp"
#             ]
#             worksheet.update("A1:H1", [headers])
            
#             # Format headers
#             worksheet.format("A1:H1", {
#                 "textFormat": {"bold": True},
#                 "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
#             })
            
#             # Freeze header row
#             worksheet.freeze(rows=1)
            
#         return worksheet
        
#     def update_sheet(self, sheet_name, case_data):
#         """Update the sheet with the given case data"""
#         worksheet = self.get_or_create_sheet(sheet_name)
        
#         # Get existing data to avoid duplicates
#         existing_cases = set()
#         try:
#             existing_data = worksheet.get_all_values()
#             if len(existing_data) > 1:  # Skip header
#                 for row in existing_data[1:]:
#                     if row:  # Non-empty row
#                         existing_cases.add(row[0])  # Case number is in first column
#         except Exception as e:
#             logging.warning(f"Could not read existing data: {e}")
        
#         # Prepare data for writing
#         rows = []
#         for case in case_data:
#             # Skip if case already exists
#             if case["case_number"] in existing_cases:
#                 logging.info(f"Skipping existing case: {case['case_number']}")
#                 continue
                
#             for rep in case["personal_representatives"]:
#                 row = [
#                     case["case_number"],
#                     case["last_filing_date"],
#                     rep["name"],
#                     rep["role"],
#                     rep["address"],
#                     case["case_foundation_parties_address"],
#                     case["case_details_url"],
#                     case["scrape_timestamp"]
#                 ]
#                 rows.append(row)
                
#         if rows:
#             # Append new data
#             worksheet.append_rows(rows)
#             logging.info(f"Added {len(rows)} new rows to sheet {sheet_name}")
            
#             # Auto-resize columns
#             try:
#                 worksheet.columns_auto_resize(0, 7)  # Columns A to H
#             except:
#                 logging.warning("Could not auto-resize columns")
#         else:
#             logging.info(f"No new data to add to sheet {sheet_name}")
        
#     def get_last_scraped_date(self):
#         """Get the last date that was scraped from all sheets"""
#         try:
#             worksheets = self.spreadsheet.worksheets()
#             latest_date = None
            
#             for worksheet in worksheets:
#                 try:
#                     # Get all values from the date column (column B)
#                     dates = worksheet.col_values(2)
#                     if len(dates) > 1:  # Skip header
#                         for date_str in dates[1:]:
#                             if date_str:
#                                 parsed_date = self.parse_date(date_str)
#                                 if parsed_date:
#                                     if latest_date is None or parsed_date > latest_date:
#                                         latest_date = parsed_date
#                 except Exception as e:
#                     logging.warning(f"Could not read dates from sheet {worksheet.title}: {e}")
#                     continue
                    
#             return latest_date
            
#         except Exception as e:
#             logging.error(f"Error getting last scraped date: {e}")
#             return None
        
#     def parse_date(self, date_str):
#         """Parse a date string into a date object"""
#         try:
#             # Handle various date formats
#             for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d/%m/%Y", "%d-%m-%Y"):
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
#     #DEFAULT_START_DATE = "01/01/2025"
    
#     # Get credentials from environment
#     google_credentials = os.environ.get("GOOGLE_CREDENTIALS")
#     spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    
#     if not google_credentials or not spreadsheet_id:
#         logging.error("Error: GOOGLE_CREDENTIALS and SPREADSHEET_ID environment variables are required")
#         return
        
#     # Initialize Google Sheets handler
#     try:
#         sheets_handler = GoogleSheetsHandler(google_credentials, spreadsheet_id)
#     except Exception as e:
#         logging.error(f"Failed to initialize Google Sheets handler: {e}")
#         return
        
#     # Determine the start date for scraping
#     last_date = sheets_handler.get_last_scraped_date()
    
#     if last_date:
#         start_date = (last_date + timedelta(days=1)).strftime("%m/%d/%Y")
#         logging.info(f"Resuming from last scrape date: {start_date}")
#     # else:
#     #     start_date = DEFAULT_START_DATE
#     #     logging.info(f"No previous scrape found, starting from: {start_date}")
        
#     # Initialize scraper
#     scraper = MontgomeryCountyScraper(headless=HEADLESS)
    
#     try:
#         # Scrape cases
#         case_data = scraper.scrape_cases(start_date=start_date)
        
#         if case_data:
#             logging.info(f"Successfully scraped {len(case_data)} cases")
            
#             # Group cases by month based on last filing date
#             cases_by_month = {}
#             for case in case_data:
#                 if case["last_filing_date"]:
#                     date_obj = sheets_handler.parse_date(case["last_filing_date"])
#                     if date_obj:
#                         month_key = date_obj.strftime("%Y-%m")
#                         if month_key not in cases_by_month:
#                             cases_by_month[month_key] = []
#                         cases_by_month[month_key].append(case)
#                     else:
#                         logging.warning(f"Could not parse date: {case['last_filing_date']}")
#                 else:
#                     # If no date, use current month
#                     month_key = datetime.datetime.now().strftime("%Y-%m")
#                     if month_key not in cases_by_month:
#                         cases_by_month[month_key] = []
#                     cases_by_month[month_key].append(case)
            
#             # Update each monthly sheet
#             for month, cases in cases_by_month.items():
#                 sheets_handler.update_sheet(month, cases)
                
#             logging.info(f"Processed cases for {len(cases_by_month)} months")
#         else:
#             logging.info("No cases found or no new cases since last scrape")
            
#     except Exception as e:
#         logging.error(f"Error during scraping: {e}")
        
#     finally:
#         scraper.close()
#         logging.info("Scraping completed")


# if __name__ == "__main__":
#     main()


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

# -----------------------------
# Credentials Loading Functions
# -----------------------------
def load_service_account_info():
    """Load Google service account credentials from file or environment variable"""
    file_env = os.environ.get("GOOGLE_CREDENTIALS_FILE")
    if file_env:
        if os.path.exists(file_env):
            with open(file_env, "r", encoding="utf-8") as fh:
                return json.load(fh)
        raise ValueError(f"GOOGLE_CREDENTIALS_FILE set but not found: {file_env}")

    creds_raw = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_raw:
        raise ValueError("GOOGLE_CREDENTIALS or GOOGLE_CREDENTIALS_FILE is required.")

    txt = creds_raw.strip()

    if txt.startswith("{"):
        # Fix escaped newlines in private_key
        txt = txt.replace("\\n", "\n")
        try:
            return json.loads(txt)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse GOOGLE_CREDENTIALS as JSON: {e}")
            # Try to fix common JSON issues
            try:
                # Handle single quotes instead of double quotes
                txt = txt.replace("'", '"')
                return json.loads(txt)
            except:
                raise ValueError("GOOGLE_CREDENTIALS is not valid JSON")

    if os.path.exists(creds_raw):
        with open(creds_raw, "r", encoding="utf-8") as fh:
            return json.load(fh)

    raise ValueError("GOOGLE_CREDENTIALS is neither valid JSON nor an existing file path.")

class MontgomeryCountyScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Initialize the Chrome driver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # Set Chrome binary location for GitHub Actions
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
            # Wait for page to load
            self.wait_for_element(By.TAG_NAME, "body")
            time.sleep(3)  # Initial page load
            return True
        except Exception as e:
            logging.error(f"Failed to navigate to search page: {e}")
            return False
            
    def perform_search(self, start_date="01/01/2025", end_date=None):
        """Perform the search with the given date range"""
        if end_date is None:
            end_date = date.today().strftime("%m/%d/%Y")
            
        try:
            # Wait for search box and enter search term
            search_box = self.wait_for_element(By.ID, "Q")
            search_box.clear()
            search_box.send_keys("probate")
            time.sleep(2)
            
            # Set filing date from
            from_date = self.wait_for_element(By.ID, "FilingDateFrom")
            from_date.clear()
            from_date.send_keys(start_date)
            time.sleep(2)
            
            # Set filing date to
            to_date = self.wait_for_element(By.ID, "FilingDateTo")
            to_date.clear()
            to_date.send_keys(end_date)
            time.sleep(2)
            
            # Click search button
            search_button = self.wait_for_element_clickable(
                By.XPATH, "//button[contains(@class, 'btn-primary') and contains(., 'Search')]"
            )
            search_button.click()
            time.sleep(5)
            
            # Wait for results table or no results message
            try:
                self.wait_for_element(By.ID, "gridViewResults", timeout=10)
                return True
            except TimeoutException:
                # Check if no results message appears
                try:
                    no_results = self.driver.find_element(By.XPATH, "//div[contains(text(), 'No results')]")
                    if no_results:
                        logging.info("No results found for the search criteria")
                        return True
                except:
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
            # Extract case number - try multiple possible selectors
            try:
                case_number_element = self.wait_for_element(
                    By.XPATH, "//td[contains(., 'Case Number')]/following-sibling::td"
                )
                case_data["case_number"] = case_number_element.text.strip()
            except:
                try:
                    case_number_element = self.driver.find_element(
                        By.XPATH, "//th[contains(., 'Case Number')]/following-sibling::td"
                    )
                    case_data["case_number"] = case_number_element.text.strip()
                except:
                    logging.warning("Could not find case number")
                
            # Extract last filing date
            try:
                last_filing_element = self.driver.find_element(
                    By.XPATH, "//td[contains(., 'Last Filing Date') or contains(., 'Filing Date')]/following-sibling::td"
                )
                # Try to parse and standardize the date format
                date_text = last_filing_element.text.strip()
                try:
                    # Try to parse various date formats
                    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%Y/%m/%d"):
                        try:
                            parsed_date = datetime.datetime.strptime(date_text, fmt)
                            case_data["last_filing_date"] = parsed_date.strftime("%Y-%m-%d")
                            break
                        except ValueError:
                            continue
                    else:
                        # If no format matched, keep the original text
                        case_data["last_filing_date"] = date_text
                except:
                    case_data["last_filing_date"] = date_text
            except:
                logging.warning("Could not find last filing date")
                
            # Extract personal representatives
            try:
                reps_tables = self.driver.find_elements(
                    By.XPATH, "//table[contains(@id, 'PersonalRepresentatives') or contains(., 'Personal Representative')]"
                )
                
                for table in reps_tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
                    
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:  # Ensure we have enough cells
                            rep = {
                                "name": cells[0].text.strip() if cells[0].text.strip() else "",
                                "role": cells[1].text.strip() if len(cells) > 1 else "",
                                "address": cells[2].text.strip().replace("\n", ", ") if len(cells) > 2 else ""
                            }
                            if rep["name"]:  # Only add if we have a name
                                case_data["personal_representatives"].append(rep)
            except Exception as e:
                logging.warning(f"Could not extract personal representatives: {e}")
                
            # Extract case foundation parties address
            try:
                parties_tables = self.driver.find_elements(
                    By.XPATH, "//table[contains(@id, 'CaseFoundationParties') or contains(., 'Parties')]"
                )
                
                for table in parties_tables:
                    rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
                    
                    if rows:
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 5:  # Address is often in the 5th column
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
            # Try to find results table
            try:
                table = self.wait_for_element(By.ID, "gridViewResults", timeout=10)
                rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header if exists
            except:
                # Check if there's a different table structure
                tables = self.driver.find_elements(By.TAG_NAME, "table")
                for table in tables:
                    if "probate" in table.text.lower():
                        rows = table.find_elements(By.TAG_NAME, "tr")[1:]
                        break
                else:
                    logging.info("No results table found")
                    return results
            
            for row in rows:
                try:
                    select_link = row.find_element(By.TAG_NAME, "a")
                    case_url = select_link.get_attribute("href")
                    if case_url and "case" in case_url:
                        results.append(case_url)
                except:
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
        except:
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
        max_pages = 50  # Safety limit to prevent infinite loops
        
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
                
                # Only include cases with personal representatives or valid data
                if case_data["case_number"] or case_data["personal_representatives"]:
                    all_case_data.append(case_data)
                else:
                    logging.warning(f"Skipping case with no data: {case_url}")
                
                # Go back to search results
                self.driver.back()
                time.sleep(3)
                # Wait for results to load
                try:
                    self.wait_for_element(By.TAG_NAME, "body")
                    self.wait_for_element(By.ID, "gridViewResults", timeout=5)
                except:
                    # If navigation fails, restart from search page
                    if not self.navigate_to_search_page() or not self.perform_search(start_date, end_date):
                        logging.error("Failed to return to search results")
                        return all_case_data
                
            # Check for next page
            if not self.has_next_page():
                break
                
            if not self.go_to_next_page():
                break
                
            page += 1
            time.sleep(2)  # Be respectful to the server
            
        return all_case_data
        
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()


class GoogleSheetsHandler:
    def __init__(self, spreadsheet_id):
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None
        self.setup_client()
        
    def setup_client(self):
        """Set up the Google Sheets client using the proper credential loading"""
        try:
            # Load service account info using the provided function
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
            
            # Log service account email for verification
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
            
            # Set up headers
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
            
            # Format headers
            worksheet.format("A1:H1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
            })
            
            # Freeze header row
            worksheet.freeze(rows=1)
            
        return worksheet
        
    def get_last_scraped_date(self, sheet_name):
        """Get the last scraped date from the specified sheet"""
        try:
            worksheet = self.get_or_create_sheet(sheet_name)
            # Get all dates from column B (Last Filing Date)
            dates = worksheet.col_values(2)
            # Skip header and find the most recent date
            if len(dates) > 1:
                # Get all dates, convert to datetime objects for comparison
                date_objects = []
                for date_str in dates[1:]:
                    try:
                        # Try to parse various date formats
                        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"):
                            try:
                                date_obj = datetime.datetime.strptime(date_str, fmt).date()
                                date_objects.append(date_obj)
                                break
                            except ValueError:
                                continue
                    except:
                        continue
                
                if date_objects:
                    # Return the most recent date
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
            # Get all case numbers from column A
            case_numbers = worksheet.col_values(1)
            # Skip header and return all case numbers
            return set(case_numbers[1:]) if len(case_numbers) > 1 else set()
        except Exception as e:
            logging.error(f"Error getting all case numbers: {e}")
            return set()
        
    def update_sheet(self, sheet_name, case_data, existing_case_numbers):
        """Update the sheet with the given case data, skipping existing cases"""
        worksheet = self.get_or_create_sheet(sheet_name)
        
        # Prepare data for writing
        rows = []
        for case in case_data:
            # Skip if case already exists
            if case["case_number"] in existing_case_numbers:
                logging.info(f"Skipping existing case: {case['case_number']}")
                continue
                
            # Validate we have at least a case number or representatives
            if not case["case_number"] and not case["personal_representatives"]:
                logging.warning(f"Skipping invalid case with no data: {case['case_details_url']}")
                continue
                
            for rep in case["personal_representatives"]:
                row = [
                    case["case_number"],
                    case["last_filing_date"],
                    rep["name"],
                    rep["role"],
                    rep["address"],
                    case["case_foundation_parties_address"],
                    case["case_details_url"],
                    case["scrape_timestamp"]
                ]
                rows.append(row)
                
        if rows:
            # Append new data
            worksheet.append_rows(rows)
            logging.info(f"Added {len(rows)} new rows to sheet {sheet_name}")
            
            # Auto-resize columns
            try:
                worksheet.columns_auto_resize(0, 8)  # Columns A to H
            except:
                logging.warning("Could not auto-resize columns")
        else:
            logging.info(f"No new data to add to sheet {sheet_name}")


def get_monthly_date_ranges(start_date_str=None):
    """Generate date ranges for each month from start_date to current date"""
    if start_date_str:
        try:
            # Parse the start date
            start_date = datetime.datetime.strptime(start_date_str, "%m/%d/%Y").date()
        except ValueError:
            logging.error(f"Invalid start date format: {start_date_str}. Using default.")
            start_date = datetime.date(2025, 1, 1)  # Default start date
    else:
        start_date = datetime.date(2025, 1, 1)  # Default start date
    
    end_date = datetime.date.today()
    
    # Generate monthly ranges
    date_ranges = []
    current = start_date
    
    while current <= end_date:
        # First day of the month
        first_day = current.replace(day=1)
        
        # Last day of the month
        if current.month == 12:
            next_month = current.replace(year=current.year+1, month=1, day=1)
        else:
            next_month = current.replace(month=current.month+1, day=1)
        
        last_day = next_month - datetime.timedelta(days=1)
        
        # If last_day is beyond today, use today
        if last_day > end_date:
            last_day = end_date
        
        # Add the range if it's valid
        if first_day <= last_day:
            date_ranges.append((
                first_day.strftime("%m/%d/%Y"),
                last_day.strftime("%m/%d/%Y"),
                first_day.strftime("%b %Y")  # Sheet name
            ))
        
        # Move to next month
        current = next_month
    
    return date_ranges


def main():
    # Configuration
    HEADLESS = True
    
    # Get spreadsheet ID from environment
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    
    if not spreadsheet_id:
        logging.error("Error: SPREADSHEET_ID environment variable is required")
        return
        
    # Initialize Google Sheets handler
    try:
        sheets_handler = GoogleSheetsHandler(spreadsheet_id)
    except Exception as e:
        logging.error(f"Failed to initialize Google Sheets handler: {e}")
        return
        
    # Initialize scraper
    scraper = MontgomeryCountyScraper(headless=HEADLESS)
    
    try:
        # Get the last scraped date from the most recent sheet
        current_month = datetime.datetime.now().strftime("%b %Y")
        last_scraped_date = sheets_handler.get_last_scraped_date(current_month)
        
        # If no data in current month, check previous months
        if not last_scraped_date:
            prev_month = (datetime.datetime.now() - datetime.timedelta(days=31)).strftime("%b %Y")
            last_scraped_date = sheets_handler.get_last_scraped_date(prev_month)
        
        # Generate monthly date ranges from the last scraped date or default
        date_ranges = get_monthly_date_ranges(last_scraped_date)
        
        if not date_ranges:
            logging.info("No date ranges to process. Data is up to date.")
            return
            
        logging.info(f"Processing {len(date_ranges)} month(s) of data")
        
        for start_date, end_date, sheet_name in date_ranges:
            logging.info(f"Processing {sheet_name}: {start_date} to {end_date}")
            
            # Get all existing case numbers for this month's sheet
            existing_case_numbers = sheets_handler.get_all_case_numbers(sheet_name)
            logging.info(f"Found {len(existing_case_numbers)} existing cases in {sheet_name}")
            
            # Scrape cases for this date range
            case_data = scraper.scrape_cases(start_date=start_date, end_date=end_date)
            
            if case_data:
                logging.info(f"Successfully scraped {len(case_data)} cases for {sheet_name}")
                
                # Update the sheet with new cases only
                sheets_handler.update_sheet(sheet_name, case_data, existing_case_numbers)
                    
                logging.info(f"Processed cases for {sheet_name}")
            else:
                logging.info(f"No new cases found for {sheet_name}")
            
            # Small delay between months
            time.sleep(2)
            
    except Exception as e:
        logging.error(f"Error during scraping: {e}")
        
    finally:
        scraper.close()
        logging.info("Scraping completed")


if __name__ == "__main__":
    main()