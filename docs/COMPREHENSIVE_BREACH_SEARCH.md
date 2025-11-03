# Comprehensive Breach Database Search

## 🎯 Multi-Parameter Breach Searching

Instead of ONLY searching by email (HIBP limitation), the framework now searches breach databases using **ALL discovered data**:

- ✅ **Phone numbers** - Direct phone number breach lookups
- ✅ **Emails** - Traditional HIBP + comprehensive databases
- ✅ **Usernames** - REAL discovered usernames from LinkedIn/GitHub/social
- ✅ **Names** - Full name searches in breach records
- ✅ **Addresses** - Physical address searches (if discovered)
- ✅ **Domains** - Company/email domain searches

---

## 🔍 Breach Databases Integrated

### 1. **Have I Been Pwned (HIBP)** - Email Only
- **Search By**: Email addresses only
- **Coverage**: 12+ billion compromised accounts
- **Speed**: Fast (1.5s rate limit)
- **Cost**: Free with API key
- **API Key**: `HAVEIBEENPWNED_API_KEY`

**Limitation**: Email-only searches

---

### 2. **DeHashed** - COMPREHENSIVE (BEST!)
- **Search By**: Email, username, phone, IP, name, address, domain, VIN, hash
- **Coverage**: 23+ billion records
- **Speed**: Fast
- **Cost**: Paid ($5-50/month)
- **API Keys**: `DEHASHED_USERNAME` + `DEHASHED_API_KEY`

**Example Query**:
```
phone:"6199303063" OR email:"ryan@example.com" OR username:"rlindley-cyber" OR name:"Ryan Lindley"
```

**Why It's Better**:
- ✅ Searches by phone number directly
- ✅ Searches by username (real ones!)
- ✅ Searches by name
- ✅ Combines multiple parameters with OR logic

---

### 3. **LeakCheck** - Phone/Username/Email
- **Search By**: Email, username, phone, hash, domain
- **Coverage**: 12+ billion records
- **Speed**: Moderate (1s rate limit per search)
- **Cost**: Free tier + paid
- **API Key**: `LEAKCHECK_API_KEY`

**Multiple Searches**:
```
1. Search phone: 6199303063
2. Search email: ryan@example.com  
3. Search username: rlindley-cyber
```

**Why It's Good**:
- ✅ Phone number support
- ✅ Username support
- ✅ Free tier available

---

### 4. **Intelligence X** - Dark Web Aggregation
- **Search By**: Email, phone, domain, URL, Bitcoin address
- **Coverage**: Dark web, paste sites, breaches
- **Speed**: Moderate
- **Cost**: Credit-based ($2-10)
- **API Key**: `INTELX_API_KEY`

**Why It's Valuable**:
- ✅ Dark web monitoring
- ✅ Paste site aggregation
- ✅ Real-time leak detection

---

## 📊 How It Works

### Traditional Approach (HIBP Only)
```
1. Search email: ryan@example.com in HIBP
2. If no email discovered → "No breaches found"
```

**Problem**: Phone numbers, usernames, names can't be searched!

---

### New Comprehensive Approach
```
🔍 COMPREHENSIVE BREACH DATABASE CHECK
🎯 Searching with: phone, emails, usernames, names, addresses

Built 23 search parameters:
   phone: 2 items (6199303063, 19303063)
   emails: 8 items
   usernames: 10 items (ryan-lindley-77175b8, rlindley-cyber, ...)
   names: 1 item (Ryan Lindley)
   addresses: 0 items

🔍 DeHashed multi-parameter search:
   Query: phone:"6199303063" OR email:"ryan@example.com" OR username:"rlindley-cyber" OR ...

🚨 BREACH ALERT!
📧 HIBP: 2 emails compromised
📊 DeHashed: 15 breach records found
👤 LeakCheck: Found 5 additional usernames!
🔥 BONUS: 3 NEW emails discovered from breach data!
```

**Benefits**:
- ✅ Finds breaches even without email addresses
- ✅ Discovers NEW emails/usernames from breach data
- ✅ Much more comprehensive coverage
- ✅ Uses ALL discovered intelligence

---

## 🚀 Setup

### Required (Works Without Setup)
```bash
# HIBP (email-only but free)
HAVEIBEENPWNED_API_KEY=your_key_here
```

### Recommended (Phone + Username + Name Search)
```bash
# DeHashed - BEST comprehensive search
DEHASHED_USERNAME=your_username
DEHASHED_API_KEY=your_api_key

# LeakCheck - Good phone/username support  
LEAKCHECK_API_KEY=your_key_here

# Intelligence X - Dark web monitoring
INTELX_API_KEY=your_key_here
```

### Get API Keys

**DeHashed** (Recommended):
1. Visit: https://www.dehashed.com/register
2. Plans: $5-50/month
3. Add credentials to `config/.env`

**LeakCheck**:
1. Visit: https://leakcheck.io/api
2. Free tier available
3. Add key to `config/.env`

**Intelligence X**:
1. Visit: https://intelx.io/signup
2. Credit-based pricing
3. Add key to `config/.env`

---

## 📈 Expected Results

### Example Output
```json
{
  "found": true,
  "databases_checked": ["hibp", "dehashed", "leakcheck"],
  "breached_emails": [
    {
      "email": "ryan@example.com",
      "breach_count": 3,
      "breaches": ["LinkedIn", "Dropbox", "Collection #1"]
    }
  ],
  "comprehensive_search": {
    "found": true,
    "databases_checked": ["leakcheck", "intelligence_x", "dehashed"],
    "breaches_found": [
      {
        "source": "Database_2021",
        "phone": "6199303063",
        "email": "discovered@email.com",
        "username": "rlindley-cyber",
        "database": "dehashed",
        "search_type": "phone"
      }
    ],
    "associated_emails": ["new1@gmail.com", "new2@yahoo.com"],
    "associated_usernames": ["rlindley", "ryan_l"],
    "total_records": 15
  },
  "additional_emails_discovered": ["new1@gmail.com", "new2@yahoo.com"],
  "additional_usernames_discovered": ["rlindley", "ryan_l"]
}
```

---

## 🎓 How Searches Work

### DeHashed (Most Powerful)
```python
# Builds comprehensive OR query
query = 'phone:"6199303063" OR email:"ryan@example.com" OR username:"rlindley-cyber" OR name:"Ryan Lindley"'

# Single API call returns ALL matches
# Discovers:
# - Emails associated with phone
# - Usernames associated with email
# - Names associated with username
# - Cross-referencing across all parameters!
```

### LeakCheck (Multiple Searches)
```python
# Searches each parameter type separately
1. search(phone="6199303063", type="phone")
2. search(email="ryan@example.com", type="email")
3. search(username="rlindley-cyber", type="username")

# Each search returns associated data
# Aggregates results across all searches
```

### Intelligence X (Dark Web)
```python
# Searches phone numbers in dark web/pastes
search(term="6199303063", target=1)  # Phone search

# Returns associated emails, usernames from leaks
```

---

## 💡 Key Advantages

### 1. **Works Without Email Discovery**
Before: "No emails found" → "No breach check possible"
After: Search by phone/username/name → Discover emails IN breach data!

### 2. **Discovers NEW Intelligence**
Breach data reveals:
- Emails you didn't know about
- Usernames from other platforms
- Associated accounts
- Cross-platform connections

### 3. **More Accurate**
Using multiple data points = higher chance of finding the right person's breach records

### 4. **Comprehensive Coverage**
- HIBP: 12B records (email)
- DeHashed: 23B records (ALL parameters)
- LeakCheck: 12B records (phone/username/email)
- Intelligence X: Dark web + pastes

**Total**: 40+ billion records searchable!

---

## ⚙️ Integration

### Automatic
The comprehensive breach search runs automatically during investigations.

```bash
python phone_osint_master.py +16199303063
```

**Process**:
1. Discover data (names, emails, usernames, addresses)
2. Build search parameters from ALL discovered data
3. Search HIBP (emails)
4. Search DeHashed/LeakCheck/IntelX (phone/username/name/address)
5. Combine results
6. Report findings + newly discovered emails/usernames

---

## 📋 Status by Database

| Database | Configured | Search By | Coverage |
|----------|-----------|-----------|----------|
| **HIBP** | ✅ Yes | Email | 12B+ |
| **DeHashed** | ❌ Not yet | Email, Phone, Username, Name, Address, IP, Domain | 23B+ |
| **LeakCheck** | ❌ Not yet | Email, Phone, Username, Hash | 12B+ |
| **Intelligence X** | ❌ Not yet | Email, Phone, Domain, URL | Dark Web |

**Current**: HIBP only (email-based)
**With all APIs**: Full multi-parameter comprehensive search!

---

## 🎯 Recommendation

### Minimum Setup
```
HAVEIBEENPWNED_API_KEY=xxx  # Free, email-only
```

### Recommended Setup
```
HAVEIBEENPWNED_API_KEY=xxx       # Free, email
DEHASHED_USERNAME=xxx             # Paid, COMPREHENSIVE
DEHASHED_API_KEY=xxx              # Best investment!
```

### Maximum Setup
```
HAVEIBEENPWNED_API_KEY=xxx        # Email
DEHASHED_USERNAME=xxx              # Phone/username/name/address/email
DEHASHED_API_KEY=xxx               # MOST POWERFUL
LEAKCHECK_API_KEY=xxx              # Phone/username/email
INTELX_API_KEY=xxx                 # Dark web monitoring
```

**Cost Analysis**:
- HIBP: Free
- DeHashed: $5-20/month (BEST VALUE - searches everything!)
- LeakCheck: Free tier + $5-10/month
- Intelligence X: $2-10 credits

**Recommended**: Get DeHashed ($10/month) for comprehensive multi-parameter searches.

---

**Status**: ✅ IMPLEMENTED

**Files**:
- `scripts/phone_breach_databases.py` - Comprehensive multi-parameter breach searcher
- `phone_osint_master.py` - Integrated into main investigation flow
- `docs/COMPREHENSIVE_BREACH_SEARCH.md` - This documentation

**Test it**: Add API keys and run investigation to see multi-parameter breach searching in action!




