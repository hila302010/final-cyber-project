import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Your GitHub token
GITHUB_TOKEN = "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"
#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
GITHUB_API_URL = "https://api.github.com"
KEYWORDS = {"SECRET", "ADMIN", "PASSWORD", "APIKEY", "TOKEN", "SESSION", "USERID", "PHONENUMBER"}
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
MAX_THREADS = 10  # Number of concurrent threads


def get_rate_limit():
    """Check the GitHub API rate limit."""
    try:
        url = f"{GITHUB_API_URL}/rate_limit"
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            remaining = data['resources']['core']['remaining']
            reset_time = data['resources']['core']['reset']
            reset_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(reset_time))
            return remaining, reset_time
        else:
            print(f"Error fetching rate limit: {response.status_code}")
            return None, None
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None, None


def fetch_code_content(url):
    """Fetch raw file content from GitHub."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for any 4xx or 5xx status code
        return response.text
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"File not found: {url}")
        else:
            print(f"HTTP error fetching {url}: {e}")
        return None
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def process_file(item, domain, email_urls, checked_urls):
    """Extract emails if the file contains relevant keywords."""
    repo, path = item["repository"]["full_name"], item["path"]
    code_url = f"https://github.com/{repo}/blob/main/{path}"
    raw_url = f"https://raw.githubusercontent.com/{repo}/main/{path}"

    if raw_url in checked_urls:  # Skip if already checked
        return

    checked_urls.add(raw_url)  # Mark as checked
    code_text = fetch_code_content(raw_url)

    if code_text and any(keyword in code_text.upper() for keyword in KEYWORDS):  # Case-insensitive match
        found_emails = set(re.findall(rf"[\w\.-]+{re.escape(domain)}", code_text))
        for email in found_emails:
            email_urls.setdefault(email, set()).add(code_url)


def search_github_emails(domain):
    """Find emails in GitHub code and save URLs only if they contain sensitive keywords."""
    email_urls = {}
    checked_urls = set()  # Track already checked URLs
    page = 1

    while True:
        # Check rate limit before making requests
        remaining, reset_time = get_rate_limit()
        if remaining is None:
            print("Skipping GitHub search due to connection issues.")
            return {}
        if remaining == 0:
            print(f"Rate limit exceeded. Try again after {reset_time}.")
            time.sleep(remaining)  # Sleep until rate limit resets

        try:
            response = requests.get(f"{GITHUB_API_URL}/search/code", headers=HEADERS,
                                    params={"q": f'"{domain}"', "per_page": 50, "page": page}, timeout=10)
            response.raise_for_status()
            results = response.json()

            if "items" not in results or not results["items"]:
                break  # Stop if no more results

            # Process files in parallel
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = {executor.submit(process_file, item, domain, email_urls, checked_urls): item for item in
                           results["items"]}
                for future in as_completed(futures):
                    future.result()  # Ensure all tasks complete

            print(f"Page {page}: Checked {len(checked_urls)} unique files, found {len(email_urls)} relevant emails...")
            page += 1  # Move to the next page
            time.sleep(2)  # Reduce API rate limiting

        except requests.RequestException as e:
            print(f"GitHub API request failed: {e}")
            break

    return email_urls

def write_to_file(output_file, results):
    """Write the results to a CSV file."""
    try:
        with open(output_file, "a", encoding="utf-8") as file:
            for key, urls in results.items():
                file.writelines(f"{key} - {url}\n" for url in urls)
        print(f"Results saved to {output_file}")
    except IOError as e:
        print(f"Error writing to file: {e}")

def getEmails():
    emails = set()
    with open("@bgu.ac.il_github_results.txt", "r", encoding="utf-8") as file:
        print("github mails: \n")
        for line in file:
            if line.strip():  # Ignore empty lines
                # Split the line by " - " and take the first part (email address)
                email = line.split(" - ")[0].strip()
                print(email,"\n")
                emails.add(email)
    return list(emails)

if __name__ == "__main__":
    domain_name = input("Enter the domain name: ").strip()
    found_emails = search_github_emails(domain_name, "email_code_results_threads.txt")
    print(f"Found {len(found_emails)} relevant emails.") if found_emails else print("No emails found.")