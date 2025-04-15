from flask import Flask, render_template, request, jsonify
import Scripts.DNS.DkimDmarc as dkim_dmarc  # your custom script
import Scripts.networksDBtoShodan.shodanAPI as shodanAPI
import Scripts.networksDBtoShodan.networksDBtoShodan as nDBtoS 
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


    # Example data (replace with actual logic to fetch data)
    session['domain'] = domain
    session['country'] = country
    session['company'] = company
    session['emails'] = ["helpDesk@bgu.ac.il", "heshbons@bgu.ac.il"]
    session['ips'] = ["132.72.124.217", "132.72.118.160"]
    session['domains'] = ["bgu.ac.il", "subdomain.bgu.ac.il"]
    session['employees'] = ["John Doe - Developer", "Jane Smith - Manager"]
    session['sensitive_data'] = ["Password123", "Admin credentials"]
    
    # Redirect to the /data route
    return redirect(url_for('data'))


@app.route('/data')
def data():
    # Use session data to render the template
    return render_template(
        'data.html',
        domain=session.get('domain', ''),
        country=session.get('country', ''),
        company=session.get('company', ''),
        emails=session.get('emails', []),
        ips=session.get('ips', []),
        domains=session.get('domains', []),
        employees=session.get('employees', []),
        sensitive_data=session.get('sensitive_data', [])
    )
    
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    import os

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, open_browser).start()

    app.run(debug=True)


