import requests
import shodanAPI  # Import your shodanAPI script


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
    for address in cidr_addresses:
        print(f"Processing Shodan for {address} in {country}...")

        # Call the lookup_country_and_ip function from shodanAPI.py
        result = shodanAPI.lookup_country_and_ip(country, address)

        # If results are found, save to CSV
        if result and 'matches' in result:
            shodanAPI.save_to_csv(result['matches'], f"shodan_results_{address.replace('/', '_')}.csv")
        else:
            print(f"No Shodan results for {address}")


if __name__ == "__main__":
    country = input("Enter the country name: ")
    ormatted_country = country.capitalize()  # Capitalize first letter
    organization = input("Enter the organization name: ")
    api_key = "751ba4ad-5a35-4428-a4d3-1ec191d9aaf6"

    if not api_key:
        print("Error: NetworksDB API key is required. You can get one at https://networksdb.io/api/plans")
    else:
        cidr_addresses = search_networksdb(ormatted_country, organization, api_key)

        if cidr_addresses:
            print(f"\nUnique CIDR/IP Addresses for '{organization}' in '{ormatted_country}':")
            for address in cidr_addresses:
                print(f"- {address}")

            # Call the Shodan API for each CIDR/IP using lookup_country_and_ip
            process_shodan_for_cidr(ormatted_country, cidr_addresses)
        else:
            print(f"\nNo CIDR/IP addresses found for '{organization}' in '{ormatted_country}'.")
