import whois
import csv
import os

url_list = []

def initialize_url_list(file_name):
    try:
        if os.path.exists(file_name):
            with open(file_name, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                header = next(reader)  # Read the header row
                domain_index = header.index("domain_name") if "domain_name" in header else None
                if domain_index is not None:
                    for row in reader:
                        if len(row) > domain_index:
                            url_list.append(row[domain_index])
    except Exception as e:
        print(f"Error initializing URL list: {e}")

def get_whois_data(target):
    try:
        # Retrieve WHOIS data
        whois_data = whois.whois(target)
        return whois_data
    except Exception as e:
        print(f"Error fetching WHOIS data for {target}: {e}")
        return None

def merge_keys(existing_keys, new_data):
    # Merge new keys into the existing keys list
    new_keys = new_data.keys()
    for key in new_keys:
        if key not in existing_keys:
            existing_keys.append(key)
    return existing_keys

def append_to_csv(data, file_name):
    try:
        if os.path.exists(file_name):
            # Read existing keys from the CSV file
            with open(file_name, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                all_keys = next(reader)
        else:
            all_keys = []
            # Write WHOIS data to a CSV file
            with open(file_name, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(all_keys)  # Write header row with all possible keys

        # Update keys if necessary
        all_keys = merge_keys(all_keys, data)

        # Read existing data
        rows = []
        with open(file_name, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)

        # Update header row
        rows[0] = all_keys

        # Append new data
        new_row = [data.get(key, "") for key in all_keys]
        rows.append(new_row)

        # Write updated data back to the CSV
        with open(file_name, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(rows)

        print(f"WHOIS data appended to {file_name}")
    except Exception as e:
        print(f"Error appending to CSV: {e}")

def open_in_excel(file_name):
    try:
        os.startfile(file_name)
    except Exception as e:
        print(f"Error opening file in Excel: {e}")

def main():
    print("WHOIS Lookup Script")
    file_name = "whois_data_combined.csv"

    # Initialize URL list from existing file
    initialize_url_list(file_name)

    print("Existing file detected. You can add new URLs.")
    while True:
        new_target = input("Enter a new URL (or press Enter to stop): ").strip()
        if not new_target:
            break
        new_target = new_target.replace("https://", "").replace("http://", "").strip("/")
        if new_target not in url_list:
            url_list.append(new_target)
            whois_data = get_whois_data(new_target)
            if whois_data:
                append_to_csv(whois_data, file_name)
        else:
            print("URL already exists!")

    open_in_excel(file_name)

if __name__ == "__main__":
    main()
