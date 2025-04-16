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

# Custom scripts
import Scripts.DNS.DkimDmarc as dkim_dmarc
import Scripts.networksDBtoShodan.shodanAPI as shodanAPI
import Scripts.networksDBtoShodan.networksDBtoShodan as nDBtoS
import Scripts.githubAndGoogleDorks.googleDorks as google
import Scripts.githubAndGoogleDorks.github_api as github
import Scripts.socialNetworkServices.linkedin as linkedin
import Scripts.mergedWhois.crtshToIPSToWhois as whois



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
    # Parse the JSON data from the AJAX request
    data = request.get_json()
    domain = data.get('domain')
    country = data.get('country')
    company = data.get('company')

    # Call your Python logic here
    #emails = dataLoadingEmails()
    emails=[]
    #employees = linkedin.execute_linkedin(domain)
    employees = []
    #ips = whois.getipsWithFields(domain)
    ips = nDBtoS.execute_networksdb_to_shodan(country, company)

    # Store the data in the session
    session['domain'] = domain
    session['country'] = country
    session['company'] = company
    session['emails'] = emails
    session['employees'] = employees
    session['ips'] = ips

    # Return a success response
    return jsonify({"message": "Data loaded successfully"})




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
def emails():
    # Render the table for emails
    return render_template('emails.html', emails = session.get('emails', []))


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


    
@app.route('/employees')
def employees():
    # Render the table for employees
    return render_template('employees.html', employees = session.get('employees', []))



# ------------------------------
# IPS html and IPS export routes
# ------------------------------
@app.route('/ips')
def ips():
    # Render the table for ips
    return render_template('ips.html', ips = session.get('ips', []))


# ------------------------------
# Helper Functions
# ------------------------------

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


