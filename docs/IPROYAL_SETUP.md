# IPRoyal Integration Guide

## Why IPRoyal?

- **Privacy**: UAE-based (non-Five Eyes jurisdiction)
- **Clean IPs**: Intelligent geo-targeting for high-reputation IPs
- **Affordable**: $2.45/GB residential proxies
- **No commitment**: Pay-as-you-go, traffic never expires
- **Easy integration**: Standard HTTP/SOCKS5 format

## Quick Setup

### 1. Get IPRoyal Account

1. Sign up at https://iproyal.com
2. Purchase residential proxy credits ($10 minimum)
3. Get your credentials from dashboard

### 2. Configure Framework

Run the interactive setup:

```bash
./venv/bin/python scripts/iproyal_manager.py
```

This will:
- Save your IPRoyal credentials to `config/iproyal_config.json`
- Generate proxy pool with clean IP targeting
- Export proxies to `config/proxies.txt`

**Manual configuration** (optional):

Edit `config/iproyal_config.json`:
```json
{
  "username": "your_iproyal_username",
  "password": "your_iproyal_password",
  "proxy_host": "pr.iproyal.com",
  "proxy_port": 12321,
  "rotation_mode": "sticky",
  "session_duration": 600,
  "min_reputation_score": 70.0,
  "max_captcha_rate": 0.2,
  "geo_targeting": true,
  "auto_blacklist_threshold": 5
}
```

### 3. Use in Investigations

Proxies are automatically used by Yandex scraper and any future scrapers:

```bash
# CLI
./venv/bin/python phone_osint_master.py +13053932786

# Web interface
# Navigate to http://localhost:5000 and run scan
```

## Clean IP Targeting

The IPRoyal manager intelligently selects IPs based on reputation:

### Preferred Countries (Clean Reputation)
- 🇺🇸 United States
- 🇬🇧 United Kingdom
- 🇨🇦 Canada
- 🇩🇪 Germany
- 🇦🇺 Australia
- 🇳🇱 Netherlands

These countries have:
- Lower fraud scores
- Better trust ratings
- Less likely to be on blocklists
- Higher success rates for web scraping

### Avoided Countries (High Fraud Scores)
- China, Russia, India, Vietnam, Indonesia
- Often flagged by anti-bot systems
- Higher CAPTCHA rates

## IP Reputation Scoring

Each proxy is scored 0-100 based on:

1. **Success Rate (40%)**: How often requests succeed
2. **CAPTCHA Rate (30%)**: How often CAPTCHAs are encountered (lower is better)
3. **Response Time (20%)**: How fast the proxy responds
4. **Recency (10%)**: How recently the proxy was used

**Only proxies with reputation ≥ 70 are used for scraping.**

## Automatic IP Management

### Smart Rotation
- Top 20% of proxies by reputation are prioritized
- Random selection within top tier (prevents patterns)
- Sticky sessions maintain same IP for 10 minutes (configurable)

### Auto-Blacklisting
- Proxies that fail 5+ times are auto-blacklisted
- Proxies with <30% success rate are removed from pool
- CAPTCHA-heavy IPs are penalized

### Performance Tracking
```bash
# View statistics
./venv/bin/python -c "
from scripts.iproyal_manager import IPRoyalManager
manager = IPRoyalManager()
stats = manager.get_statistics()
print('Proxy Pool Stats:')
for k, v in stats.items():
    print(f'  {k}: {v}')
"
```

## Advanced Usage

### Programmatic Access

```python
from scripts.iproyal_manager import IPRoyalManager

# Initialize manager
manager = IPRoyalManager()

# Get clean proxy
proxy = manager.get_proxy(prefer_clean=True)
print(f"Using proxy: {proxy}")

# Make request
import requests
response = requests.get(
    'https://yandex.com/search?text=test',
    proxies={
        'http': f'http://{proxy}',
        'https': f'http://{proxy}'
    },
    timeout=15
)

# Report success/failure
if response.status_code == 200:
    manager.report_success(
        proxy,
        response_time=response.elapsed.total_seconds(),
        got_captcha='captcha' in response.text.lower()
    )
else:
    manager.report_failure(proxy, error_type='connection')

# View statistics
stats = manager.get_statistics()
print(f"Pool health: {stats['healthy_proxies']}/{stats['total_proxies']}")
```

### Integration with Yandex Scraper

The Yandex scraper automatically uses IPRoyal proxies if configured:

```python
from scripts.yandex_scraper import YandexScraper
from scripts.iproyal_manager import IPRoyalManager

# Get clean proxies from IPRoyal
manager = IPRoyalManager()
clean_proxies = manager.export_for_yandex()

# Use in scraper
scraper = YandexScraper(
    phone_number="+13053932786",
    enriched_identity={'primary_names': ['John Doe']},
    proxy_list=clean_proxies
)

results = scraper.search()
```

## Troubleshooting

### "No proxies available"
**Solution**: Run setup again
```bash
./venv/bin/python scripts/iproyal_manager.py
```

### Low success rates (<70%)
**Causes**:
- Website has strong anti-bot (use more proxies)
- IPRoyal credits exhausted (check dashboard)
- Proxies need refresh (re-export clean ones)

**Solution**:
```bash
# Re-export with higher reputation threshold
./venv/bin/python -c "
from scripts.iproyal_manager import IPRoyalManager
import json

manager = IPRoyalManager()
manager.config['min_reputation_score'] = 80.0  # Stricter
clean = manager.export_for_yandex()

with open('config/proxies.txt', 'w') as f:
    for p in clean:
        f.write(p + '\\n')

print(f'Exported {len(clean)} ultra-clean proxies')
"
```

### High CAPTCHA rate (>20%)
**Causes**:
- IPs are being flagged
- Too many requests too fast

**Solutions**:
1. Enable geo-targeting for cleaner IPs (already default)
2. Increase delays in Yandex scraper
3. Use more proxies to spread traffic

### Credentials invalid
**Check**:
1. Login to https://iproyal.com/dashboard
2. Verify username/password
3. Check you have active proxy credits
4. Update `config/iproyal_config.json`

## Cost Optimization

### Pay-as-you-go pricing
- **1 GB**: $2.45
- **10 GB**: $22.05 ($2.21/GB)
- **100 GB**: $196 ($1.96/GB)

### Traffic usage estimates
- **1 Yandex search**: ~0.5-1 MB
- **1 GB**: ~1,000-2,000 searches
- **100 investigations** (~5 searches each): ~0.25-0.5 GB

### Cost comparison
- **100 investigations/month**:
  - IPRoyal: ~$1.25/month
  - SerpAPI: $50/month minimum
  - **Savings: 97%**

## Security Best Practices

1. **Never commit credentials**: `config/iproyal_config.json` is in `.gitignore`
2. **Use environment variables** (optional):
   ```bash
   export IPROYAL_USER="your_username"
   export IPROYAL_PASS="your_password"
   ```
3. **Rotate credentials**: Change password quarterly
4. **Monitor usage**: Check IPRoyal dashboard regularly
5. **Limit exposure**: Only use for authorized investigations

## IPRoyal Dashboard

Access your account:
- **Dashboard**: https://iproyal.com/dashboard
- **Proxy settings**: https://iproyal.com/residential-proxies
- **Usage stats**: https://iproyal.com/dashboard/statistics
- **Billing**: https://iproyal.com/dashboard/billing

## Support

- **IPRoyal Support**: support@iproyal.com
- **Documentation**: https://iproyal.com/knowledge-base
- **Proxy tester**: https://iproyal.com/proxy-tester

---

**Ready to scrape with impunity using clean, high-reputation IPs! 🚀**
