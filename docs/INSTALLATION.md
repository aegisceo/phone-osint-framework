# 📦 Installation Guide - Phone OSINT Framework

This guide provides detailed installation instructions for all supported platforms.

## 🔍 System Requirements

### Minimum Requirements
- **Python 3.8+** (Python 3.11+ recommended)
- **4GB RAM** (8GB+ recommended for concurrent investigations)
- **2GB free disk space** (more for investigation results)
- **Internet connection** (for API calls and tool downloads)

### Recommended Specifications
- **Python 3.11+**
- **8GB RAM**
- **10GB free disk space**
- **High-speed internet connection**
- **SSD storage** (for better performance)

## 🐧 Linux Installation (Ubuntu/Debian)

### Step 1: Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Python and Dependencies
```bash
# Install Python 3.11 and development tools
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install system dependencies
sudo apt install -y git curl unzip chromium-browser redis-server

# Install Go (for PhoneInfoga)
sudo snap install go --classic
```

### Step 3: Clone Repository
```bash
git clone https://github.com/yourusername/phone-osint-framework.git
cd phone-osint-framework
```

### Step 4: Create Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### Step 5: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Install PhoneInfoga
```bash
# Method 1: Pre-built binary (recommended)
curl -L -o phoneinfoga.tar.gz https://github.com/sundowndev/PhoneInfoga/releases/latest/download/phoneinfoga_linux_x86_64.tar.gz
tar -xzf phoneinfoga.tar.gz
chmod +x phoneinfoga
sudo mv phoneinfoga /usr/local/bin/

# Method 2: Build from source
# go install github.com/sundowndev/phoneinfoga/v2@latest
```

### Step 7: Install ChromeDriver
```bash
# Download compatible ChromeDriver
CHROME_VERSION=$(chromium-browser --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
curl -L -o chromedriver.zip "https://chromedriver.storage.googleapis.com/$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%%.*})/chromedriver_linux64.zip"
unzip chromedriver.zip
chmod +x chromedriver
sudo mv chromedriver /usr/local/bin/
```

### Step 8: Setup Configuration
```bash
cp config/.env.example config/.env
# Edit config/.env with your API keys (see API_SETUP.md)
```

### Step 9: Test Installation
```bash
python test_apis.py
```

## 🍎 macOS Installation

### Step 1: Install Homebrew (if not installed)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Step 2: Install Dependencies
```bash
# Install Python, Git, and other tools
brew install python@3.11 git curl unzip go redis

# Install Chrome
brew install --cask google-chrome
```

### Step 3: Clone Repository
```bash
git clone https://github.com/yourusername/phone-osint-framework.git
cd phone-osint-framework
```

### Step 4: Create Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### Step 5: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Install PhoneInfoga
```bash
# Download and install PhoneInfoga
curl -L -o phoneinfoga.tar.gz https://github.com/sundowndev/PhoneInfoga/releases/latest/download/phoneinfoga_darwin_amd64.tar.gz
tar -xzf phoneinfoga.tar.gz
chmod +x phoneinfoga
sudo mv phoneinfoga /usr/local/bin/
```

### Step 7: Install ChromeDriver
```bash
# Install ChromeDriver via Homebrew
brew install chromedriver

# Or download manually
# curl -L -o chromedriver.zip https://chromedriver.storage.googleapis.com/LATEST_RELEASE/chromedriver_mac64.zip
# unzip chromedriver.zip && mv chromedriver /usr/local/bin/
```

### Step 8: Setup Configuration
```bash
cp config/.env.example config/.env
# Edit config/.env with your API keys
```

### Step 9: Test Installation
```bash
python test_apis.py
```

## 🪟 Windows Installation

### Step 1: Install Python
1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. Run installer with "Add Python to PATH" checked
3. Choose "Customize installation" and ensure pip is included

### Step 2: Install Git
1. Download Git from [git-scm.com](https://git-scm.com/)
2. Install with default settings

### Step 3: Install Chrome
1. Download and install Google Chrome
2. Note the installation path for ChromeDriver compatibility

### Step 4: Clone Repository
```cmd
git clone https://github.com/yourusername/phone-osint-framework.git
cd phone-osint-framework
```

### Step 5: Create Virtual Environment
```cmd
python -m venv venv
venv\Scripts\activate
```

### Step 6: Install Python Dependencies
```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 7: Install PhoneInfoga
```cmd
# Download PhoneInfoga for Windows
curl -L -o phoneinfoga.zip https://github.com/sundowndev/PhoneInfoga/releases/latest/download/phoneinfoga_windows_amd64.zip
# Extract and add to PATH, or place in project directory
```

### Step 8: Install ChromeDriver
1. Check Chrome version: `chrome://version/`
2. Download matching ChromeDriver from [chromedriver.chromium.org](https://chromedriver.chromium.org/)
3. Extract and add to PATH or place in project directory

### Step 9: Setup Configuration
```cmd
copy config\.env.example config\.env
# Edit config\.env with your API keys using notepad
```

### Step 10: Test Installation
```cmd
python test_apis.py
```

## 🐳 Docker Installation (Optional)

### Prerequisites
- Docker installed and running
- Docker Compose (optional)

### Build and Run
```bash
# Clone repository
git clone https://github.com/yourusername/phone-osint-framework.git
cd phone-osint-framework

# Create .env file
cp config/.env.example config/.env
# Edit config/.env with your API keys

# Build Docker image
docker build -t phone-osint-framework .

# Run container
docker run -v $(pwd)/results:/app/results -v $(pwd)/config:/app/config phone-osint-framework +1234567890

# Or use Docker Compose
docker-compose up
```

### Dockerfile Example
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install PhoneInfoga
RUN curl -L -o phoneinfoga.tar.gz https://github.com/sundowndev/PhoneInfoga/releases/latest/download/phoneinfoga_linux_x86_64.tar.gz \
    && tar -xzf phoneinfoga.tar.gz \
    && chmod +x phoneinfoga \
    && mv phoneinfoga /usr/local/bin/

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Set up permissions
RUN chmod +x run_investigation.sh

ENTRYPOINT ["python", "phone_osint_master.py"]
```

## ⚙️ Post-Installation Configuration

### 1. Redis Setup (Optional)
```bash
# Linux/macOS
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Windows - Install Redis from releases or use WSL
```

### 2. API Configuration
See [API_SETUP.md](API_SETUP.md) for detailed API setup instructions.

### 3. Test Installation
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Test APIs
python test_apis.py

# Test basic investigation
python phone_osint_master.py +14158586273

# Test web interface
python web_interface.py
# Navigate to http://localhost:5000
```

## 🔧 Advanced Installation Options

### Development Installation
```bash
# Clone repository
git clone https://github.com/yourusername/phone-osint-framework.git
cd phone-osint-framework

# Install in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/
```

### Headless Server Installation
```bash
# For servers without GUI
export DISPLAY=:99
sudo apt install -y xvfb

# Start virtual display
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &

# Run investigations
python phone_osint_master.py +1234567890
```

## 🚨 Troubleshooting Installation Issues

### Python Version Issues
```bash
# Check Python version
python --version
python3 --version

# Install specific Python version on Ubuntu
sudo apt install -y python3.11 python3.11-venv

# Use specific version
python3.11 -m venv venv
```

### Permission Issues
```bash
# Fix permission issues on Linux/macOS
chmod +x run_investigation.sh
sudo chown -R $USER:$USER venv/
```

### ChromeDriver Issues
```bash
# Check Chrome version
google-chrome --version    # Linux
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version  # macOS

# Download matching ChromeDriver version
# Visit: https://chromedriver.chromium.org/downloads
```

### Virtual Environment Issues
```bash
# Remove corrupted virtual environment
rm -rf venv/

# Create new virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Network/Firewall Issues
```bash
# Test connectivity to APIs
curl -I https://api.numverify.com/
curl -I https://www.googleapis.com/

# Check proxy settings if needed
export HTTP_PROXY=http://proxy.company.com:8080
export HTTPS_PROXY=http://proxy.company.com:8080
```

## 📚 Next Steps

After successful installation:

1. **Configure APIs**: Follow [API_SETUP.md](API_SETUP.md)
2. **Run First Investigation**: Try with a test phone number
3. **Explore Web Interface**: Start Flask server and explore features
4. **Read Documentation**: Review user manual and troubleshooting guides
5. **Join Community**: Contribute to the project or ask questions

## 🆘 Getting Help

If you encounter issues:

1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Review [GitHub Issues](https://github.com/yourusername/phone-osint-framework/issues)
3. Create a new issue with detailed error information
4. Join community discussions

## 📋 Installation Verification Checklist

- [ ] Python 3.8+ installed and accessible
- [ ] Virtual environment created and activated
- [ ] All Python dependencies installed (`pip list`)
- [ ] PhoneInfoga installed and accessible (`phoneinfoga version`)
- [ ] Chrome/Chromium browser installed
- [ ] ChromeDriver installed and compatible
- [ ] API keys configured in `config/.env`
- [ ] Test APIs pass (`python test_apis.py`)
- [ ] Basic investigation works
- [ ] Web interface accessible

Your Phone OSINT Framework should now be ready for use!