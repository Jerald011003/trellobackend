from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    CustomUser, Board, List, Card, Label, CardLabel, 
    Checklist, ChecklistItem, Attachment, Comment, Activity
)
from rest_framework_simplejwt.tokens import RefreshToken

class UserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    isAdmin = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'name', 'isAdmin']

    def get_isAdmin(self, obj):
        return obj.is_staff

    def get_name(self, obj):
        return obj.get_full_name()

class UserSerializerWithToken(UserSerializer):
    token = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'email', 'is_staff', 'token']
    
    def get_token(self, obj):
        token = RefreshToken.for_user(obj)
        return {
            'refresh': str(token),
            'access': str(token.access_token)
        }

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = '__all__'

class ChecklistItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = '__all__'

class ChecklistSerializer(serializers.ModelSerializer):
    items = ChecklistItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Checklist
        fields = '__all__'

class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Attachment
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    
    class Meta:
        model = Comment
        fields = '__all__'

class CardSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    checklists = ChecklistSerializer(many=True, read_only=True)
    
    class Meta:
        model = Card
        fields = '__all__'

class ListSerializer(serializers.ModelSerializer):
    cards = CardSerializer(many=True, read_only=True)
    
    class Meta:
        model = List
        fields = '__all__'

class BoardSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    lists = ListSerializer(many=True, read_only=True)
    
    class Meta:
        model = Board
        fields = '__all__'

class ActivitySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Activity
        fields = '__all__'

class BoardDetailSerializer(BoardSerializer):
    activities = ActivitySerializer(many=True, read_only=True)
