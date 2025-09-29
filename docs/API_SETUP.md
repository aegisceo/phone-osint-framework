# 🔑 API Setup Guide - Phone OSINT Framework

This guide provides step-by-step instructions for setting up all supported APIs.

## 📋 API Overview

| Service | Required | Cost | Rate Limits | Setup Difficulty |
|---------|----------|------|-------------|------------------|
| NumVerify | ✅ Yes | Free tier: 1,000/month | 1,000 requests/month | Easy |
| Google Custom Search | ✅ Yes | Free: 100/day | 100 queries/day | Medium |
| Twilio | ⭐ Recommended | Pay-per-use | Varies by plan | Easy |
| Hunter.io | ⭐ Recommended | Free: 50/month | 50 searches/month | Easy |
| Shodan | ⭐ Recommended | Free tier available | Varies | Easy |
| Have I Been Pwned | ⚡ Optional | $3.50/month | 10,000/month | Easy |
| OpenCellID | ⚡ Optional | Free | Moderate | Easy |

## 🔢 NumVerify API (REQUIRED)

NumVerify provides phone number validation and carrier information.

### Step 1: Create Account
1. Visit [numverify.com](https://numverify.com/)
2. Click "Get Free API Key"
3. Register with your email
4. Verify your email address

### Step 2: Get API Key
1. Log into your NumVerify dashboard
2. Copy your API Access Key
3. Note your monthly quota

### Step 3: Configure
Add to your `config/.env`:
```bash
NUMVERIFY_API_KEY=your_api_key_here
```

### Step 4: Test
```bash
curl "http://apilayer.net/api/validate?access_key=YOUR_KEY&number=14158586273"
```

**Free Tier Limits:**
- 1,000 requests per month
- HTTPS support in paid plans only
- No commercial use in free tier

## 🔍 Google Custom Search API (REQUIRED)

Enables advanced Google dorking capabilities.

### Step 1: Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project or select existing
3. Enable billing (free tier available)

### Step 2: Enable Custom Search API
1. Go to API Library
2. Search for "Custom Search API"
3. Enable the API

### Step 3: Create API Credentials
1. Go to Credentials section
2. Click "Create Credentials" → "API Key"
3. Copy the generated API key
4. (Optional) Restrict key to Custom Search API

### Step 4: Create Custom Search Engine
1. Visit [Google Custom Search](https://cse.google.com/)
2. Click "Add" to create new search engine
3. Enter `*.com` as site to search
4. Click "Create"
5. Get your Search Engine ID

### Step 5: Configure Search Engine
1. In your custom search settings:
   - Turn ON "Search the entire web"
   - Turn ON "Image search"
   - Turn OFF "SafeSearch" (optional)

### Step 6: Configure Framework
Add to your `config/.env`:
```bash
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_search_engine_id
```

### Step 7: Test
```bash
curl "https://www.googleapis.com/customsearch/v1?key=YOUR_KEY&cx=YOUR_CSE_ID&q=test"
```

**Free Tier Limits:**
- 100 search queries per day
- $5 per 1,000 queries after free tier

## 📱 Twilio API (RECOMMENDED)

Enhanced phone number validation and caller ID services.

### Step 1: Create Twilio Account
1. Visit [twilio.com](https://www.twilio.com/)
2. Sign up for free trial account
3. Verify your phone number

### Step 2: Get Credentials
1. Go to Twilio Console
2. Find your Account SID and Auth Token
3. Note these credentials

### Step 3: Configure
Add to your `config/.env`:
```bash
TWILIO_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
```

### Step 4: Test
```bash
curl -X GET "https://lookups.twilio.com/v2/PhoneNumbers/+14158586273?Fields=carrier" \
-u "YOUR_SID:YOUR_TOKEN"
```

**Pricing:**
- Carrier lookup: $0.01 per query
- Free trial includes credits

## 📧 Hunter.io API (RECOMMENDED)

Email discovery and verification services.

### Step 1: Create Account
1. Visit [hunter.io](https://hunter.io/)
2. Sign up with email
3. Verify your account

### Step 2: Get API Key
1. Go to API section in dashboard
2. Copy your API key
3. Note your monthly quota

### Step 3: Configure
Add to your `config/.env`:
```bash
HUNTER_API_KEY=your_hunter_api_key
```

### Step 4: Test
```bash
curl "https://api.hunter.io/v2/account?api_key=YOUR_KEY"
```

**Free Tier Limits:**
- 50 searches per month
- 500 verifications per month

## 🔎 Shodan API (RECOMMENDED)

Internet device and infrastructure search.

### Step 1: Create Account
1. Visit [shodan.io](https://www.shodan.io/)
2. Create account
3. Verify email

### Step 2: Get API Key
1. Go to Account section
2. Find your API key
3. Note your query credits

### Step 3: Configure
Add to your `config/.env`:
```bash
SHODAN_KEY=your_shodan_api_key
```

### Step 4: Test
```bash
curl "https://api.shodan.io/api-info?key=YOUR_KEY"
```

**Free Tier:**
- Limited query credits
- Paid plans available for more queries

## 🔐 Have I Been Pwned API (OPTIONAL)

Data breach database access.

### Step 1: Subscribe
1. Visit [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key)
2. Subscribe to API access ($3.50/month)
3. Get your API key

### Step 2: Configure
Add to your `config/.env`:
```bash
HAVEIBEENPWNED_API_KEY=your_hibp_api_key
```

### Step 3: Test
```bash
curl -H "hibp-api-key: YOUR_KEY" \
"https://haveibeenpwned.com/api/v3/breachedaccount/test@example.com"
```

**Pricing:**
- $3.50 per month
- 10,000 requests per month included

## 📡 OpenCellID API (OPTIONAL)

Cell tower and location data.

### Step 1: Register
1. Visit [opencellid.org](https://opencellid.org/)
2. Create free account
3. Verify email

### Step 2: Get API Key
1. Go to API section
2. Generate API key
3. Note usage limits

### Step 3: Configure
Add to your `config/.env`:
```bash
OPENCELLID_API_KEY=your_opencellid_key
```

### Step 4: Test
```bash
curl "https://api.opencellid.org/cell/get?key=YOUR_KEY&mcc=310&mnc=260&lac=1&cellid=1"
```

**Note:** This API often has connectivity issues and may not be reliable.

## ⚙️ Configuration Management

### Environment File Structure
Your `config/.env` should look like this:
```bash
# Essential APIs
NUMVERIFY_API_KEY=your_numverify_key
GOOGLE_API_KEY=your_google_key
GOOGLE_CSE_ID=your_search_engine_id

# Recommended APIs
TWILIO_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
HUNTER_API_KEY=your_hunter_key
SHODAN_KEY=your_shodan_key

# Optional APIs
HAVEIBEENPWNED_API_KEY=your_hibp_key
OPENCELLID_API_KEY=your_opencellid_key
```

### Testing Your Configuration
Run the API test suite:
```bash
python test_apis.py
```

Expected output:
```
==================================================
Phone OSINT Framework - API Testing
==================================================

Testing NumVerify API...
[OK] NumVerify working! Test response:
  Carrier: AT&T Mobility LLC
  Location: Novato

Testing Google Search API...
[OK] Google Search API working!
  Total results: ~5,020,000,000

Testing Twilio API...
[OK] Twilio API working!
  Account Status: active

# ... etc
```

## 💰 Cost Management

### Free Tier Optimization
To stay within free tiers:
1. **NumVerify**: Monitor monthly usage
2. **Google**: Limit to 100 searches/day
3. **Hunter.io**: Track monthly searches
4. **Shodan**: Use sparingly

### Monitoring Usage
```bash
# Check API usage periodically
python -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv('config/.env')

# Check Hunter.io usage
response = requests.get(f\"https://api.hunter.io/v2/account?api_key={os.getenv('HUNTER_API_KEY')}\")
data = response.json()
print(f\"Hunter.io: {data['data']['requests']['used']}/{data['data']['requests']['available']}\")
"
```

### Setting Up Alerts
Consider setting up usage alerts:
1. **Google Cloud Console**: Set billing alerts
2. **Twilio**: Set usage alerts in console
3. **Hunter.io**: Monitor dashboard regularly

## 🔒 Security Best Practices

### API Key Security
1. **Never commit keys**: Always use `.env` files
2. **Rotate regularly**: Change keys quarterly
3. **Use environment-specific keys**: Different keys for dev/prod
4. **Monitor usage**: Watch for unusual activity

### Access Control
```bash
# Restrict API keys by IP (where possible)
# Set up API key permissions properly
# Use least-privilege principles
```

### Key Storage
```bash
# Good: Environment variables
export NUMVERIFY_API_KEY="your_key"

# Bad: Hardcoded in source
api_key = "your_key_here"  # NEVER DO THIS
```

## 🚨 Troubleshooting API Issues

### Common Problems

**401 Unauthorized**
- Check API key validity
- Verify key format
- Check account status

**403 Forbidden**
- Check API permissions
- Verify IP restrictions
- Check account limits

**429 Rate Limited**
- Slow down requests
- Check usage quotas
- Upgrade plan if needed

**Connection Errors**
- Check network connectivity
- Verify API endpoints
- Check firewall settings

### Debug Mode
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python phone_osint_master.py +1234567890
```

### Testing Individual APIs
```bash
# Test specific API
python -c "
from test_apis import test_numverify
test_numverify()
"
```

## 📚 Advanced Configuration

### Proxy Support
If behind corporate proxy:
```bash
# In your .env file
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=http://proxy.company.com:8080
```

### Custom Timeouts
```bash
# Adjust timeouts for slow connections
REQUEST_TIMEOUT=60
```

### Rate Limiting
```bash
# Customize rate limits
RATE_LIMIT_PER_MINUTE=5
SLEEP_BETWEEN_REQUESTS=2
```

## 🔄 API Updates and Maintenance

### Stay Updated
1. Monitor API provider announcements
2. Check for new API versions
3. Update framework when needed
4. Test after updates

### Backup Plans
1. Have alternative API keys ready
2. Consider multiple providers for critical APIs
3. Implement graceful degradation

This completes the API setup process. Your Phone OSINT Framework should now be ready for investigations!