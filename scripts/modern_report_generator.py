#!/usr/bin/env python3
"""
Modern Report Generator with Data Visualizations
Enhanced HTML reports with dashboard-style layout, charts, and drill-downs
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class ModernReportGenerator:
    """Generate modern, interactive HTML reports with data visualizations"""
    
    def __init__(self, phone_number: str, all_data: Dict, output_dir: str):
        self.phone = phone_number
        self.data = all_data
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        
    def generate(self):
        """Generate comprehensive modern HTML report"""
        
        # Calculate summary statistics
        stats = self._calculate_statistics()
        
        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Phone OSINT Report: {self.phone}</title>
    
    <!-- Chart.js for visualizations -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            color: #2c3e50;
            line-height: 1.6;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .header .meta {{
            opacity: 0.9;
            font-size: 0.9rem;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        /* Dashboard Cards */
        .dashboard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        
        .stat-card .icon {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .stat-card .value {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin: 0.5rem 0;
        }}
        
        .stat-card .label {{
            color: #7f8c8d;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        /* Sections */
        .section {{
            background: white;
            margin-bottom: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow: hidden;
        }}
        
        .section-header {{
            background: #f8f9fa;
            padding: 1.25rem 1.5rem;
            border-bottom: 2px solid #e9ecef;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .section-header:hover {{
            background: #e9ecef;
        }}
        
        .section-header h2 {{
            font-size: 1.3rem;
            color: #2c3e50;
        }}
        
        .section-header .toggle {{
            font-size: 1.5rem;
            transition: transform 0.3s;
        }}
        
        .section-header .toggle.rotated {{
            transform: rotate(180deg);
        }}
        
        .section-content {{
            padding: 1.5rem;
            max-height: 1000px;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}
        
        .section-content.collapsed {{
            max-height: 0;
            padding: 0 1.5rem;
        }}
        
        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }}
        
        th {{
            background: #667eea;
            color: white;
            padding: 0.75rem;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 0.75rem;
            border-bottom: 1px solid #e9ecef;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        /* Badges */
        .badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.85rem;
            font-weight: 600;
            margin: 0.25rem;
        }}
        
        .badge-success {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-danger {{ background: #f8d7da; color: #721c24; }}
        .badge-info {{ background: #d1ecf1; color: #0c5460; }}
        .badge-primary {{ background: #cfe2ff; color: #084298; }}
        
        /* Timeline */
        .timeline {{
            position: relative;
            padding-left: 2rem;
        }}
        
        .timeline-item {{
            position: relative;
            padding-bottom: 1.5rem;
        }}
        
        .timeline-item::before {{
            content: '';
            position: absolute;
            left: -2rem;
            top: 0.5rem;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #667eea;
        }}
        
        .timeline-item::after {{
            content: '';
            position: absolute;
            left: -1.55rem;
            top: 1.2rem;
            width: 2px;
            height: calc(100% - 1rem);
            background: #e9ecef;
        }}
        
        .timeline-item:last-child::after {{
            display: none;
        }}
        
        /* Charts */
        .chart-container {{
            position: relative;
            height: 300px;
            margin: 1rem 0;
        }}
        
        /* Lists */
        .data-list {{
            list-style: none;
            padding: 0;
        }}
        
        .data-list li {{
            padding: 0.75rem;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .data-list li:last-child {{
            border-bottom: none;
        }}
        
        /* Alerts */
        .alert {{
            padding: 1rem 1.25rem;
            border-radius: 8px;
            margin: 1rem 0;
        }}
        
        .alert-success {{ background: #d4edda; border-left: 4px solid #28a745; }}
        .alert-warning {{ background: #fff3cd; border-left: 4px solid #ffc107; }}
        .alert-danger {{ background: #f8d7da; border-left: 4px solid #dc3545; }}
        .alert-info {{ background: #d1ecf1; border-left: 4px solid #17a2b8; }}
        
        /* Grid */
        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin: 1rem 0;
        }}
        
        .grid-3 {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }}
        
        /* Profile Card */
        .profile-card {{
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .profile-card h4 {{
            color: #667eea;
            margin-bottom: 0.5rem;
        }}
        
        .profile-card p {{
            margin: 0.25rem 0;
            font-size: 0.9rem;
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .dashboard {{
                grid-template-columns: 1fr;
            }}
            
            .grid-2, .grid-3 {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>📱 Phone OSINT Investigation Report</h1>
            <div class="meta">
                <strong>Target:</strong> {self.phone} &nbsp;|&nbsp; 
                <strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')} &nbsp;|&nbsp;
                <strong>Investigation ID:</strong> {self.output_dir.name}
            </div>
        </div>
    </div>
    
    <div class="container">
        <!-- Executive Dashboard -->
        <div class="dashboard">
            {self._generate_stat_cards(stats)}
        </div>
        
        <!-- Main Content Sections -->
        {self._generate_identity_section()}
        {self._generate_contact_section()}
        {self._generate_digital_footprint_section()}
        {self._generate_location_section()}
        {self._generate_professional_section()}
        {self._generate_security_section()}
        {self._generate_social_media_section()}
        {self._generate_technical_section()}
        {self._generate_recommendations_section()}
    </div>
    
    <script>
        // Toggle section collapse/expand
        document.querySelectorAll('.section-header').forEach(header => {{
            header.addEventListener('click', () => {{
                const content = header.nextElementSibling;
                const toggle = header.querySelector('.toggle');
                content.classList.toggle('collapsed');
                toggle.classList.toggle('rotated');
            }});
        }});
        
        // Initialize charts
        {self._generate_chart_scripts()}
    </script>
</body>
</html>"""
        
        # Save report
        report_path = self.output_dir / "investigation_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return str(report_path)
    
    def _calculate_statistics(self) -> Dict:
        """Calculate summary statistics for dashboard"""
        results = self.data.get('results', {})
        
        # Count all discovered items
        names_found = len(results.get('name_hunting', {}).get('primary_names', []))
        emails_found = len(results.get('email_discovery', {}).get('emails', []))
        
        # Social media platforms
        social = results.get('social_media', {})
        platforms_found = sum(1 for platform in social.values() if isinstance(platform, dict) and platform.get('found'))
        
        # Breaches
        breaches = results.get('breaches', {})
        if not isinstance(breaches, dict):
            breaches = {}
        emails_breached = len(breaches.get('breached_emails', []))
        
        # Risk score
        risk_score = self._calculate_risk_score()
        
        # Usernames
        all_usernames = []
        for platform, data in social.items():
            if isinstance(data, dict) and data.get('usernames_discovered'):
                all_usernames.extend(data['usernames_discovered'])
        
        # Locations
        locations = set()
        if results.get('validation', {}).get('summary', {}).get('location'):
            locations.add(results['validation']['summary']['location'])
        
        return {
            'names_found': names_found,
            'emails_found': emails_found,
            'platforms_found': platforms_found,
            'usernames_found': len(all_usernames),
            'emails_breached': emails_breached,
            'locations_found': len(locations),
            'risk_score': risk_score,
            'investigation_complete': results.get('investigation_complete', False)
        }
    
    def _calculate_risk_score(self) -> int:
        """Calculate risk score 0-10"""
        score = 5  # Base score
        
        results = self.data.get('results', {})
        
        # Adjust based on findings
        if results.get('breaches', {}).get('found'):
            score += 3
        
        social = results.get('social_media', {})
        platforms_found = sum(1 for platform in social.values() if isinstance(platform, dict) and platform.get('found'))
        if platforms_found > 5:
            score -= 1  # More online presence = lower privacy risk
        
        # Cap at 0-10
        return max(0, min(10, score))
    
    def _generate_stat_cards(self, stats: Dict) -> str:
        """Generate dashboard stat cards"""
        cards = [
            ('👤', stats['names_found'], 'Names Discovered', 'primary'),
            ('📧', stats['emails_found'], 'Email Addresses', 'info'),
            ('🔗', stats['platforms_found'], 'Social Platforms', 'success'),
            ('🚨', stats['emails_breached'], 'Breached Accounts', 'danger' if stats['emails_breached'] > 0 else 'success'),
            ('⚠️', f"{stats['risk_score']}/10", 'Risk Score', 'danger' if stats['risk_score'] > 7 else 'warning' if stats['risk_score'] > 4 else 'success'),
        ]
        
        html = ''
        for icon, value, label, badge_type in cards:
            html += f"""
            <div class="stat-card">
                <div class="icon">{icon}</div>
                <div class="value">{value}</div>
                <div class="label">{label}</div>
            </div>
            """
        
        return html
    
    def _generate_identity_section(self) -> str:
        """Generate identity intelligence section"""
        try:
            results = self.data.get('results', {})
            if not isinstance(results, dict):
                results = {}
            name_data = results.get('name_hunting', {})
            if not isinstance(name_data, dict):
                name_data = {}
        except Exception as e:
            self.logger.error(f"Error accessing name data: {e}")
            name_data = {}
        
        html = f"""
        <div class="section">
            <div class="section-header">
                <h2>👤 Identity Intelligence</h2>
                <span class="toggle">▼</span>
            </div>
            <div class="section-content">
        """
        
        # Primary names
        primary_names = name_data.get('primary_names', [])
        if primary_names:
            html += f"""
            <div class="alert alert-success">
                <strong>🎯 Primary Identity:</strong> {', '.join(primary_names)}
            </div>
            """
        
        # Name sources table
        if name_data.get('all_names'):
            html += """
            <h3>Discovered Names by Source</h3>
            <table>
                <tr>
                    <th>Name</th>
                    <th>Source</th>
                    <th>Confidence</th>
                </tr>
            """
            
            for name_info in name_data.get('all_names', []):
                # Handle both string names and dict objects
                if isinstance(name_info, str):
                    # Simple string name - create a dict structure
                    name_dict = {'name': name_info, 'source': 'Unknown', 'confidence': 0.5}
                elif isinstance(name_info, dict):
                    name_dict = name_info
                else:
                    continue  # Skip invalid entries
                
                confidence = name_dict.get('confidence', 0.5)
                conf_badge = 'success' if confidence > 0.8 else 'warning' if confidence > 0.5 else 'danger'
                html += f"""
                <tr>
                    <td><strong>{name_dict.get('name', 'Unknown')}</strong></td>
                    <td>{name_dict.get('source', 'Unknown')}</td>
                    <td><span class="badge badge-{conf_badge}">{confidence:.1%}</span></td>
                </tr>
                """
            
            html += "</table>"
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _generate_contact_section(self) -> str:
        """Generate contact discovery section"""
        email_data = self.data.get('results', {}).get('email_discovery', {})
        validation_data = self.data.get('results', {}).get('validation', {})
        
        # Ensure validation_data is a dict and extract summary safely
        if isinstance(validation_data, dict):
            validation = validation_data.get('summary', {})
            # Ensure validation is also a dict
            if not isinstance(validation, dict):
                validation = {}
        else:
            validation = {}
        
        html = f"""
        <div class="section">
            <div class="section-header">
                <h2>📧 Contact Discovery</h2>
                <span class="toggle">▼</span>
            </div>
            <div class="section-content">
        """
        
        # Phone validation
        if validation:
            html += f"""
            <h3>Phone Number Analysis</h3>
            <div class="grid-2">
                <div class="profile-card">
                    <h4>Carrier Information</h4>
                    <p><strong>Carrier:</strong> {validation.get('carrier', 'Unknown')}</p>
                    <p><strong>Line Type:</strong> {validation.get('line_type', 'Unknown')}</p>
                    <p><strong>Country:</strong> {validation.get('country', 'Unknown')}</p>
                </div>
                <div class="profile-card">
                    <h4>Location Data</h4>
                    <p><strong>Location:</strong> {validation.get('location', 'Unknown')}</p>
                    <p><strong>Valid:</strong> {'✅ Yes' if validation.get('valid') else '❌ No'}</p>
                </div>
            </div>
            """
        
        # Email addresses
        emails = email_data.get('emails', [])
        if emails:
            html += f"""
            <h3>Discovered Email Addresses ({len(emails)})</h3>
            <table>
                <tr>
                    <th>Email</th>
                    <th>Source</th>
                    <th>Confidence</th>
                    <th>Status</th>
                </tr>
            """
            
            for email in emails[:20]:  # Limit to first 20
                conf = email.get('confidence', 0.5)
                conf_badge = 'success' if conf > 0.8 else 'warning' if conf > 0.5 else 'info'
                html += f"""
                <tr>
                    <td><strong>{email.get('email', 'Unknown')}</strong></td>
                    <td>{email.get('source', 'Unknown')}</td>
                    <td><span class="badge badge-{conf_badge}">{conf:.1%}</span></td>
                    <td>{'✅ Verified' if email.get('verified') else '🔍 Unverified'}</td>
                </tr>
                """
            
            if len(emails) > 20:
                html += f"""
                <tr>
                    <td colspan="4" style="text-align: center; font-style: italic;">
                        ...and {len(emails) - 20} more emails
                    </td>
                </tr>
                """
            
            html += "</table>"
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _generate_digital_footprint_section(self) -> str:
        """Generate digital footprint timeline"""
        return """
        <div class="section">
            <div class="section-header">
                <h2>🌐 Digital Footprint</h2>
                <span class="toggle">▼</span>
            </div>
            <div class="section-content">
                <p><em>Platform presence, account activity timeline, and online visibility analysis.</em></p>
                <canvas id="platformsChart"></canvas>
            </div>
        </div>
        """
    
    def _generate_location_section(self) -> str:
        """Generate location intelligence section"""
        return """
        <div class="section">
            <div class="section-header">
                <h2>📍 Location Intelligence</h2>
                <span class="toggle">▼</span>
            </div>
            <div class="section-content collapsed">
                <p><em>Current and historical locations, addresses, and geographic data.</em></p>
            </div>
        </div>
        """
    
    def _generate_professional_section(self) -> str:
        """Generate professional profile section"""
        employment = self.data.get('results', {}).get('employment_intelligence', {})
        
        html = """
        <div class="section">
            <div class="section-header">
                <h2>💼 Professional Profile</h2>
                <span class="toggle">▼</span>
            </div>
            <div class="section-content collapsed">
        """
        
        if employment:
            html += f"""
            <div class="grid-2">
                <div class="profile-card">
                    <h4>Employment Intelligence</h4>
                    <p><em>Employment history and professional affiliations discovered during investigation.</em></p>
                </div>
            </div>
            """
        else:
            html += "<p><em>No professional information discovered.</em></p>"
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _generate_security_section(self) -> str:
        """Generate security assessment section with breach data"""
        breaches_data = self.data.get('results', {}).get('breaches', {})
        
        # Ensure breaches_data is a dict
        if not isinstance(breaches_data, dict):
            breaches_data = {}
        
        html = """
        <div class="section">
            <div class="section-header">
                <h2>🔒 Security Assessment</h2>
                <span class="toggle">▼</span>
            </div>
            <div class="section-content">
        """
        
        # Breach data
        if breaches_data.get('found'):
            breached_emails = breaches_data.get('breached_emails', [])
            total_breaches = breaches_data.get('total_breaches', 0)
            
            html += f"""
            <div class="alert alert-danger">
                <strong>🚨 DATA BREACH ALERT:</strong> {len(breached_emails)} email(s) compromised in {total_breaches} breaches!
            </div>
            
            <h3>Compromised Accounts</h3>
            """
            
            for breach_info in breached_emails:
                email = breach_info.get('email')
                breach_count = breach_info.get('breach_count', 0)
                breaches_list = breach_info.get('breaches', [])
                
                html += f"""
                <div class="profile-card" style="border-left-color: #dc3545;">
                    <h4 style="color: #dc3545;">🚨 {email}</h4>
                    <p><strong>Breaches:</strong> {breach_count}</p>
                    <p><strong>Compromised Data:</strong> {', '.join(breaches_list[:5])}</p>
                </div>
                """
        else:
            emails_checked = breaches_data.get('emails_checked', 0)
            if emails_checked > 0:
                html += f"""
                <div class="alert alert-success">
                    <strong>✅ ALL CLEAR:</strong> {emails_checked} email(s) checked - no breaches found!
                </div>
                """
            else:
                html += """
                <div class="alert alert-info">
                    <strong>ℹ️</strong> No emails available for breach checking
                </div>
                """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _generate_social_media_section(self) -> str:
        """Generate social media presence section"""
        social = self.data.get('results', {}).get('social_media', {})
        
        # Ensure social is a dict
        if not isinstance(social, dict):
            social = {}
        
        html = """
        <div class="section">
            <div class="section-header">
                <h2>📱 Social Media Presence</h2>
                <span class="toggle">▼</span>
            </div>
            <div class="section-content collapsed">
        """
        
        if social:
            platforms_html = ""
            for platform_name, platform_data in social.items():
                if isinstance(platform_data, dict) and platform_data.get('found'):
                    profiles = platform_data.get('profiles', [])
                    usernames = platform_data.get('usernames_discovered', [])
                    
                    platforms_html += f"""
                    <div class="profile-card">
                        <h4>{platform_name.title()}</h4>
                        <p><strong>Profiles Found:</strong> {len(profiles)}</p>
                        <p><strong>Usernames:</strong> {', '.join([u.get('username', '') for u in usernames[:3]])}</p>
                    </div>
                    """
            
            if platforms_html:
                html += f'<div class="grid-3">{platforms_html}</div>'
            else:
                html += "<p><em>No social media profiles discovered.</em></p>"
        else:
            html += "<p><em>Social media scan not completed.</em></p>"
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _generate_technical_section(self) -> str:
        """Generate technical details section"""
        return """
        <div class="section">
            <div class="section-header">
                <h2>🔧 Technical Details</h2>
                <span class="toggle">▼</span>
            </div>
            <div class="section-content collapsed">
                <p><em>Phone number validation, carrier analysis, and technical metadata.</em></p>
            </div>
        </div>
        """
    
    def _generate_recommendations_section(self) -> str:
        """Generate security recommendations"""
        risk_score = self._calculate_risk_score()
        
        html = """
        <div class="section">
            <div class="section-header">
                <h2>💡 Recommendations</h2>
                <span class="toggle">▼</span>
            </div>
            <div class="section-content">
        """
        
        if risk_score > 7:
            html += """
            <div class="alert alert-danger">
                <strong>HIGH RISK:</strong> Immediate action recommended
            </div>
            <ul class="data-list">
                <li>✅ Change passwords on all compromised accounts</li>
                <li>✅ Enable 2FA on all online accounts</li>
                <li>✅ Monitor credit reports for fraud</li>
                <li>✅ Consider identity theft protection service</li>
            </ul>
            """
        elif risk_score > 4:
            html += """
            <div class="alert alert-warning">
                <strong>MODERATE RISK:</strong> Review and secure accounts
            </div>
            <ul class="data-list">
                <li>✅ Review account security settings</li>
                <li>✅ Enable 2FA where possible</li>
                <li>✅ Use unique passwords for each account</li>
            </ul>
            """
        else:
            html += """
            <div class="alert alert-success">
                <strong>LOW RISK:</strong> Maintain current security practices
            </div>
            <ul class="data-list">
                <li>✅ Continue using strong passwords</li>
                <li>✅ Keep 2FA enabled</li>
                <li>✅ Monitor for unusual activity</li>
            </ul>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _generate_chart_scripts(self) -> str:
        """Generate JavaScript for Chart.js visualizations"""
        social = self.data.get('results', {}).get('social_media', {})
        
        # Count platforms
        platforms_found = {}
        for platform_name, platform_data in social.items():
            if isinstance(platform_data, dict) and platform_data.get('found'):
                platforms_found[platform_name] = len(platform_data.get('profiles', []))
        
        if platforms_found:
            labels = list(platforms_found.keys())
            data = list(platforms_found.values())
            
            return f"""
            const platformsCtx = document.getElementById('platformsChart');
            if (platformsCtx) {{
                new Chart(platformsCtx, {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(labels)},
                        data: {json.dumps(data)},
                        datasets: [{{
                            label: 'Profiles Found',
                            data: {json.dumps(data)},
                            backgroundColor: 'rgba(102, 126, 234, 0.6)',
                            borderColor: 'rgba(102, 126, 234, 1)',
                            borderWidth: 2
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{
                                    precision: 0
                                }}
                            }}
                        }}
                    }}
                }});
            }}
            """
        
        return "// No chart data available"

