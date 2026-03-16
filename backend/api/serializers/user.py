from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer mapping the User instance into JSON format.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
