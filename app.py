# ------------------------------
# Imports
# ------------------------------

#adding redisfrom flask_session import Session
import redis
from flask_session import Session


from flask import Flask, render_template, request, jsonify, Response, session, redirect, url_for
import webbrowser
import threading
import os
import secrets
import time
import csv
from io import StringIO
from flask import jsonify
from concurrent.futures import ThreadPoolExecutor, as_completed

# Custom scripts
import Scripts.DNS.DkimDmarc as dkim_dmarc
import Scripts.networksDBtoShodan.shodanAPI as shodanAPI
import Scripts.networksDBtoShodan.networksDBtoShodan as nDBtoS
import Scripts.githubAndGoogleDorks.googleDorks as google
import Scripts.githubAndGoogleDorks.github_api as github
import Scripts.socialNetworkServices.linkedin as linkedin
import Scripts.mergedWhois.crtshToIPSToWhois as whois
import Scripts.githubAndGoogleDorks.main as googleAndGithub

# Simulated progress variable
progress = {"value": 0}


# ------------------------------
# Flask App Configuration
# ------------------------------
app = Flask(__name__)
app.secret_key = str(secrets.token_hex(32)) # Replace with a secure random key


# ------------------------------
# Redis session configuration
# ------------------------------
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True  # Optional: adds cryptographic signature
app.config['SESSION_REDIS'] = redis.Redis(host='localhost', port=6379, db=0)
# Initialize session
Session(app)



# A dictionary to track cancellation flags for each session or process
cancellation_flags = {}
# Simulated progress variable
progress = {"value": 0, "task": "Initializing..."}



# ------------------------------
# Routes
# ------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/cancel', methods=['POST'])
def cancel_process():
    session_id = request.json.get('session_id')
    if session_id:
        cancellation_flags[session_id] = True
        return {"message": "Process canceled successfully."}, 200
    return {"error": "Session ID is required."}, 400


# ------------------------------------------------------
# loading data from the scripts by the form fields: domain country and company
# ------------------------------------------------------
@app.route('/load_data', methods=['POST'])
def load_data():
    """
    Main function to load data based on the provided domain, country, and company.
    """
    global progress
    progress["value"] = 0  # Reset progress
    progress["task"] = "Parsing input data..."  # Update task description

    session_id = request.json.get('session_id')
    if not session_id:
        return {"error": "Session ID is required."}, 400

    # Reset the cancellation flag for this session
    cancellation_flags[session_id] = False

    # Parse the JSON data from the AJAX request
    data = request.get_json()
    domain = data.get('domain')
    country = data.get('country')
    company = data.get('company')

    # Simulate progress for each step
    progress["value"] = 5  # Step 1: Parsing input data

    # Fetch data in steps
    emails = fetch_emails(session_id, domain, company)
    # Load employees from CSV - temporarily
    employees = fetch_employees(session_id, domain)
    #employees = load_employees_from_csv()  
    merged_ips = fetch_ips(session_id, domain, country, company)
    domains = fetch_domains(session_id, domain, merged_ips)
    dkimdmarc = fetch_dkim_dmarc(session_id, domains)

    # Store the data in the session
    progress["task"] = "Finalizing data..."
    session['domain'] = domain
    session['country'] = country
    session['company'] = company

    session['emails'] = emails
    session['employees'] = employees
    session['ips'] = merged_ips
    session['domains'] = domains
    session['dkimdmarc'] = dkimdmarc

    # Finalize progress
    progress["task"] = "Data loading complete."
    progress["value"] = 100  # Step 5: Data loading complete

    # Return a success response
    return jsonify({"message": "Data loaded successfully"})

# ---------------------------
# update progress bar route
# ---------------------------
@app.route('/progress', methods=['GET'])
def get_progress():
    global progress
    return jsonify(progress)

# ------------------------------
# DATA html route
# ------------------------------
@app.route('/data')
def data():
    # Use session data to render the template
    return render_template(
        'data.html',
        domain=session.get('domain', ''),
        country=session.get('country', ''),
        company=session.get('company', ''),
        emails=session.get('emails', []),
        employees=session.get('employees', []),
        ips=session.get('ips', []),
        domains=session.get('domains', []),
        dkimdmarc=session.get('dkimdmarc', []),
    )



# ------------------------------
# Emails html and Emails export routes
# ------------------------------
@app.route('/emails')
def emails():
    emails = session.get('emails', [])
    email_count = len(emails)  # Count the number of emails
    return render_template('emails.html', emails=emails, email_count=email_count)

@app.route('/export_emails')
def export_emails():
    domain = session.get('domain', '')
    emails = session.get('emails', [])
    # Create a CSV response
    def generate():
        yield "Email Address\n"  # Header row
        for email in emails:
            yield f"{email}\n"  # Each email as a new row
    # Return the response as a CSV file
    return Response(
        generate(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment; filename=emails_{domain}.csv"})


# ------------------------------
# Employees html and Employees export routes
# ------------------------------
@app.route('/employees')
def employees():
    # Render the table for employees
    employees = session.get('employees', [])
    employees_count = len(employees)  # Count the number of employees
    return render_template('employees.html', employees=employees, employees_count=employees_count)


@app.route('/export_employees')
def export_employees():
    employees = session.get('employees', [])
    
    # Ensure the data is structured as a list of tuples
    if not employees:
        return "No employee data available to export.", 400

    # Create a CSV response
    def generate():
        output = StringIO() # Create a StringIO object to write CSV data
        writer = csv.writer(output) # Create a CSV writer object
        
        # Write the header row
        writer.writerow(["Name", "Role", "Username1", "Username2", "Username3"])
        yield output.getvalue() # Sends the current content of the output object to the client.
        output.seek(0) # Move the cursor to the beginning of the StringIO object
        output.truncate(0)# Clear the StringIO object for the next write
        
        # Write each employee's data
        for employee in employees:
            writer.writerow(employee) # Write the employee data as a new row
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    # Return the response as a CSV file
    return Response(
        generate(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=employees.csv"}
    )




# ------------------------------
# IPS html and IPS export routes
# ------------------------------
@app.route('/ips')
def ips():
    # Render the table for ips
    ips = session.get('ips', [])
    ips_count = len(ips)
    return render_template('ips.html', ips=ips, ips_count=ips_count)

@app.route('/export_ips')
def export_ips():
    ips = session.get('ips', [])
    
    # Ensure there is data to export
    if not ips:
        return "No IP data available to export.", 400

    # Create a CSV response
    def generate():
        output = StringIO()  # Create a StringIO object to write CSV data
        writer = csv.writer(output)  # Create a CSV writer object
        
        # Write the header row
        writer.writerow(["IP", "Port", "Vulnerabilities", "Country", "City", "Domains", "Hostnames", "Mnt-By", "Abuse Mailbox"])
        yield output.getvalue()  # Send the current content of the output object to the client
        output.seek(0)  # Move the cursor to the beginning of the StringIO object
        output.truncate(0)  # Clear the StringIO object for the next write
        
        # Write each IP's data
        for ip_data in ips:
            # Ensure domains and hostnames are lists before joining
            domains = ip_data.get("domains", [])
            if isinstance(domains, str):  # If it's a string, convert it to a single-item list
                domains = [domains]
            elif not isinstance(domains, list):  # If it's not a list, set it to an empty list
                domains = []

            hostnames = ip_data.get("hostnames", [])
            if isinstance(hostnames, str):  # If it's a string, convert it to a single-item list
                hostnames = [hostnames]
            elif not isinstance(hostnames, list):  # If it's not a list, set it to an empty list
                hostnames = []

            # Write the row to the CSV
            writer.writerow([
                ip_data.get("ip_str", ""),
                ip_data.get("port", ""),
                ip_data.get("vulns", ""),
                ip_data.get("country_name", ""),
                ip_data.get("city", ""),
                ", ".join(domains),  # Join domains list into a string
                ", ".join(hostnames),  # Join hostnames list into a string
                ip_data.get("mnt_by", ""),
                ip_data.get("abuse_mailbox", "")
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    # Return the response as a CSV file
    return Response(
        generate(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=ips.csv"}
    )

# ------------------------------
# Domains html and Domains export routes
# ------------------------------
@app.route('/domains')
def domains():
    # Render the table for domains
    domains = session.get('domains', [])
    domains_count = len(domains)  # Count the number of domains
    return render_template('domains.html', domains=domains, domains_count=domains_count)

@app.route('/export_domains')
def export_domains():
    domains = session.get('domains', [])
    
    # Ensure there is data to export
    if not domains:
        return "No domain data available to export.", 400

    # Create a CSV response
    def generate():
        yield "Domain Name\n"  # Header row
        for domain in domains:
            yield f"{domain}\n"  # Write only the domain name

    # Return the response as a CSV file
    return Response(
        generate(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=domains.csv"}
    )

# ------------------------------
# Dkim Dmarc html and export routes
# ------------------------------
@app.route('/dkimdmarc')
def dkimdmarc():
    # Retrieve DKIM/DMARC data from the session
    dkimdmarc = session.get('dkimdmarc', [])
    dkimdmarc_count = len(dkimdmarc)  # Count the number of DKIM/DMARC records
    return render_template('dkimdmarc.html', dkimdmarc=dkimdmarc, dkimdmarc_count=dkimdmarc_count)


@app.route('/export_dkimdmarc')
def export_dkimdmarc():
    dkimdmarc = session.get('dkimdmarc', [])
    
    # Ensure there is data to export
    if not dkimdmarc:
        return "No DKIM/DMARC data available to export.", 400

    # Create a CSV response
    def generate():
        # Write the header row
        yield "Domain,SPF,DMARC,DMARC Policy,DKIM,DKIM Status\n"
        
        # Write each record
        for record in dkimdmarc:
            yield f"{record.get('domain', '')}," \
                  f"{record.get('SPF', '')}," \
                  f"{record.get('DMARC', '')}," \
                  f"{record.get('DMARC Policy', '')}," \
                  f"{record.get('DKIM', '')}," \
                  f"{record.get('DKIM Status', '')}\n"

    # Return the response as a CSV file
    return Response(
        generate(),
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment; filename=dkimdmarc.csv"}
    )



# ------------------------------
# Helper Functions
# ------------------------------

def fetch_emails(session_id, domain, company):
    progress["task"] = "Fetching emails..."
    if is_canceled(session_id):
        handle_cancellation("email fetching")
        return []

    # Simulate fetching emails (replace with actual logic)
    emails = googleAndGithub.getEmails(["@" + domain, company])
    #emails = []
    progress["value"] = 10  # Step 2: Fetching emails
    return emails

def fetch_employees(session_id, domain):
    progress["task"] = "Fetching Employees..."
    if is_canceled(session_id):
        handle_cancellation("employees fetching")
        return []

    # Simulate fetching employees
    employees = linkedin.execute_linkedin(domain)
    for i in range(5):  # Simulate 5 steps of employee fetching
        time.sleep(1)  # Simulate delay for each step
        progress["value"] += 10  # Increment progress for each step
    return employees


def fetch_ips(session_id, domain, country, company):
    progress["task"] = "Fetching IPs..."
    if is_canceled(session_id):
        handle_cancellation("IPs fetching")
        return []

    # Fetch IPs from both sources
    dataForIpAndDomains = nDBtoS.execute_networksdb_to_shodan(country, company)
    shodan_ips = dataForIpAndDomains
    whois_ips = whois.getipsWithFields(domain)
    merged_ips = dataLoadingIPs(shodan_ips, whois_ips)
    progress["value"] = 70  # Step 4: Fetching IPs
    return merged_ips

def fetch_domains(session_id, domain, merged_ips):
    progress["task"] = "Fetching domains..."
    if is_canceled(session_id):
        handle_cancellation("domains fetching")
        return []

    # Fetch domains from WHOIS and NetworksDB
    domainsWhois = whois.fetch_subdomains(domain)
    domainsNetworksDB = merged_ips
    domains = merge_domains(domainsWhois, domainsNetworksDB)

    # Limit the number of domains to avoid exceeding the session size limit
    max_domains = 500
    domains = domains[:max_domains]
    progress["value"] = 80  # Step 5: Fetching Domains
    return domains

def fetch_dkim_dmarc(session_id, domains):
    progress["task"] = "Fetching DKIM/DMARC records..."
    if is_canceled(session_id):
        handle_cancellation("DKIM/DMARC fetching")
        return []

    # Fetch DKIM and DMARC records
    dkimdmarc = loadingDkimDmarc(domains)
    progress["value"] = 90  # Step 6: Fetching DKIM DMARC RECORDS
    return dkimdmarc


def handle_cancellation(task_name):
    print(f"Process canceled during {task_name}.")
    progress["task"] = "Process canceled."



def load_employees_from_csv(file_path="employees.csv"):
    """
    Load employees temporarily from a CSV file.
    """
    employees = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Ensure the row contains the expected fields
                employees.append((
                    row.get("Name", ""),
                    row.get("Role", ""),
                    row.get("Username1", ""),
                    row.get("Username2", ""),
                    row.get("Username3", "")
                ))
        print(f"Loaded {len(employees)} employees from {file_path}.")
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"Error loading employees from {file_path}: {e}")
    return employees



def dataLoadingIPs(shodan_ips, whois_ips):
    # Combine the two lists and ensure uniqueness based on the IP field
    merged_ips_dict = {}
    if not shodan_ips:
        print("No Shodan IPs to process.")  # Debug message
        if not whois_ips:
            print("No WHOIS IPs to process.")
            return []
        else:
            for whois_data in whois_ips:
                ip = whois_data["IP"]
                merged_ips_dict[ip] = {
                                "ip_str": ip,
                                "port": "",  # Placeholder for Shodan data
                                "vulns": "",  # Placeholder for Shodan data
                                "country_name": whois_data.get("Country", ""),
                                "city": "",  # Placeholder for Shodan data
                                "domains": whois_data.get("Domain", ""),  # Placeholder for Shodan data
                                "hostnames": "",  # Placeholder for Shodan data
                                "mnt_by": whois_data.get("Mnt-By", ""),
                                "abuse_mailbox": whois_data.get("Abuse Mailbox", "")
                            }
    else:
        # Add Shodan IPs to the dictionary
        for ip_data in shodan_ips:
            ip_str = ip_data.get("ip_str")  # Use .get() to avoid KeyError
            merged_ips_dict[ip_str] = {
                "ip_str": ip_str,
                "port": ip_data.get("port", ""),
                "vulns": ip_data.get("vulns", ""),
                "country_name": ip_data.get("country_name", ""),
                "city": ip_data.get("city", ""),
                "domains": ip_data.get("domains",""),
                "hostnames": ip_data.get("hostnames", ""),
                "mnt_by": "",  # Placeholder for WHOIS data
                "abuse_mailbox": ""  # Placeholder for WHOIS data
            }
            # Add WHOIS IPs to the dictionary (update or add new entries)
            for whois_data in whois_ips:
                ip = whois_data["IP"]
                if ip in merged_ips_dict:
                    # Update existing entry with WHOIS data
                    merged_ips_dict[ip]["mnt_by"] = whois_data.get("Mnt-By", "")
                    merged_ips_dict[ip]["abuse_mailbox"] = whois_data.get("Abuse Mailbox", "")
                else:
                    # Add new entry if IP is not already in the dictionary
                    merged_ips_dict[ip] = {
                        "ip_str": ip,
                        "port": "",  # Placeholder for Shodan data
                        "vulns": "",  # Placeholder for Shodan data
                        "country_name": whois_data.get("Country", ""),
                        "city": "",  # Placeholder for Shodan data
                        "domains": whois_data.get("Domain", ""),  # Placeholder for Shodan data
                        "hostnames": "",  # Placeholder for Shodan data
                        "mnt_by": whois_data.get("Mnt-By", ""),
                        "abuse_mailbox": whois_data.get("Abuse Mailbox", "")
                    }

    # Convert the dictionary back to a list
    return list(merged_ips_dict.values())



def dataLoadingEmails():
    # Example data loading function (replace with actual logic)
    data = github.getEmails() 
    data.extend(google.getEmails())
    return data

# Merge domainsWhois (set) with domains and hostnames from domainsNetworksDB (dict)
def merge_domains(domainsWhois, domainsNetworksDB):
    # Ensure domainsWhois is a set
    if not isinstance(domainsWhois, set):
        domainsWhois = set(domainsWhois)

    # Extract domains and hostnames from domainsNetworksDB
    extracted_domains = set()
    for entry in domainsNetworksDB:
        # Extract domains
        if "domains" in entry and isinstance(entry["domains"], str):
            extracted_domains.update(domain.strip() for domain in entry["domains"].split(", ") if domain.strip())

        # Extract hostnames
        if "hostnames" in entry and isinstance(entry["hostnames"], str):
            extracted_domains.update(hostname.strip() for hostname in entry["hostnames"].split(", ") if hostname.strip())

    # Merge the extracted domains and hostnames into domainsWhois
    domainsWhois.update(extracted_domains)

    # Convert the set back to a list and filter out empty entries
    return [domain for domain in domainsWhois if domain.strip()]


def fetch_dkim_dmarc_for_domain(domain):
    """
    Fetch DKIM/DMARC records for a single domain and extract specific keys.
    """
    try:
        # Fetch DNS records for the domain
        records = dkim_dmarc.fetch_dns_records(domain)
        print(f"Fetched records for {domain}: {records}")  # Debug statement

        # Keys to extract
        keys_to_extract = ["SPF", "DMARC", "DMARC Policy", "DKIM", "DKIM Status"]

        # Extract only the specified keys
        extracted_records = {key: records.get(key, "") for key in keys_to_extract}

        # Add the domain to the extracted records
        extracted_records["domain"] = domain

        return extracted_records
    except Exception as e:
        print(f"Error fetching DKIM/DMARC records for {domain}: {e}")
        return {"domain": domain, "error": str(e)}  # Return an error message if an exception occurs



def loadingDkimDmarc(domains):
    """
    Fetch DKIM/DMARC records for a list of domains using threads.
    """
    dkimdmarc = []  # Initialize an empty list to store DKIM/DMARC records
    max_threads = 10  # Set the maximum number of threads

    # Use ThreadPoolExecutor to fetch records concurrently
    with ThreadPoolExecutor(max_threads) as executor:
        # Submit tasks for each domain
        future_to_domain = {executor.submit(fetch_dkim_dmarc_for_domain, domain): domain for domain in domains}

        # Process completed tasks
        for future in as_completed(future_to_domain):
            try:
                # Append the result (a dictionary) to the list
                result = future.result()
                print(f"Fetched result for domain {future_to_domain[future]}: {result}")  # Debug statement
                dkimdmarc.append(result)
            except Exception as e:
                print(f"Error processing domain {future_to_domain[future]}: {e}")

    return dkimdmarc  # Return the list of DKIM/DMARC records



def is_canceled(session_id):
    return cancellation_flags.get(session_id, False)


# ------------------------------
# open browser function
# ------------------------------
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")


# ------------------------------
# Main Entry Point
# ------------------------------
if __name__ == "__main__":
    import os

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, open_browser).start()

    app.run(debug=True)


