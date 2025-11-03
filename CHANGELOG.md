# Changelog

All notable changes to the Phone OSINT Framework will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2025-11-03

### Major Features Added
- **Breach-First Discovery Architecture**: Complete framework overhaul to prioritize breach data
- **DeHashed Integration**: Multi-parameter search (phone, name, email, username, address)
- **LeakCheck Integration**: Phone and username breach database
- **TruePeopleSearch Integration**: Free people search with CAPTCHA handling
- **Conditional Email Discovery**: Smart mode (2+ verified emails) vs Full mode (<2 emails)
- **Modern Dashboard Reports**: Interactive HTML with Chart.js visualizations
- **Maigret Integration**: 2500+ platform username enumeration
- **Comprehensive Breach Search**: Search by phone+name without requiring emails first

### Flow Optimization
- Reordered investigation: Phone → Name → Breach → TruePeopleSearch → Conditional Email Discovery
- TruePeopleSearch moved to dedicated step after breach discovery (optimal timing)
- Email pattern generation now conditional (skipped when we have verified data)
- Public records scraping conditional (skipped with verified data)
- LinkedIn/GitHub/Sherlock always run (intelligence value beyond emails)

### API Fixes
- Fixed HIBP API integration (updated to valid API key)
- Fixed DeHashed API (removed username requirement, using v2 endpoint correctly)
- Fixed SerpAPI proxy support (now uses IPRoyal)
- Enhanced error handling with detailed tracebacks

### Bug Fixes
- Fixed email data loss bug (line 851 overwrite in email_hunter.py)
- Fixed breach search early exit (now searches by phone+name even without emails)
- Fixed TruePeopleSearch attribute error (phone_number → phone)
- Fixed Sherlock initialization (missing target_name parameter)
- Fixed Sherlock method name (run_sherlock_scan vs run_sherlock_username_hunt)
- Fixed Modern Report data type crashes (defensive type checking throughout)
- Fixed ChromeDriver cleanup errors (robust try/finally with error suppression)

### Performance Improvements
- 50-70% faster investigations with verified breach data
- Smart mode skips redundant enumeration (pattern generation, public records)
- Parallel name hunting for faster initial discovery
- Query result caching

### Security Enhancements
- Updated .gitignore to protect .google-cookie and session files
- Added defensive type checking throughout report generation
- Enhanced error logging without exposing sensitive data
- Removed hardcoded credentials

### Developer Experience
- Comprehensive error messages for debugging
- Created diagnostic tools (test_breach_apis_direct.py)
- Better logging with emojis and structure
- Cleaned up codebase (removed 20+ redundant documentation files)

---

## [1.5.0] - 2025-10-31

### Added
- Unified name hunting pipeline with parallel execution
- FastPeopleSearch integration
- IPRoyal proxy manager
- Enhanced Twilio identity matching
- Modern report generator with collapsible sections

### Fixed
- Twilio identity match parameter formatting
- NumVerify vs Twilio data priority
- Web interface identity data flow

---

## [1.0.0] - 2025-09-29

### Initial Release
- Basic phone validation (NumVerify)
- Twilio caller ID lookup
- Google dorking capabilities
- Social media discovery
- HIBP breach checking
- Basic HTML report generation
- Web interface with Matrix theme

---

## Version History Summary

| Version | Date | Key Feature |
|---------|------|-------------|
| 2.0.0 | 2025-11-03 | Breach-first architecture, conditional discovery |
| 1.5.0 | 2025-10-31 | Unified name hunting, FastPeopleSearch |
| 1.0.0 | 2025-09-29 | Initial release |

---

## Upgrade Notes

### Upgrading to 2.0.0

#### Required Actions:
1. Update HIBP API key in `config/.env`
2. Remove `DEHASHED_USERNAME` from `config/.env` (no longer needed)
3. Update Chrome browser to version 142+ for TruePeopleSearch
4. Install Maigret: `pip install maigret` (optional but recommended)

#### Breaking Changes:
- DeHashed integration no longer uses username (API v2 uses key-only auth)
- UnifiedNameHunter now requires `skip_truepeoplesearch` parameter
- EmailHunter.hunt_comprehensive() now accepts skip flags
- TruePeopleSearch no longer runs in parallel name hunting (dedicated step)

#### Migration Guide:
```bash
# Update dependencies
pip install -r requirements.txt --upgrade

# Update API keys
# Edit config/.env:
# - Update HAVEIBEENPWNED_API_KEY
# - Remove DEHASHED_USERNAME line (not needed)

# Test new flow
python test_breach_apis_direct.py
python phone_osint_master.py +<test_number>
```

---

## Deprecations

### Removed in 2.0.0:
- Yandex scraper (100% CAPTCHA rate, non-functional)
- Decodo API integration (replaced by IPRoyal)
- WhitePages API integration (user request)
- Session authentication system (untested, experimental)
- Multiple redundant test files (consolidated)
- 20+ session summary markdown files (consolidated into CURRENT_STATUS.md)

---

## Known Issues

### TruePeopleSearch:
- Requires Chrome 142+ (update via chrome://settings/help)
- CAPTCHA may appear (requires manual solving)
- ChromeDriver must match Chrome version

### DeHashed:
- Requires active subscription with search credits
- Uses v2 API (different from v1)
- No username needed (key-only authentication)

---

## Roadmap

### Planned Features:
- Automated CAPTCHA solving for TruePeopleSearch
- Additional breach database integrations
- Enhanced employment intelligence
- Graph visualization of connections
- API rate limit dashboard
- Batch investigation mode

### Under Consideration:
- Docker containerization
- REST API for programmatic access
- Plugin system for custom modules
- Real-time monitoring mode

---

For detailed architecture and current status, see `CURRENT_STATUS.md`.
