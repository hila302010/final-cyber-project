import requests
import re

def get_ips_for_domain(domain):
    url = f"https://networksdb.io/domain-to-ips/{domain}"
    response = requests.get(url)

    if response.status_code != 200:
        print("Failed to retrieve data")
        return []

    # Extract text directly from the raw response content
    raw_text = response.text

    # Regex to match IPv4 addresses
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ips = set(re.findall(ip_pattern, raw_text))  # Use set to remove duplicates

    return list(ips)

def save_to_file(domain, ips):
    filename = f"{domain}_ips.txt"
    with open(filename, "w") as file:
        for ip in ips:
            file.write(ip + "\n")
    print(f"IPs saved to {filename}")

def main():
    domain = input("Enter a domain: ")
    ips = get_ips_for_domain(domain)
    if ips:
        print("IP Addresses found:")
        for ip in ips:
            print(ip)
        save_to_file(domain, ips)  # Save to file
    else:
        print("No IP addresses found.")

if __name__ == "__main__":
    main()
