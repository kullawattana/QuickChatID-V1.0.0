"""
Guardrails.ai Service - LLM Output Validation
Validates LLM outputs for toxicity, PII, and compliance
"""

class GuardrailsService:
    """Validate LLM outputs using Guardrails.ai"""
    
    def __init__(self):
        self.validators = {
            'toxic_language': self._check_toxicity,
            'pii_present': self._check_pii,
            'compliance': self._check_compliance
        }
    
    def validate_output(self, text: str, validators: list = None):
        """
        Validate LLM output text.
        
        Args:
            text: LLM output to validate
            validators: List of validator names to run
            
        Returns:
            dict: Validation results
        """
        if validators is None:
            validators = list(self.validators.keys())
        
        results = {}
        passed = True
        
        for validator_name in validators:
            if validator_name in self.validators:
                result = self.validators[validator_name](text)
                results[validator_name] = result
                if not result['passed']:
                    passed = False
        
        return {
            'passed': passed,
            'text': text,
            'validations': results,
            'message': 'All validations passed' if passed else 'Some validations failed'
        }
    
    def _check_toxicity(self, text: str):
        """Check for toxic/offensive language"""
        toxic_words = ['โง่', 'ไอ้', 'เหี้ย', 'สัส']  # Thai toxic words
        
        found_toxic = []
        text_lower = text.lower()
        
        for word in toxic_words:
            if word in text_lower:
                found_toxic.append(word)
        
        return {
            'passed': len(found_toxic) == 0,
            'toxic_words_found': found_toxic,
            'severity': 'high' if found_toxic else 'none'
        }
    
    def _check_pii(self, text: str):
        """Check for PII leakage"""
        import re
        
        pii_patterns = {
            'phone': r'0\d{9}',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'id_card': r'\d{13}'
        }
        
        found_pii = {}
        for pii_type, pattern in pii_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                found_pii[pii_type] = matches
        
        return {
            'passed': len(found_pii) == 0,
            'pii_found': found_pii,
            'severity': 'high' if found_pii else 'none'
        }
    
    def _check_compliance(self, text: str):
        """Check PDPA compliance"""
        # Check if bot asks for sensitive info without proper context
        sensitive_requests = [
            'รหัสผ่าน', 'password', 'pin', 'otp',
            'บัตรเครดิต', 'credit card',
            'cvv', 'เลขบัญชี', 'account number'
        ]
        
        violations = []
        text_lower = text.lower()
        
        for request in sensitive_requests:
            if request in text_lower:
                violations.append(request)
        
        return {
            'passed': len(violations) == 0,
            'violations': violations,
            'severity': 'critical' if violations else 'none'
        }


# Singleton instance
_guardrails_service = None

def get_guardrails_service():
    """Get singleton instance"""
    global _guardrails_service
    if _guardrails_service is None:
        _guardrails_service = GuardrailsService()
    return _guardrails_service
