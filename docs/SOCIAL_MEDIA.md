# Social Media OSINT - Implementation Guide

## Overview

This guide documents the social media scraping capabilities in the Phone OSINT Framework, based on real-world techniques and 2025 best practices.

## Platform Capabilities

### Twitter/X

**Available Data (Public Profiles)**:
- Bio/Description with potential contact info
- Location (user-specified)
- Website link
- Display name and @handle
- Follower/Following counts
- Verified status

**Implementation**:
- Uses stable `data-testid` selectors (2025 standard)
- Extracts emails/phones from bio text via regex
- WebDriverWait for dynamic content

**Selectors**:
```python
'div[data-testid="UserDescription"]'  # Bio text
'div[data-testid="UserName"]'        # Full name
'span[data-testid="UserLocation"]'   # Location
'a[data-testid="UserUrl"]'           # Website
```

**Note**: Email and phone are never directly provided by API - only extractable from bio text if user includes them.

### Instagram

**Available Data**:
- Bio (160 char limit)
- Website link
- Display name and username
- Follower/Following/Post counts
- Profile picture URL
- Account type (Business/Creator/Personal)
- Verification status

**Business Account Features**:
- Contact button with email/phone (if enabled)
- Category/industry information
- Obfuscated contact info for logged-out users

**Implementation**:
- Extracts bio and contact info
- Checks for business contact buttons
- Regex extraction for emails/phones in bio
- No authentication required for basic data

**Important**: Instagram often shows obfuscated data (e.g., `j***@gmail.com`) without authentication. Business accounts may provide full contact info publicly.

### LinkedIn

**Available Data**:
- Headline/job title (limited without login)
- Basic profile URL
- Name (if public)
- Login wall bypassed via Google search

**Implementation**:
- Uses Google search (`site:linkedin.com/in/ [name]`)
- More effective than direct LinkedIn scraping
- Limited data without authentication
- No email extraction (LinkedIn protects this heavily)

**Note**: Most LinkedIn data requires authentication. Public scraping provides minimal information.

### GitHub

**Available Data** (Best for tech workers):
- Full name
- Bio
- Company/employer
- Location
- Website
- Public email (from commits or profile)
- Repository data

**Implementation**:
- Most scraper-friendly platform
- Rich metadata always public
- Commit history reveals emails
- Excellent for developer profiles

### Telegram

**Available Data**:
- Username lookup
- Profile picture (if public)
- Bio (if public)
- Last seen status (privacy dependent)

**Implementation**:
- Direct search URLs for username lookup
- Limited programmatic access
- Most data requires Telegram client

### WhatsApp

**Available Data**:
- Number validation
- Profile picture (privacy dependent)
- About/status (privacy dependent)

**Implementation**:
- Web search for WhatsApp number lookups
- No direct API access
- Heavily privacy-protected

### Facebook

**Available Data**:
- Search URLs for manual investigation
- Public profile data (very limited)
- Privacy settings restrict most data

**Implementation**:
- Generates search URLs
- Requires manual investigation
- Login required for most data

## General Implementation Notes

### Rate Limiting
- 2-second delays between platform checks
- Selenium timeouts properly configured
- Respectful of platform ToS

### Data Extraction
- Regex patterns for email/phone extraction
- Username tracking across platforms
- Deduplication of discovered data
- Aggregation of emails, locations, companies

### Anti-Detection
- Headless Chrome with proper user agents
- Human-like behavior patterns
- Appropriate timeouts and waits
- Fallback to search URLs when scraping fails

### Error Handling
- Graceful degradation on failures
- Logging of all extraction attempts
- Fallback methods when primary fails
- No investigation crash on platform errors

## Data Aggregation

The framework aggregates discovered data:
- **Emails**: Deduplicated from all platforms
- **Usernames**: Tracked with platform and URL
- **Locations**: Collected from multiple sources
- **Companies**: Extracted from bios and profiles

## Search URL Generation

For manual investigation, the framework generates search URLs for:
- Phone number searches
- Email searches
- Name searches
- Username searches

These URLs can be manually investigated when automated scraping is blocked.

## Security & Privacy

### Defensive Use Only
- Designed for authorized security investigations
- Respect privacy laws (GDPR, CCPA, etc.)
- No credential stealing or unauthorized access
- Public data only

### Data Handling
- No persistent storage beyond investigation
- Local-only results
- User-controlled data retention
- Audit trail in investigation logs

## Troubleshooting

### Selenium Issues
- Ensure ChromeDriver version matches Chrome
- Check headless mode compatibility
- Verify no display is required (headless)
- Check system resources

### Rate Limiting
- Increase delays between requests
- Use residential proxies if needed
- Respect platform ToS
- Don't run too many concurrent investigations

### Login Walls
- Some platforms require authentication
- Generate search URLs for manual investigation
- Consider API access where available
- Respect platform access restrictions

## Future Enhancements

Potential improvements:
- Residential proxy rotation for anti-detection
- CAPTCHA solving integration
- Additional platform support
- Enhanced username correlation
- ML-based profile matching

## References

Based on real-world implementations:
- twitter-scraper-selenium (2025 selectors)
- Toutatis/InstaGPy (Instagram research)
- GitHub public API documentation
- Reddit OSINT community best practices

---

**Last Updated**: October 2025
**Version**: 2.0

