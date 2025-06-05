import csv
import re
import os
import tempfile
import requests
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def setup_chrome_driver():
    """Setup Chrome driver with proper configuration to avoid conflicts"""
    chrome_options = Options()
    
    # Create a unique temporary directory for user data
    temp_dir = tempfile.mkdtemp()
    chrome_options.add_argument(f"--user-data-dir={temp_dir}")
    
    # Additional options to prevent conflicts
    chrome_options.add_argument("--no-first-run")
    chrome_options.add_argument("--no-default-browser-check")
    chrome_options.add_argument("--disable-default-apps")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-translate")
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    
    # Performance and stability options
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Add user agent to appear more like a regular browser
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Experimental options to avoid detection
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.maximize_window()
        return driver
    except Exception as e:
        logging.error(f"Failed to create Chrome driver: {e}")
        raise

def login_to_linkedin(driver, username, password):
    """Login to LinkedIn with improved error handling"""
    try:
        logging.info("Navigating to LinkedIn login page...")
        driver.get("https://www.linkedin.com/login")
        
        # Wait for login form to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        
        # Enter username
        username_field = driver.find_element(By.ID, "username")
        username_field.clear()
        username_field.send_keys(username)
        
        # Enter password
        password_field = driver.find_element(By.ID, "password")
        password_field.clear()
        password_field.send_keys(password)
        
        # Click login button
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        
        # Wait for login to complete
        WebDriverWait(driver, 15).until(
            lambda d: "feed" in d.current_url or "challenge" in d.current_url or "login" not in d.current_url
        )
        
        # Check if we're redirected to a challenge page
        if "challenge" in driver.current_url:
            logging.warning("LinkedIn requires additional verification. Please complete manually.")
            input("Press Enter after completing the challenge...")
        
        logging.info("Successfully logged into LinkedIn")
        
    except Exception as e:
        logging.error(f"Error logging into LinkedIn: {e}")
        raise

def navigate_to_company_page(driver, company_name):
    """Navigate to company page with better error handling"""
    try:
        # Create the LinkedIn URL for the company page
        company_url = f"https://www.linkedin.com/company/{company_name.lower()}/"
        logging.info(f"Navigating to company page: {company_url}")
        driver.get(company_url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Check if we're on the correct page
        if "company" not in driver.current_url:
            raise Exception("Failed to navigate to company page")
            
        logging.info("Successfully navigated to company page")
        time.sleep(3)
        
    except Exception as e:
        logging.error(f"Error navigating to company page: {e}")
        raise

def navigate_to_people_tab(driver, company_name):
    """Navigate to people tab with improved reliability"""
    try:
        # Look for the People tab with multiple strategies
        people_tab_selectors = [
            f"//a[contains(@href, '/company/{company_name.lower()}/people/')]",
            "//a[contains(text(), 'People')]",
            "//a[contains(@aria-label, 'People')]",
            "//nav//a[contains(@href, '/people/')]"
        ]
        
        people_tab = None
        for selector in people_tab_selectors:
            try:
                people_tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                break
            except:
                continue
        
        if not people_tab:
            raise Exception("Could not find People tab")
        
        # Scroll to the element and click
        driver.execute_script("arguments[0].scrollIntoView(true);", people_tab)
        time.sleep(2)
        
        # Try clicking with JavaScript if regular click fails
        try:
            people_tab.click()
        except:
            driver.execute_script("arguments[0].click();", people_tab)
        
        # Wait for the people page to load
        WebDriverWait(driver, 15).until(
            lambda d: "/people/" in d.current_url
        )
        
        logging.info(f"Successfully navigated to People tab. Current URL: {driver.current_url}")
        time.sleep(3)
        
    except Exception as e:
        logging.error(f"Error navigating to People tab: {e}")
        raise

def scroll_down(driver):
    """Improved scrolling function with better load detection"""
    logging.info("Starting to scroll and load all employees...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    max_scrolls = 50  # Prevent infinite scrolling
    
    while scroll_count < max_scrolls:
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # Wait for content to load
        
        # Check if new content loaded
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            # Try to find and click "Show more" button
            try:
                load_more_selectors = [
                    "//button[contains(@class, 'scaffold-finite-scroll__load-button')]",
                    "//button[contains(text(), 'Show more')]",
                    "//button[contains(text(), 'Load more')]"
                ]
                
                load_more_button = None
                for selector in load_more_selectors:
                    try:
                        load_more_button = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        break
                    except:
                        continue
                
                if load_more_button:
                    driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                    time.sleep(2)
                    load_more_button.click()
                    logging.info("Clicked 'Show more results' button.")
                    time.sleep(5)
                else:
                    logging.info("No more content to load.")
                    break
                    
            except Exception as e:
                logging.info(f"No more content to load. Reason: {e}")
                break
        
        last_height = new_height
        scroll_count += 1
        
        if scroll_count % 10 == 0:
            logging.info(f"Completed {scroll_count} scrolls...")
    
    logging.info("Finished scrolling.")

def remove_emojis(text):
    """Remove emojis from text"""
    if not text:
        return ""
    
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & Pictographs
        "\U0001F680-\U0001F6FF"  # Transport & Map Symbols
        "\U0001F1E0-\U0001F1FF"  # Flags (iOS)
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed Characters
        "]+",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub(r'', text).strip()

def scrape_employees_with_roles(driver, domain):
    """Scrape employees with improved selectors and error handling"""
    employees = []
    scroll_down(driver)
    
    try:
        # Multiple selectors to find employee cards
        employee_card_selectors = [
            "//li[contains(@class, 'org-people-profile-card__profile-card-spacing')]",
            "//li[contains(@class, 'org-people-profile-card')]",
            "//div[contains(@class, 'org-people-profile-card')]"
        ]
        
        employee_cards = []
        for selector in employee_card_selectors:
            try:
                employee_cards = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, selector))
                )
                if employee_cards:
                    logging.info(f"Found {len(employee_cards)} employee cards using selector: {selector}")
                    break
            except:
                continue
        
        if not employee_cards:
            logging.error("No employee cards found")
            return employees
        
        # Extract information from each card
        for i, card in enumerate(employee_cards):
            try:
                # Multiple selectors for name
                name_selectors = [
                    ".//a[contains(@class, 'link-without-visited-state')]",
                    ".//a[contains(@class, 'app-aware-link')]",
                    ".//span[contains(@class, 'org-people-profile-card__profile-title')]",
                    ".//h3//span"
                ]
                
                name = None
                for selector in name_selectors:
                    try:
                        name_element = card.find_element(By.XPATH, selector)
                        name = name_element.text.strip()
                        if name:
                            break
                    except:
                        continue
                
                # Multiple selectors for role
                role_selectors = [
                    ".//div[contains(@class, 'lt-line-clamp--multi-line')]",
                    ".//div[contains(@class, 'org-people-profile-card__summary')]",
                    ".//p[contains(@class, 'org-people-profile-card__summary')]"
                ]
                
                role_text = None
                for selector in role_selectors:
                    try:
                        role_element = card.find_element(By.XPATH, selector)
                        role_text = role_element.text.strip()
                        if role_text:
                            break
                    except:
                        continue
                
                # Clean up the extracted data
                if name:
                    name = remove_emojis(name)
                if role_text:
                    role_text = remove_emojis(role_text)
                
                # Add to the list only if both name and role are present
                if name and role_text:
                    us1, us2, us3 = generate_usernames(name, domain)
                    employees.append((name, role_text, us1, us2, us3))
                    logging.info(f"Found employee {i+1}: {name}, Role: {role_text}")
                else:
                    logging.debug(f"Skipped employee card {i+1} - missing name or role")
                    
            except Exception as e:
                logging.warning(f"Error extracting data from employee card {i+1}: {e}")
                continue
    
    except Exception as e:
        logging.error(f"Error scraping employees and roles: {e}")
    
    logging.info(f"Successfully scraped {len(employees)} employees")
    return employees

def generate_usernames(name, domain):
    """Generate username variations"""
    if not name or not domain:
        return "", "", ""
    
    parts = name.lower().split()
    if len(parts) < 2:
        # If only one name part, use it for all variations
        single_name = parts[0] if parts else name.lower()
        return (f"{single_name}@{domain}", 
                f"{single_name}@{domain}", 
                f"{single_name}@{domain}")
    
    first_name = parts[0]
    last_name = parts[-1]
    
    username1 = f"{first_name}.{last_name}@{domain}"
    username2 = f"{first_name}{last_name}@{domain}"
    username3 = f"{first_name[0]}{last_name}@{domain}"
    
    return username1, username2, username3

def save_to_csv(employees, file_name):
    """Save employees data to CSV"""
    try:
        with open(file_name, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Name", "Role", "USER1", "USER2", "USER3"])
            for name, role, us1, us2, us3 in employees:
                writer.writerow([name, role, us1, us2, us3])
        logging.info(f"Successfully saved {len(employees)} employees to {file_name}")
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")

def get_company_name(domain):
    """Get company LinkedIn name from domain using SerpAPI"""
    api_key = "6b54a08faf9e672c1fe89b3f47d1dadcc2491849931d2e4f66eb9346e45dd080"
    params = {
        "q": f"site:linkedin.com/company {domain}",
        "api_key": api_key,
        "engine": "google",
        "num": 10
    }
    
    try:
        logging.info(f"Searching for LinkedIn company page for domain: {domain}")
        response = requests.get("https://serpapi.com/search", params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        for result in data.get("organic_results", []):
            url = result.get("link", "")
            title = result.get("title", "")
            
            # Extract company name from LinkedIn URL
            match = re.search(r'https://www\.linkedin\.com/company/([^/]+)/?', url)
            if match:
                company_name = match.group(1)
                logging.info(f"Found company: {company_name} from URL: {url}")
                return company_name
        
        logging.warning(f"No LinkedIn company page found for domain: {domain}")
        return None
        
    except requests.RequestException as e:
        logging.error(f"Request error while searching for company: {e}")
    except Exception as e:
        logging.error(f"Unexpected error while searching for company: {e}")
    
    return None

def execute_linkedin(domain):
    """Main execution function with improved error handling"""
    employees = []
    
    # LinkedIn credentials
    linkedin_username = "hila.benmichael@nitzanim.tech"
    linkedin_password = "Z9*nA&6HfMwq839"
    
    if not linkedin_username or not linkedin_password:
        logging.error("LinkedIn credentials are not set.")
        return []
    
    # Get company name
    company_name = get_company_name(domain)
    if not company_name:
        logging.error("Company name not found. Cannot proceed.")
        return []
    
    company_url = f"https://www.linkedin.com/company/{company_name.lower()}/"
    logging.info(f"Company URL: {company_url}, Company name: {company_name}")
    
    driver = None
    try:
        # Setup Chrome driver
        driver = setup_chrome_driver()
        
        # Execute scraping steps
        login_to_linkedin(driver, linkedin_username, linkedin_password)
        navigate_to_company_page(driver, company_name)
        navigate_to_people_tab(driver, company_name)
        employees = scrape_employees_with_roles(driver, domain)
        
        if employees:
            save_to_csv(employees, "employees.csv")
            logging.info(f"Successfully found and saved {len(employees)} employees.")
        else:
            logging.warning("No employees found.")
            
    except Exception as e:
        logging.error(f"Error during execution: {e}")
        
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return employees

if __name__ == "__main__":
    try:
        domain_name = input("Enter the domain name: ").strip()
        if not domain_name:
            print("Domain name cannot be empty.")
            exit(1)
            
        employees = execute_linkedin(domain_name)
        
        if employees:
            print(f"\nSuccessfully scraped {len(employees)} employees:")
            for name, role, _, _, _ in employees[:5]:  # Show first 5
                print(f"- {name}: {role}")
            if len(employees) > 5:
                print(f"... and {len(employees) - 5} more")
        else:
            print("No employees found.")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"An error occurred: {e}")