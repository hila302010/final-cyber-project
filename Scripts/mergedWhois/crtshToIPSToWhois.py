import os
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

import Scripts.mergedWhois.whois_IP as whois_IP
import Scripts.mergedWhois.crtsh as crtsh
import Scripts.mergedWhois.PTRandA as PTRandA

#import whois_IP
#import crtsh
#import PTRandA

import logging
import time



# Function to fetch the A record for each subdomain
def fetch_ip_for_subdomain(subdomain):
    try:
        print(f"Fetching IP for subdomain: {subdomain}")
        ip_addresses = PTRandA.get_a_record(subdomain)
        return {"subdomain": subdomain, "ip_addresses": ip_addresses}
    
    except Exception as e:
        logging.error(f"Error fetching WHOIS ip for subdomain {subdomain}: {e}")
        return {}  # Return an empty dictionary on failure


# Function to fetch WHOIS data for each IP
def fetch_whois_data_for_ip(subdomain, ip):
    try:
        print(f"Fetching WHOIS for IP {ip} of subdomain: {subdomain}")
        whois_data = whois_IP.get_whois_data(ip, subdomain)
        return whois_data
    
    except Exception as e:
        logging.error(f"Error fetching WHOIS data for IP {ip}: {e}")
        return {}  # Return an empty dictionary on failure


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
"""


def getipsWithFields(domain):    
    # Fetch subdomains info
    subdomains_info = crtsh.fetch_subdomains_and_issuers(domain)
    if not subdomains_info:
        print("No subdomains found. Exiting.")
        exit()

    subdomains = [item["subdomain"] for item in subdomains_info]
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

         # Prepare a list to store all extracted WHOIS data
        all_extracted_data = []


        # Now fetch WHOIS data for each IP address in the same order
        for info in subdomains_ip:
            for ip in info["ip_addresses"]:
                if ip:
                    whois_future = executor.submit(fetch_whois_data_for_ip, info["subdomain"], ip)
                    whois_data = whois_future.result()  # Wait for the WHOIS data to be fetched
                    # Extract only the required fields
                    extracted_data = {
                        "IP": ip,
                        "Country": whois_data.get("Country", "N/A"),
                        "Mnt-By": whois_data.get("Mnt-By", "N/A"),
                        "Abuse Mailbox": whois_data.get("Abuse Mailbox", "N/A")
                    }
                      # Add the extracted data to the list
                    all_extracted_data.append(extracted_data)
                else:
                    print("Empty IP address, skipping.")

    # Return all the extracted data
    return all_extracted_data"""


def getipsWithFields(domain, max_time=300):
    """
    Main function to fetch subdomains, IP addresses, and WHOIS data for a given domain.
    Stops after max_time seconds and returns the data collected so far.
    """
    start_time = time.time()  # Record the start time

    # Step 1: Fetch subdomains
    subdomains_info = fetch_subdomains(domain)
    if not subdomains_info:
        print("No subdomains found. Exiting.")
        return []

    # Check if the time limit has been reached
    if time.time() - start_time > max_time:
        print(f"Time limit of {max_time} seconds reached. Returning collected data so far.")
        return []

    # Step 2: Fetch IP addresses for subdomains
    subdomains_ip = fetch_ips_for_subdomains_with_timer(subdomains_info, start_time, max_time)

    # Step 3: Fetch WHOIS data for IP addresses
    all_extracted_data = fetch_whois_for_ips_with_timer(subdomains_ip, start_time, max_time)

    # Return all the extracted data
    return all_extracted_data



def fetch_subdomains(domain):
    """
    Fetch subdomains and issuers for a given domain.
    """
    print(f"Fetching subdomains for domain: {domain}")
    subdomains_info = crtsh.fetch_subdomains_and_issuers(domain)
    if subdomains_info:
        print(f"Found {len(subdomains_info)} subdomains.")
    return subdomains_info



def fetch_ips_for_subdomains_with_timer(subdomains_info, start_time, max_time):
    """
    Fetch IP addresses for each subdomain with a time limit.
    """
    subdomains_ip = []

    print("Fetching IP addresses for subdomains...")
    with ThreadPoolExecutor() as executor:
        ip_futures = {executor.submit(fetch_ip_for_subdomain, sub): sub for sub in subdomains_info}

        for future in as_completed(ip_futures):
            # Check if the time limit has been reached
            if time.time() - start_time > max_time:
                print(f"Time limit of {max_time} seconds reached while fetching IPs. Returning collected data so far.")
                return subdomains_ip

            try:
                result = future.result()
                if result:
                    ip_addresses = result["ip_addresses"]
                    if ip_addresses and not any("Error:" in ip for ip in ip_addresses):
                        subdomains_ip.append(result)
                        print(f"IP addresses for {result['subdomain']}: {ip_addresses}")
                    else:
                        print(f"Could not fetch IPs for {result['subdomain']}")
            except Exception as e:
                print(f"Error fetching IP for subdomain: {e}")

    return subdomains_ip



def fetch_whois_for_ips_with_timer(subdomains_ip, start_time, max_time):
    """
    Fetch WHOIS data for each IP address with a time limit.
    """
    all_extracted_data = []

    print("Fetching WHOIS data for IP addresses...")
    with ThreadPoolExecutor() as executor:
        for info in subdomains_ip:
            for ip in info["ip_addresses"]:
                # Check if the time limit has been reached
                if time.time() - start_time > max_time:
                    print(f"Time limit of {max_time} seconds reached while fetching WHOIS data. Returning collected data so far.")
                    return all_extracted_data

                if ip:
                    try:
                        whois_future = executor.submit(fetch_whois_data_for_ip, info["subdomain"], ip)
                        whois_data = whois_future.result()  # Wait for the WHOIS data to be fetched
                        extracted_data = extract_whois_fields(ip, whois_data)
                        all_extracted_data.append(extracted_data)
                    except Exception as e:
                        print(f"Error fetching WHOIS data for IP {ip}: {e}")
                else:
                    print("Empty IP address, skipping.")

    return all_extracted_data


def extract_whois_fields(ip, whois_data):
    """
    Extract required fields from WHOIS data.
    """
    return {
        "IP": ip,
        "Country": whois_data.get("Country", "N/A"),
        "Domain": whois_data.get("Domain", "N/A"),
        "Mnt-By": whois_data.get("Mnt-By", "N/A"),
        "Abuse Mailbox": whois_data.get("Abuse Mailbox", "N/A")
    }





if __name__ == "__main__":
    domain = input("Enter the domain: ")
    print(f"Fetching subdomains and issuers for {domain}...")
    all_extracted_data = getipsWithFields(domain)
    for data in all_extracted_data:
        print(data)

    """# Fetch subdomains info
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

    print("DONE!!!")"""
