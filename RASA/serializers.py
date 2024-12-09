from rest_framework import serializers
from .models import Engine, Acceptance, EngineAcceptance
from django.contrib.auth.models import User


class EngineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Engine
        fields = ['id', 'title', 'description', 'engine_data', 'status', 'image_url']


class EngineAcceptanceSerializer(serializers.ModelSerializer):
    engine = EngineSerializer()

    class Meta:
        model = EngineAcceptance
        fields = ['engine', 'accepted']


class AcceptanceSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(source='creator.username')
    moderator = serializers.CharField(source='moderator.username', default=None)

    class Meta:
        model = Acceptance
        fields = ['id', 'title', 'name', 'status', 'creator', 'moderator',
                  'formation_date', 'completion_date']


class AcceptanceDetailSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(source='creator.username')
    moderator = serializers.CharField(source='moderator.username', default=None)
    engines = EngineAcceptanceSerializer(source='engineacceptance_set', many=True)

    class Meta:
        model = Acceptance
        fields = ['id', 'title', 'name', 'status', 'creator', 'moderator',
                  'formation_date', 'completion_date', 'engines']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        password = validated_data.get('password')
        if password:
            instance.set_password(password)
        instance.save()
        return instance
