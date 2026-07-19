from rest_framework import serializers
from django.contrib.auth import authenticate
from api.models import User, Hostel, Room, Asset, MaintenanceRequest


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'password', 'password_confirm', 'email', 'first_name', 'last_name']

    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            username=data.get('username'),
            password=data.get('password')
        )
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        data['user'] = user
        return data


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'description', 'asset_type', 'condition',
            'image', 'quantity', 'room', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

        
class MaintenanceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceRequest
        fields = [
            "id",
            "title",
            "description",
            "status",
            "priority",
            "asset",
            "room",
            "requested_by",
            "assigned_to",
            "notes",
            "created_at",
            "updated_at",
            "resolved_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

class RoomSerializer(serializers.ModelSerializer):
    assets = AssetSerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = ['id', 'room_number', 'floor', 'capacity', 'hostel', 'assets', 'created_at']
        read_only_fields = ['id', 'created_at']


class HostelSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, read_only=True)
    rooms_count = serializers.SerializerMethodField()

    class Meta:
        model = Hostel
        fields = ['id', 'name', 'description', 'rooms', 'rooms_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_rooms_count(self, obj):
        return obj.rooms.count()
