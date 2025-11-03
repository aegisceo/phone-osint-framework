#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime
from jinja2 import Template
import folium

class ReportGenerator:
    def __init__(self, phone_number, all_data, output_dir):
        self.phone = phone_number
        self.data = all_data
        self.output_dir = Path(output_dir)
        
    def generate(self):
        """Generate comprehensive HTML report"""
        template = Template('''
<!DOCTYPE html>
<html>
<head>
    <title>Phone OSINT Report: {{ phone }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
        .critical { color: #e74c3c; font-weight: bold; }
        .warning { color: #f39c12; font-weight: bold; }
        .success { color: #27ae60; font-weight: bold; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Phone OSINT Investigation Report</h1>
        <p>Phone Number: {{ phone }}</p>
        <p>Generated: {{ timestamp }}</p>
    </div>
    
    <div class="section">
        <h2>Executive Summary</h2>
        <ul>
            <li><strong>OWNER NAME: <span class="{{ 'success' if owner_name != 'Unknown' else 'warning' }}" style="font-size: 1.2em;">{{ owner_name }}</span></strong></li>
            <li>Valid Number: <span class="{{ 'success' if valid else 'critical' }}">{{ 'Yes' if valid else 'No' }}</span></li>
            <li>Carrier: {{ carrier }}</li>
            <li>Location: {{ location }}</li>
            <li>Line Type: {{ line_type }}</li>
            <li>Country: {{ country }}</li>
            <li>Sources Used: {{ sources_used }}</li>
            <li>Risk Score: <span class="{{ risk_class }}">{{ risk_score }}/10</span></li>
        </ul>
    </div>

    <div class="section">
        <h2>Phone Number Validation</h2>
        {{ validation_results }}
    </div>

    <div class="section">
        <h2>🎯 Advanced Name Hunting Results (THE GRAIL)</h2>
        {{ name_hunting_results }}
    </div>

    <div class="section">
        <h2>📧 Email Discovery & Intelligence</h2>
        {{ email_discovery_results }}
    </div>

    <div class="section">
        <h2>PhoneInfoga Results</h2>
        {{ phoneinfoga_results }}
    </div>
    
    <div class="section">
        <h2>Online Presence</h2>
        {{ online_presence }}
    </div>
    
    <div class="section">
        <h2>Data Breach Exposure</h2>
        {{ breach_results }}
    </div>
    
    <div class="section">
        <h2>Social Media Presence</h2>
        {{ social_media_results }}
    </div>
    
    <div class="section">
        <h2>Risk Assessment</h2>
        {{ risk_assessment }}
    </div>
    
    <div class="section">
        <h2>Recommendations</h2>
        {{ recommendations }}
    </div>
</body>
</html>
        ''')
        
        # Process data for template
        processed_data = self.process_data()
        
        # Generate HTML
        html_content = template.render(**processed_data)
        
        # Save report
        report_path = self.output_dir / "investigation_report.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        # Generate map if location data available
        if self.data.get('results', {}).get('phoneinfoga', {}).get('country_code'):
            self.generate_map()
            
        return report_path
    
    def process_data(self):
        """Process raw data for template"""
        phoneinfoga = self.data.get('results', {}).get('phoneinfoga', {})
        validation = self.data.get('results', {}).get('validation', {})
        validation_summary = validation.get('summary', {})
        name_hunting = self.data.get('results', {}).get('name_hunting', {})

        # Get the best owner name from unified name hunting (THE GRAIL!)
        owner_name = self._get_best_owner_name(name_hunting, validation_summary)

        return {
            'phone': self.phone,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'carrier': validation_summary.get('carrier', 'Unknown'),
            'location': validation_summary.get('location', 'Unknown'),
            'line_type': validation_summary.get('line_type', 'Unknown'),
            'country': validation_summary.get('country', 'Unknown'),
            'owner_name': owner_name,
            'valid': validation_summary.get('valid', False),
            'sources_used': ', '.join(validation_summary.get('sources_used', [])),
            'risk_score': self.get_intelligent_risk_score(),
            'risk_class': self.get_intelligent_risk_class(),
            'validation_results': self.format_validation_results(),
            'name_hunting_results': self.format_name_hunting_results(),
            'email_discovery_results': self.format_email_discovery_results(),
            'phoneinfoga_results': self.format_phoneinfoga_results(),
            'online_presence': self.format_online_presence(),
            'breach_results': self.format_breach_results(),
            'social_media_results': self.format_social_results(),
            'risk_assessment': self.generate_risk_assessment(),
            'recommendations': self.generate_recommendations()
        }
    
    def calculate_risk_score(self):
        """Calculate risk score based on findings"""
        score = 5  # Base score
        
        # Adjust based on findings
        if self.data.get('results', {}).get('breaches', {}).get('found'):
            score += 3
            
        social = self.data.get('results', {}).get('social_media', {})
        if sum(1 for platform in social.values() if platform.get('found')):
            score -= 1
            
        return min(10, max(1, score))
    
    def get_risk_class(self):
        """Get CSS class for risk score"""
        score = self.calculate_risk_score()
        if score >= 7:
            return 'critical'
        elif score >= 4:
            return 'warning'
        return 'success'

    def get_intelligent_risk_score(self):
        """Get risk score from intelligent risk assessment"""
        risk_data = self.data.get('results', {}).get('risk_assessment', {})
        return risk_data.get('overall_score', 5.0)

    def get_intelligent_risk_class(self):
        """Get CSS class from intelligent risk assessment"""
        risk_data = self.data.get('results', {}).get('risk_assessment', {})
        risk_color = risk_data.get('risk_color', 'yellow')

        # Map risk colors to CSS classes
        color_map = {
            'red': 'critical',
            'orange': 'critical',
            'yellow': 'warning',
            'green': 'success',
            'lightgreen': 'success'
        }
        return color_map.get(risk_color, 'warning')
    
    def format_validation_results(self):
        """Format phone validation results as HTML"""
        validation = self.data.get('results', {}).get('validation', {})

        if not validation:
            return "<p>No validation data available</p>"

        html = "<h3>NumVerify Results</h3>"
        numverify = validation.get('numverify', {})
        if numverify:
            html += "<table>"
            for key, value in numverify.items():
                if value and key not in ['error']:
                    display_key = key.replace('_', ' ').title()
                    html += f"<tr><td><strong>{display_key}</strong></td><td>{value}</td></tr>"
            html += "</table>"
        else:
            html += "<p>NumVerify data not available</p>"

        html += "<h3>Twilio Results</h3>"
        twilio = validation.get('twilio', {})
        if twilio and not twilio.get('error'):
            html += "<table>"
            html += f"<tr><td><strong>Phone Number</strong></td><td>{twilio.get('phone_number', 'Unknown')}</td></tr>"
            html += f"<tr><td><strong>National Format</strong></td><td>{twilio.get('national_format', 'Unknown')}</td></tr>"
            html += f"<tr><td><strong>Valid</strong></td><td>{twilio.get('valid', 'Unknown')}</td></tr>"
            html += f"<tr><td><strong>Country Code</strong></td><td>{twilio.get('country_code', 'Unknown')}</td></tr>"

            carrier = twilio.get('carrier', {})
            if carrier:
                html += f"<tr><td><strong>Carrier Name</strong></td><td>{carrier.get('name', 'Unknown')}</td></tr>"
                html += f"<tr><td><strong>Carrier Type</strong></td><td>{carrier.get('type', 'Unknown')}</td></tr>"
            html += "</table>"
        else:
            html += "<p>Twilio data not available</p>"

        return html

    def format_phoneinfoga_results(self):
        """Format PhoneInfoga results as HTML (cleaned up, no useless URLs)"""
        data = self.data.get('results', {}).get('phoneinfoga', {})

        html = "<table>"

        # Only show basic phone data that's actually useful
        useful_fields = ['country', 'local', 'e164', 'international', 'scanners_succeeded', 'scanners_failed']

        for key in useful_fields:
            value = data.get(key)
            if value is not None:
                # Format the value appropriately
                if key == 'scanners_failed' and isinstance(value, list):
                    formatted_value = ', '.join(value) if value else 'None'
                else:
                    formatted_value = str(value)

                html += f"<tr><td><strong>{key.replace('_', ' ').title()}</strong></td><td>{formatted_value}</td></tr>"

        # Show useful findings if any (but these are typically empty too)
        useful_findings = data.get('useful_findings', [])
        if useful_findings:
            html += f"<tr><td><strong>Additional Findings</strong></td><td>{'; '.join(useful_findings)}</td></tr>"

        html += "</table>"

        # Add note about filtered content
        html += "<p><em>Note: Search URL suggestions have been filtered out as they provide no actionable intelligence.</em></p>"

        return html
    
    def format_online_presence(self):
        """Format Google dork results"""
        data = self.data.get('results', {}).get('google_dorking', {})
        
        html = "<h3>Search Results Summary</h3><ul>"
        for category, items in data.items():
            if items:
                html += f"<li><strong>{category.replace('_', ' ').title()}</strong>: {len(items)} results found</li>"
        html += "</ul>"
        
        return html
    
    def format_breach_results(self):
        """Format breach check results with comprehensive details"""
        data = self.data.get('results', {}).get('breaches', {})

        html = '<h3>🔍 Data Breach Investigation</h3>'
        
        # Check if any data exists
        if not data or data.get('note'):
            return html + f'<p class="warning">ℹ️ {data.get("note", "No breach data available")}</p>'
        
        # Summary statistics
        emails_checked_count = data.get('emails_checked', 0)
        total_breaches = data.get('total_breaches', 0)
        breached_emails = data.get('breached_emails', [])
        clean_emails = data.get('clean_emails', [])
        error_emails = data.get('error_emails', [])

        # Overall status badge
        if data.get('found'):
            html += f'<p class="critical">🚨 <strong>BREACH ALERT:</strong> {len(breached_emails)} email(s) compromised in {total_breaches} total breaches!</p>'
        else:
            html += f'<p class="success">✅ <strong>ALL CLEAR:</strong> No breaches found for {len(clean_emails)} checked email(s)</p>'

        # Summary table
        html += '<h4>📊 Investigation Summary</h4>'
        html += '<table>'
        html += f'<tr><td><strong>Emails Investigated</strong></td><td>{emails_checked_count}</td></tr>'
        html += f'<tr><td><strong>Breached Emails</strong></td><td class="{"critical" if len(breached_emails) > 0 else "success"}">{len(breached_emails)}</td></tr>'
        html += f'<tr><td><strong>Clean Emails</strong></td><td class="success">{len(clean_emails)}</td></tr>'
        html += f'<tr><td><strong>Total Breach Incidents</strong></td><td class="{"critical" if total_breaches > 0 else "success"}">{total_breaches}</td></tr>'
        if error_emails:
            html += f'<tr><td><strong>Errors</strong></td><td class="warning">{len(error_emails)}</td></tr>'
        html += '</table>'

        # Breached emails details
        if breached_emails:
            html += '<h4>🚨 Compromised Emails</h4>'
            for breached in breached_emails:
                email = breached['email']
                breach_count = breached.get('breach_count', 0)
                breach_details = breached.get('breach_details', [])

                html += f'<div style="border-left: 4px solid #e74c3c; padding-left: 10px; margin: 10px 0;">'
                html += f'<h5 class="critical">📧 {email}</h5>'
                html += f'<p><strong>Breaches:</strong> {breach_count}</p>'
                
                if breach_details:
                    html += '<table style="margin-top: 10px;">'
                    html += '<tr><th>Breach</th><th>Date</th><th>Exposed Data</th><th>Records</th></tr>'
                    for breach in breach_details[:10]:  # Limit to first 10 breaches
                        breach_name = breach.get('title', breach.get('name', 'Unknown'))
                        breach_date = breach.get('breach_date', 'Unknown')
                        data_classes = ', '.join(breach.get('data_classes', [])[:5]) if breach.get('data_classes') else 'Unknown'
                        pwn_count = breach.get('pwn_count', 0)
                        pwn_display = f"{pwn_count:,}" if pwn_count > 0 else 'Unknown'
                        
                        html += f'<tr>'
                        html += f'<td><strong>{breach_name}</strong></td>'
                        html += f'<td>{breach_date}</td>'
                        html += f'<td>{data_classes}</td>'
                        html += f'<td>{pwn_display}</td>'
                        html += f'</tr>'
                    
                    if len(breach_details) > 10:
                        html += f'<tr><td colspan="4"><em>...and {len(breach_details) - 10} more breaches</em></td></tr>'
                    html += '</table>'
                
                html += '</div>'

        # Clean emails
        if clean_emails:
            html += '<h4>✅ Clean Emails (No Breaches Found)</h4>'
            html += '<ul style="color: #27ae60;">'
            for email in clean_emails:
                html += f'<li>{email}</li>'
            html += '</ul>'

        # Errors
        if error_emails:
            html += '<h4>⚠️ Errors During Check</h4>'
            html += '<table>'
            html += '<tr><th>Email</th><th>Error</th></tr>'
            for error_data in error_emails:
                html += f'<tr><td>{error_data["email"]}</td><td class="warning">{error_data["error"]}</td></tr>'
            html += '</table>'

        # Security recommendations
        if breached_emails:
            html += '<div style="background: #fff3cd; border: 2px solid #f39c12; padding: 15px; margin-top: 20px;">'
            html += '<h4>⚠️ Critical Security Recommendations</h4>'
            html += '<ol>'
            html += '<li><strong>Immediate Action:</strong> Change passwords on ALL accounts associated with compromised emails</li>'
            html += '<li><strong>Enable 2FA:</strong> Add two-factor authentication to all important accounts</li>'
            html += '<li><strong>Monitor Accounts:</strong> Check for unauthorized access or suspicious activity</li>'
            html += '<li><strong>Credit Monitoring:</strong> Consider credit monitoring if financial data was exposed</li>'
            html += '<li><strong>Unique Passwords:</strong> Use different passwords for each service</li>'
            html += '</ol>'
            html += '</div>'

        return html

    def format_email_discovery_results(self):
        """Format email discovery results as HTML with enhanced personal email display"""
        email_data = self.data.get('results', {}).get('email_discovery', {})

        # Always show email discovery section, even if no results
        html = '<h3>📧 Personal Email Discovery Summary</h3>'
        
        # Show what was attempted
        search_summary = email_data.get('search_summary', {})
        methods_used = email_data.get('methods_used', [])
        
        if methods_used:
            html += f'<p><strong>Methods Used:</strong> {", ".join(methods_used).title()}</p>'

        if not email_data.get('found'):
            html += '<div class="warning">'
            html += '<p><strong>⚠️ No email addresses discovered in this investigation.</strong></p>'
            html += '<p>This could mean:</p>'
            html += '<ul>'
            html += '<li>Individual maintains good privacy hygiene</li>'
            html += '<li>Uses less common email providers</li>'
            html += '<li>Email addresses not publicly linked to this phone number</li>'
            html += '<li>May require additional identity data for enhanced search</li>'
            html += '</ul>'
            
            # Show what was searched
            if search_summary:
                html += '<p><strong>Search Methods Attempted:</strong></p><ul>'
                for method, data in search_summary.items():
                    if isinstance(data, dict):
                        queries = data.get('queries_executed', 0)
                        html += f'<li>{method.title()}: {queries} queries executed</li>'
                html += '</ul>'
            html += '</div>'
            return html

        # Show results if found
        html += '<table>'

        # Summary statistics
        all_emails = email_data.get('emails', [])
        verified_emails = email_data.get('verified_emails', [])
        total_emails = len(all_emails) + len(verified_emails)
        verified_count = len(verified_emails)
        confidence = email_data.get('confidence_score', 0)

        html += f'<tr><td><strong>Total Email Candidates</strong></td><td><span class="success">{total_emails}</span></td></tr>'
        html += f'<tr><td><strong>DNS-Validated Emails</strong></td><td><span class="{"success" if verified_count > 0 else "warning"}">{verified_count}</span></td></tr>'
        html += f'<tr><td><strong>Overall Confidence</strong></td><td>{confidence:.2f}/1.0</td></tr>'

        html += '</table>'

        # Verified emails (highest priority)
        verified_emails = email_data.get('verified_emails', [])
        if verified_emails:
            html += '<h4>✅ Verified Email Addresses</h4>'
            html += '<table>'
            html += '<tr><th>Email</th><th>Status</th><th>Score</th><th>Details</th></tr>'
            for email_info in verified_emails:
                result = email_info.get('result', 'Unknown')
                score = email_info.get('score', 0)
                disposable = "⚠️ Disposable" if email_info.get('disposable') else "✅ Regular"
                html += f'<tr><td>{email_info["email"]}</td><td class="success">{result}</td><td>{score}</td><td>{disposable}</td></tr>'
            html += '</table>'

        # All discovered emails (organized by confidence)
        all_emails = email_data.get('emails', [])
        if all_emails:
            # Group emails by discovery method
            emails_by_source = {}
            for email_info in all_emails:
                source = email_info.get('source', 'unknown')
                if source not in emails_by_source:
                    emails_by_source[source] = []
                emails_by_source[source].append(email_info)

            # Display by source type
            if 'personal_google_search' in emails_by_source:
                html += '<h4>🔍 Emails Found via Google Search</h4>'
                html += '<table><tr><th>Email</th><th>Confidence</th><th>Validation</th></tr>'
                for email_info in emails_by_source['personal_google_search']:
                    confidence = email_info.get('confidence', 0)
                    validation = email_info.get('validation', {})
                    valid_status = "✅ Valid" if validation.get('valid') else "❌ Invalid" if 'valid' in validation else "🔍 Not Checked"
                    html += f'<tr><td><strong>{email_info["email"]}</strong></td><td>{confidence:.1f}</td><td>{valid_status}</td></tr>'
                html += '</table>'

            if 'hibp_breach_database' in emails_by_source:
                html += '<h4>🚨 Emails Found in Data Breaches</h4>'
                html += '<table><tr><th>Email</th><th>Breaches</th><th>Confidence</th></tr>'
                for email_info in emails_by_source['hibp_breach_database']:
                    breaches = email_info.get('breaches', 0)
                    confidence = email_info.get('confidence', 0)
                    html += f'<tr><td><strong class="critical">{email_info["email"]}</strong></td><td class="critical">{breaches} breaches</td><td>{confidence:.1f}</td></tr>'
                html += '</table>'

            if 'social_media_profiles' in emails_by_source:
                html += '<h4>📱 Emails from Social Media</h4>'
                html += '<table><tr><th>Email</th><th>Confidence</th><th>Source</th></tr>'
                for email_info in emails_by_source['social_media_profiles']:
                    confidence = email_info.get('confidence', 0)
                    html += f'<tr><td>{email_info["email"]}</td><td>{confidence:.1f}</td><td>Social Media Profile</td></tr>'
                html += '</table>'

            if 'personal_pattern_generation' in emails_by_source:
                pattern_emails = emails_by_source['personal_pattern_generation']
                # Only show pattern emails if no other sources found, or show top candidates
                if len(emails_by_source) == 1 or verified_count == 0:
                    html += '<h4>📋 Personal Email Pattern Candidates</h4>'
                    html += '<p><em>Generated based on common personal email patterns - validate before use:</em></p>'
                    html += '<table><tr><th>Email</th><th>Confidence</th><th>Pattern</th><th>Validation</th></tr>'
                    
                    # Show highest confidence patterns first
                    sorted_patterns = sorted(pattern_emails, key=lambda x: x.get('confidence', 0), reverse=True)
                    for email_info in sorted_patterns[:8]:  # Show top 8
                        confidence = email_info.get('confidence', 0)
                        pattern = email_info.get('pattern', 'unknown')
                        validation = email_info.get('validation', {})
                        valid_status = "✅ Valid" if validation.get('valid') else "❌ Invalid" if 'valid' in validation else "🔍 Checking..."
                        html += f'<tr><td>{email_info["email"]}</td><td>{confidence:.1f}</td><td>{pattern}</td><td>{valid_status}</td></tr>'
                    
                    html += '</table>'
                    html += '<p class="info"><strong>💡 Tip:</strong> These are educated guesses based on the person\'s name. Higher confidence patterns are more likely to be correct.</p>'

        return html

    def format_social_results(self):
        """Format enhanced social media results with email correlation"""
        data = self.data.get('results', {}).get('social_media', {})

        if not data:
            return '<p>No social media data available.</p>'

        # Summary information
        summary = data.get('summary', {})
        html = '<h3>📊 Search Summary</h3>'
        html += '<table>'
        html += f'<tr><td><strong>Platforms Scanned</strong></td><td>{summary.get("total_platforms", 0)}</td></tr>'
        html += f'<tr><td><strong>Emails Used for Correlation</strong></td><td>{summary.get("emails_used", 0)}</td></tr>'
        html += f'<tr><td><strong>Search URLs Generated</strong></td><td>{summary.get("search_urls_generated", 0)}</td></tr>'
        html += '</table>'

        # Platform-by-platform breakdown
        html += '<h3>🔍 Platform Analysis</h3>'
        html += '<table>'
        html += '<tr><th>Platform</th><th>Status</th><th>Search Options</th><th>Notes</th></tr>'

        for platform, result in data.items():
            if platform == 'summary' or not isinstance(result, dict):
                continue

            platform_name = platform.replace('_', ' ').title()
            status = "✅ Found" if result.get('found') else "❌ Not Found"

            # Count search URLs
            search_urls = result.get('search_urls', [])
            search_count = len(search_urls)
            search_text = f"{search_count} search options"

            # Generate search URLs list
            search_links = []
            for url_info in search_urls[:3]:  # Show top 3
                url_type = url_info.get('type', 'unknown')
                url = url_info.get('url', '#')
                if url_type == 'phone':
                    search_links.append(f'<a href="{url}" target="_blank">Phone Search</a>')
                elif url_type == 'email':
                    email = url_info.get('email', 'unknown')
                    search_links.append(f'<a href="{url}" target="_blank">Email: {email[:20]}...</a>')
                else:
                    search_links.append(f'<a href="{url}" target="_blank">{url_type.title()}</a>')

            if len(search_urls) > 3:
                search_links.append(f"... and {len(search_urls) - 3} more")

            search_links_text = "<br>".join(search_links) if search_links else "Manual check required"

            # Notes
            note = result.get('note', 'Standard platform search')

            html += f'<tr>'
            html += f'<td><strong>{platform_name}</strong></td>'
            html += f'<td>{status}</td>'
            html += f'<td>{search_links_text}</td>'
            html += f'<td><small>{note}</small></td>'
            html += f'</tr>'

        html += '</table>'

        # Enhanced correlation note
        emails_used = summary.get("emails_used", 0)
        if emails_used > 0:
            html += f'<p class="success"><strong>Enhanced Search:</strong> Using {emails_used} discovered email addresses for improved social media correlation.</p>'
        else:
            html += f'<p class="warning"><strong>Limited Search:</strong> No verified emails available - using phone number searches only.</p>'

        return html
    
    def generate_risk_assessment(self):
        """Generate intelligent risk assessment text"""
        risk_data = self.data.get('results', {}).get('risk_assessment', {})

        if not risk_data:
            return "<p>Risk assessment not available.</p>"

        html = f'<div class="risk-overview">'
        html += f'<h3>Overall Risk: <span class="{self.get_intelligent_risk_class()}">{risk_data.get("risk_level", "UNKNOWN")} ({risk_data.get("overall_score", 0):.2f}/10)</span></h3>'
        html += f'<p><em>Assessment conducted on {risk_data.get("assessment_timestamp", "Unknown date")}</em></p>'
        html += f'</div>'

        # Risk factors breakdown
        risk_factors = risk_data.get('risk_factors', [])
        if risk_factors:
            html += '<h4>Risk Factor Analysis</h4>'
            html += '<table style="margin-top: 10px;">'
            html += '<tr><th>Factor</th><th>Score</th><th>Weight</th><th>Impact</th><th>Evidence</th></tr>'

            for factor in risk_factors:
                score_class = 'critical' if factor['score'] >= 7 else 'warning' if factor['score'] >= 4 else 'success'
                evidence_text = '; '.join(factor.get('evidence', []))

                html += f'<tr>'
                html += f'<td><strong>{factor["name"]}</strong><br><small>{factor["description"]}</small></td>'
                html += f'<td><span class="{score_class}">{factor["score"]:.1f}/10</span></td>'
                html += f'<td>{int(factor["weight"] * 100)}%</td>'
                html += f'<td><span class="{score_class}">{factor["weighted_score"]:.2f}</span></td>'
                html += f'<td><small>{evidence_text}</small></td>'
                html += f'</tr>'

            html += '</table>'

        # Methodology
        methodology = risk_data.get('methodology', {})
        if methodology:
            html += '<h4>Assessment Methodology</h4>'
            html += '<ul>'
            html += f'<li>Total Factors Analyzed: {methodology.get("total_factors", 0)}</li>'
            html += f'<li>Scoring Range: {methodology.get("scoring_range", "Unknown")}</li>'
            html += f'<li>Weighting Method: {methodology.get("weighting_method", "Unknown")}</li>'
            html += '</ul>'

        return html
    
    def generate_recommendations(self):
        """Generate intelligent recommendations"""
        risk_data = self.data.get('results', {}).get('risk_assessment', {})
        recommendations = risk_data.get('recommendations', [])

        if not recommendations:
            # Fallback recommendations
            recommendations = [
                "Verify all findings through multiple sources",
                "Check with carrier for additional information",
                "Consider privacy implications of findings"
            ]

        html = "<ul>"
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        html += "</ul>"

        return html

    def generate_map(self):
        """Generate location map if coordinates available"""
        # This would create a map visualization
        pass

    def _get_best_owner_name(self, name_hunting_data, validation_summary):
        """Extract the best owner name from unified name hunting results"""
        if not name_hunting_data or not name_hunting_data.get('found'):
            # Fallback to validation data
            return validation_summary.get('owner_name', 'Unknown')

        # Use primary names from unified hunting (highest confidence)
        primary_names = name_hunting_data.get('primary_names', [])
        if primary_names:
            return primary_names[0]  # Use the first primary name

        # Fallback to any name found
        all_names = name_hunting_data.get('all_names', [])
        if all_names:
            return all_names[0]

        return 'Unknown'

    def format_name_hunting_results(self):
        """Format name hunting results as HTML"""
        name_hunting = self.data.get('results', {}).get('name_hunting', {})

        if not name_hunting or not name_hunting.get('found'):
            return '<p class="warning">No names discovered through advanced hunting techniques.</p>'

        html = ""

        # Primary Names (THE GRAIL!)
        primary_names = name_hunting.get('primary_names', [])
        if primary_names:
            html += '<h3>🔥 PRIMARY NAMES (HIGH CONFIDENCE)</h3>'
            html += '<ul class="name-list">'
            for name in primary_names:
                confidence = name_hunting.get('confidence_scores', {}).get(name, 0)
                html += f'<li><strong class="success">{name}</strong> (Confidence: {confidence:.2f})</li>'
            html += '</ul>'

        # All discovered names
        all_names = name_hunting.get('all_names', [])
        if len(all_names) > len(primary_names):
            other_names = [name for name in all_names if name not in primary_names]
            if other_names:
                html += '<h3>📋 Additional Names Discovered</h3>'
                html += '<ul class="name-list">'
                for name in other_names:
                    confidence = name_hunting.get('confidence_scores', {}).get(name, 0)
                    html += f'<li>{name} (Confidence: {confidence:.2f})</li>'
                html += '</ul>'

        # Hunting statistics
        html += '<h3>📊 Hunting Statistics</h3>'
        html += '<table>'
        html += f'<tr><td><strong>Best Confidence</strong></td><td>{name_hunting.get("best_confidence", 0):.2f}</td></tr>'
        html += f'<tr><td><strong>Total Names Found</strong></td><td>{len(all_names)}</td></tr>'
        html += f'<tr><td><strong>Execution Time</strong></td><td>{name_hunting.get("execution_time", 0):.2f}s</td></tr>'

        methods_successful = name_hunting.get('methods_successful', [])
        if methods_successful:
            html += f'<tr><td><strong>Successful Methods</strong></td><td>{", ".join(methods_successful).title()}</td></tr>'

        html += '</table>'

        # Correlation analysis
        correlation = name_hunting.get('correlation_analysis', {})
        if correlation.get('consensus_score', 0) > 0:
            html += '<h3>🧠 Correlation Analysis</h3>'
            html += '<table>'
            html += f'<tr><td><strong>Consensus Score</strong></td><td>{correlation["consensus_score"]:.2f}</td></tr>'

            name_clusters = correlation.get('name_clusters', [])
            if name_clusters:
                html += f'<tr><td><strong>Name Clusters</strong></td><td>{len(name_clusters)}</td></tr>'

            html += '</table>'

        return html