# Yandex Scraping for Phone OSINT

## Overview

Yandex is the dominant search engine in Russia and Eastern Europe, often containing data not indexed by Google. This makes it particularly valuable for OSINT investigations involving:

- Russian/Eastern European phone numbers
- International phone numbers with Russian connections
- Social media profiles on VK.com, OK.ru, Mail.ru
- Documents and public records in Cyrillic

## Features

### Built-in Anti-Detection
- **User-Agent rotation**: Mimics different browsers
- **Proxy rotation**: Cycles through proxy pool to avoid IP bans
- **CAPTCHA detection**: Identifies when blocked and retries
- **Rate limiting**: Smart delays between requests (8-15 seconds)
- **Retry logic**: Automatically retries failed requests

### Search Strategy
1. **Priority 1**: Name + Phone (most effective)
2. **Priority 2**: Email + Phone
3. **Priority 3**: Phone only (fallback)

### Result Categories
- **Russian Social Media**: VK.com, OK.ru, Mail.ru
- **International Social**: Facebook, LinkedIn, Instagram
- **Documents**: PDFs and other file types
- **Forums**: Discussion boards and communities
- **Other**: Miscellaneous findings

## Setup

### Option 1: Local Setup (Testing)

1. **Install dependencies** (already in requirements.txt):
```bash
pip install requests beautifulsoup4
```

2. **Get free proxies** (unreliable, for testing only):
```bash
./venv/bin/python scripts/proxy_scraper.py
```

This creates `config/proxies.txt` with working free proxies.

### Option 2: VPS Setup (Production)

For reliable, high-volume scraping, deploy on a VPS:

#### Recommended VPS Providers
- **Hetzner Cloud**: €4.50/month (best value)
- **DigitalOcean**: $6/month
- **Vultr**: $5/month
- **Linode**: $5/month

#### Deployment Steps

1. **Provision VPS** with Ubuntu 22.04 or Debian 12

2. **Upload framework** to VPS:
```bash
# From your local machine
scp -r phone-osint-framework root@YOUR_VPS_IP:/tmp/
```

3. **Run deployment script**:
```bash
ssh root@YOUR_VPS_IP
cd /tmp/phone-osint-framework
chmod +x deploy_vps.sh
./deploy_vps.sh
```

4. **Configure API keys**:
```bash
nano /opt/phone-osint/config/.env
# Add your API keys
```

5. **Add proxies** (optional but recommended):
```bash
# Option A: Scrape free proxies
cd /opt/phone-osint
./venv/bin/python scripts/proxy_scraper.py

# Option B: Use paid residential proxies (recommended)
# Add to /opt/phone-osint/config/proxies.txt
# Format: IP:PORT or user:pass@IP:PORT
```

6. **Start service**:
```bash
supervisorctl start phone-osint-web
```

7. **Access web interface**:
```
http://YOUR_VPS_IP
```

## Proxy Options

### Free Proxies (Not Recommended)
- **Pros**: Free, easy to get
- **Cons**: Very unreliable, slow, often blocked, short-lived
- **Use case**: Testing only

```bash
./venv/bin/python scripts/proxy_scraper.py
```

### Paid Residential Proxies (Recommended)
- **Providers**: Webshare ($3.49/GB), IPRoyal, Proxy-Cheap
- **Pros**: Reliable, high success rate, real residential IPs
- **Cons**: Costs money
- **Use case**: Production investigations

**Setup**:
1. Sign up for proxy service
2. Get proxy list (format: `IP:PORT` or `user:pass@IP:PORT`)
3. Add to `config/proxies.txt` (one per line)

### ISP Proxies (Best Performance)
- **Providers**: Bright Data, Smartproxy, Oxylabs
- **Pros**: Fast + reliable + residential-looking
- **Cons**: More expensive
- **Use case**: High-volume or time-sensitive investigations

## Usage

### Automatic Integration

Yandex scraping runs automatically during full investigations:

```bash
./venv/bin/python phone_osint_master.py +13053932786
```

Or via web interface at http://localhost:5000

### Manual Testing

Test Yandex scraper directly:

```python
from scripts.yandex_scraper import YandexScraper, load_free_proxy_list

# Load proxies
proxies = load_free_proxy_list()

# Create scraper
scraper = YandexScraper(
    phone_number="+13053932786",
    enriched_identity={'primary_names': ['John Doe']},
    proxy_list=proxies
)

# Execute search
results = scraper.search()

# View results
print(f"Russian social: {len(results['russian_social'])}")
print(f"International social: {len(results['social_media'])}")
print(f"Forums: {len(results['forums'])}")
```

## Rate Limiting & Anti-Bot Measures

### Yandex's Defenses
- **CAPTCHA**: Triggered after 10-20 requests from same IP
- **IP blocking**: Temporary or permanent based on behavior
- **Fingerprinting**: Detects automated browsers

### Our Counter-Measures
1. **Proxy rotation**: New IP for each request (if proxies available)
2. **Random delays**: 8-15 seconds between searches
3. **Browser mimicry**: Realistic headers and user agents
4. **CAPTCHA detection**: Automatically detects and retries
5. **Exponential backoff**: Longer waits after failures

## Troubleshooting

### No Results Found
- **Check**: Are proxies working? Run proxy scraper again
- **Check**: Is Yandex blocking your IP? Try from different network
- **Check**: Are search queries too specific? Simplify query

### CAPTCHA Every Request
- **Solution**: Add more proxies to rotation pool
- **Solution**: Increase delays between requests (edit `yandex_scraper.py`, line 323)
- **Solution**: Use residential proxies instead of datacenter

### Proxies Not Working
```bash
# Re-scrape and validate proxies
./venv/bin/python scripts/proxy_scraper.py

# Check proxy file exists and has content
cat config/proxies.txt | wc -l
```

### ImportError: No module named 'yandex_scraper'
```bash
# Make sure you're in the venv
source venv/bin/activate

# Or use full path
./venv/bin/python phone_osint_master.py +NUMBER
```

## Performance Tips

1. **Use residential proxies**: 10x better success rate than free proxies
2. **Deploy on VPS**: Avoids local network restrictions
3. **Limit queries**: Each phone search runs 5 queries max
4. **Monitor logs**: Watch for CAPTCHA patterns
5. **Rotate proxies**: Keep proxy list fresh (re-scrape daily)

## Advanced: Custom Proxy Sources

Edit `scripts/yandex_scraper.py` to add custom proxy sources:

```python
def load_free_proxy_list() -> List[str]:
    # Add your custom proxy source here
    proxies = []

    # Example: Load from API
    response = requests.get('https://your-proxy-api.com/list')
    proxies = response.json()['proxies']

    # Example: Load from database
    # proxies = db.query("SELECT ip_port FROM proxies WHERE active=1")

    return proxies
```

## Cost Breakdown

### DIY VPS Setup
- **VPS**: $5-6/month (Hetzner, DigitalOcean, Vultr)
- **Proxies**: $3.49/GB (Webshare) - 1GB ≈ 1000 searches
- **Total**: ~$8-10/month for unlimited searches

### vs. Paid API
- **ScraperAPI**: $49/month for 100k requests
- **Oxylabs**: $99/month minimum
- **SerpAPI**: $50/month for 5k searches

**Our solution is 5-10x cheaper!**

## Security Considerations

1. **Defensive Use Only**: Only investigate numbers you have authorization to research
2. **Proxy Privacy**: Free proxies may log your traffic
3. **Rate Limiting**: Respect Yandex's terms of service
4. **Data Storage**: Securely store investigation results
5. **API Keys**: Never commit proxies or API keys to git

## Next Steps

1. ✅ Deploy to VPS for production use
2. ✅ Set up residential proxy service
3. ✅ Test with sample investigations
4. ✅ Monitor success rates and adjust delays
5. ✅ Integrate findings into HTML reports

## Support

For issues or questions:
- Check logs: `/var/log/phone-osint/web.out.log` (VPS)
- Review code: `scripts/yandex_scraper.py`
- GitHub issues: [Your repo URL]

---

**Remember**: This tool is for defensive security and authorized investigations only.
