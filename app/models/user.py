"""
User model
"""

class User:
    """User model for application"""
    
    def __init__(self, id, email, created_at=None, avatar_url=None):
        self.id = id
        self.email = email
        self.created_at = created_at
        self.avatar_url = avatar_url
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'created_at': self.created_at,
            'avatar_url': self.avatar_url
        }
    
    @staticmethod
    def from_supabase(data):
        """Create User instance from Supabase data"""
        if not data:
            return None
        return User(
            id=data.get('id'),
            email=data.get('email'),
            created_at=data.get('created_at'),
            avatar_url=data.get('avatar_url')
        )

