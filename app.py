from flask import Flask, render_template, request, jsonify
import Scripts.DNS.DkimDmarc as dkim_dmarc  # your custom script
import Scripts.networksDBtoShodan.shodanAPI as shodanAPI
import Scripts.networksDBtoShodan.networksDBtoShodan as nDBtoS 
import webbrowser
import threading


app = Flask(__name__)

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
    emails = ["helpDesk@bgu.ac.il", "heshbons@bgu.ac.il"]
    ips = ["132.72.124.217", "132.72.118.160"]
    domains = ["bgu.ac.il", "subdomain.bgu.ac.il"]
    employees = ["John Doe - Developer", "Jane Smith - Manager"]
    sensitive_data = ["Password123", "Admin credentials"]


     # Pass the data to the template
    return render_template('data.html', emails=emails, ips=ips, domains=domains, employees=employees, sensitive_data=sensitive_data, domain=domain, country=country, company=company)


@app.route('/data')
def data():
    # Example data (replace with actual logic to fetch data)
    emails = ["helpDesk@bgu.ac.il", "heshbons@bgu.ac.il"]
    ips = ["132.72.124.217", "132.72.118.160"]
    domains = ["bgu.ac.il", "subdomain.bgu.ac.il"]
    employees = ["John Doe - Developer", "Jane Smith - Manager"]
    sensitive_data = ["Password123", "Admin credentials"]

    # Pass the data to the template
    return render_template(
        'data.html',
        emails=emails,
        ips=ips,
        domains=domains,
        employees=employees,
        sensitive_data=sensitive_data
    )

    
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    import os

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, open_browser).start()

    app.run(debug=True)


