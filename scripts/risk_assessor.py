#!/usr/bin/env python3
"""
Intelligent Risk Assessment Engine
Multi-factor risk scoring based on investigation results
"""

import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class RiskFactor:
    """Individual risk factor with weight and score"""
    name: str
    score: float  # 0-10 scale
    weight: float  # 0-1 scale
    description: str
    evidence: List[str]

class RiskAssessor:
    """
    Comprehensive risk assessment engine that evaluates investigation results
    and generates a multi-factor risk score with detailed analysis
    """

    def __init__(self, phone_number: str):
        self.phone = phone_number
        self.logger = logging.getLogger(__name__)
        self.risk_factors = []

    def assess_phone_validation_risk(self, validation_data: Dict) -> RiskFactor:
        """Assess risk based on phone validation results"""
        score = 0.0
        evidence = []

        # Check if phone is valid
        if not validation_data.get('numverify', {}).get('valid', False):
            score += 8.0
            evidence.append("Phone number validation failed")

        # Check line type
        line_type = validation_data.get('summary', {}).get('line_type', '').lower()
        if 'voip' in line_type or 'virtual' in line_type:
            score += 6.0
            evidence.append(f"VOIP/Virtual number detected: {line_type}")
        elif 'mobile' in line_type:
            score += 2.0
            evidence.append("Mobile number (moderate risk)")
        elif 'landline' in line_type:
            score += 1.0
            evidence.append("Landline number (low risk)")

        # Check carrier
        carrier = validation_data.get('summary', {}).get('carrier', '').lower()
        if not carrier or carrier == 'unknown':
            score += 4.0
            evidence.append("Unknown or missing carrier information")

        # Check international status
        country = validation_data.get('numverify', {}).get('country_name', '')
        if country and country != 'United States':
            score += 3.0
            evidence.append(f"International number: {country}")

        return RiskFactor(
            name="Phone Validation",
            score=min(score, 10.0),
            weight=0.25,
            description="Risk based on phone number validity and characteristics",
            evidence=evidence
        )

    def assess_identity_risk(self, name_hunting_data: Dict) -> RiskFactor:
        """Assess risk based on name hunting and identity results"""
        score = 0.0
        evidence = []

        # Check if name was found
        if not name_hunting_data.get('found', False):
            score += 7.0
            evidence.append("No identity information found")
        else:
            # Check confidence of name resolution
            confidence = name_hunting_data.get('best_confidence', 0)
            if confidence < 0.3:
                score += 5.0
                evidence.append(f"Low confidence identity match: {confidence:.2f}")
            elif confidence < 0.7:
                score += 2.0
                evidence.append(f"Moderate confidence identity match: {confidence:.2f}")
            else:
                score += 0.5
                evidence.append(f"High confidence identity match: {confidence:.2f}")

            # Check number of sources
            sources_count = len(name_hunting_data.get('sources_found', []))
            if sources_count == 1:
                score += 3.0
                evidence.append("Single source identity verification")
            elif sources_count == 0:
                score += 6.0
                evidence.append("No reliable identity sources")

        return RiskFactor(
            name="Identity Verification",
            score=min(score, 10.0),
            weight=0.20,
            description="Risk based on identity verification and name resolution",
            evidence=evidence
        )

    def assess_digital_footprint_risk(self, social_data: Dict, email_data: Dict) -> RiskFactor:
        """Assess risk based on digital footprint analysis"""
        score = 0.0
        evidence = []

        # Check email discovery
        email_count = len(email_data.get('emails', [])) + len(email_data.get('verified_emails', []))
        if email_count == 0:
            score += 4.0
            evidence.append("No email addresses discovered")
        elif email_count > 5:
            score += 1.0
            evidence.append(f"Multiple email addresses found: {email_count}")

        # Check social media presence
        if social_data.get('summary'):
            platforms_checked = social_data['summary'].get('total_platforms', 0)
            search_urls = social_data['summary'].get('search_urls_generated', 0)

            if search_urls == 0:
                score += 3.0
                evidence.append("No social media search opportunities")
            elif search_urls < 5:
                score += 2.0
                evidence.append(f"Limited social media presence: {search_urls} search URLs")
            else:
                score += 0.5
                evidence.append(f"Active social media presence: {search_urls} search URLs")

        # Check for platform-specific indicators
        platforms_with_data = 0
        for platform, data in social_data.items():
            if platform != 'summary' and isinstance(data, dict):
                if data.get('search_urls') and len(data['search_urls']) > 1:
                    platforms_with_data += 1

        if platforms_with_data == 0:
            score += 2.0
            evidence.append("No actionable social media data")

        return RiskFactor(
            name="Digital Footprint",
            score=min(score, 10.0),
            weight=0.15,
            description="Risk based on digital presence and email discovery",
            evidence=evidence
        )

    def assess_breach_risk(self, breach_data: Dict) -> RiskFactor:
        """Assess risk based on data breach exposure"""
        score = 0.0
        evidence = []

        if breach_data.get('found', False):
            breach_count = len(breach_data.get('breaches', []))
            emails_in_breaches = len(breach_data.get('emails_checked', []))

            # High risk for multiple breaches
            if breach_count > 10:
                score += 9.0
                evidence.append(f"High breach exposure: {breach_count} breaches found")
            elif breach_count > 5:
                score += 7.0
                evidence.append(f"Moderate breach exposure: {breach_count} breaches found")
            elif breach_count > 0:
                score += 5.0
                evidence.append(f"Some breach exposure: {breach_count} breaches found")

            # Risk based on emails in breaches
            if emails_in_breaches > 3:
                score += 3.0
                evidence.append(f"Multiple emails compromised: {emails_in_breaches}")
            elif emails_in_breaches > 0:
                score += 2.0
                evidence.append(f"Email addresses found in breaches: {emails_in_breaches}")

        else:
            # No breaches could be positive or indicate no email discovery
            if breach_data.get('note') and 'no email' in breach_data['note'].lower():
                score += 1.0
                evidence.append("No breach check possible (no emails discovered)")
            else:
                score += 0.0
                evidence.append("No known breach exposure")

        return RiskFactor(
            name="Data Breach Exposure",
            score=min(score, 10.0),
            weight=0.25,
            description="Risk based on known data breaches and email exposure",
            evidence=evidence
        )

    def assess_technical_indicators_risk(self, phoneinfoga_data: Dict) -> RiskFactor:
        """Assess risk based on technical phone analysis"""
        score = 0.0
        evidence = []

        # Check scanners success rate
        scanners_succeeded = phoneinfoga_data.get('scanners_succeeded', 0)
        scanners_failed = len(phoneinfoga_data.get('scanners_failed', []))

        if scanners_succeeded == 0:
            score += 5.0
            evidence.append("All phone analysis scanners failed")
        elif scanners_succeeded < 3:
            score += 3.0
            evidence.append(f"Limited scanner success: {scanners_succeeded} succeeded")
        else:
            score += 1.0
            evidence.append(f"Good scanner coverage: {scanners_succeeded} succeeded")

        # Check for useful findings
        useful_findings = len(phoneinfoga_data.get('useful_findings', []))
        if useful_findings == 0:
            score += 2.0
            evidence.append("No actionable technical intelligence")
        else:
            score += 0.5
            evidence.append(f"Technical intelligence available: {useful_findings} findings")

        return RiskFactor(
            name="Technical Analysis",
            score=min(score, 10.0),
            weight=0.15,
            description="Risk based on technical phone number analysis",
            evidence=evidence
        )

    def calculate_overall_risk(self, investigation_results: Dict) -> Dict:
        """Calculate comprehensive risk assessment"""
        self.logger.info("🎯 Starting intelligent risk assessment...")

        # Extract data sections
        validation_data = investigation_results.get('results', {}).get('validation', {})
        name_data = investigation_results.get('results', {}).get('name_hunting', {})
        social_data = investigation_results.get('results', {}).get('social_media', {})
        email_data = investigation_results.get('results', {}).get('email_discovery', {})
        breach_data = investigation_results.get('results', {}).get('breaches', {})
        phoneinfoga_data = investigation_results.get('results', {}).get('phoneinfoga', {})

        # Calculate individual risk factors
        self.risk_factors = [
            self.assess_phone_validation_risk(validation_data),
            self.assess_identity_risk(name_data),
            self.assess_digital_footprint_risk(social_data, email_data),
            self.assess_breach_risk(breach_data),
            self.assess_technical_indicators_risk(phoneinfoga_data)
        ]

        # Calculate weighted overall score
        total_weighted_score = 0.0
        total_weight = 0.0

        for factor in self.risk_factors:
            total_weighted_score += factor.score * factor.weight
            total_weight += factor.weight

        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0

        # Determine risk level
        if overall_score >= 8.0:
            risk_level = "CRITICAL"
            risk_color = "red"
        elif overall_score >= 6.0:
            risk_level = "HIGH"
            risk_color = "orange"
        elif overall_score >= 4.0:
            risk_level = "MEDIUM"
            risk_color = "yellow"
        elif overall_score >= 2.0:
            risk_level = "LOW"
            risk_color = "green"
        else:
            risk_level = "MINIMAL"
            risk_color = "lightgreen"

        # Generate recommendations
        recommendations = self._generate_recommendations(overall_score, self.risk_factors)

        # Compile results
        assessment = {
            'overall_score': round(overall_score, 2),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'assessment_timestamp': datetime.now().isoformat(),
            'phone_number': self.phone,
            'risk_factors': [
                {
                    'name': factor.name,
                    'score': round(factor.score, 2),
                    'weight': factor.weight,
                    'weighted_score': round(factor.score * factor.weight, 2),
                    'description': factor.description,
                    'evidence': factor.evidence
                }
                for factor in self.risk_factors
            ],
            'recommendations': recommendations,
            'methodology': {
                'total_factors': len(self.risk_factors),
                'scoring_range': "0-10 scale",
                'weighting_method': "Weighted average based on factor importance"
            }
        }

        # Log results
        self.logger.info(f"🎯 Risk assessment complete: {risk_level} ({overall_score:.2f}/10)")
        self.logger.info(f"🔍 Factors analyzed: {len(self.risk_factors)}")

        return assessment

    def _generate_recommendations(self, overall_score: float, risk_factors: List[RiskFactor]) -> List[str]:
        """Generate actionable recommendations based on risk assessment"""
        recommendations = []

        # Overall score recommendations
        if overall_score >= 8.0:
            recommendations.append("🚨 CRITICAL: This phone number presents significant security concerns and should be investigated further")
        elif overall_score >= 6.0:
            recommendations.append("⚠️ HIGH RISK: Additional verification strongly recommended before trust")
        elif overall_score >= 4.0:
            recommendations.append("⚡ MODERATE: Standard verification procedures should be followed")
        else:
            recommendations.append("✅ LOW RISK: Appears to be a legitimate phone number")

        # Factor-specific recommendations
        for factor in risk_factors:
            if factor.name == "Phone Validation" and factor.score >= 6.0:
                recommendations.append("📞 Verify phone number through alternative methods")
            elif factor.name == "Identity Verification" and factor.score >= 6.0:
                recommendations.append("🆔 Identity verification required through additional sources")
            elif factor.name == "Data Breach Exposure" and factor.score >= 5.0:
                recommendations.append("🔐 Account security measures should be enhanced due to breach exposure")
            elif factor.name == "Digital Footprint" and factor.score >= 5.0:
                recommendations.append("🌐 Limited digital presence - additional verification methods recommended")

        return recommendations


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) != 3:
        print("Usage: python risk_assessor.py <phone_number> <investigation_results.json>")
        sys.exit(1)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    phone = sys.argv[1]
    results_file = sys.argv[2]

    try:
        with open(results_file, 'r') as f:
            investigation_data = json.load(f)

        assessor = RiskAssessor(phone)
        risk_assessment = assessor.calculate_overall_risk(investigation_data)

        print(f"\n🎯 Risk Assessment for {phone}:")
        print(f"Overall Score: {risk_assessment['overall_score']}/10")
        print(f"Risk Level: {risk_assessment['risk_level']}")
        print(f"\nFactors:")
        for factor in risk_assessment['risk_factors']:
            print(f"  {factor['name']}: {factor['score']}/10 (weight: {factor['weight']})")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)