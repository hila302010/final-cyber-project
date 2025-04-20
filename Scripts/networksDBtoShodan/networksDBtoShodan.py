import requests
#import Scripts.networksDBtoShodan.shodanAPI as shodanAPI
import shodanAPI
import csv


def search_networksdb(country_name, organization_name, api_key):
    base_url = "https://networksdb.io/api"
    headers = {"X-Api-Key": api_key}

    try:
        # Step 1: Search for the organization to get its ID
        org_search_url = f"{base_url}/org-search"
        params = {"search": organization_name, "country": country_name}
        org_search_response = requests.get(org_search_url, headers=headers, params=params)
        org_search_response.raise_for_status()  # Raise an exception for bad status codes
        org_search_data = org_search_response.json()

        if org_search_data and org_search_data.get("total", 0) > 0 and org_search_data.get("results"):
            organization_id = org_search_data["results"][0]["id"]

            # Step 2: Get the networks for the found organization
            org_networks_url = f"{base_url}/org-networks"
            networks_params = {"id": organization_id}
            org_networks_response = requests.get(org_networks_url, headers=headers, params=networks_params)
            org_networks_response.raise_for_status()
            org_networks_data = org_networks_response.json()

            results = set()  # Initialize as a set to ensure uniqueness

            if org_networks_data and org_networks_data.get("results"):
                for network in org_networks_data["results"]:
                    if network.get("country") == country_name:
                        # Check for CIDR and normalize it (lowercase and strip spaces)
                        if network.get("cidr"):
                            normalized_cidr = network["cidr"].strip().lower()
                            results.add(normalized_cidr)

                        # Check for IP ranges and normalize them (strip spaces)
                        elif network.get("start_ip") and network.get("end_ip"):
                            ip_range = f"{network['start_ip'].strip()} - {network['end_ip'].strip()}"
                            results.add(ip_range)

            return results

        else:
            print(f"Organization '{organization_name}' not found in '{country_name}' or no results.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the API request: {e}")
        return []
    except ValueError as e:
        print(f"Error decoding JSON response: {e}")
        return []
    except KeyError as e:
        print(f"Missing key in JSON response: {e}")
        return []





def process_shodan_for_cidr(country, cidr_addresses):
    all_data = []
    for address in cidr_addresses:
        print(f"Processing Shodan for {address} in {country}...")

        # Call the lookup_country_and_ip function from shodanAPI.py
        result = shodanAPI.lookup_country_and_ip(country, address)

        # If results are found, collect the data
        if result and 'matches' in result:
            shodan_data = getData(result['matches'])
            all_data.extend(shodan_data)  # Add the data to the main list
        else:
            print(f"No Shodan results for {address}")
    return all_data



"""def save_to_csv(data, adress, filename):
    if not data:
        print("No data to save.")
        return []

    # Make 'address' the first field in the fieldnames list
    fieldnames = ['address', 'port', 'vulns', 'org', 'country_name', 'city', 'ip_str', 'domains', 'hostnames']

    with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        data_written = False
        result_data = []  # To collect the processed data

        for row in data:
            # Ensure it's a valid Shodan result (skip unwanted data)
            if not isinstance(row, dict) or 'ip_str' not in row or 'port' not in row:
                continue

            # Clean "vulns" field (avoid CVE lists)
            if 'vulns' in row and isinstance(row['vulns'], dict):
                row['vulns'] = ', '.join(row['vulns'].keys())  # Keep only CVE IDs, remove details

            # Convert lists to comma-separated strings for CSV readability
            for field in ['domains', 'hostnames']:
                if isinstance(row.get(field), list):
                    row[field] = ', '.join(row[field])

            # Extract country_name and city from the location dictionary
            row['country_name'] = row.get('location', {}).get('country_name', '')
            row['city'] = row.get('location', {}).get('city', '')

            # Extract only required fields and add the address as the first field
            filtered_row = {'address': adress}  # Add address as the first field
            filtered_row.update({field: row.get(field, '') for field in fieldnames if field != 'address'})

            # Avoiding blank rows
            if any(filtered_row.values()):
                writer.writerow(filtered_row)
                result_data.append(filtered_row)  # Add the row to the result data
                data_written = True

        if not data_written:
            writer.writerow({field: '' for field in fieldnames})

    print(f"Results saved to {filename}")
    return result_data  # Return the processed data
"""

def getData(data):
    if not data:
        print("No data to save.")
        return []

    # Make 'address' the first field in the fieldnames list
    fieldnames = ['ip_str', 'port', 'vulns',  'country_name', 'city', 'domains', 'hostnames']


    result_data = []  # To collect the processed data

    for row in data:
        # Ensure it's a valid Shodan result (skip unwanted data)
        if not isinstance(row, dict) or 'ip_str' not in row or 'port' not in row:
            continue

        # Clean "vulns" field (avoid CVE lists)
        if 'vulns' in row and isinstance(row['vulns'], dict):
            row['vulns'] = ', '.join(row['vulns'].keys())  # Keep only CVE IDs, remove details

        # Convert lists to comma-separated strings for CSV readability
        for field in ['domains', 'hostnames']:
            if isinstance(row.get(field), list):
                row[field] = ', '.join(row[field])

        # Extract country_name and city from the location dictionary
        row['country_name'] = row.get('location', {}).get('country_name', '')
        row['city'] = row.get('location', {}).get('city', '')

        # Extract only required fields and add the ip address as the first field 
        filtered_row = {field: row.get(field, '') for field in fieldnames}

        # Avoiding blank rows
        if any(filtered_row.values()):
            result_data.append(filtered_row)  # Add the row to the result data


    print("Results saved ", result_data)
    return result_data  # Return the processed data



def extract_domains_and_hostnames(data):
    """
    Extracts all domains, subdomains, and hostnames from the given data.
    Args: data (list): A list of dictionaries containing Shodan results.
    Returns: list: A list of unique domains, subdomains, and hostnames.
    """
    if not data:
        print("No data available to extract domains and hostnames.")
        return []
    results = set()  # Use a set to ensure uniqueness
    for row in data:
        # Extract domains
        if 'domains' in row and isinstance(row['domains'], str):
            results.update(row['domains'].split(', '))  # Split comma-separated domains and add to the set
        # Extract hostnames
        if 'hostnames' in row and isinstance(row['hostnames'], str):
            results.update(row['hostnames'].split(', '))  # Split comma-separated hostnames and add to the set
    return list(results)  # Convert the set back to a list



def execute_networksdb_to_shodan(country, organization):
    api_key = "751ba4ad-5a35-4428-a4d3-1ec191d9aaf6"
    if not api_key:
        data = "API key is required."
        print("Error: NetworksDB API key is required. You can get one at https://networksdb.io/api/plans")
    else:
        ormatted_country = country.capitalize()  # Capitalize first letter
        cidr_addresses = search_networksdb(ormatted_country, organization, api_key)

        if cidr_addresses:
            # print(f"\nUnique CIDR/IP Addresses for '{organization}' in '{ormatted_country}':")
            # for address in cidr_addresses:
            #     print(f"- {address}")

            # Call the Shodan API for each CIDR/IP using lookup_country_and_ip
            data = (process_shodan_for_cidr(ormatted_country, cidr_addresses))
            print(data)
        else:
            data = "No CIDR/IP addresses found."
            print(f"\nNo CIDR/IP addresses found for '{organization}' in '{ormatted_country}'.")
    return data 



if __name__ == "__main__":
    country = input("Enter the country name: ")
    organization = input("Enter the organization name: ")
    print(execute_networksdb_to_shodan(country, organization))
    

