#!/usr/bin/env python3
"""
IPRoyal Proxy Manager
Handles IPRoyal residential proxy integration with IP reputation filtering
Prioritizes clean, high-reputation IPs for scraping
"""
import os
import time
import json
import random
import logging
import requests
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ProxyInfo:
    """Proxy information with reputation tracking"""
    proxy_string: str  # format: user:pass@host:port
    ip_address: str
    country: str
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    avg_response_time: float = 0.0
    captcha_rate: float = 0.0
    reputation_score: float = 100.0  # 0-100, higher is better

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total

    @property
    def is_healthy(self) -> bool:
        """Check if proxy is in good standing"""
        return (
            self.success_rate >= 0.7 and
            self.captcha_rate < 0.3 and
            self.reputation_score >= 50.0
        )


class IPRoyalManager:
    """
    Manages IPRoyal residential proxies with intelligent rotation
    Focuses on clean IPs with good reputation
    """

    def __init__(self, config_file: str = 'config/iproyal_config.json'):
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        self.config = self._load_config()

        self.proxies: List[ProxyInfo] = []
        self.blacklist: set = set()  # IPs that consistently fail

        # IP reputation preferences
        self.preferred_countries = ['US', 'GB', 'CA', 'DE', 'AU', 'NL']  # Clean IP reputation
        self.avoid_countries = ['CN', 'RU', 'IN', 'VN', 'ID']  # Often flagged

        self._load_proxies()

    def _load_config(self) -> Dict:
        """Load IPRoyal configuration"""
        default_config = {
            'username': '',  # IPRoyal username
            'password': '',  # IPRoyal password
            'proxy_host': 'pr.iproyal.com',  # IPRoyal gateway
            'proxy_port': 12321,
            'rotation_mode': 'sticky',  # 'sticky' or 'rotating'
            'session_duration': 600,  # Sticky session duration in seconds
            'min_reputation_score': 60.0,  # Minimum IP reputation to use
            'max_captcha_rate': 0.2,  # Max acceptable CAPTCHA rate
            'geo_targeting': True,  # Prefer clean-reputation countries
            'auto_blacklist_threshold': 5,  # Failures before blacklisting IP
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")

        return default_config

    def _save_config(self):
        """Save configuration"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def _load_proxies(self):
        """Load proxy list from IPRoyal credentials"""
        if not self.config.get('username') or not self.config.get('password'):
            self.logger.warning("IPRoyal credentials not configured")
            return

        # IPRoyal uses a gateway approach - generate proxy strings
        # Format: username-country-session:password@host:port

        # For residential proxies, we can specify country codes
        if self.config.get('geo_targeting'):
            countries = self.preferred_countries
        else:
            countries = ['']  # Random country

        for country in countries:
            for session_id in range(1, 11):  # Create 10 sessions per country
                # IPRoyal format: username-country-sessionID:password@host:port
                if country:
                    username = f"{self.config['username']}-country-{country.lower()}-session-{session_id}"
                else:
                    username = f"{self.config['username']}-session-{session_id}"

                proxy_string = f"{username}:{self.config['password']}@{self.config['proxy_host']}:{self.config['proxy_port']}"

                proxy_info = ProxyInfo(
                    proxy_string=proxy_string,
                    ip_address='rotating',  # IPRoyal rotates automatically
                    country=country or 'RANDOM'
                )

                self.proxies.append(proxy_info)

        self.logger.info(f"Loaded {len(self.proxies)} IPRoyal proxy sessions")

    def get_proxy(self, prefer_clean: bool = True) -> Optional[str]:
        """
        Get next proxy with intelligent selection

        Args:
            prefer_clean: Prioritize high-reputation IPs

        Returns:
            Proxy string in format 'username:password@host:port'
        """
        if not self.proxies:
            self.logger.error("No proxies available")
            return None

        # Filter healthy proxies
        healthy_proxies = [p for p in self.proxies if p.is_healthy]

        if not healthy_proxies:
            self.logger.warning("No healthy proxies, using all available")
            healthy_proxies = self.proxies

        # Filter by country preference if enabled
        if prefer_clean and self.config.get('geo_targeting'):
            preferred = [p for p in healthy_proxies if p.country in self.preferred_countries]
            if preferred:
                healthy_proxies = preferred

        # Sort by reputation score
        healthy_proxies.sort(key=lambda p: (
            p.reputation_score,
            p.success_rate,
            -p.captcha_rate
        ), reverse=True)

        # Select from top 20% with some randomness
        top_tier_count = max(1, len(healthy_proxies) // 5)
        selected_proxy = random.choice(healthy_proxies[:top_tier_count])

        selected_proxy.last_used = datetime.now()

        self.logger.debug(
            f"Selected proxy: {selected_proxy.country} "
            f"(rep: {selected_proxy.reputation_score:.1f}, "
            f"success: {selected_proxy.success_rate:.2%}, "
            f"captcha: {selected_proxy.captcha_rate:.2%})"
        )

        return selected_proxy.proxy_string

    def report_success(self, proxy_string: str, response_time: float = 0.0, got_captcha: bool = False):
        """
        Report successful proxy usage

        Args:
            proxy_string: The proxy that was used
            response_time: Response time in seconds
            got_captcha: Whether a CAPTCHA was encountered
        """
        proxy = self._find_proxy(proxy_string)
        if not proxy:
            return

        proxy.success_count += 1

        # Update average response time
        if response_time > 0:
            if proxy.avg_response_time == 0:
                proxy.avg_response_time = response_time
            else:
                proxy.avg_response_time = (proxy.avg_response_time * 0.8) + (response_time * 0.2)

        # Update CAPTCHA rate
        total_requests = proxy.success_count + proxy.failure_count
        if got_captcha:
            proxy.captcha_rate = ((proxy.captcha_rate * (total_requests - 1)) + 1.0) / total_requests
        else:
            proxy.captcha_rate = (proxy.captcha_rate * (total_requests - 1)) / total_requests

        # Update reputation score
        self._update_reputation(proxy)

        self.logger.debug(f"Proxy success reported: {proxy.country} (new rep: {proxy.reputation_score:.1f})")

    def report_failure(self, proxy_string: str, error_type: str = 'unknown'):
        """
        Report proxy failure

        Args:
            proxy_string: The proxy that failed
            error_type: Type of error (timeout, connection, captcha, ban)
        """
        proxy = self._find_proxy(proxy_string)
        if not proxy:
            return

        proxy.failure_count += 1

        # Severe penalties for certain errors
        if error_type in ['ban', 'blocked']:
            proxy.reputation_score = max(0, proxy.reputation_score - 30)
        elif error_type == 'captcha':
            proxy.reputation_score = max(0, proxy.reputation_score - 10)
        else:
            proxy.reputation_score = max(0, proxy.reputation_score - 5)

        # Auto-blacklist consistently failing IPs
        if proxy.failure_count >= self.config.get('auto_blacklist_threshold', 5):
            if proxy.success_rate < 0.3:
                self.blacklist.add(proxy.proxy_string)
                self.logger.warning(f"Blacklisted proxy: {proxy.country} (too many failures)")

        self.logger.debug(f"Proxy failure reported: {proxy.country} (new rep: {proxy.reputation_score:.1f})")

    def _find_proxy(self, proxy_string: str) -> Optional[ProxyInfo]:
        """Find proxy by proxy string"""
        for proxy in self.proxies:
            if proxy.proxy_string == proxy_string:
                return proxy
        return None

    def _update_reputation(self, proxy: ProxyInfo):
        """
        Update proxy reputation score based on performance
        Score factors:
        - Success rate (40%)
        - CAPTCHA rate (30%)
        - Response time (20%)
        - Recency (10%)
        """
        # Success rate component (0-40 points)
        success_component = proxy.success_rate * 40

        # CAPTCHA rate component (0-30 points, inverted)
        captcha_component = (1.0 - proxy.captcha_rate) * 30

        # Response time component (0-20 points)
        # Assume good response time is < 2 seconds
        if proxy.avg_response_time > 0:
            response_component = max(0, (2.0 - proxy.avg_response_time) / 2.0) * 20
        else:
            response_component = 20

        # Recency component (0-10 points)
        if proxy.last_used:
            hours_since_use = (datetime.now() - proxy.last_used).total_seconds() / 3600
            recency_component = max(0, (24 - hours_since_use) / 24) * 10
        else:
            recency_component = 10

        # Calculate new reputation
        new_reputation = success_component + captcha_component + response_component + recency_component

        # Smooth transition (80% old, 20% new)
        proxy.reputation_score = (proxy.reputation_score * 0.8) + (new_reputation * 0.2)

    def get_statistics(self) -> Dict:
        """Get proxy pool statistics"""
        if not self.proxies:
            return {}

        healthy = [p for p in self.proxies if p.is_healthy]
        total_requests = sum(p.success_count + p.failure_count for p in self.proxies)
        total_successes = sum(p.success_count for p in self.proxies)

        avg_reputation = sum(p.reputation_score for p in self.proxies) / len(self.proxies)
        avg_captcha_rate = sum(p.captcha_rate for p in self.proxies) / len(self.proxies)

        return {
            'total_proxies': len(self.proxies),
            'healthy_proxies': len(healthy),
            'blacklisted': len(self.blacklist),
            'total_requests': total_requests,
            'overall_success_rate': total_successes / total_requests if total_requests > 0 else 0,
            'avg_reputation_score': avg_reputation,
            'avg_captcha_rate': avg_captcha_rate,
            'countries': list(set(p.country for p in self.proxies)),
        }

    def export_for_yandex(self) -> List[str]:
        """
        Export clean proxies in format for yandex_scraper.py
        Only returns high-reputation proxies
        """
        clean_proxies = [
            p.proxy_string for p in self.proxies
            if p.reputation_score >= self.config.get('min_reputation_score', 60.0)
            and p.proxy_string not in self.blacklist
        ]

        self.logger.info(f"Exported {len(clean_proxies)} clean proxies for Yandex scraping")
        return clean_proxies


def setup_iproyal(username: str, password: str, prefer_clean_ips: bool = True) -> IPRoyalManager:
    """
    Quick setup for IPRoyal integration

    Args:
        username: Your IPRoyal username
        password: Your IPRoyal password
        prefer_clean_ips: Use geo-targeting for clean IP reputation

    Returns:
        Configured IPRoyalManager instance
    """
    config = {
        'username': username,
        'password': password,
        'geo_targeting': prefer_clean_ips,
        'min_reputation_score': 70.0 if prefer_clean_ips else 50.0,
    }

    # Save config
    os.makedirs('config', exist_ok=True)
    with open('config/iproyal_config.json', 'w') as f:
        json.dump(config, f, indent=2)

    return IPRoyalManager()


if __name__ == '__main__':
    # Example usage
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("IPRoyal Proxy Manager Setup")
    print("=" * 50)
    print()
    print("Get your credentials from: https://iproyal.com/dashboard")
    print()

    username = input("IPRoyal Username: ").strip()
    password = input("IPRoyal Password: ").strip()

    print("\nPrefer clean IPs? (Targets US/GB/CA/DE/AU for better reputation)")
    clean = input("Use clean IPs? [Y/n]: ").strip().lower() != 'n'

    print("\nSetting up IPRoyal integration...")
    manager = setup_iproyal(username, password, prefer_clean_ips=clean)

    print("\n✓ IPRoyal configured successfully!")
    print(f"\nProxy Statistics:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nExporting clean proxies for Yandex...")
    clean_proxies = manager.export_for_yandex()

    with open('config/proxies.txt', 'w') as f:
        for proxy in clean_proxies:
            f.write(proxy + '\n')

    print(f"✓ Saved {len(clean_proxies)} clean proxies to config/proxies.txt")
    print("\nReady to use! Run an investigation to test.")
