# 🔧 Troubleshooting Guide - Phone OSINT Framework

This guide helps resolve common issues with the Phone OSINT Framework.

## 🚨 Emergency Quick Fixes

### Framework Won't Start
```bash
# 1. Check Python version
python --version  # Should be 3.8+

# 2. Recreate virtual environment
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Check API configuration
python test_apis.py
```

### Investigation Fails Immediately
```bash
# 1. Check phone number format
python phone_osint_master.py "+1234567890"  # Include country code

# 2. Check permissions
chmod +x *.sh
mkdir -p results logs cache

# 3. Check dependencies
phoneinfoga version
chromedriver --version
```

## 🐛 Common Issues & Solutions

### 1. Python Environment Issues

#### Problem: `ModuleNotFoundError`
```
ModuleNotFoundError: No module named 'requests'
```

**Solution:**
```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt

# Check installed packages
pip list
```

#### Problem: Python Version Incompatibility
```
SyntaxError: invalid syntax (Python 2.7 detected)
```

**Solution:**
```bash
# Install Python 3.8+
# Ubuntu/Debian
sudo apt install python3.11 python3.11-venv

# Use specific Python version
python3.11 -m venv venv
```

### 2. API Configuration Issues

#### Problem: API Test Failures
```
[X] NumVerify error: Invalid API key
```

**Solutions:**
```bash
# 1. Check .env file exists and has correct format
ls -la config/.env
cat config/.env

# 2. Verify API key format
# NumVerify keys are alphanumeric, ~32 characters
# Google API keys start with "AIza"
# Check for extra spaces or quotes

# 3. Test API directly
curl "http://apilayer.net/api/validate?access_key=YOUR_KEY&number=14158586273"

# 4. Check account status on provider website
```

#### Problem: Rate Limiting Errors
```
[X] Google Search error: HTTP 429 Too Many Requests
```

**Solutions:**
```bash
# 1. Check your quota usage on provider dashboards
# 2. Implement delays between requests
# 3. Upgrade to paid plan if needed
# 4. Use alternative APIs temporarily

# Configure rate limiting
echo "RATE_LIMIT_PER_MINUTE=5" >> config/.env
```

### 3. PhoneInfoga Issues

#### Problem: PhoneInfoga Not Found
```
phoneinfoga: command not found
```

**Solutions:**
```bash
# Method 1: Install via binary
curl -L -o phoneinfoga.tar.gz https://github.com/sundowndev/PhoneInfoga/releases/latest/download/phoneinfoga_linux_x86_64.tar.gz
tar -xzf phoneinfoga.tar.gz
sudo mv phoneinfoga /usr/local/bin/

# Method 2: Install via Go
go install github.com/sundowndev/phoneinfoga/v2@latest

# Method 3: Use Docker
docker run --rm sundowndev/phoneinfoga scan -n +1234567890

# Verify installation
phoneinfoga version
which phoneinfoga
```

#### Problem: PhoneInfoga Returns No Results
```
PhoneInfoga scan complete. Country: Unknown
```

**Solutions:**
```bash
# 1. Test PhoneInfoga directly
phoneinfoga scan -n +14158586273

# 2. Check phone number format
# Must include country code: +1234567890

# 3. Update PhoneInfoga
curl -L -o phoneinfoga.tar.gz https://github.com/sundowndev/PhoneInfoga/releases/latest/download/phoneinfoga_linux_x86_64.tar.gz
tar -xzf phoneinfoga.tar.gz
sudo mv phoneinfoga /usr/local/bin/
```

### 4. ChromeDriver Issues

#### Problem: ChromeDriver Version Mismatch
```
SessionNotCreatedException: This version of ChromeDriver only supports Chrome version 114
Current browser version is 140.0.7339.207
```

**Solutions:**
```bash
# 1. Check Chrome version
google-chrome --version
chromium --version

# 2. Download matching ChromeDriver
CHROME_VERSION="140.0.7339.207"
curl -L -o chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip"
unzip chromedriver.zip
sudo mv chromedriver-linux64/chromedriver /usr/local/bin/

# 3. Verify compatibility
chromedriver --version
```

#### Problem: Chrome/Chromium Not Found
```
WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

**Solutions:**
```bash
# Linux
sudo apt install chromium-browser

# macOS
brew install --cask google-chrome

# Add ChromeDriver to PATH
export PATH=$PATH:/usr/local/bin

# Or specify full path in script
which chromedriver
```

### 5. Selenium Issues

#### Problem: Selenium Crashes
```
selenium.common.exceptions.WebDriverException: Message: unknown error: Chrome failed to start
```

**Solutions:**
```bash
# 1. Add Chrome options for headless operation
# (Already implemented in social_scanner.py)

# 2. Check display server (Linux)
export DISPLAY=:99
sudo apt install xvfb
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &

# 3. Run with different Chrome options
python -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
print('Selenium working')
driver.quit()
"
```

### 6. Network & Firewall Issues

#### Problem: Connection Timeouts
```
requests.exceptions.ConnectTimeout: HTTPSConnectionPool(host='api.example.com', port=443)
```

**Solutions:**
```bash
# 1. Test connectivity
curl -I https://api.numverify.com/
ping google.com

# 2. Check proxy settings
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080

# 3. Increase timeout
echo "REQUEST_TIMEOUT=60" >> config/.env

# 4. Check firewall
sudo ufw status  # Linux
```

#### Problem: DNS Resolution Issues
```
requests.exceptions.ConnectionError: Failed to establish a new connection
```

**Solutions:**
```bash
# 1. Check DNS
nslookup api.numverify.com
dig google.com

# 2. Use alternative DNS
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf

# 3. Flush DNS cache
sudo systemctl restart systemd-resolved  # Linux
sudo dscacheutil -flushcache  # macOS
ipconfig /flushdns  # Windows
```

### 7. Permission Issues

#### Problem: Permission Denied Errors
```
PermissionError: [Errno 13] Permission denied: '/usr/local/bin/chromedriver'
```

**Solutions:**
```bash
# 1. Fix file permissions
chmod +x /usr/local/bin/chromedriver
chmod +x /usr/local/bin/phoneinfoga

# 2. Fix directory permissions
sudo chown -R $USER:$USER venv/
mkdir -p results logs cache
chmod 755 results logs cache

# 3. Run without sudo when possible
```

### 8. Memory & Performance Issues

#### Problem: Out of Memory
```
MemoryError: Unable to allocate array
```

**Solutions:**
```bash
# 1. Check available memory
free -h

# 2. Close unnecessary applications
# 3. Reduce concurrent investigations
echo "MAX_WORKERS=2" >> config/.env

# 4. Monitor memory usage
top -p $(pgrep -f python)
```

#### Problem: Slow Performance
**Solutions:**
```bash
# 1. Optimize rate limiting
echo "SLEEP_BETWEEN_REQUESTS=1" >> config/.env

# 2. Use SSD storage if available
# 3. Check network speed
speedtest-cli

# 4. Limit investigation scope
# Focus on essential APIs only
```

## 🔍 Diagnostic Commands

### System Information
```bash
# Python environment
python --version
pip --version
which python

# System info
uname -a
df -h
free -h

# Network
curl -I https://google.com
nslookup api.numverify.com
```

### Framework Status
```bash
# Check all dependencies
phoneinfoga version
chromedriver --version
google-chrome --version

# Test framework components
python -c "
import requests
import selenium
import phonenumbers
import twilio
print('All modules imported successfully')
"

# Test APIs
python test_apis.py
```

### Investigation Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python phone_osint_master.py +1234567890 2>&1 | tee debug.log

# Check investigation results
ls -la results/
cat results/*/investigation.log
```

## 📊 Log Analysis

### Common Log Patterns

#### API Errors
```bash
# Search for API errors
grep -i "error\|exception" results/*/investigation.log

# Check specific API failures
grep "NumVerify error" results/*/investigation.log
grep "Google API error" results/*/investigation.log
```

#### Performance Issues
```bash
# Find slow operations
grep "timeout\|slow" results/*/investigation.log

# Check investigation duration
grep "Investigation complete" results/*/investigation.log
```

### Log Locations
```bash
# Investigation logs
results/TIMESTAMP_PHONE/investigation.log

# Application logs (if configured)
logs/phone_osint.log

# System logs
/var/log/syslog  # Linux
/var/log/system.log  # macOS
```

## 🔄 Reset Procedures

### Complete Reset
```bash
# 1. Stop all running processes
pkill -f "python.*phone_osint"
pkill -f "chromedriver"

# 2. Clean up files
rm -rf venv/ __pycache__/ *.pyc
rm -rf results/* logs/* cache/*

# 3. Reinstall
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Reconfigure
cp config/.env.example config/.env
# Edit config/.env with your API keys

# 5. Test
python test_apis.py
```

### Partial Reset
```bash
# Reset just Python environment
rm -rf venv/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Reset configuration
cp config/.env.example config/.env
# Re-enter your API keys

# Clean results
rm -rf results/*
```

## 📞 Getting Additional Help

### Before Asking for Help
1. **Check this troubleshooting guide**
2. **Review error messages carefully**
3. **Test with a fresh environment**
4. **Gather relevant information:**
   - Operating system and version
   - Python version
   - Error messages (full stack trace)
   - Configuration (without API keys)
   - Steps to reproduce

### Where to Get Help
1. **GitHub Issues**: [Create an issue](https://github.com/yourusername/phone-osint-framework/issues)
2. **Documentation**: Review all docs in `/docs/`
3. **Community**: GitHub Discussions

### Issue Template
When reporting issues, include:

```markdown
**Environment:**
- OS: Ubuntu 22.04
- Python: 3.11.2
- Framework Version: 1.0.0

**Problem:**
Brief description of the issue

**Steps to Reproduce:**
1. Run command X
2. See error Y

**Error Message:**
```
Full error message here
```

**Configuration:**
- APIs configured: NumVerify, Google
- Special setup: Docker, Proxy, etc.

**Additional Context:**
Any other relevant information
```

### Self-Help Checklist
Before seeking help, verify:

- [ ] Python 3.8+ is installed
- [ ] Virtual environment is activated
- [ ] All dependencies are installed
- [ ] API keys are properly configured
- [ ] External tools (PhoneInfoga, ChromeDriver) are installed
- [ ] Network connectivity is working
- [ ] Permissions are correct
- [ ] No conflicting processes are running

## 🎯 Prevention Tips

### Regular Maintenance
```bash
# Weekly checks
python test_apis.py
pip list --outdated

# Monthly updates
pip install --upgrade -r requirements.txt

# Quarterly tasks
# - Rotate API keys
# - Clean old results
# - Update external tools
```

### Monitoring
```bash
# Set up monitoring for:
# - API usage quotas
# - System resources
# - Error rates
# - Investigation success rates
```

This troubleshooting guide should resolve most common issues. For persistent problems, don't hesitate to create a GitHub issue with detailed information!