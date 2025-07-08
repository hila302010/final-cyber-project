import csv
import requests
from bs4 import BeautifulSoup
import os


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
        "Country": ""
    }

    for line in data_lines:
        if "orgname:" in line.lower():
            extracted_data["OrgName"] = line.split(':', 1)[-1].strip()
        elif "org-name:" in line.lower():
            extracted_data["OrgName"] = line.split(':', 1)[-1].strip()
        elif "country:" in line.lower():
            extracted_data["Country"] = line.split(':', 1)[-1].strip()

    return extracted_data



def save_to_csv(data, filename="whois_data.csv"):
    # Define the fieldnames that match the keys in the data dictionary
    fieldnames = ["Domain", "IP Address", "OrgName", "Country"]

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
                "Country": data["Country"]
            })

        print(f"Data saved to {filename}")
    except Exception as e:
        print(f"Error saving data to {filename}: {e}")



if __name__ == "__main__":
    ip_address = input("Enter IP address: ")
    data = get_whois_data(ip_address)

    if data:
        save_to_csv(data)
