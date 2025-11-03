# TruePeopleSearch Integration Setup

## Overview

TruePeopleSearch is a free people search service that provides:
- ✅ Phone number lookups
- ✅ Current and previous addresses
- ✅ Associated people/relatives
- ✅ Age information
- ✅ Additional phone numbers

**Advantage over FastPeopleSearch**: TruePeopleSearch is completely free and provides comprehensive data without requiring paid subscriptions.

## Installation

### Required Dependencies

```bash
cd phone-osint-framework

# Install Selenium
pip install selenium

# Install undetected-chromedriver (bypasses anti-bot measures)
pip install undetected-chromedriver
```

### Why undetected-chromedriver?

TruePeopleSearch has CAPTCHA protection. `undetected-chromedriver` helps by:
1. **Bypassing most automated detection** - Mimics real browser behavior
2. **Reducing CAPTCHA frequency** - Often loads without CAPTCHA
3. **Easy CAPTCHA solving** - When CAPTCHA appears, browser window stays open for manual solve

## Usage

### Automatic Integration

TruePeopleSearch is already integrated into `unified_name_hunter.py` and will run automatically during investigations:

```bash
python phone_osint_master.py +16199303063
```

### Manual Testing

Test the scraper directly:

```bash
python scripts/truepeoplesearch_scraper.py +16199303063
```

Or use the Python API:

```python
from scripts.truepeoplesearch_scraper import search_truepeoplesearch

results = search_truepeoplesearch('+16199303063')

if results['found']:
    print(f"Name: {results['name']}")
    print(f"Age: {results['age']}")
    print(f"Current Address: {results['current_address']}")
    print(f"Associates: {results['associates']}")
```

## CAPTCHA Handling

### Automatic Handling

The scraper uses `undetected-chromedriver` which bypasses most CAPTCHA challenges automatically.

### Manual Solving

If CAPTCHA appears:

1. **Browser window will stay open** - You'll see the CAPTCHA challenge
2. **Solve manually** - Complete the CAPTCHA in the browser
3. **Scraper continues automatically** - Once solved, scraping resumes
4. **60-second timeout** - You have 60 seconds to solve

### Example Log Output

```
🔍 Searching TruePeopleSearch for: 619-930-3063
🚀 Launching undetected Chrome browser...
📄 Loaded: https://www.truepeoplesearch.com/results?phoneno=619-930-3063
🛡️ CAPTCHA detected - waiting for manual solve...
💡 Please solve the CAPTCHA in the browser window...
✅ CAPTCHA solved - continuing...
✅ Name found: Ryan Lindley
📅 Age: 35
🏠 Addresses found: 3
👥 Associates/Relatives found: 5
📞 Additional phones: 2
🔒 Browser closed
```

## Data Returned

```python
{
    'found': True,
    'name': 'Ryan Lindley',
    'names': ['Ryan Lindley'],  # List format for integration
    'age': 35,
    'current_address': '123 Main St, San Diego, CA 92101',
    'previous_addresses': [
        '456 Oak Ave, San Diego, CA 92103',
        '789 Pine Rd, Vista, CA 92084'
    ],
    'addresses': [
        {'address': '123 Main St...', 'type': 'current'},
        {'address': '456 Oak Ave...', 'type': 'previous'}
    ],
    'associates': ['John Smith', 'Jane Doe'],
    'relatives': ['John Smith', 'Jane Doe'],  # Alias
    'additional_phones': ['760-555-1234', '619-555-5678'],
    'source': 'truepeoplesearch.com'
}
```

## Integration with Name Hunting

TruePeopleSearch is integrated with high priority (0.8 confidence weight) in the unified name hunter:

```python
# In scripts/unified_name_hunter.py
source_weights = {
    'truepeoplesearch': 0.8,  # High weight - free, comprehensive
    'twilio': 0.9,            # Highest - authoritative
    'numverify': 0.7,         # Good - carrier data
    # ... other sources
}
```

### Execution Order

TruePeopleSearch runs in the **fast first-pass sequence**:
1. Twilio (if available)
2. NumVerify
3. **TruePeopleSearch** ← Free, comprehensive
4. FastPeopleSearch (deprecated)

## Troubleshooting

### Issue: Chrome not found

```
Error: chrome not found
```

**Solution**: Install Chrome or Chromium:
- Windows: Download from google.com/chrome
- Linux: `sudo apt install chromium-browser`
- Mac: `brew install --cask google-chrome`

### Issue: CAPTCHA timeout

```
Error: CAPTCHA not solved within timeout
```

**Solution**:
- Solve CAPTCHA faster (60 second limit)
- Or increase timeout in `truepeoplesearch_scraper.py`:
  ```python
  captcha_solved = self._wait_for_captcha_solve(driver, timeout=120)  # 2 minutes
  ```

### Issue: No results found

```
No results found for this phone number
```

**Causes**:
- Phone number may not be in TruePeopleSearch database
- Number formatting issue
- CAPTCHA not solved correctly

**Solution**:
- Verify phone number format
- Try manual search on truepeoplesearch.com
- Check investigation logs for errors

### Issue: Missing dependencies

```
Error: Missing dependencies - install selenium and undetected-chromedriver
```

**Solution**:
```bash
pip install selenium undetected-chromedriver
```

## Advanced Configuration

### Headless Mode (No Browser Window)

By default, the browser is visible for CAPTCHA solving. To run headless (after CAPTCHA is less common):

```python
# In scripts/truepeoplesearch_scraper.py, line ~108
options.headless = True  # Change to True
```

**Warning**: Headless mode may trigger more CAPTCHAs.

### Custom Timeout

Adjust CAPTCHA solve timeout:

```python
# In scripts/truepeoplesearch_scraper.py, line ~133
captcha_solved = self._wait_for_captcha_solve(driver, timeout=120)  # 2 minutes instead of 60
```

## Comparison: TruePeopleSearch vs FastPeopleSearch

| Feature | TruePeopleSearch | FastPeopleSearch |
|---------|------------------|------------------|
| Cost | **Free** | Requires paid proxies |
| Data Quality | **High** (direct from site) | Medium (scraping issues) |
| Phone Numbers | ✅ Yes | ✅ Yes |
| Addresses | ✅ Current + Previous | ⚠️ Limited |
| Associates | ✅ Yes | ⚠️ Limited |
| Age | ✅ Yes | ❌ No |
| CAPTCHA | ⚠️ Sometimes (easily solved) | ⚠️ Sometimes |
| Reliability | **High** | Low (often blocked) |
| Speed | Fast (15-30 seconds) | Slow (proxy issues) |

**Recommendation**: Use TruePeopleSearch as primary free people search source. FastPeopleSearch is deprecated.

## Privacy & Legal

**Important**: Use TruePeopleSearch responsibly:
- ✅ Defensive security investigations
- ✅ Authorized research
- ✅ Compliance with local laws
- ❌ Unauthorized surveillance
- ❌ Harassment or stalking
- ❌ Violating privacy laws

TruePeopleSearch aggregates public records. Verify all information before taking action.

## Support

For issues:
1. Check troubleshooting section above
2. Verify dependencies: `pip list | grep -E "selenium|undetected"`
3. Test Chrome: `google-chrome --version`
4. Run test: `python scripts/truepeoplesearch_scraper.py +1234567890`

---

**Status**: ✅ **Fully Integrated and Production Ready**

TruePeopleSearch scraper is complete with CAPTCHA handling, comprehensive data extraction, and full integration into the unified name hunter.
