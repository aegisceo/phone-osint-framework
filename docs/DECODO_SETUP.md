# Decodo Integration Guide

## Overview

Decodo (formerly Smartproxy) offers two ways to scrape Yandex:

1. **Residential Proxies** - You handle scraping, they provide IPs
2. **Scraping API** - They handle everything (proxies, CAPTCHA, anti-bot)

We've integrated both so you can compare and choose the best option.

## Trials Available

| Service | Trial | Duration | Credit Card? |
|---------|-------|----------|--------------|
| Residential Proxies | 100MB | 3 days | ✅ Required |
| Scraping API | 1,000 requests | 7 days | ✅ Required |

Both have 14-day money-back guarantee.

---

## Option 1: Residential Proxies

### Setup

1. **Sign up**: https://decodo.com/proxies/residential-proxies
2. **Get credentials** from dashboard
3. **Run setup**:

```bash
./venv/bin/python scripts/decodo_proxy_manager.py
```

4. **Enter**:
   - Username (from dashboard)
   - Password (from dashboard)
   - Country (optional): `us`, `gb`, `ca`, `de` for clean IPs
   - Session type: Rotating (recommended)

### How It Works

- Gateway: `gate.decodo.com:7000`
- Format: `username-sessid-session1-country-us:password@gate.decodo.com:7000`
- Creates 10 proxy sessions for rotation
- Saves to `config/proxies.txt`
- Auto-used by `yandex_scraper.py`

### Usage

```bash
# Automatic (in investigations)
./venv/bin/python phone_osint_master.py +13053932786

# Manual test
./venv/bin/python -c "
from scripts.decodo_proxy_manager import DecodaProxyManager
manager = DecodaProxyManager()
print('Testing proxy...')
if manager.test_connection():
    print('✓ Working!')
"
```

### Pricing

- Trial: $1 for 100MB (3 days)
- Regular: $1.50/GB minimum
- Tiers: 2GB-1000GB
- **1 GB ≈ 1,000-2,000 Yandex searches**

### Pros/Cons

**Pros:**
- ✅ Lower cost per GB
- ✅ Full control over scraping logic
- ✅ Works with existing yandex_scraper.py

**Cons:**
- ⚠️ Manual CAPTCHA handling
- ⚠️ More complex error handling
- ⚠️ Slower (need delays between requests)

---

## Option 2: Scraping API

### Setup

1. **Sign up**: https://decodo.com/scraping
2. **Get API credentials** from dashboard
3. **Run setup**:

```bash
./venv/bin/python scripts/decodo_api_scraper.py
```

4. **Enter**:
   - API Username
   - API Password

### How It Works

- Endpoint: `https://scraper-api.decodo.com/v2/scrape`
- Target: `yandex` with search URL
- They handle: proxies, CAPTCHA, JavaScript, anti-bot
- Returns: Raw HTML (we parse it)

### Usage

```bash
# Test directly
./venv/bin/python scripts/decodo_api_scraper.py

# Or use comparison tool (see below)
./venv/bin/python scripts/scraper_comparison.py +13053932786 api
```

### Pricing

- Trial: 1,000 requests free (7 days)
- Core Plan: $29/month (100K requests = $0.29/1K)
- Advanced Plan: $50/month (25K requests = $2/1K)
- **1 phone investigation ≈ 5-10 requests**

### Pros/Cons

**Pros:**
- ✅ Fully managed (no CAPTCHA/anti-bot handling)
- ✅ Faster (no manual delays needed)
- ✅ Higher success rate
- ✅ Better for high-volume

**Cons:**
- ⚠️ More expensive for low volume
- ⚠️ Less control over proxy selection
- ⚠️ Request-based billing

---

## Comparison Tool

Test all methods side-by-side:

```bash
# Test all methods
./venv/bin/python scripts/scraper_comparison.py +13053932786

# Test specific methods
./venv/bin/python scripts/scraper_comparison.py +13053932786 proxies,api

# Skip direct (no proxy)
./venv/bin/python scripts/scraper_comparison.py +13053932786 proxies,api
```

### What It Tests

1. **Direct Scraping** - No proxies (baseline, will likely get blocked)
2. **Decodo Proxies** - Manual scraping with proxy rotation
3. **Decodo API** - Fully managed scraping

### Output Example

```
COMPARISON RESULTS
==========================================

Method: DIRECT SCRAPING
----------------------------------------
  Status: ✓ Success
  Time: 45.23s
  Total Results: 12
  Russian Social: 3
  Cost: $0 (free)
  Notes: High risk of blocking, CAPTCHAs

Method: DECODO PROXIES
----------------------------------------
  Status: ✓ Success
  Time: 78.45s
  Total Results: 18
  Russian Social: 6
  Cost: ~$0.02 (100MB trial)
  Notes: Manual anti-bot handling

Method: DECODO API
----------------------------------------
  Status: ✓ Success
  Time: 32.11s
  Total Results: 22
  Russian Social: 8
  Cost: ~$0.25 (1000 req trial)
  Notes: Fully managed

🏆 Most Results: decodo_api (22 results)
⚡ Fastest: decodo_api (32.11s)
💰 Best Value: decodo_proxies
```

---

## Which Should I Use?

### Use Residential Proxies If:
- ✅ Low volume (<100 investigations/month)
- ✅ Want to minimize cost
- ✅ Comfortable handling CAPTCHAs manually
- ✅ Need full control

**Cost: ~$1.50-3/month for 100 investigations**

### Use Scraping API If:
- ✅ High volume (>100 investigations/month)
- ✅ Want highest success rate
- ✅ Need faster results
- ✅ Prefer managed service

**Cost: ~$29-50/month for unlimited investigations**

### Use Both If:
- ✅ Want redundancy
- ✅ Testing which works better
- ✅ Proxies as primary, API as fallback

---

## Integration with Main Framework

### Automatic Integration

The framework automatically detects which method is configured:

1. Checks for `config/decodo_api_config.json` → Uses API
2. Checks for `config/decodo_config.json` → Uses Proxies
3. Checks for `config/proxies.txt` → Uses any proxies
4. Falls back to direct scraping

### Manual Selection

Edit `phone_osint_master.py` line 423:

```python
# Use Decodo API explicitly
from scripts.decodo_api_scraper import DecodaAPIScraper
scraper = DecodaAPIScraper(self.phone_number, enriched_identity)
yandex_results = scraper.search()

# OR use Decodo Proxies explicitly
from scripts.yandex_scraper import YandexScraper
from scripts.decodo_proxy_manager import DecodaProxyManager
manager = DecodaProxyManager()
proxies = manager.export_for_yandex()
scraper = YandexScraper(self.phone_number, enriched_identity, proxies)
yandex_results = scraper.search()
```

---

## Troubleshooting

### Residential Proxies

**"Authentication failed"**
- Check username/password in `config/decodo_config.json`
- Verify credentials at https://decodo.com/dashboard

**"No results found"**
- Check trial credits remaining
- Try different country targeting
- Increase delays in `yandex_scraper.py`

**Test connection:**
```bash
./venv/bin/python -c "
from scripts.decodo_proxy_manager import DecodaProxyManager
manager = DecodaProxyManager()
manager.test_connection()
"
```

### Scraping API

**"401 Authentication failed"**
- Check API username/password in `config/decodo_api_config.json`
- Verify at https://decodo.com/dashboard/api

**"402 Payment required"**
- Trial expired or out of credits
- Add credits at https://decodo.com/dashboard/billing

**"429 Rate limited"**
- Automatic retry with backoff
- Wait 30-60 seconds

**Test API:**
```bash
./venv/bin/python -c "
from scripts.decodo_api_scraper import DecodaAPIScraper
scraper = DecodaAPIScraper('+10000000000')
print('Testing API...')
# Check config file exists
import os
if os.path.exists('config/decodo_api_config.json'):
    print('✓ Config found')
else:
    print('✗ Run setup first')
"
```

---

## Cost Examples

### Scenario 1: 10 investigations/month
- **Proxies**: ~$0.20 (uses 200MB of 100MB trial + $1.50/GB)
- **API**: ~$0 (uses 50 of 1,000 trial requests)
- **Winner**: Either (both effectively free during trial)

### Scenario 2: 100 investigations/month
- **Proxies**: ~$1.50 (1GB at $1.50/GB)
- **API**: ~$15 (500 requests at $0.03/request)
- **Winner**: Proxies (10x cheaper)

### Scenario 3: 1,000 investigations/month
- **Proxies**: ~$15 (10GB at $1.50/GB)
- **API**: ~$29 (5,000 requests on Core plan)
- **Winner**: API (better value, fully managed)

---

## Privacy & Security

**Decodo Details:**
- **Jurisdiction**: Lithuania (EU, not Five Eyes)
- **Privacy Policy**: https://decodo.com/privacy-policy
- **No-logging**: Not explicitly stated for proxies
- **Payment**: Credit card required for trials

**Recommendations:**
- Use for authorized investigations only
- Review privacy policy before use
- Consider privacy coins for payment (after trial)
- Rotate credentials regularly

---

## Next Steps

1. ✅ Sign up for Decodo trial
2. ✅ Run setup scripts
3. ✅ Run comparison test
4. ✅ Choose best method for your needs
5. ✅ Integrate into investigations

**Get Started:**
```bash
# Proxies
./venv/bin/python scripts/decodo_proxy_manager.py

# API
./venv/bin/python scripts/decodo_api_scraper.py

# Compare
./venv/bin/python scripts/scraper_comparison.py +13053932786
```

---

**Ready to scrape Yandex with professional infrastructure! 🚀**
