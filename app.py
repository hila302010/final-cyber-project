from flask import Flask, render_template, request, jsonify
from Scripts.extract_data import extract_info  # your custom script
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
    result = extract_info(domain, country, company)
    
    return jsonify(result=result)

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == "__main__":
    import os

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, open_browser).start()

    app.run(debug=True)


