"""
Authentication Middleware
Handles JWT token validation and user authentication
"""

from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
from sqlalchemy.orm import Session

from database.simple_connection import get_db
from database.models import User, Tenant
from api.services.auth_service import auth_service

logger = logging.getLogger(__name__)

class AuthMiddleware:
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)

    async def get_current_user(
        self, 
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = None,
        db: Session = None
    ) -> Optional[User]:
        """Get current authenticated user from token"""
        if not db:
            db = next(get_db())
            
        if not credentials:
            return None
            
        try:
            token = credentials.credentials
            payload = auth_service.verify_token(token)
            
            if not payload:
                return None
                
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            
            if not user_id or not tenant_id:
                return None
                
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                return None
                
            # Verify tenant is active
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant or not tenant.is_active:
                return None
                
            return user
            
        except Exception as e:
            logger.error(f"Authentication middleware error: {str(e)}")
            return None

    def require_auth(self, require_verified: bool = True, allowed_roles: list = None):
        """Decorator to require authentication"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract request and get credentials
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if not request:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Request object not found"
                    )
                
                # Get authorization header
                authorization = request.headers.get("authorization")
                if not authorization or not authorization.startswith("Bearer "):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required",
                        headers={"WWW-Authenticate": "Bearer"}
                    )
                
                # Create credentials object
                token = authorization.replace("Bearer ", "")
                credentials = HTTPAuthorizationCredentials(
                    scheme="Bearer",
                    credentials=token
                )
                
                # Get current user
                db = next(get_db())
                user = await self.get_current_user(request, credentials, db)
                
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired token",
                        headers={"WWW-Authenticate": "Bearer"}
                    )
                
                # Check if email verification is required
                if require_verified and not user.is_verified:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Email verification required"
                    )
                
                # Check role permissions
                if allowed_roles and user.role not in allowed_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions"
                    )
                
                # Add user to kwargs
                kwargs['current_user'] = user
                kwargs['db'] = db
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator

    def optional_auth(self):
        """Decorator for optional authentication"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Extract request
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                user = None
                db = next(get_db())
                
                if request:
                    # Try to get authorization header
                    authorization = request.headers.get("authorization")
                    if authorization and authorization.startswith("Bearer "):
                        token = authorization.replace("Bearer ", "")
                        credentials = HTTPAuthorizationCredentials(
                            scheme="Bearer",
                            credentials=token
                        )
                        user = await self.get_current_user(request, credentials, db)
                
                # Add user to kwargs (can be None)
                kwargs['current_user'] = user
                kwargs['db'] = db
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator

# Global instance
auth_middleware = AuthMiddleware()
