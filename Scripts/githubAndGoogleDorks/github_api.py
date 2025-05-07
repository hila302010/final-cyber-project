import requests
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import pickle
import os
import threading
from collections import deque

# queue of user agents
user_agents = deque([
    # Firefox User Agents
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
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0',

    # Chrome User Agents
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',

    # Safari User Agents
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Safari/605.1.15',

    # Edge User Agents
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.0.0',

    # Mobile User Agents
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 9; Pixel 3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Mobile Safari/537.36'
])



# Your GitHub token
GITHUB_TOKENS = []

GITHUB_API_URL = "https://api.github.com"
KEYWORDS = {
    "SECRET", "ADMIN", "PASSWORD", "APIKEY", "TOKEN", "SESSION",
    "USERID", "PHONENUMBER", "EMAIL", "CONTACT", "CREDENTIALS"
}
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}
MAX_THREADS = 5  # Number of concurrent threads


# Rotate through GitHub tokens
def get_next_token():
    token = GITHUB_TOKENS[0]
    GITHUB_TOKENS.append(GITHUB_TOKENS.pop(0))  # Rotate tokens
    return token


# Rotate through user agents
def get_next_user_agent():
    user_agent = user_agents[0]  # Get the first user agent
    user_agents.rotate(-1)  # Rotate the deque to the left
    return user_agent

def get_rate_limit():
    """Check the GitHub API rate limit."""
    try:
        headers = HEADERS.copy()
        headers["Authorization"] = f"token {get_next_token()}"  # Rotate token
        headers["User-Agent"] = get_next_user_agent()  # Rotate user agent
        url = f"{GITHUB_API_URL}/rate_limit"
        response = requests.get(url, headers=headers)
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
        headers = HEADERS.copy()
        headers["Authorization"] = f"token {get_next_token()}"  # Rotate token
        headers["User-Agent"] = get_next_user_agent()  # Rotate user agent
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

"""
function to extract emails from commit history
and add them to the email_urls dictionary"""
def get_emails_from_commits(repo_full_name, domain, email_urls, lock):
    """Extract emails from the commit history of a GitHub repo."""
    page = 1
    while True:
        url = f"{GITHUB_API_URL}/repos/{repo_full_name}/commits"
        params = {"per_page": 100, "page": page}
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=10)
            if response.status_code != 200:
                break

            commits = response.json()
            if not commits:
                break

            for commit in commits:
                for key in ["author", "committer"]:
                    email = commit.get("commit", {}).get(key, {}).get("email", "")
                    if email and domain.lower() in email.lower():
                        with lock:
                            email_urls[email].add(f"https://github.com/{repo_full_name}/commit/{commit['sha']}")

            page += 1
            time.sleep(1)

        except requests.RequestException as e:
            print(f"Failed to fetch commits from {repo_full_name}: {e}")
            break

def process_file(item, domain, email_urls, checked_urls, lock, seen_repos):
    """Extract emails if the file contains relevant keywords."""
    repo, path = item["repository"]["full_name"], item["path"]
    code_url = f"https://github.com/{repo}/blob/main/{path}"
    raw_url = f"https://raw.githubusercontent.com/{repo}/main/{path}"

    #with lock:
    if raw_url in checked_urls:
        return
    checked_urls.add(raw_url)

    code_text = fetch_code_content(raw_url)

    
    """ # Search commit history only once per repo
    with lock:
        if repo not in seen_repos:
            seen_repos.add(repo)
            get_emails_from_commits(repo, domain, email_urls, lock)"""

    if code_text and any(keyword in code_text.upper() for keyword in KEYWORDS):
        found_emails = set(re.findall(rf"[a-zA-Z0-9_.+-]+@{re.escape(domain)}", code_text, re.IGNORECASE))
        with lock:
            for email in found_emails:
                email_urls.setdefault(email, set()).add(code_url)



def search_github_emails(domain):
    """Find emails in GitHub code and save URLs only if they contain sensitive keywords."""
    email_urls = defaultdict(set)  # Store email URLs
    checked_urls = set()  # Track already checked URLs
    seen_repos = set()  # Track already seen repositories
    page = 1
    lock = threading.Lock()


    while True:
        # Check rate limit before making requests
        remaining, reset_time = get_rate_limit()
        if remaining is None:
            print("Skipping GitHub search due to connection issues.")
            return {}
        if remaining == 0:
            print(f"Rate limit exceeded. Try again after {reset_time}.")
            sleep_time = int(reset_time) - int(time.time())
            print(f"Rate limit exceeded. Sleeping for {sleep_time} seconds.")
            time.sleep(max(sleep_time, 1))

        try:
            headers = HEADERS.copy()
            headers["Authorization"] = f"token {get_next_token()}"  # Rotate token
            headers["User-Agent"] = get_next_user_agent()  # Rotate user agent
            response = requests.get(
                f"{GITHUB_API_URL}/search/code",
                headers=headers,
                params={"q": f'"{domain}"', "per_page": 50, "page": page},
                timeout=10
            )                      
            #params={"q": f'"{domain}" in:file language:python language:javascript language:env', "per_page": 50, "page": page}, timeout=10)
            
            response.raise_for_status()
            results = response.json()

            if "items" not in results or not results["items"]:
                break  # Stop if no more results

            # Process files in parallel
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = {
                    executor.submit(process_file, item, domain, 
                                    email_urls, checked_urls, lock, seen_repos): item
                    for item in results["items"]
                }

                for future in as_completed(futures):  # Timeout after 60 seconds
                    try:
                        future.result()  # Ensure all tasks complete
                    except Exception as e:
                        print(f"Error processing file: {e}")

            print(f"Page {page}: Checked {len(checked_urls)} unique files, found {len(email_urls)} relevant emails...")
            page += 1  # Move to the next page
            time.sleep(2)  # Reduce API rate limiting

        except requests.RequestException as e:
            print(f"GitHub API request failed: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    # Return only the unique emails
    return set(email_urls.keys())

def write_to_file(output_file, emails):
    """Write unique emails to a file."""
    try:
        # Write the unique emails to the file
        with open(output_file, "w", encoding="utf-8") as file:  # Use "w" to overwrite
            for email in emails:
                file.write(f"{email}\n")

        print(f"Unique emails saved to {output_file}")
    except IOError as e:
        print(f"Error writing to file: {e}")


# function for testing
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


# function to save the results to a pickle file
def save_results(domain, results):
    with open(f"cache_{domain}.pkl", "wb") as f:
        pickle.dump(results, f)

# function to load the results from a pickle file
def load_cached_results(domain):
    if os.path.exists(f"cache_{domain}.pkl"):
        with open(f"cache_{domain}.pkl", "rb") as f:
            return pickle.load(f)
    return None



if __name__ == "__main__":
    domain_name = input("Enter the domain name: ").strip()
    found_emails = search_github_emails(domain_name)
    if found_emails:
        print(f"Found {len(found_emails)} unique emails:")
        write_to_file(f"{domain_name}_emails.txt", found_emails)
    else:
        print("No emails found.")

# unitest
# pytest