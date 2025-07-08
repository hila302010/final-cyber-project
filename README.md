# 🕵️‍♀️ OsinTech

**OsinTech** is an open-source intelligence (OSINT) tool designed to help cybersecurity professionals, ethical hackers, and investigators gather, analyze, and visualize publicly available information about individuals, companies, and domains.

## 🌐 About the Project

OsinTech automates the process of collecting data from multiple public sources to provide deep insights with minimal effort. It's built to be modular, efficient, and adaptable to various investigation needs—whether you're researching a company's digital footprint or assessing potential threats.

## ⚙️ Features

- 🔍 Domain & Subdomain scanning
- 🧠 Company technology stack detection
- 🧾 Leaked credentials search (via GitHub Dorks)
- 🌐 WHOIS and DNS record analysis
- 🔐 TLS/SSL certificate inspection
- 🛰️ Shodan integration for port and service scanning
- 🧑‍💼 LinkedIn scraping for employee metadata
- 📊 Visual reports and exportable results

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Git
- Virtualenv (recommended)

### Installation

```bash
git clone https://github.com/your-username/OsinTech.git
cd OsinTech
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
