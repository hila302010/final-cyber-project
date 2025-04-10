import re
import time
from collections import deque
from contextlib import nullcontext
from googlesearch import search
import requests

API_KEY = "YOUR_GOOGLE_API_KEY"
CX = "YOUR_CUSTOM_SEARCH_ENGINE_ID"

# queue of user agents
user_agents = deque([
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) Gecko/20100101 Firefox/117.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:114.0) Gecko/20100101 Firefox/114.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:113.0) Gecko/20100101 Firefox/113.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:111.0) Gecko/20100101 Firefox/111.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'
])

def google_dork_admin(domain, num_results=10):
    """Search Google for admin panels & login pages."""
    dorks = [
        f"site:{domain} inurl:admin",
        f"site:{domain} inurl:login",
        f"site:{domain} inurl:dashboard",
        f"site:{domain} inurl:controlpanel",
        f"site:{domain} intitle:'Admin Panel'",
        f"site:{domain} inurl:wp-admin",
        f"site:{domain} inurl:cpanel"
    ]

    admin_links = []

    for dork in dorks:
        print(f"Searching: {dork}")
        try:
            search_results = search(dork, num_results=num_results)  # Google Search (Might Be Blocked)
            for url in search_results:
                user_agent = user_agents[0]  # Peek at the first user agent
                try:
                    response = requests.get(url, timeout=5, headers={'User-Agent': user_agent})
                    if response.status_code == 200:
                        admin_links.append((url, dork))
                finally:
                    user_agents.rotate(-1) # Move the used user agent to the end of the deque
                    time.sleep(2)  # Sleep to avoid hitting the server too fast
        except Exception as e:
            time.sleep(2)  # Sleep to avoid hitting the server too fast
            print(f"Error with search: {e}")

    return admin_links


def google_dork_files(domain, num_results=10):
    """Search Google for publicly indexed files."""
    dorks = [
        f"site:{domain} filetype:pdf",
        f"site:{domain} filetype:docx",
        f"site:{domain} filetype:xlsx",
        f"site:{domain} filetype:pptx",
        f"site:{domain} filetype:txt",
        f"site:{domain} filetype:csv"
    ]

    file_links = []

    for dork in dorks:
        print(f"Searching: {dork}")
        try:
            search_results = search(dork, num_results=num_results)  # Google Search (Might Get Blocked)
            for file_url in search_results:
                user_agent = user_agents[0]  # Peek at the first user agent
                try:
                    response = requests.get(file_url, timeout=5, headers={'User-Agent': user_agent})
                    if response.status_code == 200:
                        file_links.append((file_url, dork))
                finally:
                    user_agents.rotate(-1) # Move the used user agent to the end of the deque
                    time.sleep(2) # Sleep to avoid hitting the server too fast
        except Exception as e:
            time.sleep(2)  # Sleep to avoid hitting the server too fast
            print(f"Error with search: {e}")

    return file_links

def google_dork_passwords(domain, num_results=10):
    dorks = [
        f"site:{domain} intext:\"SELECT\" intext:\"password\"",
        f"site:{domain} filetype:env intext:\"DB_PASSWORD\""
    ]
    passwords_data = []
    for dork in dorks:
        print(f"Searching: {dork}")
        try:
            search_results = search(dork, num_results=num_results)
            for url in search_results:
                user_agent = user_agents[0]
                try:
                    response = requests.get(url, timeout=5, headers={'User-Agent': user_agent})
                    if response.status_code == 200:
                        # Regular expressions to match potential password patterns
                        found_passwords = set(re.findall(r'(?i)(password\s*[:=]?\s*[\w!@#$%^&*()_+={}\[\]:";\'<>,./?\\|-]+)', response.text))

                        # Extracting domain-related sensitive information (e.g., password)
                        found_credentials = set(re.findall(r'(?i)(DB_PASSWORD\s*[:=]?\s*[\w!@#$%^&*()_+={}\[\]:";\'<>,./?\\|-]+)', response.text))

                        # Combine found passwords and credentials
                        found_passwords.update(found_credentials)

                        # Store the result (password, url, dork used)
                        for password in found_passwords:
                            passwords_data.append((password, url, dork))
                except requests.RequestException:
                    time.sleep(2)  # Sleep to avoid hitting the server too fast
                    continue
                finally:
                    user_agents.rotate(-1) # Move the used user agent to the end of the deque
                    time.sleep(2)  # Sleep to avoid hitting the server too fast
        except Exception as e:
            time.sleep(2)  # Sleep to avoid hitting the server too fast
            print(f"Error with search: {e}")
    return passwords_data



def google_dork_emails(domain, num_results=10):
    dorks = [
        f"intext:{domain}",
        f"inurl:{domain}",
        f"site:{domain} intext:{domain}"
    ]

    email_data = []

    for dork in dorks:
        print(f"Searching: {dork}")
        try:
            search_results = search(dork, num_results=num_results)

            for url in search_results:
                user_agent = user_agents[0]  # Peek at the first user agent
                try:
                    # Get the user agent from the front of the deque
                    response = requests.get(url, timeout=5, headers={'User-Agent': user_agent})

                    if response.status_code == 200:
                        found_emails = set(re.findall(r'[\w\.-]+' + domain, response.text))
                        for email in found_emails:
                            email_data.append((email, url, dork))
                except requests.RequestException:
                    continue
                finally:
                    # Move the used user agent to the end of the deque
                    user_agents.rotate(-1) # Move the used user agent to the end of the deque
                    time.sleep(2)  # Sleep to avoid hitting the server too fast
        except Exception as e:
            time.sleep(2)  # Sleep to avoid hitting the server too fast
            print(f"Error with search: {e}")

    return email_data



def save_to_txt(email_data, password_data, files_data,admin_data, domain, filename):
    with open(filename, mode='w', encoding='utf-8') as file:
        #EMAILS:
        file.write("Email Address\tSource URL\tEmail Dork\n")  # Header row
        for email, url, dork in email_data:
            file.write(f"{email}\t{url}\t{dork}\n")

        #PASSWORDS:
        file.write("Passwords\tSource URL\tPassword Dork\n")  # Header row
        for password, url, dork in password_data:
            file.write(f"{password}\t{url}\t{dork}\n")

        #FILES
        file.write("Files\tSource URL\tFiles Dork\n")  # Header row
        for url, dork in files_data:
            file.write(f"File URL: {url}\n")
            file.write(f"Dork Used: {dork}\n")
            file.write("=" * 50 + "\n")  # Separator

        #ADMIN
        file.write("Admin\tSource URL\tAdmin Dork\n")  # Header row
        for url, dork in admin_data:
            file.write(f"Admin URL: {url}\n")
            file.write(f"Dork Used: {dork}\n")
            file.write("=" * 50 + "\n")  # Separator


    print(f"Data about {domain} saved to {filename}")

if __name__ == "__main__":
    domain = input("Enter domain: ").strip()
    email_data = google_dork_emails(domain)
    password_data = google_dork_passwords(domain)
    files_data = google_dork_files(domain)
    admin_data = google_dork_admin(domain)

    if files_data or email_data or password_data or admin_data:
        save_to_txt(email_data, password_data,files_data,admin_data,domain)