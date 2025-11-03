#!/usr/bin/env python3
"""
Shared Chrome configuration for Selenium across the framework
Optimized for headless operation with minimal error output
"""

from selenium.webdriver.chrome.options import Options
import logging
import random

def get_stealth_chrome_options(user_agent=None):
    """
    Get Chrome options optimized for headless scraping with minimal errors
    Suppresses all the common Chrome internal errors on Windows
    """
    
    options = Options()
    
    # Basic headless configuration
    options.add_argument('--headless=new')  # Use new headless mode (Chrome 109+)
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    # Suppress specific error types from your logs
    options.add_argument('--log-level=3')  # Only show fatal errors
    options.add_argument('--silent')  # General silence flag
    options.add_argument('--disable-logging')  # Disable most logging
    
    # GPU/WebGL error suppression
    options.add_argument('--disable-gpu-process-crash-limit')
    options.add_argument('--disable-features=VizDisplayCompositor,WebRTC')
    options.add_argument('--disable-webgl')
    options.add_argument('--disable-webgl2')
    options.add_argument('--disable-3d-apis')
    
    # USB/Device enumeration error suppression  
    options.add_argument('--disable-device-discovery-notifications')
    options.add_argument('--disable-usb-keyboard-detect')
    
    # Google services error suppression (GCM, sync, etc.)
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    options.add_argument('--disable-ipc-flooding-protection')
    options.add_argument('--disable-component-extensions-with-background-pages')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-extensions')
    
    # Audio/media error suppression
    options.add_argument('--mute-audio')
    options.add_argument('--disable-audio-output')
    
    # Memory and performance optimization
    options.add_argument('--memory-pressure-off')
    options.add_argument('--max_old_space_size=4096')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-backgrounding-occluded-windows')
    
    # Security and privacy (good for OSINT)
    options.add_argument('--incognito')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Anti-detection measures
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Set user agent if provided
    if user_agent:
        options.add_argument(f'--user-agent={user_agent}')
    else:
        # Default user agents for anti-detection
        default_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ]
        options.add_argument(f'--user-agent={random.choice(default_user_agents)}')
    
    # Prefs to disable additional features that cause errors
    prefs = {
        'profile.default_content_setting_values.notifications': 2,
        'profile.default_content_settings.popups': 0,
        'profile.managed_default_content_settings.images': 2,  # Don't load images (faster)
        'profile.default_content_setting_values.geolocation': 2,
        'profile.default_content_setting_values.media_stream': 2,
    }
    options.add_experimental_option('prefs', prefs)
    
    return options

def get_debug_chrome_options():
    """
    Get Chrome options for debugging (shows more output)
    Use only when troubleshooting specific Chrome issues
    """
    options = Options()
    
    # Basic configuration
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    
    # Show more information for debugging
    options.add_argument('--enable-logging')
    options.add_argument('--log-level=0')  # Show all logs
    options.add_argument('--verbose')
    
    return options

# Default configuration for the framework
def get_default_chrome_options():
    """Get the standard Chrome configuration for the Phone OSINT Framework"""
    return get_stealth_chrome_options()

def create_silent_webdriver():
    """
    Create a Chrome WebDriver with maximum error suppression
    Redirects Chrome's stderr to suppress internal error messages
    """
    import os
    import subprocess
    from selenium import webdriver
    
    # Get stealth options
    options = get_stealth_chrome_options()
    
    # Create Chrome service with stderr suppression
    try:
        from selenium.webdriver.chrome.service import Service
        
        # Redirect stderr to devnull to suppress Chrome internal errors
        service = Service()
        
        # Set environment variables to suppress additional Chrome output
        env = os.environ.copy()
        env['CHROME_LOG_FILE'] = 'NUL' if os.name == 'nt' else '/dev/null'
        
        # Create driver with suppressed output
        driver = webdriver.Chrome(
            service=service,
            options=options
        )
        
        # Set timeouts
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        return driver
        
    except Exception as e:
        # Fallback to regular webdriver if service configuration fails
        logging.getLogger(__name__).warning(f"Silent webdriver creation failed, using regular: {e}")
        return webdriver.Chrome(options=options)

# User agent lists for rotation
COMMON_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36", 
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]
