import json

import github_api as github
import googleDorksNoPagodo as google

import subprocess

def connect_to_nordvpn(country_code=None):
    try:
        command = ['nordvpn', 'connect']
        if country_code:
            command.append(country_code)
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Connected to NordVPN successfully in {country_code if country_code else 'the best available server'}.")
        else:
            print(f"Error connecting to NordVPN: {result.stderr}")
    except Exception as e:
        print(f"Exception occurred: {e}")

def disconnect_from_nordvpn():
    try:
        result = subprocess.run(['nordvpn', 'disconnect'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Disconnected from NordVPN successfully.")
        else:
            print(f"Error disconnecting from NordVPN: {result.stderr}")
    except Exception as e:
        print(f"Exception occurred: {e}")

def run_all_queries(queries):
    for query in queries:
        print(f"\n🔍 Searching for: {query}")

        # Run GitHub search
        github_results = github.search_github_emails(query)
        if not github_results:
            print(f"Skipping GitHub results for '{query}' due to connection issues.")
        else:
            path = f"{query}_github_results.txt"
            github.write_to_file(path, github_results)

        # Run Google search
        email_data = google.google_dork_emails(query)
        password_data = google.google_dork_passwords(query)
        files_data = google.google_dork_files(query)
        admin_data = google.google_dork_admin(query)

        if files_data or email_data or password_data or admin_data:
            path = f"{query}_google_results.txt"
            google.save_to_txt(email_data, password_data, files_data, admin_data, query, path)

        print(f"✅ Results for '{query}' saved.")

def main():
    print("🕵️ Information Gathering Tool")
    try:

        # Example usage
        connect_to_nordvpn('de')
        # Run your Google search script here

        domain = input("Enter domain name (e.g., example.com): ").strip()
        company_name = input("Enter company name: ").strip()
        nickname = input("Enter company nickname: (optional) ").strip()

        if not domain or not company_name:
            raise ValueError("All inputs must be provided and non-empty.")
        if nickname:
            run_all_queries(["@" + domain, company_name, nickname])
        else:
            run_all_queries(["@" + domain, company_name])
        disconnect_from_nordvpn()
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()