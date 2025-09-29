# Phone OSINT Framework - Claude Code Best Practices

## Overview

This document outlines best practices, coding standards, and governance guidelines for the Phone OSINT Investigation Framework when working with Claude Code.

## Project Structure

```
phone-osint-framework/
├── config/                    # Configuration files and API keys
├── scripts/                   # Individual module components
├── results/                   # Investigation output directory
├── venv/                      # Python virtual environment
├── phone_osint_master.py      # Main orchestrator script
├── web_interface.py           # Flask web interface
├── test_apis.py              # API testing utilities
└── requirements.txt          # Python dependencies
```

## Coding Standards

### Python Code Style
- **PEP 8 Compliance**: Follow Python PEP 8 style guidelines
- **Type Hints**: Use type hints for function parameters and returns when possible
- **Docstrings**: Include docstrings for all classes and public methods
- **Error Handling**: Implement comprehensive try-catch blocks with meaningful error messages
- **Logging**: Use the logging module instead of print statements

### Security Best Practices
- **Never commit API keys**: Always use environment variables in `config/.env`
- **Input validation**: Validate all phone number inputs before processing
- **Rate limiting**: Implement appropriate delays between API calls
- **Secure defaults**: Use secure configuration defaults (HTTPS, headless browsers)

## API Configuration

### Required APIs
- **NumVerify**: Phone validation and carrier lookup
- **Google Custom Search**: Advanced dorking capabilities
- **Twilio**: Enhanced phone validation and caller ID
- **Hunter.io**: Email finder and verification
- **Shodan**: Internet device search
- **Have I Been Pwned**: Data breach checking

### Optional APIs
- **OpenCellID**: Cell tower and location data (often has connectivity issues)

### API Key Management
```bash
# All API keys stored in config/.env
# Format: SERVICE_API_KEY=your_key_here
# Never commit this file to version control
```

## Testing Procedures

### Before Making Changes
1. Run API tests: `./venv/bin/python test_apis.py`
2. Test individual modules: Import and basic functionality
3. Run end-to-end test: `./venv/bin/python phone_osint_master.py +14158586273`
4. Test web interface: Start Flask server and verify accessibility

### Deployment Checklist
- [ ] Virtual environment activated
- [ ] All requirements installed: `pip install -r requirements.txt`
- [ ] API keys configured in `config/.env`
- [ ] External tools installed (PhoneInfoga, ChromeDriver, Redis)
- [ ] Results directory exists and is writable
- [ ] Selenium ChromeDriver version matches installed Chrome/Chromium

## Common Issues & Solutions

### Selenium/ChromeDriver Issues
- **Problem**: Version mismatch between Chrome and ChromeDriver
- **Solution**: Download compatible ChromeDriver from Google's official releases
- **Commands**:
  ```bash
  curl -L -o chromedriver.zip https://storage.googleapis.com/chrome-for-testing-public/[VERSION]/linux64/chromedriver-linux64.zip
  unzip chromedriver.zip && sudo mv chromedriver /usr/local/bin/
  ```

### Google Search API Issues
- **Problem**: Parameter compatibility with googlesearch-python library
- **Solution**: Use correct parameters: `num_results`, `sleep_interval`
- **Rate Limiting**: Always include delays between searches

### PhoneInfoga Integration
- **Output Format**: PhoneInfoga outputs text, not JSON by default
- **Parsing**: Use custom parser to extract key information
- **Error Handling**: Handle cases where PhoneInfoga fails or returns no data

## Performance Guidelines

### Rate Limiting
- **Google Searches**: 5-second delay between queries
- **API Calls**: Respect individual API rate limits
- **Social Media**: 2-second delays between platform checks

### Resource Management
- **Memory**: Close Selenium drivers properly
- **Files**: Use context managers for file operations
- **Processes**: Clean up subprocess calls

## Security Considerations

### Defensive Use Only
- This framework is designed for defensive security and authorized investigations
- Always obtain proper authorization before investigating phone numbers
- Respect privacy laws and regulations (GDPR, CCPA, etc.)
- Do not use for malicious purposes or unauthorized surveillance

### Data Handling
- **Temporary Data**: Clear sensitive data after investigations
- **Logs**: Avoid logging sensitive information
- **Results**: Store investigation results securely
- **API Keys**: Rotate keys regularly and never share

## Dependencies Management

### Core Dependencies
```
requests>=2.31.0          # HTTP requests
beautifulsoup4>=4.12.2    # HTML parsing
selenium>=4.15.2          # Web automation
phonenumbers>=8.13.24     # Phone number utilities
flask>=3.0.0              # Web interface
jinja2>=3.1.2             # Template engine
twilio>=8.10.1            # Twilio API client
```

### System Dependencies
- **Python 3.8+**: Core runtime
- **Chrome/Chromium**: For Selenium automation
- **ChromeDriver**: Compatible version with browser
- **PhoneInfoga**: External OSINT tool
- **Redis**: Optional caching (not currently used)

## Troubleshooting

### Installation Issues
1. **Permission errors**: Use `sudo` for system-wide installations
2. **Virtual environment**: Always work within the virtual environment
3. **Missing packages**: Check requirements.txt and install missing dependencies

### Runtime Issues
1. **API failures**: Check `test_apis.py` results and API key validity
2. **ChromeDriver**: Ensure version compatibility
3. **Network timeouts**: Increase timeout values or check connectivity

### Investigation Issues
1. **No results**: Check phone number format and API responses
2. **Incomplete data**: Verify all APIs are functional
3. **Report generation**: Ensure output directory permissions

## Development Workflow

### Making Changes
1. **Test first**: Run existing tests to ensure baseline functionality
2. **Incremental changes**: Make small, focused changes
3. **Test changes**: Run full test suite after modifications
4. **Documentation**: Update this file with any new patterns or issues

### Adding New Features
1. **API Integration**: Follow existing pattern in `test_apis.py`
2. **Module Structure**: Follow existing script module patterns
3. **Error Handling**: Implement graceful degradation
4. **Logging**: Add appropriate logging statements

## Monitoring & Maintenance

### Regular Tasks
- **API Key Rotation**: Update keys quarterly
- **Dependency Updates**: Monitor for security updates
- **ChromeDriver Updates**: Keep synchronized with browser versions
- **Test Suite**: Run monthly to catch API changes

### Performance Monitoring
- **API Response Times**: Monitor for degradation
- **Investigation Duration**: Track time per investigation
- **Success Rates**: Monitor API success/failure rates

## Emergency Procedures

### API Key Compromise
1. Immediately revoke compromised keys
2. Generate new keys from provider
3. Update `config/.env` file
4. Test functionality with new keys

### System Compromise
1. Stop all running investigations
2. Review logs for unauthorized access
3. Rotate all API keys as precaution
4. Update system packages and dependencies

---

*This document should be updated whenever significant changes are made to the framework architecture, dependencies, or security practices.*

**Last Updated**: September 29, 2025
**Version**: 1.0