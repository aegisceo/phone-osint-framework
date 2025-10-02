#!/usr/bin/env python3
"""
Decodo Residential Proxy Manager
Handles Decodo (formerly Smartproxy) residential proxy integration
"""
import os
import json
import logging
from typing import List, Dict, Optional

class DecodaProxyManager:
    """
    Manages Decodo residential proxies
    Simple wrapper for gate.decodo.com proxy gateway
    """

    def __init__(self, config_file: str = 'config/decodo_config.json'):
        self.logger = logging.getLogger(__name__)
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load Decodo configuration"""
        default_config = {
            'username': '',  # Decodo username
            'password': '',  # Decodo password
            'proxy_host': 'gate.decodo.com',
            'proxy_port': 7000,  # Decodo SOCKS5 port
            'proxy_protocol': 'socks5h',  # Use SOCKS5 (socks5h for DNS resolution through proxy)
            'session_type': 'rotating',  # 'rotating' or 'sticky'
            'country': '',  # Optional: 'us', 'gb', 'de', etc. Leave empty for random
            'city': '',     # Optional: specific city targeting
            'session_time': 10,  # Sticky session duration in minutes (1-30)
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

    def get_proxy_string(self) -> Optional[str]:
        """
        Get proxy string for requests
        Format: user-USERNAME-session-N:password@gate.decodo.com:7000

        Returns:
            Proxy string or None if not configured
        """
        if not self.config.get('username') or not self.config.get('password'):
            self.logger.error("Decodo credentials not configured")
            return None

        # Build username with Decodo SOCKS5 format: user-USERNAME-session-N
        username = f"user-{self.config['username']}"

        # Add session identifier
        username += f"-session-{self._get_session_id()}"

        # Add country targeting if specified
        if self.config.get('country'):
            username += f"-country-{self.config['country']}"

        # Add city targeting if specified
        if self.config.get('city'):
            username += f"-city-{self.config['city']}"

        proxy_string = (
            f"{username}:{self.config['password']}"
            f"@{self.config['proxy_host']}:{self.config['proxy_port']}"
        )

        return proxy_string

    def _get_session_id(self) -> str:
        """Generate or retrieve session ID for sticky sessions"""
        # Use a consistent session ID per instance
        # Could be made more sophisticated with time-based rotation
        return "1"

    def get_proxies_dict(self) -> Optional[Dict]:
        """
        Get proxies dictionary for requests library

        Returns:
            {'http': 'socks5h://...', 'https': 'socks5h://...'} or None
        """
        proxy_string = self.get_proxy_string()
        if not proxy_string:
            return None

        protocol = self.config.get('proxy_protocol', 'socks5h')
        return {
            'http': f'{protocol}://{proxy_string}',
            'https': f'{protocol}://{proxy_string}'
        }

    def export_for_yandex(self) -> List[str]:
        """
        Export proxy list in SOCKS5 format for yandex_scraper.py
        Creates multiple session IDs for rotation
        """
        if not self.config.get('username') or not self.config.get('password'):
            self.logger.error("Decodo credentials not configured")
            return []

        proxies = []
        protocol = self.config.get('proxy_protocol', 'socks5h')

        # Create 10 different sessions for rotation
        for session_num in range(1, 11):
            # Decodo SOCKS5 format: user-USERNAME-session-N
            username = f"user-{self.config['username']}-session-{session_num}"

            # Add country targeting if specified
            if self.config.get('country'):
                username += f"-country-{self.config['country']}"

            # Add city targeting if specified
            if self.config.get('city'):
                username += f"-city-{self.config['city']}"

            proxy_string = (
                f"{protocol}://{username}:{self.config['password']}"
                f"@{self.config['proxy_host']}:{self.config['proxy_port']}"
            )

            proxies.append(proxy_string)

        self.logger.info(f"Exported {len(proxies)} Decodo SOCKS5 proxy sessions")
        return proxies

    def test_connection(self) -> bool:
        """
        Test proxy connection
        Returns True if working, False otherwise
        """
        try:
            import requests

            proxies = self.get_proxies_dict()
            if not proxies:
                return False

            # Test with httpbin
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Proxy working! IP: {data.get('origin')}")
                return True

        except Exception as e:
            self.logger.error(f"Proxy test failed: {e}")

        return False


def setup_decodo(username: str, password: str, country: str = '', prefer_sticky: bool = False) -> DecodaProxyManager:
    """
    Quick setup for Decodo integration

    Args:
        username: Your Decodo username
        password: Your Decodo password
        country: Optional country code (us, gb, de, etc.)
        prefer_sticky: Use sticky sessions (same IP for 10 min)

    Returns:
        Configured DecodaProxyManager instance
    """
    config = {
        'username': username,
        'password': password,
        'proxy_host': 'gate.decodo.com',
        'proxy_port': 7000,
        'proxy_protocol': 'socks5h',
        'session_type': 'sticky' if prefer_sticky else 'rotating',
        'country': country,
        'session_time': 10,
    }

    # Save config
    os.makedirs('config', exist_ok=True)
    with open('config/decodo_config.json', 'w') as f:
        json.dump(config, f, indent=2)

    return DecodaProxyManager()


if __name__ == '__main__':
    # Setup wizard
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 60)
    print("Decodo Residential Proxy Setup")
    print("=" * 60)
    print()
    print("Get your credentials from: https://decodo.com/dashboard")
    print("Trial: 3 days, 100MB (requires credit card)")
    print()

    username = input("Decodo Username: ").strip()
    password = input("Decodo Password: ").strip()

    print("\nOptional: Target specific country for clean IPs")
    print("Examples: us, gb, ca, de, au (leave empty for random)")
    country = input("Country code [optional]: ").strip().lower()

    print("\nSession type:")
    print("  - Rotating: New IP every request (better for avoiding blocks)")
    print("  - Sticky: Same IP for 10 minutes (better for browsing)")
    sticky = input("Use sticky sessions? [y/N]: ").strip().lower() == 'y'

    print("\nSetting up Decodo integration...")
    manager = setup_decodo(username, password, country, prefer_sticky=sticky)

    print("\n✓ Decodo configured successfully!")

    print("\nTesting connection...")
    if manager.test_connection():
        print("✓ Proxy connection working!")
    else:
        print("✗ Proxy connection failed. Check credentials.")

    print("\nExporting proxies for Yandex scraper...")
    proxies = manager.export_for_yandex()

    with open('config/proxies.txt', 'w') as f:
        for proxy in proxies:
            f.write(proxy + '\n')

    print(f"✓ Saved {len(proxies)} proxy sessions to config/proxies.txt")
    print("\nReady to use! Run an investigation to test.")
    print("\nUsage:")
    print("  ./venv/bin/python phone_osint_master.py +13053932786")
