import os

from rest_framework import serializers

from .models import *
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'user_nickname', 'user_name', 'user_password', 'user_email', 'user_avatar',
                  'user_description', 'user_instruction_complete']
        extra_kwargs = {
            'user_password': {'write_only': True},

        }

    # 创建时对密码加密
    def create(self, validated_data):
        user = User(**validated_data)
        user.user_password = make_password(validated_data["user_password"])
        user.save()
        return user


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'


class UserGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroup
        fields = '__all__'


class UserGroupDetailSerializer(serializers.ModelSerializer):
    ## 嵌套序列化
    user = UserSerializer()

    class Meta:
        model = UserGroup
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'


class ProjectDetailSerializer(serializers.ModelSerializer):
    project_creator = UserSerializer()

    class Meta:
        model = Project
        fields = '__all__'


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = '__all__'


class PrototypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProtoType
        fields = '__all__'
