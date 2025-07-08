import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# GitHub config
GITHUB_TOKEN = "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"
GITHUB_API_URL = "https://api.github.com"
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}

# Constants
KEYWORDS = {"SECRET", "ADMIN", "PASSWORD", "APIKEY", "TOKEN", "SESSION", "USERID", "PHONENUMBER", "TOP_SECRET"}
MAX_THREADS = 10


def get_rate_limit():
    """Check the GitHub API rate limit."""
    url = f"{GITHUB_API_URL}/rate_limit"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        data = response.json()
        remaining = data['resources']['core']['remaining']
        reset_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['resources']['core']['reset']))
        return remaining, reset_time
    except requests.RequestException as e:
        print(f"Error checking rate limit: {e}")
        return 0, "unknown"


def fetch_code_content(url):
    """Fetch raw file content from GitHub."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error ({e.response.status_code}) for {url}")
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
    return None


def extract_emails(code_text, domain):
    """Extract emails from code text that match the domain."""
    pattern = rf"[\w\.-]+@{re.escape(domain)}"
    return set(re.findall(pattern, code_text))


def file_contains_keywords(code_text):
    """Check if any of the sensitive keywords appear in the code."""
    return any(keyword in code_text.upper() for keyword in KEYWORDS)


def process_file(item, domain, email_urls, checked_urls):
    """Process a single file result from the GitHub search."""
    repo = item["repository"]["full_name"]
    path = item["path"]
    raw_url = f"https://raw.githubusercontent.com/{repo}/main/{path}"
    code_url = f"https://github.com/{repo}/blob/main/{path}"

    if raw_url in checked_urls:
        return

    checked_urls.add(raw_url)
    code_text = fetch_code_content(raw_url)

    if code_text and file_contains_keywords(code_text):
        for email in extract_emails(code_text, domain):
            email_urls.setdefault(email, set()).add(code_url)


def search_github_by_domain(domain):
    """Search GitHub for hardcoded emails and keywords."""
    email_urls = {}
    checked_urls = set()
    page = 1

    while True:
        remaining, reset_time = get_rate_limit()
        if remaining == 0:
            print(f"Rate limit exceeded. Try again after {reset_time}.")
            break

        try:
            response = requests.get(
                f"{GITHUB_API_URL}/search/code",
                headers=HEADERS,
                params={"q": f'"@{domain}"', "per_page": 50, "page": page},
                timeout=10
            )
            response.raise_for_status()
            results = response.json()

            if not results.get("items"):
                break

            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = [
                    executor.submit(process_file, item, domain, email_urls, checked_urls)
                    for item in results["items"]
                ]
                for future in as_completed(futures):
                    future.result()

            print(f"Page {page}: {len(checked_urls)} files checked, {len(email_urls)} emails found.")
            page += 1
            time.sleep(2)

        except requests.RequestException as e:
            print(f"GitHub API error: {e}")
            break

    return email_urls

# CHECK WHY THIS DOESNT WORK!!!!
def search_github_company_mentions(company_name):
    """Search GitHub for hardcoded urls of code with the company name and keywords."""
    email_urls = {}
    checked_urls = set()
    page = 1

    while True:
        remaining, reset_time = get_rate_limit()
        if remaining == 0:
            print(f"Rate limit exceeded. Try again after {reset_time}.")
            break

        try:
            response = requests.get(
                f"{GITHUB_API_URL}/search/code",
                headers=HEADERS,
                params={"q": f'"{company_name}"', "per_page": 50, "page": page},
                timeout=10
            )
            response.raise_for_status()
            results = response.json()

            if not results.get("items"):
                break

            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = [
                    executor.submit(process_file, item, company_name, email_urls, checked_urls)
                    for item in results["items"]
                ]
                for future in as_completed(futures):
                    future.result()

            print(f"Page {page}: {len(checked_urls)} files checked, {len(email_urls)} emails found.")
            page += 1
            time.sleep(2)

        except requests.RequestException as e:
            print(f"GitHub API error: {e}")
            break

    return email_urls

def write_to_file(results, output_file):
    """Write the results to a CSV file."""
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            for key, urls in results.items():
                file.writelines(f"{key} - {url}\n" for url in urls)
        print(f"Results saved to {output_file}")
    except IOError as e:
        print(f"Error writing to file: {e}")



def main():
    print("Choose an option:")
    print("1) Search for emails by domain")
    print("2) Search for company name mentions")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        domain = input("Enter the domain name: ").strip()
        results = search_github_by_domain(domain)
        if results:
            write_to_file(results, "domain_code_results.txt")
            print(f"Found {len(results)} unique urls.")
        else:
            print("No relevant emails found.")
    elif choice == "2":
        company_names = input("Enter the company names or nicknames (comma-separated): ").strip().split(',')
        results = search_github_company_mentions([name.strip() for name in company_names])
        if results:
            write_to_file(results,"company_mentions_results.txt")
            print(f"Found {len(results)} unique urls.")
        else:
            print("No relevant emails found.")
    else:
        print("Invalid option selected.")




if __name__ == "__main__":
    main()
