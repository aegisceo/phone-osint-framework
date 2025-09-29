# 🤝 Contributing to Phone OSINT Framework

Thank you for your interest in contributing to the Phone OSINT Framework! This document provides guidelines for contributing to this defensive security tool.

## 📋 Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Contribute](#how-to-contribute)
4. [Development Guidelines](#development-guidelines)
5. [Security Considerations](#security-considerations)
6. [Testing Requirements](#testing-requirements)
7. [Documentation Standards](#documentation-standards)
8. [Pull Request Process](#pull-request-process)
9. [Issue Reporting](#issue-reporting)
10. [Community Guidelines](#community-guidelines)

## 📜 Code of Conduct

### Our Pledge

This project is committed to providing a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Use of sexualized language or imagery
- Personal attacks or trolling
- Public or private harassment
- Publishing others' private information without permission
- Conduct which could reasonably be considered inappropriate

### Ethical Use Requirements

**CRITICAL**: This project is for defensive security and authorized OSINT investigations only.

**Absolutely Prohibited**:
- Using the framework for stalking, harassment, or intimidation
- Unauthorized surveillance or privacy violations
- Any illegal activities or circumventing security without authorization
- Contributing features that could primarily serve malicious purposes

**Required for Contributors**:
- Understand and respect the ethical implications of OSINT tools
- Ensure contributions support only legitimate, authorized use cases
- Consider privacy and legal implications of new features

## 🚀 Getting Started

### Prerequisites

- Python 3.8+ (3.11+ recommended)
- Git knowledge
- Understanding of OSINT principles and ethics
- Familiarity with web scraping and API integration
- Basic knowledge of cybersecurity and privacy laws

### Development Setup

1. **Fork the Repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/phone-osint-framework.git
   cd phone-osint-framework
   ```

2. **Set Up Development Environment**
   ```bash
   # Create virtual environment
   python3.11 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows

   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

3. **Configure Development Environment**
   ```bash
   # Copy example configuration
   cp config/.env.example config/.env
   # Add your API keys for testing (keep them secure!)
   ```

4. **Install External Dependencies**
   ```bash
   # Install PhoneInfoga (see INSTALLATION.md for platform-specific instructions)
   # Install ChromeDriver matching your Chrome version
   # Install Redis (optional, for caching)
   ```

5. **Run Tests**
   ```bash
   # Test APIs
   python test_apis.py

   # Run unit tests
   python -m pytest tests/

   # Test basic functionality
   python phone_osint_master.py +14158586273
   ```

## 🛠️ How to Contribute

### Types of Contributions

1. **Bug Reports** - Help us identify and fix issues
2. **Feature Requests** - Suggest new defensive capabilities
3. **Code Contributions** - Implement features, fix bugs, improve performance
4. **Documentation** - Improve guides, add examples, fix typos
5. **API Integrations** - Add new legitimate OSINT data sources
6. **Testing** - Add test cases, improve test coverage
7. **Security Enhancements** - Improve data protection and ethical safeguards

### Contribution Areas

**High Priority:**
- Additional legitimate OSINT API integrations
- Improved error handling and resilience
- Performance optimizations
- Enhanced security and privacy protections
- Better documentation and examples

**Medium Priority:**
- UI/UX improvements for web interface
- Additional output formats
- Caching and rate limiting improvements
- Mobile-responsive design

**Low Priority:**
- Code refactoring and cleanup
- Additional visualization options
- Integration with other security tools

## 💻 Development Guidelines

### Code Style

1. **Python Style**
   ```python
   # Follow PEP 8 with these specific guidelines:
   # - Line length: 88 characters (Black formatter)
   # - Use type hints where possible
   # - Comprehensive docstrings for all functions
   # - Clear variable and function names

   def validate_phone_number(phone: str) -> Dict[str, Any]:
       """
       Validate and normalize a phone number.

       Args:
           phone: Raw phone number string

       Returns:
           Dictionary containing validation results and normalized number

       Raises:
           ValueError: If phone number format is invalid
       """
   ```

2. **Error Handling**
   ```python
   # Always use specific exception handling
   try:
       response = api_call()
   except requests.exceptions.Timeout:
       logger.error("API timeout occurred")
       return {"error": "timeout", "data": None}
   except requests.exceptions.ConnectionError:
       logger.error("Connection error")
       return {"error": "connection", "data": None}
   ```

3. **Logging**
   ```python
   # Use appropriate logging levels
   import logging
   logger = logging.getLogger(__name__)

   logger.debug("Detailed debug information")
   logger.info("General information")
   logger.warning("Something unexpected happened")
   logger.error("An error occurred")
   logger.critical("Critical system error")
   ```

### Security Requirements

1. **API Key Management**
   ```python
   # NEVER hardcode API keys
   # Bad:
   api_key = "abc123xyz"

   # Good:
   api_key = os.getenv('API_KEY')
   if not api_key:
       raise ValueError("API_KEY environment variable required")
   ```

2. **Input Validation**
   ```python
   # Always validate and sanitize inputs
   def sanitize_phone_number(phone: str) -> str:
       # Remove non-numeric characters except +
       sanitized = re.sub(r'[^\d+]', '', phone)

       # Validate format
       if not re.match(r'^\+\d{10,15}$', sanitized):
           raise ValueError("Invalid phone number format")

       return sanitized
   ```

3. **Rate Limiting**
   ```python
   # Implement proper rate limiting
   import time

   class RateLimiter:
       def __init__(self, calls_per_minute: int = 10):
           self.calls_per_minute = calls_per_minute
           self.calls = []

       def wait_if_needed(self):
           now = time.time()
           # Remove calls older than 1 minute
           self.calls = [call for call in self.calls if now - call < 60]

           if len(self.calls) >= self.calls_per_minute:
               sleep_time = 60 - (now - self.calls[0])
               time.sleep(sleep_time)

           self.calls.append(now)
   ```

### File Structure

```
phone-osint-framework/
├── phone_osint_master.py      # Main orchestrator
├── test_apis.py               # API testing suite
├── web_interface.py           # Flask web interface
├── scripts/                   # Investigation modules
│   ├── __init__.py
│   ├── phone_validator.py     # Phone number validation
│   ├── google_dorker.py       # Google search automation
│   ├── social_scanner.py      # Social media scanning
│   ├── breach_checker.py      # Data breach checking
│   └── phoneinfoga_runner.py  # PhoneInfoga integration
├── templates/                 # HTML templates
├── static/                    # CSS, JS, images
├── config/                    # Configuration files
├── docs/                      # Documentation
├── tests/                     # Unit tests
└── requirements.txt           # Python dependencies
```

## 🔒 Security Considerations

### Code Review Checklist

- [ ] No hardcoded credentials or API keys
- [ ] Proper input validation and sanitization
- [ ] Rate limiting implemented for API calls
- [ ] Error handling doesn't expose sensitive information
- [ ] Logging doesn't include sensitive data
- [ ] User data is handled according to privacy laws
- [ ] Features support only authorized use cases

### Privacy Protection

1. **Data Minimization**
   - Collect only necessary data for the investigation
   - Provide options to limit data collection scope
   - Implement automatic data cleanup

2. **Secure Storage**
   - Encrypt sensitive investigation results
   - Use secure temporary files
   - Implement proper data disposal

3. **User Consent**
   - Clear warnings about data collection
   - Options to opt-out of certain investigations
   - Transparency about what data is gathered

## 🧪 Testing Requirements

### Test Categories

1. **Unit Tests** (`tests/unit/`)
   ```python
   import pytest
   from scripts.phone_validator import PhoneValidator

   def test_phone_validation():
       validator = PhoneValidator()
       result = validator.validate("+14158586273")
       assert result["valid"] is True
       assert result["country"] == "US"
   ```

2. **Integration Tests** (`tests/integration/`)
   ```python
   def test_api_integration():
       # Test actual API calls with test keys
       pass
   ```

3. **Security Tests** (`tests/security/`)
   ```python
   def test_no_hardcoded_credentials():
       # Scan code for potential credential leaks
       pass
   ```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test category
python -m pytest tests/unit/ -v

# Run with coverage
python -m pytest tests/ --cov=scripts --cov-report=html

# Test specific functionality
python test_apis.py
```

### Test Data

- Use test phone numbers: +14158586273 (official test number)
- Mock API responses for consistent testing
- Never use real personal data in tests

## 📚 Documentation Standards

### Code Documentation

1. **Module Docstrings**
   ```python
   """
   Phone number validation module for OSINT investigations.

   This module provides comprehensive phone number validation using multiple
   APIs and validation techniques. It supports international phone numbers
   and provides detailed carrier and location information.

   Example:
       >>> validator = PhoneValidator()
       >>> result = validator.validate("+14158586273")
       >>> print(result["carrier"])
       'AT&T Mobility LLC'
   """
   ```

2. **Function Docstrings**
   ```python
   def validate_phone_number(phone: str, include_carrier: bool = True) -> Dict[str, Any]:
       """
       Validate a phone number and gather available information.

       Args:
           phone: Phone number in international format (+1234567890)
           include_carrier: Whether to include carrier lookup (default: True)

       Returns:
           Dictionary containing:
               - valid (bool): Whether number is valid
               - formatted (str): Properly formatted number
               - country (str): Country code
               - carrier (str): Carrier name (if include_carrier=True)
               - location (str): General location information

       Raises:
           ValueError: If phone number format is invalid
           APIError: If validation services are unavailable

       Example:
           >>> result = validate_phone_number("+14158586273")
           >>> result["valid"]
           True
       """
   ```

### Markdown Documentation

- Use clear headings and structure
- Include code examples for all features
- Add troubleshooting sections
- Keep language accessible to different skill levels

## 🔄 Pull Request Process

### Before Submitting

1. **Code Quality**
   ```bash
   # Format code
   black scripts/ *.py

   # Check style
   flake8 scripts/ *.py

   # Type checking
   mypy scripts/ *.py

   # Run tests
   python -m pytest tests/
   ```

2. **Security Review**
   - Run security checklist
   - Verify no credentials in code
   - Test with limited permissions
   - Review privacy implications

### Pull Request Template

```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (existing functionality affected)
- [ ] Documentation update
- [ ] Security enhancement

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Security review completed

## Security Checklist
- [ ] No hardcoded credentials
- [ ] Input validation implemented
- [ ] Rate limiting considered
- [ ] Privacy implications reviewed
- [ ] Only supports authorized use cases

## Screenshots/Examples
Include relevant screenshots or usage examples.

## Additional Notes
Any additional information for reviewers.
```

### Review Process

1. **Automated Checks**
   - Code style and formatting
   - Test suite execution
   - Security vulnerability scanning
   - Documentation building

2. **Manual Review**
   - Code quality and maintainability
   - Security and privacy considerations
   - Ethical implications
   - Documentation completeness

3. **Approval Requirements**
   - At least one maintainer approval
   - All automated checks passing
   - Security review completed (for security-related changes)

## 🐛 Issue Reporting

### Bug Reports

Use this template for bug reports:

```markdown
**Bug Description**
Clear description of the bug.

**Environment**
- OS: Ubuntu 22.04
- Python: 3.11.2
- Framework Version: 1.0.0

**Steps to Reproduce**
1. Run command X
2. Observe behavior Y
3. Expected Z instead

**Error Messages**
```
Full error message and stack trace
```

**Configuration**
- APIs used: NumVerify, Google
- Special setup: Docker, Proxy, etc.

**Security Note**
Have you verified this is not a security vulnerability?
If it might be security-related, please email [security contact] instead.
```

### Feature Requests

```markdown
**Feature Description**
Clear description of the proposed feature.

**Use Case**
Explain the defensive security use case this addresses.

**Ethical Considerations**
How does this feature support only authorized use?

**Implementation Ideas**
Any thoughts on how this could be implemented.

**Alternatives Considered**
Other solutions you've considered.
```

### Security Issues

**DO NOT** report security vulnerabilities in public issues.

Email security issues to: [INSERT SECURITY EMAIL]

Include:
- Detailed description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested mitigation (if any)

## 🌟 Community Guidelines

### Communication Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas
- **Pull Requests**: Code contributions
- **Security Email**: Private security reports

### Best Practices

1. **Be Respectful**
   - Treat all community members with respect
   - Provide constructive feedback
   - Help newcomers get started

2. **Be Ethical**
   - Always consider the ethical implications of contributions
   - Support only defensive and authorized use cases
   - Respect privacy and legal boundaries

3. **Be Collaborative**
   - Work together to solve problems
   - Share knowledge and expertise
   - Help improve the project for everyone

### Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes for significant contributions
- Project documentation for major features

## 📞 Getting Help

### For Contributors

- **Technical Questions**: Create a GitHub Discussion
- **Contribution Process**: Review this document and existing PRs
- **Security Questions**: Email security contact
- **General Help**: Create an issue with the "help wanted" label

### For Users

- **Installation Issues**: Check TROUBLESHOOTING.md
- **Usage Questions**: Review documentation or create a Discussion
- **Bug Reports**: Create an issue with the bug template

## 🎯 Development Roadmap

### Short Term (Next Release)
- Improved error handling
- Additional API integrations
- Enhanced web interface
- Better mobile support

### Medium Term (6 months)
- Advanced visualization features
- Machine learning integration
- API rate limiting improvements
- Enhanced privacy controls

### Long Term (1+ year)
- Plugin architecture
- Advanced reporting features
- Integration with other security tools
- Community-driven feature development

## 📝 License and Legal

By contributing to this project, you agree that:

1. Your contributions will be licensed under the MIT License with additional terms
2. You have the right to submit your contributions
3. You understand and agree to the ethical use requirements
4. You will not contribute code that could primarily serve malicious purposes

## 🙏 Acknowledgments

Special thanks to:
- All contributors who help improve this project
- The OSINT community for sharing knowledge and best practices
- API providers who enable these investigations
- Security researchers who help identify and fix vulnerabilities

Thank you for contributing to making Phone OSINT Framework a better tool for defensive security and authorized investigations! 🛡️