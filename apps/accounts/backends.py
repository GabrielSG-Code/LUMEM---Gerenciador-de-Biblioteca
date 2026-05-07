from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameBackend(ModelBackend):
    """
    Custom authentication backend that allows login with either email or username
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        try:
            # Try to find user by email or username
            user = User.objects.get(
                Q(email=username) | Q(username=username)
            )
            
            # Check if password is correct
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None