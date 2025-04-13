import os
import csv
import PTRandA
import whois_IP
from concurrent.futures import ThreadPoolExecutor, as_completed
import crtsh

# Function to fetch the A record for each subdomain
def fetch_ip_for_subdomain(subdomain):
    print(f"Fetching IP for subdomain: {subdomain}")
    ip_addresses = PTRandA.get_a_record(subdomain)
    return {"subdomain": subdomain, "ip_addresses": ip_addresses}


# Function to fetch WHOIS data for each IP
def fetch_whois_data_for_ip(subdomain, ip):
    print(f"Fetching WHOIS for IP {ip} of subdomain: {subdomain}")
    whois_data = whois_IP.get_whois_data(ip, subdomain)
    return whois_data


# Function to append data to CSV file
def append_to_csv(data, file_name="whois_data_combined.csv"):
    try:
        file_exists = os.path.exists(file_name)

        # If the file exists, check if it's empty or doesn't have headers
        if file_exists:
            with open(file_name, mode='r', newline='', encoding='utf-8') as file:
                first_line = file.readline().strip()
                # If the first line is not the header row, write headers
                if first_line != "Domain,IP_Address,OrgName,Country,Mnt-By,Abuse_Mailbox":
                    is_empty = not file.read().strip()  # Check if the file has any more content
                    if is_empty:
                        with open(file_name, mode='a', newline='', encoding='utf-8') as append_file:
                            writer = csv.writer(append_file)
                            writer.writerow(["Domain", "IP_Address", "OrgName", "Country", "Mnt-By", "Abuse_Mailbox"])
        else:
            # If the file doesn't exist, create it and write headers
            with open(file_name, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["Domain", "IP_Address", "OrgName", "Country", "Mnt-By", "Abuse_Mailbox"])

        # Now append the actual data
        with open(file_name, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([data.get("Domain", ""),
                             data.get("IP Address", ""),
                             data.get("OrgName", ""),
                             data.get("Country", ""),
                             data.get("Mnt-By", ""),
                             data.get("Abuse Mailbox", "")])

        print(f"WHOIS data appended to {file_name}")
    except Exception as e:
        print(f"Error appending to CSV: {e}")


if __name__ == "__main__":
    domain = input("Enter the domain: ")
    print(f"Fetching subdomains and issuers for {domain}...")

    # Fetch subdomains info
    subdomains_info = crtsh.fetch_subdomains_and_issuers(domain)
    if not subdomains_info:
        print("No subdomains found. Exiting.")
        exit()
    print(f"Found {len(subdomains_info)} subdomains.")
    print("Extracting subdomains..")
    subdomains = [item["subdomain"] for item in subdomains_info]

    print("Found these subdomains:")
    for sub in subdomains:
        print(sub)

    # Use ThreadPoolExecutor to fetch IP addresses and WHOIS data in parallel
    with ThreadPoolExecutor() as executor:
        # First fetch the A records (IP addresses) for subdomains
        ip_futures = {executor.submit(fetch_ip_for_subdomain, sub): sub for sub in subdomains}
        subdomains_ip = []

        # Process results from IP fetch
        for future in as_completed(ip_futures):
            result = future.result()
            if result:
                ip_addresses = result["ip_addresses"]
                if ip_addresses and not any("Error:" in ip for ip in ip_addresses):
                    subdomains_ip.append(result)
                    print(f"IP for {result['subdomain']}: {ip_addresses}")
                else:
                    print(f"Could not fetch IPs for {result['subdomain']}")

        # Now fetch WHOIS data for each IP address in the same order
        for info in subdomains_ip:
            for ip in info["ip_addresses"]:
                if ip:
                    whois_future = executor.submit(fetch_whois_data_for_ip, info["subdomain"], ip)
                    whois_data = whois_future.result()  # Wait for the WHOIS data to be fetched
                    append_to_csv(whois_data)  # Save to CSV
                else:
                    print("Empty IP address, skipping.")

    print("DONE!!!")
