# 📱 Phone Deep (SO DEEP) OSINT Investigation Framework

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Defensive Security](https://img.shields.io/badge/Use%20Case-Defensive%20Security-green.svg)]()
[![Matrix Themed](https://img.shields.io/badge/Interface-Matrix%20Themed-red.svg)]()

A comprehensive, professional-grade phone number investigation framework that combines multiple OSINT tools and techniques with **aggressive name hunting** capabilities. Built with a Matrix-themed web interface for the ultimate cyber investigation experience.

**🎯 THE GRAIL: Our primary focus is extracting the full name of phone number owners through advanced multi-API techniques.**

> ⚠️ **Important**: This tool is designed exclusively for authorized security testing, defensive investigations, and educational purposes. Always obtain proper authorization before investigating phone numbers.

## 🚀 Features

### 🎯 Aggressive Name Hunting (THE GRAIL)
- **🔥 Advanced Twilio Integration**: Leverages caller_name, validation, line_type_intelligence, and identity_match fields
- **💰 Multi-API Name Resolution**: Combines NumVerify and Twilio for maximum name extraction success
- **🎯 Targeted Owner Discovery**: Prioritizes full name extraction as primary investigation objective
- **📊 Enhanced Validation Pipeline**: Comprehensive phone validation with name hunting emphasis

### 🔍 Intelligence Gathering
- **🔍 Multi-Source Intelligence**: Combines 7+ OSINT APIs and tools (NumVerify, Twilio, Google, HIBP, etc.)
- **📊 PhoneInfoga Integration**: Automated phone number format analysis and scanning
- **🕵️ Advanced Google Dorking**: Intelligent search queries with categorization
- **📱 Social Media Discovery**: Cross-platform phone number association checks
- **🔐 Data Breach Analysis**: Have I Been Pwned integration with enhanced breach correlation
- **📡 Carrier Intelligence**: Deep carrier and location analysis with real data

### 🎭 Matrix-Themed Experience
- **🎭 Hacker-Style Web Interface**: Full Matrix theme with animated rain effects
- **⚡ Real-Time Streaming**: Live investigation progress with color-coded terminal output
- **🤖 Matrix Quotes**: Random humorous Matrix-inspired quotes during investigations
- **📊 Professional Reporting**: Comprehensive HTML reports with inline browser viewing
- **🎨 Color-Coded Output**: Different colors for quotes, errors, and investigation stages

### 🛡️ Security & Reliability
- **🛡️ Security-First Design**: Built with defensive security best practices
- **📈 Professional Reporting**: Risk scoring and comprehensive intelligence summaries
- **🔒 API Key Protection**: Secure environment variable management

## 🏗️ Architecture

```
📁 phone-osint-framework/
├── 📁 config/                 # Configuration and API keys
├── 📁 scripts/                # Modular scanner components
│   ├── phone_validator.py     # NumVerify + Twilio validation
│   ├── google_dorker.py       # Google search intelligence
│   ├── social_scanner.py      # Social media discovery
│   ├── breach_checker.py      # Data breach analysis
│   ├── carrier_analyzer.py    # Carrier intelligence
│   └── report_generator.py    # Report generation
├── 📁 results/                # Investigation outputs
├── 📄 phone_osint_master.py   # Main orchestrator
├── 🎭 web_interface.py        # Matrix-themed web interface
├── 🧪 test_apis.py           # API testing suite
└── 📚 docs/                   # Documentation
```

## 🔧 Prerequisites

- **Python 3.11+** (tested with 3.11.2, recommended)
- **Google Chrome/Chromium** (for web automation)
- **ChromeDriver** (auto-downloaded or manual installation)
- **Git** (for installation and updates)
- **Linux/macOS/Windows** (cross-platform support)

## ⚡ Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/yourusername/phone-osint-framework.git
cd phone-osint-framework

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure APIs
```bash
# Copy example configuration
cp config/.env.example config/.env

# Edit with your API keys
nano config/.env
```

### 3. Test Setup
```bash
# Verify all APIs are working
python test_apis.py

# Run sample investigation
python phone_osint_master.py +14158586273
```

### 4. Launch Matrix Web Interface
```bash
python web_interface.py
# Navigate to http://localhost:5000 for the full Matrix experience
```

Experience the future of OSINT investigations with our Matrix-themed terminal interface featuring:
- **Real-time streaming output** with hacker-style formatting
- **Animated Matrix rain effects** with Japanese characters
- **Live progress monitoring** as investigations run
- **Professional terminal aesthetics** for the ultimate cyber experience

## 📋 API Requirements

| Service | Required | Purpose | Cost |
|---------|----------|---------|------|
| [NumVerify](https://numverify.com/) | ✅ Yes | Phone validation & carrier lookup | Free tier available |
| [Google Custom Search](https://developers.google.com/custom-search) | ✅ Yes | Advanced dorking capabilities | Free 100 queries/day |
| [Twilio](https://www.twilio.com/) | ⭐ Recommended | Enhanced phone validation | Pay-per-use |
| [Hunter.io](https://hunter.io/) | ⭐ Recommended | Email discovery | Free tier available |
| [Shodan](https://www.shodan.io/) | ⭐ Recommended | Infrastructure intelligence | Free tier available |
| [Have I Been Pwned](https://haveibeenpwned.com/API/v3) | ⚡ Optional | Breach database access | Paid service |
| [OpenCellID](https://opencellid.org/) | ⚡ Optional | Cell tower data | Free registration |

## 📱 Usage Examples

### Command Line
```bash
# Basic investigation
python phone_osint_master.py +1234567890

# International number
python phone_osint_master.py +44123456789

# View results
ls results/20231215_143022_+1234567890/
```

### Matrix Web Interface
1. Start server: `python web_interface.py`
2. Navigate to `http://localhost:5000`
3. Enter target phone number in the terminal
4. Click "HACK THE MATRIX" to begin investigation
5. Watch real-time streaming output with Matrix effects
6. Access comprehensive HTML report when complete

**Features:**
- Real-time investigation streaming
- Matrix rain background animation
- Hacker-style terminal formatting
- Live progress indicators
- Professional cyber aesthetics

### Python Integration
```python
from phone_osint_master import PhoneOSINTMaster

# Initialize investigator
investigator = PhoneOSINTMaster("+1234567890")

# Run investigation
report_path = investigator.run_full_investigation()
print(f"Report generated: {report_path}")
```

## 📊 Output Structure

Each investigation creates a timestamped directory:
```
results/20231215_143022_+1234567890/
├── 📄 investigation.log          # Detailed execution log
├── 📄 complete_results.json      # Raw investigation data
├── 📄 phone_validation.json      # NumVerify + Twilio validation
├── 📄 phoneinfoga_results.json   # PhoneInfoga format analysis
├── 📄 google_dork_results.json   # Search intelligence
├── 📄 social_media_results.json  # Social platform findings
├── 📄 breach_check_results.json  # Data breach results
├── 📄 carrier_analysis.json      # Carrier intelligence
└── 📄 investigation_report.html  # Professional HTML report
```

## 🧪 Testing & Validation

### API Testing
```bash
# Test all configured APIs
python test_apis.py

# Expected output:
# NumVerify            [OK] Working
# Google Search        [OK] Working
# Twilio               [OK] Working
# Hunter.io            [OK] Working
# Shodan               [OK] Working
# Have I Been Pwned    [OK] Working
# OpenCellID           [X] Failed (common)
```

### Integration Testing
```bash
# Test with known phone number
python phone_osint_master.py +14158586273

# Verify output generation
ls -la results/
```

## 🛡️ Security & Privacy

### Security Features
- 🔐 **API Key Protection**: Environment variable management
- 🚫 **No Data Persistence**: Investigations are self-contained
- 🕵️ **Headless Operation**: No GUI components for stealth
- ⚡ **Rate Limiting**: Built-in delays to respect API limits
- 🔒 **Secure Defaults**: HTTPS-only, secure browser flags

### Privacy Compliance
- **GDPR Ready**: No personal data storage
- **Audit Trail**: Complete investigation logging
- **Access Control**: Local-only web interface
- **Data Retention**: User-controlled result management

### Legal Compliance
> ⚖️ **Legal Notice**: This tool is designed for:
> - Authorized security testing
> - Defensive cybersecurity investigations
> - Educational and research purposes
> - Law enforcement (with proper authorization)
>
> **NOT for**: Stalking, harassment, unauthorized surveillance, or any illegal activities.

## 🔧 Configuration

### Environment Variables
Create `config/.env` with your API keys:
```bash
# Phone Validation
NUMVERIFY_API_KEY=your_numverify_key

# Search Intelligence
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id

# Enhanced Services
TWILIO_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
HUNTER_API_KEY=your_hunter_io_key
SHODAN_KEY=your_shodan_api_key
HAVEIBEENPWNED_API_KEY=your_hibp_key

# Optional Services
OPENCELLID_API_KEY=your_opencellid_key
```

### Performance Settings
```bash
# Rate Limiting
MAX_WORKERS=5
RATE_LIMIT_PER_MINUTE=10
REQUEST_TIMEOUT=30

# Caching
CACHE_EXPIRY=86400  # 24 hours
REDIS_HOST=localhost
REDIS_PORT=6379
```

## 🚨 Troubleshooting

### Common Issues

**ChromeDriver Version Mismatch**
```bash
# Download compatible ChromeDriver
curl -L -o chromedriver.zip https://chromedriver.storage.googleapis.com/LATEST_RELEASE/chromedriver_linux64.zip
unzip chromedriver.zip && sudo mv chromedriver /usr/local/bin/
```

**API Key Issues**
```bash
# Verify API configuration
python test_apis.py

# Check environment variables
source venv/bin/activate
python -c "import os; print([k for k in os.environ.keys() if 'API' in k])"
```

**Permission Errors**
```bash
# Fix permissions
chmod +x run_investigation.sh
chmod 755 results/
```

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for detailed solutions.

## 📚 Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[API Setup Guide](docs/API_SETUP.md)** - API key configuration
- **[User Manual](docs/USER_MANUAL.md)** - Complete usage documentation
- **[Developer Guide](docs/DEVELOPER.md)** - Architecture and development
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Contributing](CONTRIBUTING.md)** - How to contribute
- **[Changelog](CHANGELOG.md)** - Version history

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code style guidelines
- Development workflow
- Testing requirements
- Pull request process

### Contributors
- [Your Name] - Initial development and architecture
- Community contributors welcome!

## 🏆 Acknowledgments

- **[PhoneInfoga](https://github.com/sundowndev/PhoneInfoga)** - Excellent phone OSINT tool
- **[Have I Been Pwned](https://haveibeenpwned.com/)** - Breach intelligence API
- **Security research community** - For tools and techniques

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Additional Terms:**
- This software is provided for educational and authorized professional use only
- Users are responsible for compliance with all applicable laws and regulations
- The authors are not responsible for misuse of this software

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yourusername/phone-osint-framework/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/phone-osint-framework/discussions)
- 📧 **Security Issues**: Please report privately to [security@yourdomain.com]

---

<div align="center">
<b>⭐ If this project helped you, please consider giving it a star! ⭐</b>
<br><br>
<sub>Built with ❤️ for the cybersecurity community</sub>
</div>