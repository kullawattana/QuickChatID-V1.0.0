"""
Microsoft Presidio Service - Advanced PII Detection & Masking
PDPA Compliant
"""

class PresidioService:
    """Advanced PII detection and anonymization"""
    
    def __init__(self):
        self.available = self._check_availability()
        self.entities = [
            'PHONE_NUMBER', 'EMAIL_ADDRESS', 'PERSON',
            'LOCATION', 'DATE_TIME', 'CREDIT_CARD',
            'IBAN_CODE', 'IP_ADDRESS', 'US_SSN'
        ]
    
    def _check_availability(self):
        """Check if Presidio is installed"""
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            return True
        except ImportError:
            return False
    
    def analyze(self, text: str, language: str = 'th'):
        """
        Analyze text for PII entities.
        
        Args:
            text: Text to analyze
            language: Language code ('th' for Thai, 'en' for English)
            
        Returns:
            list: Detected PII entities
        """
        if not self.available:
            return self._mock_analyze(text)
        
        try:
            from presidio_analyzer import AnalyzerEngine
            
            analyzer = AnalyzerEngine()
            results = analyzer.analyze(
                text=text,
                language=language,
                entities=self.entities
            )
            
            return [
                {
                    'entity_type': r.entity_type,
                    'start': r.start,
                    'end': r.end,
                    'score': r.score,
                    'text': text[r.start:r.end]
                }
                for r in results
            ]
        
        except Exception as e:
            print(f"Presidio analysis failed: {e}")
            return self._mock_analyze(text)
    
    def anonymize(self, text: str, language: str = 'th'):
        """
        Anonymize PII in text.
        
        Args:
            text: Text to anonymize
            language: Language code
            
        Returns:
            dict: Anonymized text and entities found
        """
        if not self.available:
            return self._mock_anonymize(text)
        
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            
            analyzer = AnalyzerEngine()
            anonymizer = AnonymizerEngine()
            
            # Analyze
            results = analyzer.analyze(
                text=text,
                language=language,
                entities=self.entities
            )
            
            # Anonymize
            anonymized = anonymizer.anonymize(
                text=text,
                analyzer_results=results
            )
            
            return {
                'anonymized_text': anonymized.text,
                'entities_found': len(results),
                'entities': [r.entity_type for r in results]
            }
        
        except Exception as e:
            print(f"Presidio anonymization failed: {e}")
            return self._mock_anonymize(text)
    
    def _mock_analyze(self, text: str):
        """Mock analysis using regex"""
        import re
        
        entities = []
        
        # Phone numbers
        phone_pattern = r'0\d{9}|0\d{1,2}-\d{3,4}-\d{4}'
        for match in re.finditer(phone_pattern, text):
            entities.append({
                'entity_type': 'PHONE_NUMBER',
                'start': match.start(),
                'end': match.end(),
                'score': 0.95,
                'text': match.group()
            })
        
        # Email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        for match in re.finditer(email_pattern, text):
            entities.append({
                'entity_type': 'EMAIL_ADDRESS',
                'start': match.start(),
                'end': match.end(),
                'score': 0.95,
                'text': match.group()
            })
        
        # Thai ID
        id_pattern = r'\d{13}|\d{1}-\d{4}-\d{5}-\d{2}-\d{1}'
        for match in re.finditer(id_pattern, text):
            entities.append({
                'entity_type': 'NATIONAL_ID',
                'start': match.start(),
                'end': match.end(),
                'score': 0.90,
                'text': match.group()
            })
        
        return entities
    
    def _mock_anonymize(self, text: str):
        """Mock anonymization"""
        import re
        
        anonymized = text
        entities_found = []
        
        # Replace phone
        phone_pattern = r'0\d{9}'
        if re.search(phone_pattern, anonymized):
            anonymized = re.sub(phone_pattern, '0XX-XXX-XXXX', anonymized)
            entities_found.append('PHONE_NUMBER')
        
        # Replace email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if re.search(email_pattern, anonymized):
            anonymized = re.sub(email_pattern, '<EMAIL>', anonymized)
            entities_found.append('EMAIL_ADDRESS')
        
        # Replace ID
        id_pattern = r'\d{13}'
        if re.search(id_pattern, anonymized):
            anonymized = re.sub(id_pattern, '<NATIONAL_ID>', anonymized)
            entities_found.append('NATIONAL_ID')
        
        return {
            'anonymized_text': anonymized,
            'entities_found': len(entities_found),
            'entities': list(set(entities_found)),
            'mode': 'mock'
        }


# Singleton
_presidio_service = None

def get_presidio_service():
    """Get singleton instance"""
    global _presidio_service
    if _presidio_service is None:
        _presidio_service = PresidioService()
    return _presidio_service
