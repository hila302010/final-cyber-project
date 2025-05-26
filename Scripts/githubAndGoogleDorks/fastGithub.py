import asyncio
import aiohttp
import re
import time
import os
from typing import Set, List
import json
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

@dataclass
class SearchResult:
    emails: Set[str]
    source: str
    count: int

class AsyncGitHubEmailExtractor:
    def __init__(self, max_concurrent=10):
        # Get tokens from environment variable or use your tokens
        self.tokens = os.getenv('GITHUB_TOKENS', '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').split(',')
        self.current_token_index = 0
        self.base_url = "https://api.github.com"
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session = None
        
    def get_current_token(self):
        """Get current token and rotate"""
        token = self.tokens[self.current_token_index]
        self.current_token_index = (self.current_token_index + 1) % len(self.tokens)
        return token
    
    def get_headers(self):
        """Get headers with current token"""
        return {
            "Authorization": f"token {self.get_current_token()}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AsyncEmailExtractor/1.0"
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=self.max_concurrent)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def check_rate_limit(self):
        """Check and handle rate limits"""
        try:
            async with self.semaphore:
                async with self.session.get(
                    f"{self.base_url}/rate_limit",
                    headers=self.get_headers()
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        remaining = data['resources']['search']['remaining']
                        reset_time = data['resources']['search']['reset']
                        
                        if remaining < 5:
                            sleep_time = reset_time - int(time.time()) + 10
                            if sleep_time > 0:
                                print(f"Rate limit low. Sleeping for {sleep_time} seconds...")
                                await asyncio.sleep(sleep_time)
                        
                        return remaining
        except Exception as e:
            print(f"Rate limit check failed: {e}")
            await asyncio.sleep(10)
        return 0
    
    async def search_code_single_query(self, query: str, domain: str, page: int = 1) -> SearchResult:
        """Search GitHub code for a single query"""
        emails = set()
        
        try:
            async with self.semaphore:
                await self.check_rate_limit()
                
                url = f"{self.base_url}/search/code"
                params = {
                    "q": query,
                    "per_page": 30,
                    "page": page
                }
                
                async with self.session.get(
                    url, 
                    headers=self.get_headers(), 
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', [])
                        
                        # Process files concurrently
                        file_tasks = [
                            self.extract_emails_from_file(item, domain) 
                            for item in items
                        ]
                        
                        if file_tasks:
                            file_results = await asyncio.gather(*file_tasks, return_exceptions=True)
                            for result in file_results:
                                if isinstance(result, set):
                                    emails.update(result)
                                    
                    elif response.status == 403:
                        print(f"Rate limit exceeded for query: {query}")
                        await asyncio.sleep(60)
                    else:
                        print(f"Search failed for '{query}' with status {response.status}")
                
                # Small delay to be nice to the API
                await asyncio.sleep(0.5)
                
        except Exception as e:
            print(f"Error searching with query '{query}': {e}")
        
        return SearchResult(emails=emails, source=f"code_query_{query}", count=len(emails))
    
    async def extract_emails_from_file(self, item: dict, domain: str) -> Set[str]:
        """Extract emails from a specific file asynchronously"""
        emails = set()
        
        try:
            repo_name = item['repository']['full_name']
            file_path = item['path']
            
            # Try different branches
            branches = ['main', 'master', 'develop', 'dev']
            
            for branch in branches:
                try:
                    raw_url = f"https://raw.githubusercontent.com/{repo_name}/{branch}/{file_path}"
                    
                    async with self.session.get(raw_url) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Extract emails using regex
                            email_pattern = rf'\b[A-Za-z0-9._%+-]+@{re.escape(domain)}\b'
                            found_emails = re.findall(email_pattern, content, re.IGNORECASE)
                            
                            # Clean and validate emails
                            for email in found_emails:
                                email = email.lower().strip()
                                if self.is_valid_email(email):
                                    emails.add(email)
                            
                            break  # If successful, don't try other branches
                            
                except Exception:
                    continue  # Try next branch
                    
        except Exception as e:
            print(f"Error extracting from file: {e}")
            
        return emails
    
    async def search_commits_for_emails(self, domain: str) -> SearchResult:
        """Search commit history for emails asynchronously"""
        emails = set()
        
        try:
            await self.check_rate_limit()
            
            # First, search for repositories
            url = f"{self.base_url}/search/repositories"
            params = {
                "q": f"{domain}",
                "per_page": 20,
                "sort": "updated"
            }
            
            async with self.session.get(
                url, 
                headers=self.get_headers(), 
                params=params
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    repos = data.get('items', [])
                    
                    # Process repositories concurrently
                    repo_tasks = [
                        self.get_emails_from_repo_commits(repo['full_name'], domain)
                        for repo in repos[:10]  # Limit to top 10 repos
                    ]
                    
                    if repo_tasks:
                        repo_results = await asyncio.gather(*repo_tasks, return_exceptions=True)
                        for result in repo_results:
                            if isinstance(result, set):
                                emails.update(result)
                                
        except Exception as e:
            print(f"Error searching commits: {e}")
            
        return SearchResult(emails=emails, source="commits", count=len(emails))
    
    async def get_emails_from_repo_commits(self, repo_name: str, domain: str) -> Set[str]:
        """Get emails from a specific repository's commits"""
        emails = set()
        
        try:
            async with self.semaphore:
                await self.check_rate_limit()
                
                url = f"{self.base_url}/repos/{repo_name}/commits"
                params = {"per_page": 50}
                
                async with self.session.get(
                    url, 
                    headers=self.get_headers(), 
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        commits = await response.json()
                        
                        for commit in commits:
                            # Check author email
                            author_email = commit.get('commit', {}).get('author', {}).get('email', '')
                            if author_email and domain.lower() in author_email.lower():
                                if self.is_valid_email(author_email):
                                    emails.add(author_email.lower())
                            
                            # Check committer email
                            committer_email = commit.get('commit', {}).get('committer', {}).get('email', '')
                            if committer_email and domain.lower() in committer_email.lower():
                                if self.is_valid_email(committer_email):
                                    emails.add(committer_email.lower())
                                    
        except Exception as e:
            print(f"Error getting commits from {repo_name}: {e}")
            
        return emails
    
    def is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        if not email or len(email) < 5:
            return False
        
        # Skip obviously fake emails
        fake_patterns = [
            'noreply', 'no-reply', 'example.com', 'test.com', 
            'localhost', 'dummy', 'fake', 'temp', 'github.com'
        ]
        
        email_lower = email.lower()
        for pattern in fake_patterns:
            if pattern in email_lower:
                return False
        
        # Basic regex check
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    async def extract_emails(self, domain: str, max_pages: int = 3) -> List[str]:
        """Main async function to extract all emails for a domain"""
        print(f"Async searching for emails with domain: {domain}")
        all_emails = set()
        
        # Define search queries
        queries = [
            f'"{domain}" language:python',
            f'"{domain}" filename:.env',
            f'"{domain}" filename:config',
            f'"{domain}" extension:yml',
            f'"{domain}" extension:json',
            f'@{domain}',
            f'"{domain}" extension:py',
            f'"{domain}" extension:js',
        ]
        
        # Create all search tasks
        search_tasks = []
        
        # Add code search tasks for multiple pages
        for query in queries:
            for page in range(1, max_pages + 1):
                search_tasks.append(
                    self.search_code_single_query(query, domain, page)
                )
        
        # Add commit search task
        search_tasks.append(self.search_commits_for_emails(domain))
        
        print(f"Starting {len(search_tasks)} concurrent search tasks...")
        
        # Execute all tasks concurrently
        start_time = time.time()
        results = await asyncio.gather(*search_tasks, return_exceptions=True)
        end_time = time.time()
        
        # Process results
        total_found = 0
        for result in results:
            if isinstance(result, SearchResult):
                all_emails.update(result.emails)
                total_found += result.count
                if result.count > 0:
                    print(f"✓ {result.source}: found {result.count} emails")
            elif isinstance(result, Exception):
                print(f"✗ Task failed: {result}")
        
        final_emails = sorted(list(all_emails))
        print(f"\nCompleted in {end_time - start_time:.2f} seconds")
        print(f"Total unique emails found: {len(final_emails)}")
        
        return final_emails


# Synchronous wrapper for easy use
class FastGitHubEmailExtractor:
    def __init__(self, max_concurrent=10):
        self.max_concurrent = max_concurrent
    
    def extract_emails(self, domain: str, max_pages: int = 3) -> List[str]:
        """Synchronous wrapper for async email extraction"""
        return asyncio.run(self._async_extract_emails(domain, max_pages))
    
    async def _async_extract_emails(self, domain: str, max_pages: int = 3) -> List[str]:
        """Internal async method"""
        async with AsyncGitHubEmailExtractor(self.max_concurrent) as extractor:
            return await extractor.extract_emails(domain, max_pages)


def main():
    """Main function to run the async email extractor"""
    print("🚀 Fast Async GitHub Email Extractor")
    print("=" * 50)
    
    # Get domain from user
    domain = input("Enter domain to search for (e.g., 'bgu.ac.il'): ").strip()
    
    if not domain:
        print("Please enter a valid domain")
        return
    
    # Create extractor with higher concurrency for speed
    extractor = FastGitHubEmailExtractor(max_concurrent=15)
    
    # Extract emails
    start_time = time.time()
    emails = extractor.extract_emails(domain, max_pages=2)
    total_time = time.time() - start_time
    
    # Display results
    if emails:
        print(f"\n🎯 Found {len(emails)} unique emails in {total_time:.2f} seconds:")
        print("-" * 60)
        for email in emails:
            print(f"📧 {email}")
        
        # Save to file
        filename = f"{domain.replace('.', '_')}_github_emails_fast.txt"
        with open(filename, 'w') as f:
            for email in emails:
                f.write(f"{email}\n")
        print(f"\n💾 Results saved to: {filename}")
        print(f"⚡ Speed: {len(emails)/total_time:.2f} emails/second")
    else:
        print("❌ No emails found for this domain")
    
    return emails


if __name__ == "__main__":
    main()