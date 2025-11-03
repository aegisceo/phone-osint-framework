#!/usr/bin/env python3
"""
Unified Name Hunting Pipeline
THE GRAIL: Coordinated multi-source name extraction with advanced correlation
"""

import logging
import time
import asyncio
from typing import Dict, List, Set, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from difflib import SequenceMatcher

# Import our hunting modules
from scripts.phone_validator import PhoneValidator
from scripts.truepeoplesearch_scraper import search_truepeoplesearch

class UnifiedNameHunter:
    """
    Advanced unified name hunting pipeline that coordinates multiple sources
    and applies intelligent correlation to extract phone number owners
    """

    def __init__(self, phone_number: str, identity_data: Dict = None, skip_truepeoplesearch: bool = False):
        self.phone = phone_number
        self.identity_data = identity_data or {}
        self.skip_truepeoplesearch = skip_truepeoplesearch
        self.logger = logging.getLogger(__name__)

        # Log identity data if provided
        if self.identity_data:
            self.logger.info(f"🎯 Enhanced hunting with identity data: {list(self.identity_data.keys())}")

        # Initialize all hunting modules
        self.phone_validator = PhoneValidator(phone_number)

        # Name correlation settings
        self.min_name_similarity = 0.7  # Minimum similarity for name correlation
        self.confidence_weights = {
            'twilio': 0.9,          # Highest weight for official Twilio data
            'truepeoplesearch': 0.8,  # High weight - free, comprehensive data
            'numverify': 0.6        # Lower weight for basic validation
        }

    def hunt_parallel(self) -> Dict:
        """
        Execute all hunting methods in parallel for maximum speed
        """
        self.logger.info(f"🚀 Starting PARALLEL NAME HUNTING for: {self.phone}")
        start_time = time.time()

        results = {
            'found': False,
            'primary_names': [],
            'all_names': [],
            'confidence_scores': {},
            'source_summary': {},
            'correlation_analysis': {},
            'execution_time': 0.0,
            'methods_attempted': [],
            'methods_successful': []
        }

        # Define hunting tasks
        hunting_tasks = [
            ('twilio', self._hunt_twilio_enhanced),
            ('numverify', self._hunt_numverify)
        ]
        
        # Only add TruePeopleSearch if not skipped
        if not self.skip_truepeoplesearch:
            hunting_tasks.append(('truepeoplesearch', self._hunt_truepeoplesearch))
        else:
            self.logger.info("⏭️ TruePeopleSearch skipped (will run in dedicated step after breach discovery)")

        # Execute in parallel using ThreadPoolExecutor
        max_workers = 3 if not self.skip_truepeoplesearch else 2
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_method = {
                executor.submit(task_func): method_name
                for method_name, task_func in hunting_tasks
            }

            for future in as_completed(future_to_method, timeout=120):
                method_name = future_to_method[future]
                results['methods_attempted'].append(method_name)

                try:
                    method_result = future.result()
                    results['source_summary'][method_name] = method_result

                    if method_result.get('found', False):
                        results['methods_successful'].append(method_name)
                        self.logger.info(f"✅ {method_name.upper()} SUCCESS: {method_result.get('names', [])}")

                except Exception as e:
                    self.logger.warning(f"❌ {method_name} hunting failed: {e}")
                    results['source_summary'][method_name] = {'error': str(e), 'found': False}

        # Correlate and analyze all results
        results.update(self._correlate_all_results(results['source_summary']))

        results['execution_time'] = time.time() - start_time
        self.logger.info(f"🎯 PARALLEL HUNT COMPLETE: {results['execution_time']:.2f}s")

        return results

    def hunt_sequential_aggressive(self) -> Dict:
        """
        Execute hunting methods sequentially with increasing aggression
        Stops early if high-confidence result is found
        """
        self.logger.info(f"🎯 Starting SEQUENTIAL AGGRESSIVE HUNTING for: {self.phone}")
        start_time = time.time()

        results = {
            'found': False,
            'primary_names': [],
            'all_names': [],
            'confidence_scores': {},
            'source_summary': {},
            'execution_time': 0.0,
            'early_termination': False,
            'termination_reason': None
        }

        # Sequential hunting order (fastest/most reliable first)
        hunting_sequence = [
            ('twilio', self._hunt_twilio_enhanced, 0.8),         # High confidence threshold
            ('numverify', self._hunt_numverify, 0.6),           # Medium threshold
            ('truepeoplesearch', self._hunt_truepeoplesearch, 0.7)  # High quality free data
        ]

        for method_name, hunt_func, confidence_threshold in hunting_sequence:
            self.logger.info(f"🔍 Attempting {method_name} hunting...")

            try:
                method_result = hunt_func()
                results['source_summary'][method_name] = method_result

                if method_result.get('found', False):
                    self.logger.info(f"✅ {method_name.upper()} SUCCESS")

                    # Update results
                    temp_results = self._correlate_all_results(results['source_summary'])
                    results.update(temp_results)

                    # Check if we should terminate early
                    if results['found'] and results.get('best_confidence', 0) >= confidence_threshold:
                        results['early_termination'] = True
                        results['termination_reason'] = f"High confidence from {method_name} ({results['best_confidence']:.2f})"
                        self.logger.info(f"🚀 EARLY TERMINATION: {results['termination_reason']}")
                        break

            except Exception as e:
                self.logger.warning(f"❌ {method_name} hunting failed: {e}")
                results['source_summary'][method_name] = {'error': str(e), 'found': False}

        results['execution_time'] = time.time() - start_time
        return results

    def _hunt_twilio_enhanced(self) -> Dict:
        """Enhanced Twilio hunting with aggressive name extraction and identity matching"""
        try:
            # Use enhanced Twilio validation with identity data if available
            if self.identity_data:
                self.logger.info("🎯 Using identity data for enhanced Twilio hunting")
                validation_results = self._validate_with_twilio_identity()
            else:
                validation_results = self.phone_validator.validate_with_twilio()

            names = []

            # Extract owner name if found
            if validation_results.get('OWNER_NAME'):
                names.append(validation_results['OWNER_NAME'])

            # Look for caller name data
            if 'caller_name_data' in validation_results:
                caller_data = validation_results['caller_name_data']
                if isinstance(caller_data, dict) and caller_data.get('caller_name'):
                    names.append(caller_data['caller_name'])
                elif hasattr(caller_data, 'caller_name') and caller_data.caller_name:
                    names.append(caller_data.caller_name)

            return {
                'found': len(names) > 0,
                'names': names,
                'confidence': 0.9 if names else 0.0,
                'raw_data': validation_results,
                'used_identity_data': bool(self.identity_data)
            }
        except Exception as e:
            return {'error': str(e), 'found': False}

    def _validate_with_twilio_identity(self) -> Dict:
        """Enhanced Twilio validation using identity data for better matching"""
        try:
            from twilio.rest import Client
            import os

            twilio_sid = os.getenv('TWILIO_SID')
            twilio_token = os.getenv('TWILIO_AUTH_TOKEN')

            if not twilio_sid or not twilio_token:
                self.logger.warning("Twilio credentials not configured")
                return {}

            client = Client(twilio_sid, twilio_token)
            result = {}

            # Try identity match with provided data
            if self.identity_data:
                self.logger.info("🎯 Attempting Twilio identity match with provided data")

                # Prepare identity match fields
                fields = ['identity_match']
                params = {}

                # Map our identity data to Twilio's expected format (snake_case)
                if 'first_name' in self.identity_data:
                    params['first_name'] = self.identity_data['first_name']
                if 'last_name' in self.identity_data:
                    params['last_name'] = self.identity_data['last_name']
                if 'address' in self.identity_data:
                    params['address_line_1'] = self.identity_data['address']
                if 'city' in self.identity_data:
                    params['city'] = self.identity_data['city']
                if 'state' in self.identity_data:
                    params['state'] = self.identity_data['state']
                if 'postal_code' in self.identity_data:
                    params['postal_code'] = self.identity_data['postal_code']

                if params:  # Only try if we have at least some identity data
                    try:
                        # Use the correct Twilio API format - fields as parameter, identity data as separate params
                        enhanced_lookup = client.lookups.v2.phone_numbers(self.phone).fetch(
                            fields='identity_match',
                            **params
                        )

                        if hasattr(enhanced_lookup, 'identity_match'):
                            identity_match = enhanced_lookup.identity_match
                            result['identity_match_data'] = identity_match

                            # Extract any confirmed name information
                            if hasattr(identity_match, 'summary_score'):
                                score = identity_match.summary_score
                                result['identity_match_score'] = score

                                if score and score > 0.5:  # High confidence match
                                    # Construct full name from matched parts
                                    full_name_parts = []
                                    if 'first_name' in self.identity_data and getattr(identity_match, 'first_name_match', None):
                                        full_name_parts.append(self.identity_data['first_name'])
                                    if 'last_name' in self.identity_data and getattr(identity_match, 'last_name_match', None):
                                        full_name_parts.append(self.identity_data['last_name'])

                                    if full_name_parts:
                                        result['OWNER_NAME'] = ' '.join(full_name_parts)
                                        self.logger.info(f"🔥 IDENTITY MATCH SUCCESS: {result['OWNER_NAME']} (score: {score})")

                    except Exception as e:
                        self.logger.warning(f"Twilio identity match failed: {e}")
                        result['identity_match_error'] = str(e)

            # Also try standard caller name lookup as fallback
            try:
                caller_lookup = client.lookups.v2.phone_numbers(self.phone).fetch(fields='caller_name')
                if hasattr(caller_lookup, 'caller_name'):
                    result['caller_name_data'] = caller_lookup.caller_name
            except Exception as e:
                self.logger.warning(f"Twilio caller name lookup failed: {e}")

            return result

        except Exception as e:
            self.logger.error(f"Enhanced Twilio validation error: {e}")
            return {'error': str(e)}

    def _hunt_truepeoplesearch(self) -> Dict:
        """
        TruePeopleSearch hunting - Free comprehensive people search
        Returns: names, addresses, age, associates, relatives
        """
        try:
            self.logger.info(f"🔍 Searching TruePeopleSearch for: {self.phone}")
            results = search_truepeoplesearch(self.phone)
            
            if results.get('found'):
                # Convert to unified format
                names = results.get('names', [])
                return {
                    'found': True,
                    'names': names,
                    'confidence': 0.8,  # High confidence - direct match
                    'source': 'truepeoplesearch',
                    'metadata': {
                        'current_address': results.get('current_address'),
                        'previous_addresses': results.get('previous_addresses', []),
                        'age': results.get('age'),
                        'associates': results.get('associates', []),
                        'relatives': results.get('relatives', [])
                    }
                }
            else:
                return {
                    'found': False,
                    'source': 'truepeoplesearch',
                    'note': results.get('note', 'No results found')
                }
                
        except Exception as e:
            self.logger.error(f"TruePeopleSearch error: {e}")
            return {'error': str(e), 'found': False, 'source': 'truepeoplesearch'}

    def _hunt_numverify(self) -> Dict:
        """Enhanced NumVerify hunting"""
        try:
            validation_results = self.phone_validator.validate_with_numverify()
            # NumVerify typically doesn't provide names, but we include it for completeness
            return {
                'found': False,  # NumVerify doesn't provide names
                'names': [],
                'confidence': 0.0,
                'carrier_info': validation_results.get('carrier', 'Unknown'),
                'raw_data': validation_results
            }
        except Exception as e:
            return {'error': str(e), 'found': False}

    def _correlate_all_results(self, source_results: Dict) -> Dict:
        """
        Advanced correlation of all hunting results with confidence scoring
        """
        self.logger.info("🧠 Starting advanced name correlation analysis...")

        correlation_results = {
            'found': False,
            'primary_names': [],
            'all_names': [],
            'confidence_scores': {},
            'best_confidence': 0.0,
            'correlation_analysis': {
                'name_clusters': [],
                'confidence_matrix': {},
                'consensus_score': 0.0
            }
        }

        # Collect all names from all sources
        all_names_with_sources = []

        for source, results in source_results.items():
            if not results.get('found', False):
                continue

            source_names = []

            # Extract names based on source format
            if source == 'whitepages':
                source_names.extend(results.get('names', []))
                if results.get('caller_id_name'):
                    source_names.append(results['caller_id_name'])
            elif source in ['truepeoplesearch', 'twilio']:
                source_names.extend(results.get('names', []))
            elif source == 'numverify':
                # NumVerify doesn't provide names
                continue

            # Add source weight to each name
            source_weight = self.confidence_weights.get(source, 0.5)
            for name in source_names:
                if name and len(name.strip()) > 2:
                    cleaned_name = self._clean_name(name)
                    if cleaned_name:
                        all_names_with_sources.append({
                            'name': cleaned_name,
                            'source': source,
                            'weight': source_weight
                        })

        if not all_names_with_sources:
            self.logger.warning("No names found across all sources")
            return correlation_results

        # Cluster similar names
        name_clusters = self._cluster_similar_names(all_names_with_sources)
        correlation_results['correlation_analysis']['name_clusters'] = name_clusters

        # Calculate confidence scores for each cluster
        cluster_scores = []
        for cluster in name_clusters:
            cluster_score = self._calculate_cluster_confidence(cluster)
            cluster_scores.append({
                'names': [item['name'] for item in cluster],
                'representative_name': cluster[0]['name'],  # Use first name as representative
                'confidence': cluster_score,
                'sources': list(set(item['source'] for item in cluster)),
                'source_count': len(set(item['source'] for item in cluster))
            })

        # Sort by confidence
        cluster_scores.sort(key=lambda x: x['confidence'], reverse=True)

        if cluster_scores:
            correlation_results['found'] = True
            correlation_results['best_confidence'] = cluster_scores[0]['confidence']

            # Primary names (highest confidence cluster)
            correlation_results['primary_names'] = cluster_scores[0]['names']

            # All unique names
            all_unique_names = set()
            for cluster in cluster_scores:
                all_unique_names.update(cluster['names'])
            correlation_results['all_names'] = list(all_unique_names)

            # Individual name confidence scores
            for cluster in cluster_scores:
                for name in cluster['names']:
                    correlation_results['confidence_scores'][name] = cluster['confidence']

            # Consensus score (agreement between sources)
            consensus_score = self._calculate_consensus_score(cluster_scores)
            correlation_results['correlation_analysis']['consensus_score'] = consensus_score

            self.logger.info(f"🎯 CORRELATION COMPLETE: {len(correlation_results['primary_names'])} primary names, confidence: {correlation_results['best_confidence']:.2f}")

        return correlation_results

    def _cluster_similar_names(self, names_with_sources: List[Dict]) -> List[List[Dict]]:
        """
        Cluster similar names together using string similarity
        """
        clusters = []
        processed = set()

        for i, name_item in enumerate(names_with_sources):
            if i in processed:
                continue

            current_cluster = [name_item]
            processed.add(i)

            # Find similar names
            for j, other_item in enumerate(names_with_sources):
                if j in processed or i == j:
                    continue

                similarity = self._calculate_name_similarity(
                    name_item['name'],
                    other_item['name']
                )

                if similarity >= self.min_name_similarity:
                    current_cluster.append(other_item)
                    processed.add(j)

            clusters.append(current_cluster)

        return clusters

    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two names
        """
        # Normalize names
        norm1 = re.sub(r'[^\w\s]', '', name1.lower()).strip()
        norm2 = re.sub(r'[^\w\s]', '', name2.lower()).strip()

        # Use sequence matcher for similarity
        return SequenceMatcher(None, norm1, norm2).ratio()

    def _calculate_cluster_confidence(self, cluster: List[Dict]) -> float:
        """
        Calculate confidence score for a name cluster
        """
        if not cluster:
            return 0.0

        # Base confidence from source weights
        base_confidence = sum(item['weight'] for item in cluster) / len(cluster)

        # Bonus for multiple sources
        unique_sources = len(set(item['source'] for item in cluster))
        multi_source_bonus = min(unique_sources * 0.1, 0.3)

        # Bonus for multiple occurrences
        occurrence_bonus = min((len(cluster) - 1) * 0.05, 0.2)

        total_confidence = base_confidence + multi_source_bonus + occurrence_bonus

        return min(total_confidence, 1.0)

    def _calculate_consensus_score(self, cluster_scores: List[Dict]) -> float:
        """
        Calculate consensus score based on agreement between sources
        """
        if not cluster_scores:
            return 0.0

        # High consensus if top cluster has multiple sources
        top_cluster = cluster_scores[0]
        consensus = top_cluster['source_count'] / 4.0  # Normalize by max possible sources

        return min(consensus, 1.0)

    def _clean_name(self, name: str) -> Optional[str]:
        """
        Clean and validate a name string
        Handles formats like "LINDLEY, DAVID" or "Lindley, David" and converts to "David Lindley"
        """
        if not name:
            return None

        # Handle "LastName, FirstName" format (common in Twilio responses)
        if ',' in name:
            parts = name.split(',')
            if len(parts) == 2:
                last_name = parts[0].strip()
                first_name = parts[1].strip()
                # Reconstruct as "FirstName LastName"
                name = f"{first_name} {last_name}"
                self.logger.info(f"🔧 Reformatted name: '{parts[0].strip()}, {parts[1].strip()}' -> '{name}'")

        # Remove extra whitespace and special characters
        cleaned = re.sub(r'[^\w\s\-\.]', '', name).strip()

        # Skip if too short or contains numbers
        if len(cleaned) < 3 or re.search(r'\d', cleaned):
            return None

        # Skip common false positives
        false_positives = {
            'unknown', 'private', 'blocked', 'restricted', 'anonymous',
            'unavailable', 'withheld', 'caller', 'number', 'phone'
        }

        if cleaned.lower() in false_positives:
            return None

        # Title case
        return ' '.join(word.capitalize() for word in cleaned.split())

    def hunt_ultimate(self) -> Dict:
        """
        Ultimate name hunting that combines parallel and sequential strategies
        """
        self.logger.info(f"🔥 ULTIMATE NAME HUNTING INITIATED for: {self.phone}")

        # Try parallel first for speed
        parallel_results = self.hunt_parallel()

        # If parallel didn't achieve high confidence, try sequential aggressive
        if not parallel_results['found'] or parallel_results.get('best_confidence', 0) < 0.8:
            self.logger.info("🎯 Escalating to sequential aggressive hunting...")
            sequential_results = self.hunt_sequential_aggressive()

            # Use best results
            if sequential_results.get('best_confidence', 0) > parallel_results.get('best_confidence', 0):
                return sequential_results

        return parallel_results


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python unified_name_hunter.py <phone_number>")
        sys.exit(1)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    phone = sys.argv[1]
    hunter = UnifiedNameHunter(phone)
    results = hunter.hunt_ultimate()

    print(f"\n🎯 ULTIMATE NAME HUNTING RESULTS for {phone}:")
    print(f"Found: {results['found']}")
    print(f"Primary Names: {results['primary_names']}")
    print(f"All Names: {results['all_names']}")
    print(f"Best Confidence: {results.get('best_confidence', 0):.2f}")
    print(f"Execution Time: {results['execution_time']:.2f}s")

    if results.get('methods_successful'):
        print(f"Successful Methods: {', '.join(results['methods_successful'])}")