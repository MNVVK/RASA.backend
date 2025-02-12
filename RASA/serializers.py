from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Engine, Acceptance, EngineAcceptance

User = get_user_model()


class EngineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Engine
        fields = ['id', 'title', 'description', 'engine_data', 'status',
                  'image_url']
        read_only_fields = ['id', 'image_url']


class EngineAcceptanceSerializer(serializers.ModelSerializer):
    engine = EngineSerializer(read_only=True)

    class Meta:
        model = EngineAcceptance
        fields = ['engine', 'accepted']
        read_only_fields = ['engine']


class AcceptanceSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(source='creator.username', read_only=True)
    moderator = serializers.CharField(source='moderator.username',
                                      default=None, read_only=True)

    class Meta:
        model = Acceptance
        fields = ['id', 'title', 'name', 'status', 'creator', 'moderator',
                  'formation_date', 'completion_date', 'total_accepted']
        read_only_fields = ['id', 'status', 'formation_date',
                            'completion_date', 'total_accepted']


class AcceptanceDetailSerializer(serializers.ModelSerializer):
    creator = serializers.CharField(source='creator.username', read_only=True)
    moderator = serializers.CharField(source='moderator.username',
                                      default=None, read_only=True)
    engines = EngineAcceptanceSerializer(source='engineacceptance_set',
                                         many=True)

    class Meta:
        model = Acceptance
        fields = ['id', 'title', 'name', 'status', 'creator', 'moderator',
                  'formation_date', 'completion_date', 'engines',
                  'total_accepted']
        read_only_fields = ['id', 'status', 'formation_date',
                            'completion_date', 'total_accepted']


class AcceptanceStatusSerializer(serializers.Serializer):
    status = serializers.CharField()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'is_staff', 'is_superuser']
        read_only_fields = ['is_staff', 'is_superuser']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        instance.username = validated_data.get('username', instance.username)
        password = validated_data.get('password')
        if password:
            instance.set_password(password)
        instance.save()
        return instance
