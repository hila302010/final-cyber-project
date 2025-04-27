import dns.resolver
import re


def find_dkim_selector(domain, common_selectors=None):
    """Find a valid DKIM selector for the given domain."""
    if common_selectors is None:
        common_selectors = ['default', 'selector1', 'selector2', 'google', 'badeba3b8450']

    for selector in common_selectors:
        try:
            query = f'{selector}._domainkey.{domain}'
            dkim_record = dns.resolver.resolve(query, 'TXT')
            dkim_data = ' '.join(part.decode('utf-8') for txt_rec in dkim_record for part in txt_rec.strings)
            return selector, dkim_data
        except Exception:
            continue
    return None, "No valid DKIM selector found in the given list."

# Function to extract p= value from DMARC record
def parse_dmarc_record(dmarc_record):
    """Extract DMARC policy."""
    dmarc_policy = re.search(r'p=([^;]+)', dmarc_record)
    return dmarc_policy.group(1) if dmarc_policy else "No DMARC policy found"

# Function to extract p= value from DKIM record
def parse_dkim_record(dkim_data):
    for part in dkim_data.split(';'):
        if part.strip().startswith('p='):
            return part.strip().split('=')[1]
    return None  # No 'p=' found in DKIM record (Key Revoked)

def fetch_dns_records(domain):
    records = {}

    # Fetch SPF record (TXT record starting with "v=spf1")
    try:
        txt_records = dns.resolver.resolve(domain, 'TXT')
        spf_record = next((str(txt_rec) for txt_rec in txt_records if 'v=spf1' in str(txt_rec)), None)
        records['SPF'] = spf_record or "No SPF record found"
    except Exception as e:
        records['SPF'] = f"No SPF record found"

    # Fetch DMARC record (_dmarc.domain as TXT record)
    try:
        dmarc_records = dns.resolver.resolve(f'_dmarc.{domain}', 'TXT')
        dmarc_data = ' '.join(part.decode('utf-8') for txt_rec in dmarc_records for part in txt_rec.strings)
        records['DMARC'] = dmarc_data
        policy = parse_dmarc_record(dmarc_data)
        if policy is None:
            records['DMARC Policy'] = "WARNING: No DMARC policy found (p=None)"
        elif policy.lower() == "none":
            records['DMARC Policy'] = "WARNING: DMARC policy is set to p=none (Monitoring Only)"
        else:
            records['DMARC Policy'] = f"DMARC policy: p={policy}"
    except Exception as e:
        records['DMARC'] = f"No DMARC record found"
        records['DMARC Policy'] = "Not found"

        # Fetch DKIM records (selector._domainkey.domain as TXT record)
    try:
        selector, dkim_data = find_dkim_selector(domain)
        if selector:
            records['DKIM Selector'] = selector
            records['DKIM'] = dkim_data

            # Extract DKIM 'p=' value
            dkim_key = parse_dkim_record(dkim_data)
            if dkim_key is None:
                records['DKIM Status'] = "WARNING: DKIM p= is missing (Key Revoked!)"
            elif dkim_key.lower() == "none":
                records['DKIM Status'] = "WARNING: DKIM p=none (Invalid Configuration!)"
            else:
                records['DKIM Status'] = "DKIM  public key found"
        else:
            records['DKIM Selector'] = "Not found"
            records['DKIM'] = "No DKIM record found"
    except Exception as e:
        records['DKIM Selector'] = "Error"
        records['DKIM'] = f"Error fetching DKIM: {e}"

    return records

def save_to_text_file(domain, results, filename="dns_records.txt"):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(f"DNS Records for {domain}\n")
            file.write("=" * 40 + "\n")
            for record_type, record_value in results.items():
                file.write(f"{record_type}: {record_value}\n")
        print(f"Results saved to {filename}")
    except Exception as e:
        print(f"An error occurred while saving to the file: {e}")

def main():
    domain = input("Enter the domain: ")
    results = fetch_dns_records(domain)
    save_to_text_file(domain, results)

if __name__ == "__main__":
    main()