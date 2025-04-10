import csv
import re

import requests
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def login_to_linkedin(driver, username, password):
    try:
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        # Enter username
        driver.find_element(By.ID, "username").send_keys(username)
        # Enter password
        driver.find_element(By.ID, "password").send_keys(password)
        # Click login
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(10)
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


from selenium.webdriver.common.action_chains import ActionChains


def navigate_to_people_tab(driver, company_name):
    try:
        # Wait for the People tab to load
        people_tab = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//a[contains(@href, '/company/{company_name.lower()}/people/')]"))
        )
        time.sleep(2)  # Allow time to visually see the element

        # Create an ActionChains object to simulate the mouse actions
        actions = ActionChains(driver)

        # Move the mouse to the People tab
        actions.move_to_element(people_tab).perform()
        logging.info("Mouse moved to the People tab.")
        time.sleep(2)  # Wait to see the mouse move

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
        time.sleep(3)  # Delay to mimic human behavior
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def scrape_employees(driver):
    employees = []
    scroll_down(driver)

    try:
        # Wait until the employee data becomes available (adjust the XPath accordingly)
        employee_elements = WebDriverWait(driver, 60).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@class, 'link-without-visited-state')]/div"))
        )

        # Loop through the elements and extract employee names
        for element in employee_elements:
            name = element.text.strip()
            if name:
                # Use regex to match only names with English letters and spaces
                if re.match("^[a-zA-Z\\s]*$", name):
                    employees.append(name)
                    logging.info(f"Found employee: {name}")
    except Exception as e:
        logging.error(f"Error scraping employees: {e}")

    return employees


def generate_usernames(employees):
    usernames = []
    for name in employees:
        parts = name.lower().split()
        if len(parts) < 2:
            continue
        first_name, last_name = parts[0], parts[-1]
        usernames.append(f"{first_name}.{last_name}")
        usernames.append(f"{first_name}{last_name}")
        usernames.append(f"{first_name[0]}{last_name}")
    return usernames


def save_to_csv(usernames, file_name):
    try:
        with open(file_name, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Username"])
            for username in usernames:
                writer.writerow([username])
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")
        raise


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
    linkedin_username = "bulipik34@gmail.com"
    linkedin_password = "D5gVmR-6@@gM_rp"

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

    driver = webdriver.Chrome()
    driver.maximize_window()

    try:
        login_to_linkedin(driver, linkedin_username, linkedin_password)
        navigate_to_company_page(driver, company_name)
        navigate_to_people_tab(driver, company_name)
        employees = scrape_employees(driver)
        logging.info(f"Found {len(employees)} employees.")

        usernames = generate_usernames(employees)
        save_to_csv(usernames, "usernames.csv")
        logging.info("Usernames saved to usernames.csv")

    finally:
        driver.quit()

if __name__ == "__main__":
    #company_name = input("Enter the company name: ")

    domain_name = input("Enter the domain name: ")
    execute_linkedin(domain_name)



