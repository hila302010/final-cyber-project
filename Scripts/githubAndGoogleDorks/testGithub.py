import requests
import re
import time
import os
from typing import Set, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

class GitHubEmailExtractor:
    def __init__(self, max_workers=10):
        #self.tokens = os.getenv('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', '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', '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').split(',')
        self.tokens = [
            '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',
            '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',
            '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'
        ]
        self.current_token_index = 0
        self.base_url = "https://api.github.com"
        self.session = requests.Session()
        self.max_workers = max_workers

    def get_current_token(self):
        token = self.tokens[self.current_token_index]
        self.current_token_index = (self.current_token_index + 1) % len(self.tokens)
        return token

    def get_headers(self):
        return {
            "Authorization": f"token {self.get_current_token()}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "EmailExtractor/1.0"
        }

    def check_rate_limit(self):
        try:
            response = self.session.get(f"{self.base_url}/rate_limit", headers=self.get_headers())
            if response.status_code == 200:
                data = response.json()
                remaining = data['resources']['search']['remaining']
                reset_time = data['resources']['search']['reset']
                if remaining < 5:
                    sleep_time = reset_time - int(time.time()) + 10
                    if sleep_time > 0:
                        print(f"Rate limit low. Sleeping for {sleep_time} seconds...")
                        time.sleep(sleep_time)
                return remaining
        except Exception as e:
            print(f"Rate limit check failed: {e}")
            time.sleep(60)
        return 0

    def search_code_for_emails(self, domain: str, page: int = 1) -> Set[str]:
        emails = set()
        queries = [
            f'"{domain}" language:python',
            f'"{domain}" filename:.env',
            f'"{domain}" filename:config',
            f'"{domain}" extension:yml',
            f'"{domain}" extension:json',
            f'@{domain}',
        ]

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for query in queries:
                self.check_rate_limit()
                url = f"{self.base_url}/search/code"
                params = {"q": query, "per_page": 30, "page": page}
                try:
                    response = self.session.get(url, headers=self.get_headers(), params=params, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get('items', [])
                        for item in items:
                            futures.append(executor.submit(self.extract_emails_from_file, item, domain))
                    elif response.status_code == 403:
                        print("Rate limit exceeded, sleeping 10 seconds...")
                        time.sleep(10)
                except Exception as e:
                    print(f"Query error [{query}]: {e}")

            for future in as_completed(futures):
                try:
                    result = future.result()
                    emails.update(result)
                except Exception as e:
                    print(f"Thread error: {e}")

        return emails

    def extract_emails_from_file(self, item: dict, domain: str) -> Set[str]:
        emails = set()
        repo_name = item['repository']['full_name']
        file_path = item['path']
        branches = ['main', 'master', 'develop', 'dev']
        for branch in branches:
            raw_url = f"https://raw.githubusercontent.com/{repo_name}/{branch}/{file_path}"
            try:
                response = self.session.get(raw_url, timeout=10)
                if response.status_code == 200:
                    content = response.text
                    pattern = rf'\b[A-Za-z0-9._%+-]+@{re.escape(domain)}\b'
                    for email in re.findall(pattern, content, re.IGNORECASE):
                        email = email.lower().strip()
                        if self.is_valid_email(email):
                            emails.add(email)
                    break  # Stop after first successful fetch
            except Exception as e:
                continue
        return emails

    def search_commits_for_emails(self, domain: str) -> Set[str]:
        emails = set()
        try:
            self.check_rate_limit()
            url = f"{self.base_url}/search/repositories"
            params = {"q": domain, "per_page": 20, "sort": "updated"}
            response = self.session.get(url, headers=self.get_headers(), params=params, timeout=15)
            if response.status_code == 200:
                repos = response.json().get('items', [])
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = [
                        executor.submit(self.get_emails_from_repo_commits, repo['full_name'], domain)
                        for repo in repos[:10]
                    ]
                    for future in as_completed(futures):
                        try:
                            emails.update(future.result())
                        except Exception as e:
                            print(f"Commit thread error: {e}")
        except Exception as e:
            print(f"Commit search error: {e}")
        return emails

    def get_emails_from_repo_commits(self, repo_name: str, domain: str) -> Set[str]:
        emails = set()
        try:
            self.check_rate_limit()
            url = f"{self.base_url}/repos/{repo_name}/commits"
            response = self.session.get(url, headers=self.get_headers(), params={"per_page": 50}, timeout=15)
            if response.status_code == 200:
                for commit in response.json():
                    for key in ['author', 'committer']:
                        email = commit.get('commit', {}).get(key, {}).get('email', '')
                        if email and domain.lower() in email.lower() and self.is_valid_email(email):
                            emails.add(email.lower())
        except Exception as e:
            print(f"Failed getting commits from {repo_name}: {e}")
        return emails

    def is_valid_email(self, email: str) -> bool:
        if not email or len(email) < 5:
            return False
        blacklist = ['noreply', 'no-reply', 'example.com', 'test.com', 'localhost', 'dummy', 'fake', 'temp']
        if any(term in email.lower() for term in blacklist):
            return False
        return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

    def extract_emails(self, domain: str, max_pages: int = 3) -> List[str]:
        print(f"Searching for emails with domain: {domain}")
        all_emails = set()

        for page in range(1, max_pages + 1):
            print(f"Searching code (page {page})...")
            code_emails = self.search_code_for_emails(domain, page)
            all_emails.update(code_emails)
            print(f"Found {len(code_emails)} emails on page {page}")
            if not code_emails:
                break

        print("Searching commits...")
        commit_emails = self.search_commits_for_emails(domain)
        all_emails.update(commit_emails)
        print(f"Found {len(commit_emails)} emails in commits")

        final_emails = sorted(all_emails)
        print(f"\nTotal unique emails found: {len(final_emails)}")
        return final_emails
    
def execute_github(domain):
    # Extract emails
    """Main function to run the email extractor"""
    extractor = GitHubEmailExtractor()
    emails = extractor.extract_emails(domain)
    
    # Display results
    if emails:
        print(f"\nFound {len(emails)} unique emails:")
        print("-" * 50)
        for email in emails:
            print(email)
    return emails

def main():
    extractor = GitHubEmailExtractor(max_workers=10)
    domain = input("Enter domain to search (e.g., 'bgu.ac.il'): ").strip()
    if not domain:
        print("Invalid domain.")
        return
    emails = extractor.extract_emails(domain)
    if emails:
        print("\nUnique emails found:")
        print("-" * 50)
        for email in emails:
            print(email)
        filename = f"{domain.replace('.', '_')}_github_emails.txt"
        with open(filename, 'w') as f:
            for email in emails:
                f.write(email + '\n')
        print(f"\nSaved to {filename}")
    else:
        print("No emails found.")

if __name__ == "__main__":
    main()


