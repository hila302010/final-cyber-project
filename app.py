# ------------------------------
# Imports
# ------------------------------
from flask import Flask, render_template, request, jsonify, Response, session, redirect, url_for
import webbrowser
import threading
import os
import secrets
import time
import csv
from io import StringIO
from flask import jsonify

# Custom scripts
import Scripts.DNS.DkimDmarc as dkim_dmarc
import Scripts.networksDBtoShodan.shodanAPI as shodanAPI
import Scripts.networksDBtoShodan.networksDBtoShodan as nDBtoS
import Scripts.githubAndGoogleDorks.googleDorks as google
import Scripts.githubAndGoogleDorks.github_api as github
import Scripts.socialNetworkServices.linkedin as linkedin
import Scripts.mergedWhois.crtshToIPSToWhois as whois
import Scripts.githubAndGoogleDorks.main as mainGG

# Simulated progress variable
progress = {"value": 0}


# ------------------------------
# Flask App Configuration
# ------------------------------
app = Flask(__name__)
app.secret_key = str(secrets.token_hex(32)) # Replace with a secure random key



# ------------------------------
# Routes
# ------------------------------

@app.route('/')
def index():
    return render_template('index.html')



# ------------------------------------------------------
# loading data from the scripts by the form fields: domain country and company
# ------------------------------------------------------
@app.route('/load_data', methods=['POST'])
def load_data():
    global progress
    progress["value"] = 0  # Reset progress

    # Parse the JSON data from the AJAX request
    data = request.get_json()
    domain = data.get('domain')
    country = data.get('country')
    company = data.get('company')

    # Simulate progress for each step
    progress["value"] = 10  # Step 1: Parsing input data


    # Call your Python logic here
    #emails = dataLoadingEmails()
    #emails = mainGG.getEmails(["@" + domain, company])  # Function to fetch emails from GitHub and Google Dorks
    emails = []
    progress["value"] = 30  # Step 2: Fetching emails

    employees = linkedin.execute_linkedin(domain)
    for i in range(5):  # Simulate 5 steps of employee fetching
        time.sleep(1)  # Simulate delay for each step
        progress["value"] += 10  # Increment progress for each step
    #employees = []
    
    # Fetch IPs from both sources
    #shodan_ips = nDBtoS.execute_networksdb_to_shodan(country, company)
    #whois_ips = whois.getipsWithFields(domain)  # Function to fetch WHOIS data
    #merged_ips = dataLoadingIPs(shodan_ips, whois_ips)  # Function to merge and process IPs
    merged_ips = []
    progress["value"] = 90  # Step 4: Fetching IPs

    # Store the data in the session
    session['domain'] = domain
    session['country'] = country
    session['company'] = company
    session['emails'] = emails
    session['employees'] = employees
    session['ips'] = merged_ips

    progress["value"] = 100  # Step 5: Data loading complete

    # Return a success response
    return jsonify({"message": "Data loaded successfully"})


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
        ips=session.get('ips', [])
    )



# ------------------------------
# Emails html and Emails export routes
# ------------------------------
@app.route('/emails')
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
# Helper Functions
# ------------------------------
def dataLoadingIPs(shodan_ips, whois_ips):
    # Combine the two lists and ensure uniqueness based on the IP field
    merged_ips_dict = {}

    # Add Shodan IPs to the dictionary
    for ip_data in shodan_ips:
        merged_ips_dict[ip_data["ip_str"]] = {
            "ip_str": ip_data["ip_str"],
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


