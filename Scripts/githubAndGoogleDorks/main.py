import Scripts.githubAndGoogleDorks.github_api as github
import Scripts.githubAndGoogleDorks.googleDorksNoPagodo as google

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


#["@" + domain, company_name] == query
def getEmails(domain):
    emails = set()
    connect_to_nordvpn('de')

    # GitHub email search
    github_results = github.search_github_emails(domain)
    if isinstance(github_results, dict):
        emails.update(github_results.keys())  # Flattening the keys into the list
    else:
        emails.update(github_results)

    # Google email search
    email_data = google.google_dork_emails(domain)
    emails.update([email for email, _, _ in email_data])  # Just the emails

    disconnect_from_nordvpn()
    return list(emails)


def main():
    print("🕵️ Information Gathering Tool")
    try:

        domain = input("Enter domain name (e.g., example.com): ").strip()
        company = input("Enter company name: ").strip()

        queries = ["@" + domain, company]
        emails = getEmails(queries)

        print(emails)
        if  emails:
            path = f"{queries}_emails_results.txt"
            # should save to file            

        print(f"✅ Results for '{queries}' saved.")

    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()