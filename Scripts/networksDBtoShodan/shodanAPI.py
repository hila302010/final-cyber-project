from shodan import Shodan
import pycountry

API_KEY = 'WYaEdNYjNutWoxMbLNWcdH2XwHsQSHKJ'
api = Shodan(API_KEY)


# Function to convert country name to country code
def get_country_code(country_name):
    try:
        country = pycountry.countries.get(name=country_name)
        if country:
            return country.alpha_2
        else:
            print(f"Country name '{country_name}' not found.")
            return None
    except Exception as e:
        print(f"Error while converting country name '{country_name}' to country code: {e}")
        return None


# Looking by API for IP - by host
def lookup_ip(ip):
    try:
        return api.host(ip)
    except Exception as e:
        print(f"Error retrieving IP {ip}: {e}")
        return None


# Looking by API for domain names - by search
def lookup_domain(domain):
    try:
        return api.search(f'hostname:{domain}')
    except Exception as e:
        print(f"Error retrieving domain {domain}: {e}")
        return None


# Looking by API for IP ranges - by search
def lookup_ip_range(ip_range):
    try:
        return api.search(f'net:{ip_range}')
    except Exception as e:
        print(f"Error retrieving IP range {ip_range}: {e}")
        return None


# Search by country AND IP (after converting country name to code)
def lookup_country_and_ip(country_name, ip):
    country_code = get_country_code(country_name)
    if not country_code:
        print(f"Cannot lookup: Country '{country_name}' could not be resolved.")
        return None

    try:
        return api.search(f'country:{country_code} ip:{ip}')
    except Exception as e:
        print(f"Error retrieving country '{country_name}' and IP '{ip}': {e}")
        return None



if __name__ == "__main__":
    target = input(
        "Enter IP, domain, IP range, country name (full name), or country+IP (e.g., United States 192.168.1.1): ").strip()

    if ' ' in target:  # If input contains a space, assume country + IP
        parts = target.split()
        if len(parts) == 2:  # Format: "<Country Name> <IP>"
            country_name, ip = parts
            result = lookup_country_and_ip(country_name, ip)
        else:
            print("Invalid format. Use: <Country Name> <IP>")
            result = None
    elif '/' in target:  # IP Range
        result = api.search(f'net:{target}')
    elif any(c.isalpha() for c in target) and len(target) == 2:  # Country code
        result = api.search(f'country:{target.upper()}')
    elif any(c.isalpha() for c in target):  # Domain name
        result = api.search(f'hostname:{target}')
    else:  # IP
        result = api.host(target)

    if result and 'matches' in result:
        save_to_csv(result['matches'], 'shodan_results.csv')
    else:
        print("No results found.")
