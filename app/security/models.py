"""
Authentication and Authorization Models
"""
from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    GUEST = "guest"


class Action(str, Enum):
    """System actions that require authorization"""
    RESEARCH = "research"
    SUMMARIZE = "summarize"
    PLAN = "plan"
    CRITIQUE = "critique"
    EXECUTE_WORKFLOW = "execute_workflow"
    VIEW_RESULTS = "view_results"
    MANAGE_USERS = "manage_users"
    MODIFY_POLICIES = "modify_policies"


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str = Field(..., description="Subject (user ID)")
    user_id: str
    username: str
    roles: List[UserRole]
    permissions: List[Action]
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")


class UserCredentials(BaseModel):
    """User login credentials"""
    username: str
    password: str


class UserInfo(BaseModel):
    """User information"""
    user_id: str
    username: str
    roles: List[UserRole]
    permissions: List[Action]
    created_at: datetime
    is_active: bool = True


class ActionRequest(BaseModel):
    """Action request with metadata"""
    action: Action
    agent_name: str
    task_data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str = Field(..., description="Unique request identifier")


class AuthorizationResult(BaseModel):
    """Authorization check result"""
    authorized: bool
    reason: Optional[str] = None
    required_role: Optional[UserRole] = None
    user_roles: List[UserRole]
    action: Action
