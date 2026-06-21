"""
Entity extraction from documents (names, dates, organizations, etc.)
"""

import logging
from typing import Dict, List
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extract entities from document text"""

    def __init__(self, use_transformer: bool = True):
        """
        Initialize entity extractor

        Args:
            use_transformer: Use transformer-based NER (slower but more accurate)
        """
        self.use_transformer = use_transformer
        self.ner_pipeline = None

        if use_transformer:
            try:
                from transformers import pipeline
                self.ner_pipeline = pipeline(
                    "ner",
                    model="dslim/bert-base-NER",
                    aggregation_strategy="simple"
                )
                logger.info("Loaded transformer NER model")
            except Exception as e:
                logger.warning(f"Could not load transformer model: {e}")
                self.use_transformer = False

    def extract_entities(self, content: str) -> Dict:
        """
        Extract all entities from document

        Args:
            content: Document text

        Returns:
            Dict with categorized entities
        """
        try:
            if self.use_transformer and self.ner_pipeline:
                entities = self._extract_with_transformer(content)
            else:
                entities = self._extract_with_regex(content)

            # Additional extractions
            entities['dates'] = self._extract_dates(content)
            entities['emails'] = self._extract_emails(content)
            entities['urls'] = self._extract_urls(content)
            entities['phone_numbers'] = self._extract_phone_numbers(content)
            entities['currency'] = self._extract_currency(content)

            return entities

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {
                "error": str(e),
                "persons": [],
                "organizations": [],
                "locations": []
            }

    def _extract_with_transformer(self, content: str) -> Dict:
        """Extract entities using transformer model"""
        # Limit content length for transformer
        content_chunk = content[:5000]

        results = self.ner_pipeline(content_chunk)

        entities = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "misc": []
        }

        for entity in results:
            entity_type = entity['entity_group']
            text = entity['word']
            score = entity['score']

            if entity_type == 'PER':
                entities['persons'].append({
                    "text": text,
                    "confidence": score
                })
            elif entity_type == 'ORG':
                entities['organizations'].append({
                    "text": text,
                    "confidence": score
                })
            elif entity_type == 'LOC':
                entities['locations'].append({
                    "text": text,
                    "confidence": score
                })
            else:
                entities['misc'].append({
                    "text": text,
                    "type": entity_type,
                    "confidence": score
                })

        return entities

    def _extract_with_regex(self, content: str) -> Dict:
        """Extract entities using regex patterns (fallback)"""
        entities = {
            "persons": [],
            "organizations": [],
            "locations": []
        }

        # Simple capitalized word patterns (basic heuristic)
        # This is a fallback - transformer is more accurate

        # Common titles that indicate person names
        person_titles = r'\b(Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        for match in re.finditer(person_titles, content):
            entities['persons'].append({
                "text": match.group(0),
                "confidence": 0.6
            })

        # Organization patterns (ending with Inc., LLC, Corp., etc.)
        org_patterns = r'\b([A-Z][a-zA-Z\s&]+(?:Inc\.|LLC|Corp\.|Ltd\.|Co\.))'
        for match in re.finditer(org_patterns, content):
            entities['organizations'].append({
                "text": match.group(0),
                "confidence": 0.6
            })

        return entities

    def _extract_dates(self, content: str) -> List[Dict]:
        """Extract dates from text"""
        dates = []

        # Pattern for various date formats
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD-MM-YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
            r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b'  # DD Month YYYY
        ]

        for pattern in date_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                dates.append({
                    "text": match.group(0),
                    "position": match.start()
                })

        return dates

    def _extract_emails(self, content: str) -> List[str]:
        """Extract email addresses"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(pattern, content)))

    def _extract_urls(self, content: str) -> List[str]:
        """Extract URLs"""
        pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return list(set(re.findall(pattern, content)))

    def _extract_phone_numbers(self, content: str) -> List[str]:
        """Extract phone numbers"""
        patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US format
            r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',  # (123) 456-7890
            r'\+\d{1,3}\s*\d{1,4}\s*\d{1,4}\s*\d{1,9}\b'  # International
        ]

        numbers = []
        for pattern in patterns:
            numbers.extend(re.findall(pattern, content))

        return list(set(numbers))

    def _extract_currency(self, content: str) -> List[Dict]:
        """Extract currency amounts"""
        pattern = r'[$€£¥]\s*\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|EUR|GBP|JPY|dollars?|euros?)'

        amounts = []
        for match in re.finditer(pattern, content, re.IGNORECASE):
            amounts.append({
                "text": match.group(0),
                "position": match.start()
            })

        return amounts

    def extract_named_entities_by_type(
        self,
        content: str,
        entity_type: str
    ) -> List[str]:
        """
        Extract specific entity type

        Args:
            content: Document text
            entity_type: Type to extract (persons, organizations, locations, etc.)

        Returns:
            List of entities of specified type
        """
        entities = self.extract_entities(content)
        return [e['text'] if isinstance(e, dict) else e
                for e in entities.get(entity_type, [])]

    def get_entity_frequency(self, content: str) -> Dict:
        """
        Get frequency count of entities

        Args:
            content: Document text

        Returns:
            Dict with entity frequencies
        """
        entities = self.extract_entities(content)

        frequencies = {}

        for entity_type, entity_list in entities.items():
            if isinstance(entity_list, list) and entity_list:
                freq = {}
                for entity in entity_list:
                    text = entity['text'] if isinstance(entity, dict) else entity
                    freq[text] = freq.get(text, 0) + 1

                # Sort by frequency
                frequencies[entity_type] = sorted(
                    freq.items(),
                    key=lambda x: x[1],
                    reverse=True
                )

        return frequencies

    def extract_key_entities(
        self,
        content: str,
        top_n: int = 10
    ) -> Dict:
        """
        Extract most important entities

        Args:
            content: Document text
            top_n: Number of top entities per type

        Returns:
            Dict with top entities by type
        """
        frequencies = self.get_entity_frequency(content)

        key_entities = {}
        for entity_type, freq_list in frequencies.items():
            key_entities[entity_type] = freq_list[:top_n]

        return key_entities

    def extract_relationships(self, content: str) -> List[Dict]:
        """
        Extract relationships between entities (basic pattern matching)

        Args:
            content: Document text

        Returns:
            List of relationship triples (entity1, relation, entity2)
        """
        relationships = []

        # Simple relationship patterns
        patterns = [
            (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is|was)\s+(?:the\s+)?(\w+)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'role'),
            (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+works?\s+(?:at|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'works_at'),
            (r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+founded\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', 'founded'),
        ]

        for pattern, relation_type in patterns:
            for match in re.finditer(pattern, content):
                relationships.append({
                    "entity1": match.group(1),
                    "relation": relation_type,
                    "entity2": match.group(2) if relation_type != 'role' else match.group(3),
                    "context": match.group(0)
                })

        return relationships
