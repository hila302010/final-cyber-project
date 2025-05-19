import csv
import re

import requests
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def login_to_linkedin(driver, username, password):
    try:
        driver.get("https://www.linkedin.com/login")
        time.sleep(5)
        # Enter username
        driver.find_element(By.ID, "username").send_keys(username)
        # Enter password
        driver.find_element(By.ID, "password").send_keys(password)
        # Click login
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(5)
    except Exception as e:
        logging.error(f"Error logging into LinkedIn: {e}")
        raise

def navigate_to_company_page(driver, company_name):
    try:
        # Create the LinkedIn URL for the company page (format: https://www.linkedin.com/company/<company_name>)
        company_url = f"https://www.linkedin.com/company/{company_name.lower()}/"
        driver.get(company_url)
        time.sleep(5)
    except Exception as e:
        logging.error(f"Error navigating to company page: {e}")
        raise


def navigate_to_people_tab(driver, company_name):
    try:
        # Wait for the People tab to load
        people_tab = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//a[contains(@href, '/company/{company_name.lower()}/people/')]"))
        )
        time.sleep(5)  # Allow time to visually see the element

        # Create an ActionChains object to simulate the mouse actions
        actions = ActionChains(driver)

        # Move the mouse to the People tab
        actions.move_to_element(people_tab).perform()
        logging.info("Mouse moved to the People tab.")
        time.sleep(5)  # Wait to see the mouse move

        # Click on the People tab
        actions.click().perform()
        logging.info("Mouse clicked on the People tab.")
        time.sleep(5)  # Allow the page to load

        # Print the current URL after the page loads
        current_url = driver.current_url
        logging.info(f"Current URL after clicking on People tab: {current_url}")

        logging.info("Successfully navigated to the People tab.")
    except Exception as e:
        logging.error(f"Error navigating to People tab: {e}")
        raise


def scroll_down(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Delay to mimic human behavior
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            try:
                # Wait for the first clickable one
                load_more_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//button[contains(@class, 'scaffold-finite-scroll__load-button')]")
                    )
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                time.sleep(5)
                load_more_button.click()
                logging.info("Clicked 'Show more results' button.")

            except Exception as e:
                logging.info(f"No 'Show more results' button found or clickable. Reason: {e}")
                break
        last_height = new_height



def remove_emojis(text):
    # Regular expression to match emojis
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
    return emoji_pattern.sub(r'', text)  # Remove emojis from the text



def scrape_employees_with_roles(driver, domain):
    employees = []
    scroll_down(driver)

    try:
        # Get all employee cards (parent <li> elements)
        employee_cards = WebDriverWait(driver, 60).until(
            EC.presence_of_all_elements_located((By.XPATH, "//li[contains(@class, 'org-people-profile-card__profile-card-spacing')]"))
        )

        # Iterate through each employee card and extract name and role
        for card in employee_cards:
            try:
                # Extract the name
                name_element = card.find_element(By.XPATH, ".//a[contains(@class, 'link-without-visited-state')]")
                name = name_element.text.strip()
                name = remove_emojis(name)  # Remove emojis from the name


                # Extract the role
                role_element = card.find_element(By.XPATH, ".//div[contains(@class, 'lt-line-clamp--multi-line')]")
                role_text = role_element.text.strip()

                # Add to the list only if both name and role are present
                if name and role_text:
                    us1, us2, us3 = generate_usernames(name, domain)
                    employees.append((name, role_text, us1, us2, us3))
                    logging.info(f"Found employee: {name}, Role: {role_text}")
                else:
                    logging.info("Skipped an employee card with missing name or role.")
            except Exception as e:
                logging.warning(f"Error extracting name or role from a card: {e}")

    except Exception as e:
        logging.error(f"Error scraping employees and roles: {e}")

    return employees



def generate_usernames(name, domain):
    parts = name.lower().split()
    if len(parts) < 2:
        return name
    first_name, last_name = parts[0], parts[-1]
    username1 = (f"{first_name}.{last_name}@{domain}")
    username2 = (f"{first_name}{last_name}@{domain}")
    username3 = (f"{first_name[0]}{last_name}@{domain}")
    return username1, username2, username3


def save_to_csv(employees, file_name):
    with open(file_name, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Name", "Role", "USER1", "USER2", "USER3" ])
        for name, role , us1, us2, us3 in employees:
            writer.writerow([name, role, us1, us2, us3])


def save_to_csv_usernames(usernames, file_name):
    with open(file_name, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Username"])  # Header for the CSV
        for username in usernames:
            writer.writerow([username])  # Write each username as a single row


def get_company_name(domain):
    api_key = "your_serpapi_key"
    params = {
        "q": f"site:linkedin.com/company OR site:linkedin.com {domain}",
        "api_key": "6b54a08faf9e672c1fe89b3f47d1dadcc2491849931d2e4f66eb9346e45dd080",
        "engine": "google"
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        data = response.json()

        for result in data.get("organic_results", []):
            url = result.get("link", "")
            match = re.search(r'https://www\.linkedin\.com/company/([^/]+)/?', url)
            if match:
                return match.group(1)
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
    except re.error as e:
        logging.error(f"Regex error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    return None



def execute_linkedin(domain):
    
    employees = []  # Initialize employees as an empty list
    linkedin_username = "pikshaked@gmail.com"
    linkedin_password = "SP210601!"

    # linkedin_username = "benmhila@post.bgu.ac.il"
    # linkedin_password = "L)qvR$s~=8$J7FD"

    company_name = get_company_name(domain)
    if company_name:
        company_url = f"https://www.linkedin.com/company/{company_name.lower()}/"
        print("company url: " + company_url + " company name: " + company_name)
    else:
        print("Company name not found.")
        return

    if not linkedin_username or not linkedin_password:
        logging.error("LinkedIn credentials are not set.")
        exit(1)
    
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    # Do NOT add "--headless" if you want to see the window 
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()

    try:
        login_to_linkedin(driver, linkedin_username, linkedin_password)
        navigate_to_company_page(driver, company_name)
        navigate_to_people_tab(driver, company_name)
        employees = scrape_employees_with_roles(driver, domain)
        save_to_csv(employees, "employees.csv")
        logging.info(f"Found {len(employees)} employees.")

        #save_to_csv_usernames(usernames, "usernames.csv")
        logging.info("Usernames saved to usernames.csv")

    finally:
        driver.quit()
        print(employees)
        return employees


if __name__ == "__main__":
    #company_name = input("Enter the company name: ")

    domain_name = input("Enter the domain name: ")
    execute_linkedin(domain_name)



