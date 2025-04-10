import csv
import requests
from bs4 import BeautifulSoup
import os


"""
def get_whois_data(ip, domain_name="N/A"):
    url = f"https://www.whois.com/whois/{ip}"
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Failed to retrieve data for {ip}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    whois_data = soup.find('pre', {'id': 'registryData'})

    if not whois_data:
        print(f"No WHOIS data found for {ip}")
        return None

    data_lines = whois_data.text.split('\n')
    extracted_data = {"Domain":"", "IP_ADDRESS": "","Org_Name": "", "Country": "", "Mnt-By": "", "Abuse_Mailbox": ""}

    for line in data_lines:
        extracted_data["Domain"] = domain_name
        extracted_data["IP_ADDRESS"] = ip
        if "org-name:" in line.lower():
            extracted_data["Org_Name"] = line.split(':', 1)[-1].strip()
        elif "country:" in line.lower():
            extracted_data["Country"] = line.split(':', 1)[-1].strip()
        elif "mnt-by:" in line.lower():
            extracted_data["Mnt-By"] = line.split(':', 1)[-1].strip()
        elif "abuse-mailbox:" in line.lower():
            extracted_data["Abuse_Mailbox"] = line.split(':', 1)[-1].strip()

    return extracted_data
"""
def get_whois_data(ip, domain_name="N/A"):
    url = f"https://www.whois.com/whois/{ip}"
    response = requests.get(url)

    if response.status_code != 200:
        print("Failed to retrieve data")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    whois_data = soup.find('pre', {'id': 'registryData'})

    if not whois_data:
        print("No WHOIS data found")
        return None

    data_lines = whois_data.text.split('\n')
    extracted_data = {
        "Domain": domain_name,
        "IP Address": ip,
        "OrgName": "",
        "Country": "",
        "Mnt-By": "",
        "Abuse Mailbox": ""
    }

    for line in data_lines:
        if "orgname:" in line.lower():
            extracted_data["OrgName"] = line.split(':', 1)[-1].strip()
        elif "org-name:" in line.lower():
            extracted_data["OrgName"] = line.split(':', 1)[-1].strip()
        elif "country:" in line.lower():
            extracted_data["Country"] = line.split(':', 1)[-1].strip()
        elif "mnt-by:" in line.lower():
            extracted_data["Mnt-By"] = line.split(':', 1)[-1].strip()
        elif "abuse-mailbox:" in line.lower():
            extracted_data["Abuse Mailbox"] = line.split(':', 1)[-1].strip()

    return extracted_data



def save_to_csv(data, filename="whois_data.csv"):
    # Define the fieldnames that match the keys in the data dictionary
    fieldnames = ["Domain", "IP Address", "OrgName", "Country", "Mnt-By", "Abuse Mailbox"]

    try:
        # Open the CSV file in append mode so that we don't overwrite existing data
        file_exists = os.path.exists(filename)
        with open(filename, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write the header only if the file is empty
            if not file_exists:
                writer.writeheader()

            # Write the actual data row
            writer.writerow({
                "Domain": data["Domain"],
                "IP Address": data["IP Address"],
                "OrgName": data["OrgName"],
                "Country": data["Country"],
                "Mnt-By": data["Mnt-By"],
                "Abuse Mailbox": data["Abuse Mailbox"]
            })

        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data to {filename}: {e}")



if __name__ == "__main__":
    ip_address = input("Enter IP address: ")
    data = get_whois_data(ip_address)

    if data:
        save_to_csv(data)
