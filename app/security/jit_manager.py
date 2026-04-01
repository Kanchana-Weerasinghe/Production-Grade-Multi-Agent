"""
Just-in-Time privilege management for tools and agent communication
"""
import uuid
import time
from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from app.utils.logger import logger
from app.security.models import Action


@dataclass
class JITToken:
    """Just-in-Time access token"""
    token_id: str
    subject: str  # Agent or user ID
    resource: str  # Tool name or agent name
    action: str  # Action being granted
    issued_at: float
    expires_at: float
    signature: str

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def is_valid(self) -> bool:
        return not self.is_expired()


class JITManager:
    """Manages Just-in-Time privileges"""

    def __init__(self):
        from app.config.settings import settings
        self.active_tokens: Dict[str, JITToken] = {}
        self.token_lifetime_seconds = getattr(settings, 'JIT_TOKEN_LIFETIME_SECONDS', 300)
        self.max_concurrent_tokens = getattr(settings, 'MAX_JIT_TOKENS', 100)

    def request_privilege(
        self,
        subject: str,
        resource: str,
        action: str,
        duration_seconds: Optional[int] = None
    ) -> Optional[JITToken]:
        """
        Request a JIT privilege token

        Args:
            subject: Agent/user requesting access
            resource: Tool/agent being accessed
            action: Action to perform
            duration_seconds: How long the privilege should last

        Returns:
            JITToken if granted, None if denied
        """
        # Check if subject has base permission (this would integrate with authorization)
        # For now, assume we check against user permissions passed in context

        # Check token limits
        if len(self.active_tokens) >= self.max_concurrent_tokens:
            logger.security_warning("JIT token limit reached", subject=subject)
            return None

        # Create token
        duration = duration_seconds or self.token_lifetime_seconds
        now = time.time()

        token = JITToken(
            token_id=str(uuid.uuid4()),
            subject=subject,
            resource=resource,
            action=action,
            issued_at=now,
            expires_at=now + duration,
            signature=self._generate_signature(subject, resource, action, now)
        )

        self.active_tokens[token.token_id] = token
        logger.security_info("JIT token issued",
                          subject=subject,
                          resource=resource,
                          action=action,
                          token_id=token.token_id)

        return token

    def validate_privilege(self, token_id: str, subject: str, resource: str, action: str) -> bool:
        """
        Validate a JIT token for a specific operation

        Args:
            token_id: The token ID
            subject: Who is performing the action
            resource: What is being accessed
            action: What action is being performed

        Returns:
            True if valid, False otherwise
        """
        token = self.active_tokens.get(token_id)
        if not token:
            logger.security_error("Invalid JIT token", token_id=token_id)
            return False

        if token.is_expired():
            logger.security_warning("Expired JIT token used", token_id=token_id)
            self.revoke_privilege(token_id)
            return False

        # Verify token details match request
        if (token.subject != subject or
            token.resource != resource or
            token.action != action):
            logger.security_error("JIT token mismatch",
                                token_subject=token.subject,
                                request_subject=subject)
            return False

        # Verify signature
        if not self._verify_signature(token):
            logger.security_error("Invalid JIT token signature", token_id=token_id)
            return False

        logger.security_check("JIT token validated", token_id=token_id)
        return True

    def revoke_privilege(self, token_id: str):
        """Revoke a JIT token"""
        if token_id in self.active_tokens:
            del self.active_tokens[token_id]
            logger.security_info("JIT token revoked", token_id=token_id)

    def cleanup_expired_tokens(self):
        """Remove expired tokens"""
        expired = [tid for tid, token in self.active_tokens.items() if token.is_expired()]
        for tid in expired:
            del self.active_tokens[tid]
        if expired:
            logger.security_info("Cleaned up expired JIT tokens", count=len(expired))

    def _generate_signature(self, subject: str, resource: str, action: str, timestamp: float) -> str:
        """Generate a simple signature (in production, use crypto)"""
        # Simple HMAC-like signature for demo
        import hashlib
        import hmac
        from app.config.settings import settings

        secret = getattr(settings, 'JIT_SECRET_KEY', "default-jit-secret-change-in-production")
        message = f"{subject}:{resource}:{action}:{timestamp}"
        signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
        return signature

    def _verify_signature(self, token: JITToken) -> bool:
        """Verify token signature"""
        expected = self._generate_signature(token.subject, token.resource, token.action, token.issued_at)
        return token.signature == expected

    def get_active_privileges(self, subject: str) -> List[JITToken]:
        """Get all active privileges for a subject"""
        return [token for token in self.active_tokens.values()
                if token.subject == subject and not token.is_expired()]


# Global instance
jit_manager = JITManager()