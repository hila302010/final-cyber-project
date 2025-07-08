# <p align="center"><img src="static/images/osintech.png" width="200"/></p> 

# <p align="center"><img src="static/images/welcomeReadme.png"/></p> 
## Welcome to OsinTech
<p class="large-text" style="color: #43c0ce;">Welcome to OsinTech!</p> 

<p class="small-text">
At OsinTech, we harness the power of Open Source Intelligence (OSINT) to collect and analyze publicly available data about a target domain name, company name, and country.
</p> 

<p class="small-text">
Our custom-built Python scripts integrate with leading tools like Shodan, WHOIS, and NetworksDB to extract technical infrastructure data. We also leverage LinkedIn to gather human intelligence, and use GitHub and Google Dorks to uncover code repositories and exposed components linked to the organization.
</p> 

<p class="small-text">
All collected data is compiled into a detailed report, providing insights into your digital footprint, exposures, vulnerabilities, and recommendations.
Whether you're a cybersecurity professional, researcher, or analyst, OsinTech empowers you with actionable intelligence to assess and reduce online risks to your organization.
</p> 

# <p align="center"><img src="static/images/workflow.png"/></p> 

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

