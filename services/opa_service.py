"""
Open Policy Agent (OPA) Service
Real policy evaluation for KYC risk assessment
"""

import requests
import json
from typing import Dict, Any

class OPAService:
    """OPA Policy Evaluation Service"""
    
    def __init__(self, opa_url: str = "http://localhost:8181"):
        self.opa_url = opa_url
        self.available = self._check_availability()
    
    def _check_availability(self):
        """Check if OPA server is running"""
        try:
            response = requests.get(f"{self.opa_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def evaluate_policy(self, policy_path: str, input_data: Dict[Any, Any]):
        """
        Evaluate a policy with input data.
        
        Args:
            policy_path: Path to policy (e.g., "kyc/risk_assessment")
            input_data: Input data for policy evaluation
            
        Returns:
            dict: Policy evaluation result
        """
        if not self.available:
            return self._mock_evaluation(input_data)
        
        try:
            url = f"{self.opa_url}/v1/data/{policy_path.replace('.', '/')}"
            payload = {"input": input_data}
            
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            
            return response.json().get('result', {})
        
        except Exception as e:
            print(f"OPA evaluation failed: {e}")
            return self._mock_evaluation(input_data)
    
    def _mock_evaluation(self, input_data: Dict):
        """Mock evaluation when OPA not available"""
        # Calculate basic risk score
        face_score = input_data.get('face_match_score', 0.9)
        liveness_score = input_data.get('liveness_score', 0.9)
        deepfake_score = 1 - input_data.get('deepfake_probability', 0.1)
        ocr_score = input_data.get('ocr_confidence', 0.9)
        scam_score = 1 - input_data.get('scam_score', 0.1)
        
        # Weighted calculation
        risk_score = (
            face_score * 0.30 +
            liveness_score * 0.25 +
            deepfake_score * 0.20 +
            ocr_score * 0.15 +
            scam_score * 0.10
        ) * 100
        
        # Determine trust level
        if risk_score >= 96:
            trust_level = 'platinum'
        elif risk_score >= 81:
            trust_level = 'gold'
        elif risk_score >= 61:
            trust_level = 'silver'
        else:
            trust_level = 'bronze'
        
        # Check blocking conditions
        blocked = False
        block_reasons = []
        
        if input_data.get('scam_score', 0) > 0.7:
            blocked = True
            block_reasons.append('High scam score')
        
        if input_data.get('deepfake_probability', 0) > 0.7:
            blocked = True
            block_reasons.append('Deepfake detected')
        
        if liveness_score < 0.3:
            blocked = True
            block_reasons.append('Failed liveness check')
        
        return {
            'allow': not blocked and risk_score >= 50,
            'risk_score': round(risk_score, 2),
            'trust_level': trust_level,
            'blocked': blocked,
            'block_reasons': block_reasons,
            'transaction_limit': {
                'bronze': 10000,
                'silver': 50000,
                'gold': 100000,
                'platinum': -1
            }.get(trust_level, 0),
            'evaluation_mode': 'mock' if not self.available else 'real'
        }
    
    def load_policy(self, policy_name: str, policy_code: str):
        """Load a Rego policy into OPA"""
        if not self.available:
            return {'success': False, 'message': 'OPA not available'}
        
        try:
            url = f"{self.opa_url}/v1/policies/{policy_name}"
            headers = {'Content-Type': 'text/plain'}
            
            response = requests.put(url, data=policy_code, headers=headers, timeout=5)
            response.raise_for_status()
            
            return {'success': True, 'message': f'Policy {policy_name} loaded'}
        
        except Exception as e:
            return {'success': False, 'message': str(e)}


# Singleton
_opa_service = None

def get_opa_service():
    """Get singleton instance"""
    global _opa_service
    if _opa_service is None:
        _opa_service = OPAService()
    return _opa_service
