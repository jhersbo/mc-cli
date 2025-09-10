from enum import Enum

class PermissionLevel(Enum):
    """Permission levels for players on the server"""
    VISITOR = "visitor"
    MEMBER = "member"
    OPERATOR = "operator"
    ADMIN = "admin"