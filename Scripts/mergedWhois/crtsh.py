import os
import requests
import csv
import re
import PTRandA
import whois_IP

def fetch_subdomains_and_issuers(domain):
    url = f"https://crt.sh/?q=%.{domain}&output=json"
    allowed_issuers = {"DigiCert", "Let's Encrypt", "Global Sign"}

    try:
        response = requests.get(url)
        response.raise_for_status()
        certificates = response.json()

        # Extract subdomains and issuer information
        subdomains_info = []
        seen_subdomains = set()  # Keep track of already added subdomains
        for cert in certificates:
            name = cert.get("name_value", "")
            issuer = cert.get("issuer_name", "")
            not_before = cert.get("not_before", "").strip()
            not_after = cert.get("not_after", "").strip()

            # Extract only the part after "O="
            match = re.search(r"O=([^,]+)", issuer)
            issuer_organization = match.group(1).strip() if match else ""

            # Check if the issuer is in the allowed list
            unknown_issuer = not any(allowed_issuer in issuer for allowed_issuer in allowed_issuers)

            # Add all subdomains and their issuer status to the list
            for subdomain in name.split("\n"):
                subdomain = subdomain.strip()
                if subdomain.endswith(domain) and subdomain not in seen_subdomains:
                    seen_subdomains.add(subdomain)  # Mark the subdomain as seen
                    subdomains_info.append({
                        "subdomain": subdomain,
                        "unknown_issuer": issuer_organization if unknown_issuer else "",
                        "not_before": not_before,
                        "not_after": not_after
                    })


        return subdomains_info
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from crt.sh: {e}")
        return []

def save_to_csv(subdomains_info, filename = "crtsh.csv"):
    try:
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["Subdomain", "Unknown Issuer", "Not Before", "Not After"])
            writer.writeheader()
            for info in subdomains_info:
                writer.writerow({
                    "Subdomain": info["subdomain"],
                    "Unknown Issuer": info["unknown_issuer"],
                    "Not Before": info["not_before"],
                    "Not After": info["not_after"]
                })
        print(f"Subdomains saved to {filename}")
    except IOError as e:
        print(f"Error saving data to {filename}: {e}")

def open_in_excel(file_name):
    try:
        os.startfile(file_name)
    except Exception as e:
        print(f"Error opening file in Excel: {e}")


if __name__ == "__main__":
    domain = input("Enter the domain: ")
    print(f"Fetching subdomains and issuers for {domain}...")
    subdomains_info = fetch_subdomains_and_issuers(domain)
    if not subdomains_info:
        print("No subdomains found. Exiting.")
        exit()
    print(f"Found {len(subdomains_info)} subdomains.")
    save_to_csv(subdomains_info)
