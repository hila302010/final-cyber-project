import subprocess
import json
import tempfile
import re


def run_pagodo(dork, num_results=10):
    """Run pagodo with the specified dork and return the results."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_dork_file:
            temp_dork_file.write(dork)
            temp_dork_file_path = temp_dork_file.name

        result = subprocess.run(
            ['python', 'pagodo.py', '-g', temp_dork_file_path, '-m', str(num_results)],
            capture_output=True,
            text=True,
            cwd='./pagodo'  # Updated to use relative path
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Error running pagodo: {result.stderr}")
            return []
    except Exception as e:
        print(f"Exception running pagodo: {e}")
        return []

def google_dork_admin(domain, num_results=10):
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
        search_results = run_pagodo(dork, num_results)
        for result in search_results:
            admin_links.append((result['link'], dork))

    return admin_links

def google_dork_files(domain, num_results=10):
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
        search_results = run_pagodo(dork, num_results)
        for result in search_results:
            file_links.append((result['link'], dork))

    return file_links

def google_dork_passwords(domain, num_results=10):
    dorks = [
        f"site:{domain} intext:\"SELECT\" intext:\"password\"",
        f"site:{domain} filetype:env intext:\"DB_PASSWORD\""
    ]
    passwords_data = []

    for dork in dorks:
        print(f"Searching: {dork}")
        search_results = run_pagodo(dork, num_results)
        for result in search_results:
            passwords_data.append((result['link'], dork))

    return passwords_data

def google_dork_emails(domain, num_results=10):
    dorks = [
        f"intext:@{domain}",
        f"inurl:@{domain}",
        f"site:{domain} intext:@{domain}"
    ]

    email_data = []

    for dork in dorks:
        print(f"Searching: {dork}")
        search_results = run_pagodo(dork, num_results)
        for result in search_results:
            email_data.append((result['link'], dork))

    return email_data

def save_to_txt(email_data, password_data, files_data,admin_data, domain):
    filename = f"{domain}_data.txt"
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
    

def getEmails():
    emails = set()  # Use a set to avoid duplicates
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    print("google emails: \n")
    with open("@bgu.ac.il_google_results.txt", "r", encoding="utf-8") as file:
         for line in file:
            matches = re.findall(email_pattern, line)
            print(matches)
            emails.update(matches)
    return list(emails)




def main(domain):
    email_data = google_dork_emails(domain)
    password_data = google_dork_passwords(domain)
    files_data = google_dork_files(domain)
    admin_data = google_dork_admin(domain)

    if files_data or email_data or password_data or admin_data:
        save_to_txt(email_data, password_data,files_data,admin_data,domain)

if __name__ == "__main__":
    domain = input("Enter domain: ").strip()
    main(domain)