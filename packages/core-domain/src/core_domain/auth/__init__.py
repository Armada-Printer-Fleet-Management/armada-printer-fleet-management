"""The auth domain's entity and rules, shared by every app that handles users."""

from core_domain.auth.entities import User, UserRole, UserStatus

__all__ = ["User", "UserRole", "UserStatus"]
