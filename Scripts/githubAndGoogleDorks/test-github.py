# test_github.py
import requests

url = "https://api.github.com"

try:
    response = requests.get(url, timeout=10)
    print("Status Code:", response.status_code)
    print("Headers:", response.headers)
except requests.exceptions.RequestException as e:
    print("Connection error:", e)


def load_data():
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

    emails = employees = merged_ips = domains = dkimdmarc = None

    def fetch_emails_thread():
        nonlocal emails
        emails = fetch_emails(session_id, domain)

    def fetch_employees_thread():
        nonlocal employees
        employees = []
        #employees = fetch_employees(session_id, domain)

    def fetch_ips_domains_dkim_thread():
        nonlocal merged_ips, domains, dkimdmarc
        merged_ips = fetch_ips(session_id, domain, country, company)
        domains = fetch_domains(session_id, domain, merged_ips)
        dkimdmarc = fetch_dkim_dmarc(session_id, domains)

    # Create threads
    t1 = threading.Thread(target=fetch_emails_thread)
    t2 = threading.Thread(target=fetch_employees_thread)
    t3 = threading.Thread(target=fetch_ips_domains_dkim_thread)

    # Start threads
    t1.start()
    t2.start()
    t3.start()

    # Wait for all to finish
    t1.join()
    t2.join()
    t3.join()

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