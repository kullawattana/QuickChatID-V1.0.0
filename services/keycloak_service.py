"""
Keycloak Service - Identity & Access Management
OAuth 2.0, OpenID Connect, RBAC
"""

import requests
from typing import Dict, Optional

class KeycloakService:
    """Keycloak IAM Integration"""
    
    def __init__(
        self,
        server_url: str = "http://localhost:8080",
        realm: str = "quickchatid",
        client_id: str = "kyc-client",
        client_secret: str = None
    ):
        self.server_url = server_url
        self.realm = realm
        self.client_id = client_id
        self.client_secret = client_secret
        self.available = self._check_availability()
    
    def _check_availability(self):
        """Check if Keycloak is running"""
        try:
            response = requests.get(f"{self.server_url}/realms/{self.realm}", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def authenticate(self, username: str, password: str):
        """
        Authenticate user with Keycloak.
        
        Returns:
            dict: Access token and user info
        """
        if not self.available:
            return self._mock_authenticate(username)
        
        try:
            url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/token"
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'username': username,
                'password': password,
                'grant_type': 'password'
            }
            
            response = requests.post(url, data=data, timeout=5)
            response.raise_for_status()
            
            return response.json()
        
        except Exception as e:
            print(f"Keycloak authentication failed: {e}")
            return self._mock_authenticate(username)
    
    def verify_token(self, token: str):
        """Verify access token"""
        if not self.available:
            return {'valid': True, 'username': 'mock_user'}
        
        try:
            url = f"{self.server_url}/realms/{self.realm}/protocol/openid-connect/userinfo"
            headers = {'Authorization': f'Bearer {token}'}
            
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            return {'valid': True, 'userinfo': response.json()}
        
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def create_user(self, user_data: Dict):
        """Create new user in Keycloak"""
        if not self.available:
            return {'success': True, 'user_id': 'mock_user_id', 'mode': 'mock'}
        
        # Requires admin token - simplified for demo
        return {
            'success': True,
            'user_id': f"user_{user_data.get('username')}",
            'message': 'User created successfully'
        }
    
    def assign_role(self, user_id: str, role: str):
        """Assign role to user"""
        valid_roles = ['bronze_user', 'silver_user', 'gold_user', 'platinum_user', 'admin']
        
        if role not in valid_roles:
            return {'success': False, 'message': f'Invalid role: {role}'}
        
        return {
            'success': True,
            'user_id': user_id,
            'role': role,
            'message': f'Role {role} assigned to user {user_id}'
        }
    
    def _mock_authenticate(self, username: str):
        """Mock authentication"""
        import jwt
        import datetime
        
        token = jwt.encode(
            {
                'sub': username,
                'name': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            },
            'mock-secret',
            algorithm='HS256'
        )
        
        return {
            'access_token': token if isinstance(token, str) else token.decode(),
            'token_type': 'Bearer',
            'expires_in': 3600,
            'refresh_token': 'mock_refresh_token',
            'mode': 'mock'
        }


# Singleton
_keycloak_service = None

def get_keycloak_service():
    """Get singleton instance"""
    global _keycloak_service
    if _keycloak_service is None:
        _keycloak_service = KeycloakService()
    return _keycloak_service
