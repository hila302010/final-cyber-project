import requests
import re
import time


#CODE WITHOUT USER AGENT

GITHUB_TOKEN = "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"  # Replace with your actual token
GITHUB_API_URL = "https://api.github.com"

def get_default_branch(repo_full_name):
    """Fetches the default branch of a repository."""
    url = f"{GITHUB_API_URL}/repos/{repo_full_name}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("default_branch", "main")
    return "main"


def search_github_emails(domain):
    """Search for email addresses associated with the domain."""
    search_url = f"{GITHUB_API_URL}/search/code"
    query = f'"@{domain}"'
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    emails = set()
    page = 1
    while True:  # Loop through pages
        params = {"q": query, "per_page": 50, "page": page}  # Fetch up to 50 results per page
        response = requests.get(search_url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Error fetching emails (Page {page}): {response.status_code}")
            break

        results = response.json()
        if "items" not in results or not results["items"]:
            break  # No more results

        for item in results["items"]:
            file_url = f"https://raw.githubusercontent.com/{item['repository']['full_name']}/main/{item['path']}"
            file_response = requests.get(file_url)

            if file_response.status_code == 200:
                found_emails = re.findall(rf"[\w\.-]+@{re.escape(domain)}", file_response.text)
                emails.update(found_emails)

        print(f"Page {page}: Found {len(emails)} emails so far...")
        page += 1
        time.sleep(5)  # Prevent rate limiting

    return emails

# Search url code that contains the emails we found earlier
def search_codes_for_emails(emails, output_file):
    search_url = f"{GITHUB_API_URL}/search/code"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    with open(output_file, "w") as file:
        for email in emails:
            query = f'"{email}" in:file' #we search the email in the code
            page = 1
            while True:
                params = {"q": query, "per_page": 50, "page": page} # Fetch up to 50 results per page
                response = requests.get(search_url, headers=headers, params=params)

                if response.status_code != 200:
                    print(f"Error fetching code for {email} (Page {page}): {response.status_code}")
                    break

                results = response.json()
                if "items" not in results or not results["items"]:
                    break  # No more results

                for item in results["items"]: # Creating the url code related to the email found
                    repo_name = item["repository"]["full_name"]
                    file_path = item["path"]
                    branch = get_default_branch(repo_name)
                    code_url = f"https://github.com/{repo_name}/blob/{branch}/{file_path}"
                    file.write(f"{email} - {code_url}\n") # This is the output in the email_code_results.txt
                    print(f"Found: {email} in {code_url}")

                page += 1
                time.sleep(5)  # Prevent rate limiting
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    domain_name = input("Enter the domain name: ").strip()
    output_filename = "email_code_results.txt"
    # Step 1: Find emails related to the domain
    found_emails = search_github_emails(domain_name)
    if found_emails:
        print(f"Found {len(found_emails)} emails: {found_emails}")
        # Step 2: Search for those emails in the GitHub code
        search_codes_for_emails(found_emails, output_filename)
    else:
        print("No emails found.")
