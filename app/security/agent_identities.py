"""
Non-human identity management for agents
"""
import uuid
from typing import Dict, Optional
from dataclasses import dataclass
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from app.utils.logger import logger


@dataclass
class AgentIdentity:
    """Represents an agent's identity"""
    agent_id: str
    agent_name: str
    public_key: str
    private_key: str  # In production, store securely, not in memory
    capabilities: list[str]
    created_at: str

    def sign_message(self, message: str) -> str:
        """Sign a message with agent's private key"""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        import base64

        private_key_obj = serialization.load_pem_private_key(
            self.private_key.encode(),
            password=None,
            backend=default_backend()
        )

        signature = private_key_obj.sign(
            message.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        return base64.b64encode(signature).decode()

    def verify_signature(self, message: str, signature: str) -> bool:
        """Verify a signature with agent's public key"""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        import base64

        try:
            public_key_obj = serialization.load_pem_public_key(
                self.public_key.encode(),
                backend=default_backend()
            )

            public_key_obj.verify(
                base64.b64decode(signature),
                message.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            logger.security_error("Signature verification failed", error=str(e))
            return False


class AgentIdentityManager:
    """Manages agent identities and authentication"""

    def __init__(self):
        self.identities: Dict[str, AgentIdentity] = {}
        self._initialize_agent_identities()

    def _initialize_agent_identities(self):
        """Create identities for all agents"""
        agents = [
            ("PlannerAgent", ["plan", "delegate"]),
            ("ResearchAgent", ["research", "search"]),
            ("SummarizerAgent", ["summarize", "analyze"]),
            ("CriticAgent", ["critique", "review"]),
        ]

        for agent_name, capabilities in agents:
            self._create_identity(agent_name, capabilities)

    def _create_identity(self, agent_name: str, capabilities: list[str]):
        """Create a new agent identity with key pair"""
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()

        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        # Create identity
        identity = AgentIdentity(
            agent_id=str(uuid.uuid4()),
            agent_name=agent_name,
            public_key=public_pem,
            private_key=private_pem,
            capabilities=capabilities,
            created_at="2026-03-28T00:00:00Z"  # Current date
        )

        self.identities[agent_name] = identity
        logger.security_info("Agent identity created", agent=agent_name, id=identity.agent_id)

    def get_identity(self, agent_name: str) -> Optional[AgentIdentity]:
        """Get agent identity by name"""
        return self.identities.get(agent_name)

    def authenticate_agent(self, agent_name: str, signature: str, message: str) -> bool:
        """Authenticate an agent by verifying its signature"""
        identity = self.get_identity(agent_name)
        if not identity:
            logger.security_error("Unknown agent attempted authentication", agent=agent_name)
            return False

        return identity.verify_signature(message, signature)

    def get_all_public_keys(self) -> Dict[str, str]:
        """Get public keys for all agents (for distribution)"""
        return {name: identity.public_key for name, identity in self.identities.items()}


# Global instance
agent_identity_manager = AgentIdentityManager()