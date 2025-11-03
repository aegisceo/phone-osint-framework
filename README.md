# Phone OSINT Investigation Framework

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Defensive Security](https://img.shields.io/badge/Use-Defensive_Security-green.svg)]()

Professional-grade phone number intelligence platform implementing **breach-first discovery architecture**. 
Searches breach databases by phone+name to discover verified emails/usernames, then enriches with TruePeopleSearch, 
social media, and employment intelligence.

> **Warning**: This tool is for authorized security testing, defensive investigations, and educational purposes only. 
> Always obtain proper authorization before investigating phone numbers.

---

## Key Features

### Breach-First Discovery
- Search DeHashed/LeakCheck/HIBP by **phone+name** (no emails required!)
- Discover verified emails, usernames, addresses from breach records
- High confidence matches (phone+name in same breach record = verified)
- Foundation for all downstream intelligence gathering

### Conditional Intelligence Gathering
- **Smart Mode** (2+ verified emails): Skip pattern generation, keep profile scraping
- **Full Mode** (<2 verified emails): Run comprehensive enumeration
- Intelligent decision-making based on available data quality

### Comprehensive OSINT
- **Name Discovery**: Twilio Caller ID + NumVerify
- **Breach Search**: DeHashed (phone/name/email/username) + LeakCheck + HIBP
- **People Search**: TruePeopleSearch (free, CAPTCHA-enabled)
- **Email Discovery**: LinkedIn, GitHub, theHarvester, Holehe
- **Username Enumeration**: Sherlock (400+ sites), Maigret (2500+ sites)
- **Social Media**: 7 platforms (Facebook, Twitter, Instagram, LinkedIn, GitHub, Telegram, WhatsApp)
- **Employment**: Company/domain discovery
- **Risk Assessment**: Multi-factor scoring

### Professional Reporting
- **Modern Dashboard**: Interactive HTML with Chart.js visualizations
- **Classic Report**: Comprehensive data tables
- **Collapsible Sections**: Easy navigation
- **Stat Cards**: Quick overview metrics

---

## Quick Start

### Installation
```bash
# Clone repository
git clone <your-repo-url>
cd phone-osint-framework

# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp config/.env.example config/.env
# Edit config/.env with your API keys
```

### Run Investigation
```bash
# Command line
python phone_osint_master.py +16199303063

# Web interface
python web_interface.py
# Then open http://localhost:5000 in browser
```

### View Results
```bash
cd results/<timestamp>_<phone>/
# Open investigation_report.html in browser
```

---

## API Requirements

### Essential (Required):
- **NumVerify** - Phone validation and carrier lookup
- **Google Custom Search** - Advanced dorking capabilities

### Highly Recommended:
- **Twilio** - Caller ID and name discovery (THE GRAIL!)
- **Have I Been Pwned** - Email breach checking
- **DeHashed** - Multi-parameter breach search (phone/name/email/username)
- **SerpAPI** - Enhanced search with higher limits

### Optional (Enhanced Results):
- **Hunter.io** - Email discovery and verification
- **Shodan** - Internet device search
- **LeakCheck** - Additional breach database
- **Intelligence X** - Dark web monitoring
- **IPRoyal** - Residential/mobile proxies

See `docs/API_SETUP.md` for detailed configuration instructions.

---

## Investigation Flow

```
1. Phone Validation
   └─ Carrier, location, line type (NumVerify + Twilio)

2. Name Hunting
   └─ Discover primary name (Twilio Caller ID)

3. BREACH DISCOVERY (The Key!)
   └─ Search DeHashed/LeakCheck by phone+name
   └─ Discover VERIFIED emails, usernames, addresses
   └─ High confidence (data from same breach record)

4. TruePeopleSearch Enrichment
   └─ Free people search (addresses, associates, relatives, age)

5. Email Discovery - CONDITIONAL
   └─ 2+ verified emails: SMART MODE (skip patterns, keep profiles)
   └─ <2 verified emails: FULL MODE (comprehensive enumeration)

6. Employment, Social Media, Risk Assessment
   └─ Use all verified data for targeted searches

7. Report Generation
   └─ Modern dashboard + Classic report
```

---

## Performance

| Scenario | Time | Data Quality | Confidence |
|----------|------|--------------|------------|
| **With Breach Data** (2+ emails) | 3-5 min | 80% verified | 0.8-0.95 |
| **Without Breach Data** (<2 emails) | 8-12 min | 30% verified | 0.3-0.7 |

**Smart Mode Benefits**:
- 50-70% faster investigations
- Higher confidence scores
- No wasted pattern generation
- Still gets intelligence from LinkedIn/GitHub/Sherlock

---

## Dependencies

### Core Python Packages:
- requests, beautifulsoup4, selenium, phonenumbers
- twilio, google-api-python-client
- flask, jinja2
- python-dotenv, pyyaml

### Optional OSINT Tools:
- **Maigret** - 2500+ platform username search
- **PhoneInfoga** - Additional phone intelligence
- **Sherlock** - Included in framework

### System Requirements:
- Python 3.8 or higher
- Chrome/Chromium browser (for TruePeopleSearch)
- 2GB+ RAM recommended
- Internet connection

---

## Documentation

- **Installation Guide**: `docs/INSTALLATION.md`
- **API Setup**: `docs/API_SETUP.md`
- **Breach Search**: `docs/COMPREHENSIVE_BREACH_SEARCH.md`
- **TruePeopleSearch**: `docs/TRUEPEOPLESEARCH_SETUP.md`
- **IPRoyal Proxies**: `docs/IPROYAL_SETUP.md`
- **Social Media OSINT**: `docs/SOCIAL_MEDIA.md`
- **Troubleshooting**: `docs/TROUBLESHOOTING.md`
- **Current Status**: `CURRENT_STATUS.md`
- **Best Practices**: `CLAUDE.md`

---

## Testing

### Test All APIs:
```bash
python test_apis.py
```

### Test Breach APIs:
```bash
python test_breach_apis_direct.py
```

### Run Sample Investigation:
```bash
python phone_osint_master.py +16199303063
```

---

## Security

### Never Commit:
- `config/.env` (API keys and secrets)
- `results/` (investigation data with PII)
- `.google-cookie` (authentication tokens)
- Any files with personal/sensitive data

### Before Public Sharing:
- Rotate all API keys
- Clear results directory
- Review git history for secrets
- Test with dummy data only

---

## Recent Updates (v2.0 - November 2025)

### Major Features:
- ✅ Breach-first discovery architecture
- ✅ DeHashed integration (multi-parameter search)
- ✅ TruePeopleSearch integration (free people search)
- ✅ Conditional email discovery (smart vs full mode)
- ✅ Modern dashboard reports with visualizations
- ✅ Maigret integration (2500+ platforms)
- ✅ IPRoyal proxy support

### Bug Fixes:
- ✅ Fixed email data loss bug
- ✅ Fixed breach search early exit
- ✅ Fixed Sherlock integration errors
- ✅ Fixed Modern Report crashes
- ✅ Fixed ChromeDriver cleanup issues
- ✅ Fixed HIBP and DeHashed API integrations

See `CHANGELOG.md` for complete version history.

---

## Contributing

Contributions welcome! Please see `CONTRIBUTING.md` for guidelines.

---

## License

MIT License - See `LICENSE` file for details.

---

## Disclaimer

This framework is intended for:
- Defensive security investigations
- Authorized penetration testing
- Educational and research purposes
- Legal compliance verification

**Not intended for**:
- Unauthorized surveillance
- Harassment or stalking
- Privacy violations
- Illegal activities

Users are responsible for ensuring their use complies with all applicable laws and regulations (GDPR, CCPA, etc.).

---

**Status**: Production Ready | **Version**: 2.0 | **Last Updated**: November 2025

For detailed status and architecture, see `CURRENT_STATUS.md`.
