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
        with open(report_path, 'w') as f:
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

        return {
            'phone': self.phone,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'carrier': validation_summary.get('carrier', 'Unknown'),
            'location': validation_summary.get('location', 'Unknown'),
            'line_type': validation_summary.get('line_type', 'Unknown'),
            'country': validation_summary.get('country', 'Unknown'),
            'owner_name': validation_summary.get('owner_name', 'Unknown'),
            'valid': validation_summary.get('valid', False),
            'sources_used': ', '.join(validation_summary.get('sources_used', [])),
            'risk_score': self.calculate_risk_score(),
            'risk_class': self.get_risk_class(),
            'validation_results': self.format_validation_results(),
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
        """Format PhoneInfoga results as HTML"""
        data = self.data.get('results', {}).get('phoneinfoga', {})

        html = "<table>"
        for key, value in data.items():
            if value and key != 'raw_local':
                html += f"<tr><td><strong>{key.replace('_', ' ').title()}</strong></td><td>{value}</td></tr>"
        html += "</table>"

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
        """Format breach check results"""
        data = self.data.get('results', {}).get('breaches', {})
        
        if not data.get('found'):
            return '<p class="success">No data breaches found.</p>'
            
        html = '<p class="critical">Data breach exposure detected!</p>'
        return html
    
    def format_social_results(self):
        """Format social media results"""
        data = self.data.get('results', {}).get('social_media', {})
        
        html = "<ul>"
        for platform, result in data.items():
            status = "Found" if result.get('found') else "Not Found"
            html += f"<li><strong>{platform.title()}</strong>: {status}"
            if result.get('manual_check_url'):
                html += f' [<a href="{result["manual_check_url"]}" target="_blank">Manual Check</a>]'
            html += "</li>"
        html += "</ul>"
        
        return html
    
    def generate_risk_assessment(self):
        """Generate risk assessment text"""
        risk_factors = []
        
        if self.data.get('results', {}).get('breaches', {}).get('found'):
            risk_factors.append("Phone number found in data breaches")
            
        if not self.data.get('results', {}).get('phoneinfoga', {}).get('valid'):
            risk_factors.append("Phone number validation failed")
            
        if risk_factors:
            return "<ul>" + "".join(f"<li>{factor}</li>" for factor in risk_factors) + "</ul>"
        return "<p>No significant risk factors identified.</p>"
    
    def generate_recommendations(self):
        """Generate recommendations"""
        recommendations = [
            "Verify all findings through multiple sources",
            "Check with carrier for additional information",
            "Consider privacy implications of findings"
        ]
        
        return "<ul>" + "".join(f"<li>{rec}</li>" for rec in recommendations) + "</ul>"
    
    def generate_map(self):
        """Generate location map if coordinates available"""
        # This would create a map visualization
        pass