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
import threading
from io import StringIO
import json
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


from datetime import datetime


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
redis_client = redis.Redis(host='localhost', port=6379, db=0)
# Initialize session
Session(app)



# A dictionary to track cancellation flags for each session or process
cancellation_flags = {}
# Simulated progress variable
# If status is 1, it means the process is running
# If status is 0, it means the process is finished
progress = {"value": 0, "task": "Initializing...", "status": 1}



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
    global progress
    progress["status"] = 1  # Set status to running
    session_id = request.json.get('session_id')
    if not session_id:
        return {"error": "Session ID is required."}, 400

    # Reset the cancellation flag for this session
    cancellation_flags[session_id] = False

    session['session_id'] = session_id

    # Parse the JSON data from the AJAX request
    data = request.get_json()
    domain = data.get('domain')
    country = data.get('country')
    company = data.get('company')

    session['domain'] = domain
    session['country'] = country
    session['company'] = company

    progress["value"] = 0  # Reset progress
    progress["task"] = "Parsing input data..."  # Update task description

    emails = employees = merged_ips = domains = dkimdmarc = None
    
    # Thread completion tracking
    completed_threads = {"count": 0}
    thread_lock = threading.Lock()

    def check_all_threads_complete():
        """Check if all threads are complete and finalize the process"""
        with thread_lock:
            completed_threads["count"] += 1
            if completed_threads["count"] == 3:  # All 3 threads completed
                # Set progress to 100% and mark as finished
                progress["value"] = 100
                progress["task"] = "Data loading complete."
                progress["status"] = 0  # Mark the process as finished
                # Save completion time ONLY when ALL threads are done
                redis_client.set(f"{session_id}_completion_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def fetch_emails_thread():
        nonlocal emails
        # time.sleep(20)  # Simulate a slow operation
        # emails = load_emails_from_csv()  # Load emails from CSV for testing
        emails = fetch_emails(session_id, domain)
        redis_client.set(f"{session_id}_emails", json.dumps(emails))
        check_all_threads_complete()  # Check if this is the last thread

    def fetch_employees_thread():
        nonlocal employees
        time.sleep(30)  # Simulate a slower operation
        employees = load_employees_from_csv()  # Load employees from CSV for testing
        #employees = fetch_employees(session_id, domain)
        redis_client.set(f"{session_id}_employees", json.dumps(employees))
        check_all_threads_complete()  # Check if this is the last thread

    def fetch_ips_domains_dkim_thread():
        nonlocal merged_ips, domains, dkimdmarc
        time.sleep(20)  # Simulate the slowest operation
        merged_ips = load_ips_from_csv()
        time.sleep(20)  # Simulate the slowest operation
        domains = load_domains_from_csv()
        time.sleep(20)  # Simulate the slowest operation
        dkimdmarc = load_dkim_dmarc_from_csv()
        # merged_ips = fetch_ips(session_id, domain, country, company)
        # domains = fetch_domains(session_id, domain, merged_ips)
        # dkimdmarc = fetch_dkim_dmarc(session_id, domains)
        redis_client.set(f"{session_id}_ips", json.dumps(merged_ips))
        redis_client.set(f"{session_id}_domains", json.dumps(domains))
        redis_client.set(f"{session_id}_dkimdmarc", json.dumps(dkimdmarc))
        check_all_threads_complete()  # Check if this is the last thread

    # Create threads
    t1 = threading.Thread(target=fetch_emails_thread)
    t2 = threading.Thread(target=fetch_employees_thread)
    t3 = threading.Thread(target=fetch_ips_domains_dkim_thread)

    # Start threads
    t1.start()
    t2.start()
    t3.start()

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
    # Get session data
    session_id = session.get('session_id')
    emails = json.loads(redis_client.get(f"{session_id}_emails") or "[]")
    ips = json.loads(redis_client.get(f"{session_id}_ips") or "[]")
    employees = json.loads(redis_client.get(f"{session_id}_employees") or "[]")
    domains = json.loads(redis_client.get(f"{session_id}_domains") or "[]")
    dkimdmarc = json.loads(redis_client.get(f"{session_id}_dkimdmarc") or "[]")

    # Count the number of emails, IPs, and employees
    email_count = len(emails)
    ips_count = len(ips)
    employees_count = len(employees)
    domains_count = len(domains)
    #shaked added- 25.5
    current_time = get_current_time()

    # Pass counts along with other session data to the template
    return render_template(
        'data.html',
        domain=session.get('domain', ''),
        country=session.get('country', ''),
        company=session.get('company', ''),
        emails=emails,
        employees=employees,
        ips=ips,
        domains=domains,
        dkimdmarc=dkimdmarc,
        email_count=email_count,          # Pass email count
        ips_count=ips_count,              # Pass IPs count
        employees_count=employees_count, # Pass employees count
        domains_count=domains_count,       # Pass domains count
        current_time=current_time # Pass the current time   
    )

def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.route('/data_json')
def data_json():
    session_id = session.get('session_id')
    emails = json.loads(redis_client.get(f"{session_id}_emails") or "[]")
    ips = json.loads(redis_client.get(f"{session_id}_ips") or "[]")
    employees = json.loads(redis_client.get(f"{session_id}_employees") or "[]")
    domains = json.loads(redis_client.get(f"{session_id}_domains") or "[]")
    dkimdmarc = json.loads(redis_client.get(f"{session_id}_dkimdmarc") or "[]")
    completion_time = redis_client.get(f"{session_id}_completion_time")
    if completion_time:
        completion_time = completion_time.decode("utf-8")
    return jsonify({
        "email_count": len(emails),
        "ips_count": len(ips),
        "employees_count": len(employees),
        "domains_count": len(domains),
        "dkimdmarc": dkimdmarc,
        "ips": ips,
        "completion_time": completion_time  # ✅ Include here
    })


# ------------------------------
# Emails html and Emails export routes
# ------------------------------
@app.route('/emails')
def emails():
    #emails = session.get('emails', [])
    session_id = session.get('session_id')
    emails = json.loads(redis_client.get(f"{session_id}_emails") or "[]")
    email_count = len(emails)  # Count the number of emails
    return render_template('emails.html', emails=emails, email_count=email_count)

@app.route('/export_emails')
def export_emails():
    domain = session.get('domain', '')
    session_id = session.get('session_id')
    emails = json.loads(redis_client.get(f"{session_id}_emails") or "[]")
    # Create a CSV response
    def generate():
        yield "Email Address,Source\n"  # Header row
        for email in emails:
            # email is expected to be a dict: {'email': ..., 'source': ...}
            yield f"{email.get('email', '')},{email.get('source', '')}\n"
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
    session_id = session.get('session_id')
    employees = json.loads(redis_client.get(f"{session_id}_employees") or "[]")
    employees_count = len(employees)  # Count the number of employees
    return render_template('employees.html', employees=employees, employees_count=employees_count)


@app.route('/export_employees')
def export_employees():
    session_id = session.get('session_id')
    employees = json.loads(redis_client.get(f"{session_id}_employees") or "[]")
    
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
    #ips = session.get('ips', [])
    session_id = session.get('session_id')
    ips = json.loads(redis_client.get(f"{session_id}_ips") or "[]")
    ips_count = len(ips)
    return render_template('ips.html', ips=ips, ips_count=ips_count)

@app.route('/export_ips')
def export_ips():
    session_id = session.get('session_id')
    ips = json.loads(redis_client.get(f"{session_id}_ips") or "[]")
    
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
    #domains = session.get('domains', [])
    session_id = session.get('session_id')
    domains = json.loads(redis_client.get(f"{session_id}_domains") or "[]")
    domains_count = len(domains)  # Count the number of domains
    return render_template('domains.html', domains=domains, domains_count=domains_count)

@app.route('/export_domains')
def export_domains():
    session_id = session.get('session_id')
    domains = json.loads(redis_client.get(f"{session_id}_domains") or "[]")
    
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
    #dkimdmarc = session.get('dkimdmarc', [])
    session_id = session.get('session_id')
    dkimdmarc = json.loads(redis_client.get(f"{session_id}_dkimdmarc") or "[]")
    dkimdmarc_count = len(dkimdmarc)  # Count the number of DKIM/DMARC records
    return render_template('dkimdmarc.html', dkimdmarc=dkimdmarc, dkimdmarc_count=dkimdmarc_count)


@app.route('/export_dkimdmarc')
def export_dkimdmarc():
    session_id = session.get('session_id')
    dkimdmarc = json.loads(redis_client.get(f"{session_id}_dkimdmarc") or "[]")
    
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

def fetch_emails(session_id, domain):
    progress["task"] = "Fetching emails..."
    progress["value"] += 10  # Step 2: Fetching emails
    if is_canceled(session_id):
        handle_cancellation("email fetching")
        return []

    # Simulate fetching emails (replace with actual logic)
    emails = googleAndGithub.getEmails(domain)
    progress["value"] += 10  # Step 2: Fetching emails
    progress["task"] = "Done Fetching emails..."
    return emails

def fetch_employees(session_id, domain):
    if is_canceled(session_id):
        handle_cancellation("employees fetching")
        return []
    progress["value"] += 10  # Increment progress 
    progress["task"] = "Fetching Employees..."
    # Simulate fetching employees
    employees = linkedin.execute_linkedin(domain)
    progress["value"] += 10  # Increment progress
    progress["task"] = "Done Fetching Employees..."
 
    return employees


def fetch_ips(session_id, domain, country, company):
    progress["task"] = "Fetching IPs..."
    progress["value"] += 10  # Step 4: Fetching IPs
    if is_canceled(session_id):
        handle_cancellation("IPs fetching")
        return []

    # Fetch IPs from both sources
    dataForIpAndDomains = nDBtoS.execute_networksdb_to_shodan(country, company)
    shodan_ips = dataForIpAndDomains
    whois_ips = whois.getipsWithFields(domain)
    merged_ips = dataLoadingIPs(shodan_ips, whois_ips)
    progress["value"] += 10  # Step 4: Fetching IPs
    progress["task"] = "Done Fetching IPs..."
    return merged_ips

def fetch_domains(session_id, domain, merged_ips):
    progress["task"] = "Fetching domains..."
    progress["value"] += 10  # Step 5: Fetching Domains
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
    progress["value"] += 10  # Step 5: Fetching Domains
    progress["task"] = "Done Fetching domains..."
    return domains

def fetch_dkim_dmarc(session_id, domains):
    progress["task"] = "Fetching DKIM/DMARC records..."
    if is_canceled(session_id):
        handle_cancellation("DKIM/DMARC fetching")
        return []

    progress["value"] += 10  # Step 6: Fetching DKIM DMARC RECORDS
    # Fetch DKIM and DMARC records
    dkimdmarc = loadingDkimDmarc(domains)
    progress["value"] += 10  # Step 6: Fetching DKIM DMARC RECORDS
    progress["task"] = "Done Fetching DKIM/DMARC records..."
    return dkimdmarc


def handle_cancellation(task_name):
    print(f"Process canceled during {task_name}.")
    progress["task"] = "Process canceled."


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

# ------------------------------
# Testing Functions
# ------------------------------


def load_employees_from_csv(file_path="employees.csv"):
    """
    Load employees temporarily from a CSV file.
    """
    progress["task"] = "Fetching employees..."
    progress["value"] += 10  # Step 2: Fetching emails
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
        progress["value"] += 10  # Step 2: Fetching emails

        print(f"Loaded {len(employees)} employees from {file_path}.")
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"Error loading employees from {file_path}: {e}")
    return employees

import csv

def load_emails_from_csv(file_path="emails.csv"):
    """
    Load emails with source from a CSV file.
    Returns a list of dictionaries with 'source' and 'email' keys.
    """
    progress["task"] = "Fetching emails..."
    progress["value"] += 10  # Step 2: Fetching emails
    emails = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                source = row.get("Source", "").strip().lower()
                email = row.get("Email Address", "").strip()
                if source and email:
                    emails.append({'source': source, 'email': email})
        progress["value"] += 10  # Step 2: Fetching emails

        print(f"Loaded {len(emails)} emails from {file_path}.")
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"Error loading emails from {file_path}: {e}")
    return emails


def load_ips_from_csv(file_path="ips.csv"):
    """
    Load IPs temporarily from a CSV file.
    """
    progress["task"] = "Fetching ips..."
    progress["value"] += 10  # Step 2: Fetching emails
    ips = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ips.append({
                    "ip_str": row.get("IP", ""),
                    "port": row.get("Port", ""),
                    "vulns": row.get("Vulnerabilities", ""),
                    "country_name": row.get("Country", ""),
                    "city": row.get("City", ""),
                    "domains": row.get("Domains", ""),
                    "hostnames": row.get("Hostnames", ""),
                    "mnt_by": row.get("Mnt-By", ""),
                    "abuse_mailbox": row.get("Abuse Mailbox", "")
                })
        progress["value"] += 10  # Step 2: Fetching emails

        print(f"Loaded {len(ips)} IPs from {file_path}.")
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"Error loading IPs from {file_path}: {e}")
    return ips


def load_domains_from_csv(file_path="domains.csv"):
    """
    Load domains temporarily from a CSV file.
    """
    progress["task"] = "Fetching domains..."
    progress["value"] += 10  # Step 2: Fetching emails
    domains = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            for row in reader:
                domains.append(row[0])  # Assuming domains are in the first column
        print(f"Loaded {len(domains)} domains from {file_path}.")
        progress["value"] += 10  # Step 2: Fetching emails

    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"Error loading domains from {file_path}: {e}")
    return domains


def load_dkim_dmarc_from_csv(file_path="dkimdmarc.csv"):
    """
    Load DKIM/DMARC records from a CSV file.
    """
    progress["task"] = "Fetching dkim dmarc..."
    progress["value"] += 10  # Step 2: Fetching emails
    dkimdmarc = []
    try:
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Append each row as a dictionary to the list
                dkimdmarc.append({
                    "domain": row.get("Domain", ""),
                    "SPF": row.get("SPF", ""),
                    "DMARC": row.get("DMARC", ""),
                    "DMARC Policy": row.get("DMARC Policy", ""),
                    "DKIM": row.get("DKIM", ""),
                    "DKIM Status": row.get("DKIM Status", "")
                })
        progress["value"] += 10  # Step 2: Fetching emails

        print(f"Loaded {len(dkimdmarc)} DKIM/DMARC records from {file_path}.")
    except FileNotFoundError:
        print(f"File {file_path} not found.")
    except Exception as e:
        print(f"Error loading DKIM/DMARC records from {file_path}: {e}")
    return dkimdmarc

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


    # for testing
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




def is_canceled(session_id):
    return cancellation_flags.get(session_id, False)


# ------------------------------
# open browser function
# ------------------------------
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

#careers.checkmarx.com
# ------------------------------
# Main Entry Point
# ------------------------------
if __name__ == "__main__":
    import os

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, open_browser).start()

    app.run(debug=True)




