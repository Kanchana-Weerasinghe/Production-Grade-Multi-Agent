"""
Authentication service - handles token generation, validation, and user management
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config.settings import settings
from app.security.models import (
    TokenPayload, UserInfo, UserRole, Action, UserCredentials
)


class AuthenticationService:
    """Manages user authentication and JWT tokens"""
    
    def __init__(self):
        # Use pbkdf2 instead of bcrypt to avoid version compatibility issues
        self.pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
        self.secret_key = getattr(settings, "AUTH_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.token_expiration_hours = getattr(settings, "TOKEN_EXPIRATION_HOURS", 24)
        
        # In-memory user store (replace with database in production)
        self.users_db: Dict[str, UserInfo] = {}
        self._init_demo_users()
    
    def _init_demo_users(self):
        """Initialize demo users for testing"""
        demo_users = {
            "admin": {
                "user_id": "admin-001",
                "username": "admin",
                "roles": [UserRole.ADMIN],
                "permissions": [
                    Action.RESEARCH, Action.SUMMARIZE, Action.PLAN, Action.CRITIQUE,
                    Action.EXECUTE_WORKFLOW, Action.VIEW_RESULTS, Action.MANAGE_USERS,
                    Action.MODIFY_POLICIES
                ],
                "password": self.get_password_hash("admin123"),
                "is_active": True
            },
            "user": {
                "user_id": "user-001",
                "username": "user",
                "roles": [UserRole.USER],
                "permissions": [
                    Action.RESEARCH, Action.SUMMARIZE, Action.PLAN, Action.CRITIQUE,
                    Action.EXECUTE_WORKFLOW, Action.VIEW_RESULTS
                ],
                "password": self.get_password_hash("user123"),
                "is_active": True
            },
            "guest": {
                "user_id": "guest-001",
                "username": "guest",
                "roles": [UserRole.GUEST],
                "permissions": [Action.VIEW_RESULTS],
                "password": self.get_password_hash("guest123"),
                "is_active": True
            }
        }
        
        for username, user_data in demo_users.items():
            password_hash = user_data.pop("password")
            user_info = UserInfo(
                created_at=datetime.utcnow(),
                **user_data
            )
            self.users_db[username] = (user_info, password_hash)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def authenticate_user(self, credentials: UserCredentials) -> Optional[UserInfo]:
        """Authenticate user with credentials"""
        if credentials.username not in self.users_db:
            print(f"⚠️ Login attempt with non-existent username: {credentials.username}")
            return None
        
        user_info, password_hash = self.users_db[credentials.username]
        
        if not user_info.is_active:
            print(f"⚠️ Login attempt with inactive user: {credentials.username}")
            return None
        
        if not self.verify_password(credentials.password, password_hash):
            print(f"⚠️ Failed login attempt for user: {credentials.username}")
            return None
        
        print(f"✅ User authenticated successfully: {credentials.username}")
        return user_info
    
    def create_token(self, user_info: UserInfo) -> str:
        """Create JWT token for user"""
        now = datetime.utcnow()
        expiration = now + timedelta(hours=self.token_expiration_hours)
        
        # Convert to Unix timestamps (seconds since epoch)
        now_timestamp = int(now.timestamp())
        exp_timestamp = int(expiration.timestamp())
        
        # Create payload dict with Unix timestamps (not datetime objects)
        payload = {
            "sub": user_info.user_id,
            "user_id": user_info.user_id,
            "username": user_info.username,
            "roles": [r.value for r in user_info.roles],
            "permissions": [p.value for p in user_info.permissions],
            "iat": now_timestamp,
            "exp": exp_timestamp
        }
        
        encoded_jwt = jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenPayload]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Check expiration (payload['exp'] is already a Unix timestamp)
            exp_timestamp = payload.get("exp")
            if exp_timestamp and exp_timestamp < datetime.utcnow().timestamp():
                print("⚠️ Token has expired")
                return None
            
            # Convert permission and role strings back to enums
            permissions = [Action(p) for p in payload.get("permissions", [])]
            roles = [UserRole(r) for r in payload.get("roles", [])]
            
            # Convert Unix timestamps back to datetime objects
            iat_timestamp = payload.get("iat", 0)
            exp_timestamp = payload.get("exp", 0)
            iat_dt = datetime.fromtimestamp(iat_timestamp)
            exp_dt = datetime.fromtimestamp(exp_timestamp)
            
            token_payload = TokenPayload(
                sub=payload.get("sub"),
                user_id=payload.get("user_id"),
                username=payload.get("username"),
                roles=roles,
                permissions=permissions,
                iat=iat_dt,
                exp=exp_dt
            )
            
            return token_payload
            
        except JWTError as e:
            print(f"❌ Token validation failed: {str(e)}")
            return None
    
    def extract_token_from_header(self, authorization: str) -> Optional[str]:
        """Extract token from Authorization header"""
        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                return None
            return token
        except (ValueError, AttributeError):
            return None


# Global instance
auth_service = AuthenticationService()
