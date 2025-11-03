#!/usr/bin/env python3
"""
Unified Data Models for Phone OSINT Framework
Standardized data structures for consistent collection across all modules
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

@dataclass
class ProfileData:
    """Comprehensive profile data structure"""
    # Identity
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    nicknames: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    
    # Usernames & Handles
    username: Optional[str] = None
    display_name: Optional[str] = None
    handle: Optional[str] = None
    
    # Bio & Description
    bio: Optional[str] = None
    description: Optional[str] = None
    headline: Optional[str] = None
    tagline: Optional[str] = None
    
    # Contact
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    websites: List[str] = field(default_factory=list)
    
    # Location
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    coordinates: Optional[Dict[str, float]] = None  # {'lat': ..., 'lon': ...}
    
    # Professional
    occupation: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    industry: Optional[str] = None
    employer_history: List[Dict] = field(default_factory=list)  # [{'company': ..., 'title': ..., 'dates': ...}]
    
    # Education
    education: List[Dict] = field(default_factory=list)  # [{'school': ..., 'degree': ..., 'field': ...}]
    
    # Social Metadata
    followers_count: Optional[int] = None
    following_count: Optional[int] = None
    posts_count: Optional[int] = None
    verified: bool = False
    
    # Media
    profile_photo_url: Optional[str] = None
    cover_photo_url: Optional[str] = None
    media_urls: List[str] = field(default_factory=list)
    
    # Timestamps
    joined_date: Optional[str] = None
    last_active: Optional[str] = None
    
    # Connections & Associations
    connections: List[str] = field(default_factory=list)  # Other usernames
    associates: List[str] = field(default_factory=list)  # Real names
    groups: List[str] = field(default_factory=list)
    
    # Skills & Interests
    skills: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    
    # Platform Specific
    platform: str = 'unknown'
    profile_url: Optional[str] = None
    profile_id: Optional[str] = None
    
    # Confidence & Source
    confidence_score: float = 0.0  # 0.0 - 1.0
    source: str = 'unknown'
    discovered_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Raw Data
    raw_data: Dict = field(default_factory=dict)  # Store original scraped data
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def merge_with(self, other: 'ProfileData') -> 'ProfileData':
        """Merge two profiles, combining data"""
        merged = ProfileData()
        
        for key in asdict(self).keys():
            self_val = getattr(self, key)
            other_val = getattr(other, key)
            
            # Lists: combine and deduplicate
            if isinstance(self_val, list):
                combined = list(set(self_val + other_val))
                setattr(merged, key, combined)
            # Strings: prefer non-None, longer value
            elif isinstance(self_val, str):
                if self_val and other_val:
                    setattr(merged, key, self_val if len(self_val) >= len(other_val) else other_val)
                else:
                    setattr(merged, key, self_val or other_val)
            # Numbers: prefer higher value
            elif isinstance(self_val, (int, float)):
                setattr(merged, key, max(self_val or 0, other_val or 0))
            # Booleans: OR operation
            elif isinstance(self_val, bool):
                setattr(merged, key, self_val or other_val)
            # Dicts: deep merge
            elif isinstance(self_val, dict):
                setattr(merged, key, {**self_val, **other_val})
            else:
                setattr(merged, key, self_val or other_val)
        
        return merged


@dataclass
class InvestigationData:
    """Complete investigation data structure"""
    # Target
    phone_number: str
    target_name: Optional[str] = None
    
    # Profiles
    profiles: List[ProfileData] = field(default_factory=list)
    
    # Aggregated Data
    all_names: List[str] = field(default_factory=list)
    all_usernames: List[str] = field(default_factory=list)
    all_emails: List[str] = field(default_factory=list)
    all_locations: List[str] = field(default_factory=list)
    all_employers: List[str] = field(default_factory=list)
    all_schools: List[str] = field(default_factory=list)
    all_websites: List[str] = field(default_factory=list)
    all_associates: List[str] = field(default_factory=list)
    all_skills: List[str] = field(default_factory=list)
    all_interests: List[str] = field(default_factory=list)
    
    # Metadata
    investigation_start: str = field(default_factory=lambda: datetime.now().isoformat())
    investigation_end: Optional[str] = None
    total_profiles_found: int = 0
    platforms_checked: List[str] = field(default_factory=list)
    
    def add_profile(self, profile: ProfileData):
        """Add a profile and update aggregated data"""
        self.profiles.append(profile)
        self.total_profiles_found += 1
        
        # Update aggregated lists
        if profile.full_name:
            self.all_names.append(profile.full_name)
        if profile.username:
            self.all_usernames.append(profile.username)
        self.all_emails.extend(profile.emails)
        if profile.location:
            self.all_locations.append(profile.location)
        if profile.company:
            self.all_employers.append(profile.company)
        self.all_employers.extend([e.get('company') for e in profile.employer_history if e.get('company')])
        self.all_schools.extend([e.get('school') for e in profile.education if e.get('school')])
        self.all_websites.extend(profile.websites)
        self.all_associates.extend(profile.associates)
        self.all_skills.extend(profile.skills)
        self.all_interests.extend(profile.interests)
        
        # Deduplicate
        self.all_names = list(set(self.all_names))
        self.all_usernames = list(set(self.all_usernames))
        self.all_emails = list(set(self.all_emails))
        self.all_locations = list(set(self.all_locations))
        self.all_employers = list(set([e for e in self.all_employers if e]))
        self.all_schools = list(set([s for s in self.all_schools if s]))
        self.all_websites = list(set(self.all_websites))
        self.all_associates = list(set(self.all_associates))
        self.all_skills = list(set(self.all_skills))
        self.all_interests = list(set(self.all_interests))
    
    def get_primary_identity(self) -> Dict:
        """Determine primary identity from all profiles"""
        if not self.profiles:
            return {}
        
        # Name consensus
        name_counts = {}
        for name in self.all_names:
            name_counts[name] = name_counts.get(name, 0) + 1
        primary_name = max(name_counts, key=name_counts.get) if name_counts else None
        
        # Location consensus
        loc_counts = {}
        for loc in self.all_locations:
            loc_counts[loc] = loc_counts.get(loc, 0) + 1
        primary_location = max(loc_counts, key=loc_counts.get) if loc_counts else None
        
        # Most recent employer
        all_employers = []
        for profile in self.profiles:
            if profile.employer_history:
                all_employers.extend(profile.employer_history)
            elif profile.company:
                all_employers.append({'company': profile.company, 'title': profile.job_title})
        
        current_employer = all_employers[0] if all_employers else None
        
        return {
            'primary_name': primary_name,
            'primary_location': primary_location,
            'current_employer': current_employer,
            'total_emails': len(self.all_emails),
            'total_usernames': len(self.all_usernames),
            'total_profiles': self.total_profiles_found,
            'platforms': list(set([p.platform for p in self.profiles]))
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'phone_number': self.phone_number,
            'target_name': self.target_name,
            'profiles': [p.to_dict() for p in self.profiles],
            'aggregated_data': {
                'names': self.all_names,
                'usernames': self.all_usernames,
                'emails': self.all_emails,
                'locations': self.all_locations,
                'employers': self.all_employers,
                'schools': self.all_schools,
                'websites': self.all_websites,
                'associates': self.all_associates,
                'skills': self.all_skills,
                'interests': self.all_interests
            },
            'primary_identity': self.get_primary_identity(),
            'metadata': {
                'investigation_start': self.investigation_start,
                'investigation_end': self.investigation_end,
                'total_profiles_found': self.total_profiles_found,
                'platforms_checked': self.platforms_checked
            }
        }


# Helper functions for data extraction

def extract_location_components(location_string: str) -> Dict:
    """Extract city, state, country from location string"""
    if not location_string:
        return {}
    
    components = [c.strip() for c in location_string.split(',')]
    
    result = {'full': location_string}
    
    if len(components) >= 3:
        result['city'] = components[0]
        result['state'] = components[1]
        result['country'] = components[2]
    elif len(components) == 2:
        result['city'] = components[0]
        result['state'] = components[1]
    elif len(components) == 1:
        result['city'] = components[0]
    
    return result


def extract_name_components(full_name: str) -> Dict:
    """Extract first, middle, last from full name"""
    if not full_name:
        return {}
    
    parts = full_name.strip().split()
    
    result = {'full_name': full_name}
    
    if len(parts) >= 3:
        result['first_name'] = parts[0]
        result['middle_name'] = ' '.join(parts[1:-1])
        result['last_name'] = parts[-1]
    elif len(parts) == 2:
        result['first_name'] = parts[0]
        result['last_name'] = parts[1]
    elif len(parts) == 1:
        result['first_name'] = parts[0]
    
    return result


def standardize_phone(phone: str) -> str:
    """Standardize phone number format"""
    import re
    digits = re.sub(r'[^\d]', '', phone)
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    if len(digits) == 10:
        return f"+1{digits}"
    return phone


def standardize_email(email: str) -> str:
    """Standardize email format"""
    return email.lower().strip()




