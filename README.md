# ![OsinTech](Static/images/logo.png) 

**OsinTech** is an open-source intelligence (OSINT) tool designed to help cybersecurity professionals, ethical hackers, and investigators gather, analyze, and visualize publicly available information about individuals, companies, and domains.

## 🌐 About the Project

OsinTech automates the process of collecting data from multiple public sources to provide deep insights with minimal effort. It's built to be modular, efficient, and adaptable to various investigation needs—whether you're researching a company's digital footprint or assessing potential threats.

## ⚙️ Features

- Domain & Subdomain scanning
- Company technology stack detection
- Leaked credentials search (via GitHub Dorks)
- WHOIS and DNS record analysis
- TLS/SSL certificate inspection
- Shodan integration for port and service scanning
- LinkedIn scraping for employee metadata
- Visual reports and exportable results

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


##⚠️ Disclaimer
This tool is intended only for educational and ethical purposes.
Unauthorized use of OsinTech against targets without explicit consent may be illegal and is strictly discouraged.

OsinTech/
├── core/              # Core scanning and OSINT modules
│   ├── domain_scan.py
│   ├── github_dorks.py
│   └── ...  
├── utils/             # Helper functions and configuration
│   ├── config.py
│   └── logger.py
├── reports/           # Generated reports (JSON, HTML, CSV, etc.)
├── data/              # Cached or temporary data
├── osintech.py        # Main application script
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation

