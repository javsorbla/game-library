from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    # we expose the password field as write‑only so that it is never returned in
    # API responses.
    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        # use the manager's create_user method so that the password is hashed
        return User.objects.create_user(**validated_data)
