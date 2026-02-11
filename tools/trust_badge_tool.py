"""Trust Badge Tool"""
import jwt
import datetime

SECRET = "quickchatid-secret-key-change-in-production"

def issue_trust_badge(trust_level: str, risk_score: float, user_id: str = ""):
    limits = {'bronze': 10000, 'silver': 50000, 'gold': 100000, 'platinum': -1}
    
    benefits = {
        'bronze': ['Basic verification', 'Standard transactions', 'Email support'],
        'silver': ['Enhanced verification', 'Priority processing', 'Chat support', 'Lower fees'],
        'gold': ['Premium verification', 'Fast-track', '24/7 support', 'Waived fees', 'Premium features'],
        'platinum': ['Highest verification', 'Instant processing', 'Dedicated manager', 'Zero fees', 'VIP features']
    }
    
    expires = datetime.datetime.utcnow() + datetime.timedelta(days=365)
    
    payload = {
        'trust_level': trust_level,
        'risk_score': risk_score,
        'transaction_limit': limits[trust_level],
        'benefits': benefits[trust_level],
        'issued_at': datetime.datetime.utcnow().isoformat(),
        'expires_at': expires.isoformat(),
        'user_id': user_id if user_id else None
    }
    
    token = jwt.encode(payload, SECRET, algorithm='HS256')
    
    return {
        'jwt_token': token if isinstance(token, str) else token.decode(),
        'trust_level': trust_level,
        'risk_score': risk_score,
        'transaction_limit': limits[trust_level],
        'benefits': benefits[trust_level],
        'expires_at': expires.isoformat(),
        'message': f"Badge issued: {trust_level.upper()}"
    }
