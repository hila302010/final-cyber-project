import dns.resolver
import dns.reversename
import ipaddress

#Fetches the A record for a given domain name.
def get_a_record(domain):
    try:
        answer = dns.resolver.resolve(domain, "A")
        return [rdata.to_text() for rdata in answer]
    except Exception as e:
        return [f"Error: {e}"]

#Fetches the PTR record for a given IP address.
def get_ptr_record(ip_address):
    try:
        rev_name = dns.reversename.from_address(ip_address)
        ptr_records = dns.resolver.resolve(rev_name, 'PTR')
        return [record.to_text() for record in ptr_records]
    except Exception as e:
        return [f"Error: {e}"]


#Saves the DNS results to a text file.
def save_to_file(identifier, records, filename):
    with open(filename, "a", encoding="utf-8") as file:
        for record in records:
            file.write(f"{identifier} -> {record}\n")


if __name__ == "__main__":
    user_input = input("Enter a domain name or an IP address: ").strip()

    try:
        # Check if the input is an IP address
        ip = ipaddress.ip_address(user_input)
        records = get_ptr_record(user_input)
        save_to_file(user_input, records, "../ptr_results.txt")
        print("\nResults saved to ptr_results.txt")
    except ValueError:
        # If it's not an IP address, assume it's a domain name
        records = get_a_record(user_input)
        save_to_file(user_input, records, "../a_records.txt")
        print("\nResults saved to a_records.txt")

