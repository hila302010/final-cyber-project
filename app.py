from flask import Flask, render_template, request, jsonify
import Scripts.DNS.DkimDmarc as dkim_dmarc  # your custom script
import Scripts.networksDBtoShodan.shodanAPI as shodanAPI
import Scripts.networksDBtoShodan.networksDBtoShodan as nDBtoS 
import Scripts.githubAndGoogleDorks.googleDorks   as google
import Scripts.githubAndGoogleDorks.github_api as github
import Scripts.socialNetworkServices.linkedin as linkedin
from flask import Response
from flask import session
from flask import redirect, url_for
import webbrowser
import threading
import os
import secrets
import time  # Add this import at the top of your file


app = Flask(__name__)
app.secret_key = str(secrets.token_hex(32)) # Replace with a secure random key



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/load_data', methods=['POST'])
def load_data():
    # Parse the JSON data from the AJAX request
    data = request.get_json()
    domain = data.get('domain')
    country = data.get('country')
    company = data.get('company')

    # Call your Python logic here
    emails = dataLoadingEmails()
    employees = linkedin.execute_linkedin(domain)

    # Store the data in the session
    session['domain'] = domain
    session['country'] = country
    session['company'] = company
    session['emails'] = emails
    session['employees'] = employees

    # Return a success response
    return jsonify({"message": "Data loaded successfully"})




def dataLoadingEmails():
    # Example data loading function (replace with actual logic)
    data = github.getEmails() 
    data.extend(google.getEmails())
    return data


@app.route('/data')
def data():
    # Use session data to render the template
    return render_template(
        'data.html',
        domain=session.get('domain', ''),
        country=session.get('country', ''),
        company=session.get('company', ''),
        emails=session.get('emails', []),
        employees=session.get('employees', [])
    )


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

@app.route('/export_employees')
def export_employees():
    domain = session.get('domain', '')
    employees = session.get('employees', [])
    # Create a CSV response
    def generate():
        # Header row
        yield "Employee Name,Role,Username1,Username2,Username3\n"
        for employee in employees:
            # each employee is a list that has 'name', 'role', 'username1', 'username2', 'username3' 
            yield f"{employee[0]},{employee[1]},{employee[2]},{employee[3]},{employee[4]}\n"
    # Return the response as a CSV file
    return Response(
        generate(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment; filename=employees_{domain}.csv"})


    
@app.route('/employees')
def employees():
    # Render the table for employees
    return render_template('employees.html', employees = session.get('employees', []))



def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    import os

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, open_browser).start()

    app.run(debug=True)


