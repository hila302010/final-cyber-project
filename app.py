from flask import Flask, render_template, request, jsonify
import Scripts.DNS.DkimDmarc as dkim_dmarc  # your custom script
import Scripts.networksDBtoShodan.shodanAPI as shodanAPI
import Scripts.networksDBtoShodan.networksDBtoShodan as nDBtoS 
import Scripts.githubAndGoogleDorks.googleDorks   as google
import Scripts.githubAndGoogleDorks.github_api as github
from flask import Response
from flask import session
from flask import redirect, url_for
import webbrowser
import threading
import os
import secrets


app = Flask(__name__)
app.secret_key = str(secrets.token_hex(32)) # Replace with a secure random key



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():

    domain = request.form['domain']
    country = request.form['country']
    company = request.form['company']
    
    # Call your Python logic here
    #result = dkim_dmarc.fetch_dns_records(domain)
    #data = nDBtoS.execute_networksdb_to_shodan(country, company)
    #print("result", data)
    
    emails = dataLoading()

    # Example data (replace with actual logic to fetch data)
    session['domain'] = domain
    session['country'] = country
    session['company'] = company
    session['emails'] = emails

    
    # Redirect to the /data route
    return redirect(url_for('data'))


def dataLoading():
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



def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    import os

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, open_browser).start()

    app.run(debug=True)


