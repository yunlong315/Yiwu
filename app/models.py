import datetime
from django.db import models
from django.utils import timezone
from app.enum import DictEnum
from app.tools import random_avatar_path
import uuid
import os


class Base(models.Model):
    class Meta:
        abstract = True

    def to_dict(self, mode: int = 0):
        fields = {}
        model_name = str(self._meta.model_name).upper()
        if mode:
            model_name = model_name + str(mode)
            print(model_name)
        for field in self._meta.fields:
            value = getattr(self, field.name)
            if model_name not in DictEnum.__members__ or field.name in DictEnum[model_name].value:
                if isinstance(value, models.Model):
                    value = value.to_dict(mode)
                elif isinstance(value, timezone.datetime):
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, datetime.timedelta):
                    value = value.total_seconds()
                fields[field.name] = value
        return fields

    def __str__(self):
        return 'meta'


DEFAULT_AVATAR = 'avatar/default_avatar.png'
DEFAULT_CHAT_AVATAR = 'avatar/DEFAULT_CHAT_AVATAR.jpg'


class User(Base):
    user_id = models.AutoField(primary_key=True)
    user_nickname = models.CharField(max_length=255, db_index=True, unique=True)
    user_name = models.CharField(max_length=255, default='')
    user_password = models.CharField(max_length=255, default='')
    user_email = models.CharField(max_length=255, default='', unique=True)
    user_avatar = models.ImageField(max_length=255, default=DEFAULT_AVATAR, upload_to=random_avatar_path)
    user_description = models.TextField(default='')
    user_instruction_complete = models.BooleanField(default=False)

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.user_nickname

    def info(self):
        return {
            'user_id': self.user_id,
            'user_nickname': self.user_nickname,
            'user_name': self.user_name,
            'user_email': self.user_email,
            'user_avatar': self.user_avatar.url,
            'user_description': self.user_description,
            'user_instruction_complete': self.user_instruction_complete,
        }


class Group(Base):
    group_id = models.AutoField(primary_key=True)
    group_name = models.CharField(max_length=255, default='')
    group_avatar = models.ImageField(max_length=255, default=DEFAULT_CHAT_AVATAR, upload_to=random_avatar_path)
    group_description = models.TextField(default='', blank=True)

    class Meta:
        db_table = 'group'


class UserGroup(Base):
    TEAM_CREATOR = 'creator'
    TEAM_ADMIN = 'admin'
    TEAM_MEMBER = 'member'

    ROLE_CHOICES = (
        (TEAM_CREATOR, 'creator'),
        (TEAM_ADMIN, 'admin'),
        (TEAM_MEMBER, 'member'),
    )

    user = models.ForeignKey('User', on_delete=models.CASCADE)
    group = models.ForeignKey('Group', on_delete=models.CASCADE)
    identity = models.CharField(max_length=20, choices=ROLE_CHOICES, default=TEAM_MEMBER)

    class Meta:
        db_table = 'userGroup'
        unique_together = ('user', 'group')


class Chat(Base):
    CHAT_DEFAULT = 'default'
    CHAT_PUBLIC = 'public'
    CHAT_PRIVATE = 'private'

    CHAT_CHOICE = (
        (CHAT_DEFAULT, 'default'),
        (CHAT_PUBLIC, 'public'),
        (CHAT_PRIVATE, 'private'),
    )

    chat_id = models.AutoField(primary_key=True)
    chat_name = models.CharField(max_length=255, default='')
    chat_avatar = models.CharField(max_length=255, default=DEFAULT_CHAT_AVATAR)
    chat_description = models.TextField(default='')
    chat_type = models.CharField(max_length=20, choices=CHAT_CHOICE, default=CHAT_DEFAULT)
    chat_owner = models.ForeignKey('User', on_delete=models.CASCADE, blank=True, null=True)

    # group default chat
    chat_group = models.ForeignKey('Group', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        db_table = 'chat'


class Message(Base):
    MESSAGE_TEXT = 'text'
    MESSAGE_FILE = 'file'
    MESSAGE_IMAGE = 'image'
    MESSAGE_VIDEO = 'video'

    MESSAGE_TYPE = (
        (MESSAGE_TEXT, 'text'),
        (MESSAGE_FILE, 'file'),
        (MESSAGE_IMAGE, 'image'),
        (MESSAGE_VIDEO, 'video'),
    )

    FORWARD_NONE = 'none'
    FORWARD_ITEM = 'item'
    FORWARD_COMBINED = 'combined'

    FORWARD_TYPE = (
        (FORWARD_NONE, 'none'),
        (FORWARD_ITEM, 'item'),
        (FORWARD_COMBINED, 'combined'),
    )

    message_id = models.AutoField(primary_key=True)
    message_title = models.TextField(default='')
    message_description = models.TextField(default='')
    message_time = models.DateTimeField(auto_now_add=True)
    message_from = models.ForeignKey('User', on_delete=models.CASCADE)
    message_to = models.ForeignKey('Chat', on_delete=models.CASCADE)
    message_type = models.CharField(max_length=255, choices=MESSAGE_TYPE, default=MESSAGE_TEXT)

    # forward relevant
    forward_type = models.CharField(max_length=255, choices=FORWARD_TYPE, default=FORWARD_NONE)

    class Meta:
        db_table = 'message'

    def info(self):
        return {
            'user_id': self.message_from.user_id,
            'avatar': self.message_from.user_avatar.__str__(),
            'user_name': self.message_from.user_nickname,
            'post_time': self.message_time.strftime('%Y-%m-%d %H:%M'),
            'post_short_time': self.message_time.strftime('%H:%M'),
            'chat_content': self.message_description,
            'message_id': self.message_id,
            'message_type': self.message_type,
            'forward_type': self.forward_type,
            'message_title': self.message_title
        }


class Forward(Base):
    forward_from = models.ForeignKey('Message', on_delete=models.CASCADE, related_name='forward_from')
    froward_to = models.ForeignKey('Message', on_delete=models.CASCADE, related_name='forward_to')
    time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'forward'


class At(Base):
    AT_MESSAGE = 'chat'
    AT_DOCUMENT = 'document'
    AT_INVITATION = 'invitation'

    AT_TYPE = (
        (AT_MESSAGE, 'chat'),
        (AT_DOCUMENT, 'document'),
        (AT_INVITATION, 'invitation')
    )

    at_id = models.AutoField(primary_key=True)
    at_from = models.ForeignKey('User', on_delete=models.CASCADE, related_name='at_from')
    at_user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='at_user')
    at_type = models.CharField(max_length=255, choices=AT_TYPE, default=AT_MESSAGE)
    at_message = models.ForeignKey('Message', on_delete=models.CASCADE, null=True, blank=True)
    at_document = models.ForeignKey('Document', on_delete=models.CASCADE, null=True, blank=True)
    at_chat = models.ForeignKey('Chat', on_delete=models.CASCADE, null=True, blank=True)
    at_group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True)
    at_time = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'at'

    def info(self):
        return {
            'message_id': self.at_id,  # 消息id
            'message_from_name': self.at_from.user_name,  # 消息发送者的名字,@我的用户的真实姓名，或者邀请我的用户的真实姓名
            'message_from_location': self.get_message_from_location(),  # type为message时，为群聊名；type为document时，为文档名；type为邀请时，为邀请加入的团队名称或者群聊名称
            'message_time': self.at_time.strftime('%Y-%m-%d %H:%M'),  # 消息发送时间
            'message_content': self.at_message.message_description if self.at_type == 'message' else '',  # 消息内容 如果是文档或者邀请的话，发一个空字符串
            'at_type': self.get_type(),  # 消息类型，document or message or chat_invitation or group_invitation
            'if_read': self.is_read,  # 是否已读，已读为"true"，未读为"false"
        }

    def get_message_from_location(self):
        if self.at_type == 'message':
            return self.at_message.message_to.chat_name
        if self.at_type == 'document':
            return self.at_document.document_title
        if self.at_type == 'invitation':
            if self.at_chat is not None:
                return self.at_chat.chat_name
            if self.at_group is not None:
                return self.at_group.group_name
        return ''

    def get_type(self):
        if self.at_type == 'message' or self.at_type == 'document':
            return self.at_type
        if self.at_chat is not None:
            return 'chat_invitation'
        if self.at_group is not None:
            return 'group_invitation'
        return ''


class UserChat(Base):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    chat = models.ForeignKey('Chat', on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'userChat'


class UserMessage(Base):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    message = models.ForeignKey('Message', on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_at = models.BooleanField(default=False)

    class Meta:
        db_table = 'userMessage'


class Project(Base):
    project_id = models.AutoField(primary_key=True)
    project_name = models.CharField(max_length=255)
    project_create_date = models.DateField(auto_now_add=True)
    project_creator = models.ForeignKey('User', on_delete=models.CASCADE)
    project_group = models.ForeignKey('Group', on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)
    deletion_date = models.DateTimeField(null=True, blank=True)
    clone_times = models.IntegerField(default=0)

    class Meta:
        db_table = 'project'
        ordering = ['-project_id']

    def soft_delete(self):
        self.is_deleted = True
        self.deletion_date = timezone.now()
        self.save()

    def recover(self):
        self.is_deleted = False
        self.deletion_date = None
        self.save()


def default_to_date():
    return timezone.now() + datetime.timedelta(minutes=10)


class ConfirmCode(Base):
    cc_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=10)
    user_email = models.CharField(max_length=255, blank=False)
    # 有效时间设定10
    # 服务器运行时，如果注册时不指定to_date,服务器上存的时间会错误
    to_date = models.DateTimeField(default=default_to_date, db_index=True)

    class Meta:
        ordering = ['-to_date']
        db_table = 'confirm_code'


class ResetCode(Base):
    rc_id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=10)
    user_email = models.CharField(max_length=255, blank=False)

    # 有效时间设定为10分钟
    to_date = models.DateTimeField(default=default_to_date, db_index=True)

    class Meta:
        ordering = ['-to_date']
        db_table = 'reset_code'


class ProtoType(Base):
    prototype_id = models.AutoField(primary_key=True)
    prototype_project = models.ForeignKey('Project', on_delete=models.CASCADE)
    prototype_creator = models.ForeignKey('User', on_delete=models.CASCADE)
    prototype_name = models.CharField(max_length=255, default='')
    prototype_description = models.CharField(max_length=255, default='')
    prototype_content = models.JSONField()

    class Meta:
        db_table = 'prototype'


class ChangeInPrototype(Base):
    cip_id = models.AutoField(primary_key=True)
    cip_prototype = models.ForeignKey('ProtoType', on_delete=models.CASCADE)
    cip_time = models.DateTimeField(auto_now=True)
    cip_content = models.JSONField()

    class Meta:
        db_table = 'change_in_prototype'


class Document(Base):
    document_id = models.AutoField(primary_key=True)
    document_directory = models.ForeignKey('Directory', on_delete=models.CASCADE, null=True, blank=True)
    document_creator = models.ForeignKey('User', on_delete=models.CASCADE)
    document_title = models.CharField(max_length=255, default='')
    document_content = models.JSONField()

    class Meta:
        db_table = 'document'


class DocumentVersion(Base):
    dv_origin_document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='dv_origin_document')
    dv_saved_document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='dv_saved_document')
    dv_time = models.DateTimeField(auto_now=True)
    dv_saver = models.ForeignKey('User', on_delete=models.CASCADE)

    class Meta:
        db_table = 'document_version'


class Directory(Base):
    directory_id = models.AutoField(primary_key=True)
    directory_name = models.CharField(max_length=255)
    directory_project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True,
                                          blank=True)  # for base directory
    directory_directory = models.ForeignKey('Directory', on_delete=models.CASCADE, null=True,
                                            blank=True)  # for secondary directory

    class Meta:
        db_table = 'directory'


class Preview(Base):
    preview_id = models.AutoField(primary_key=True)
    project = models.OneToOneField('Project', on_delete=models.CASCADE)
    code = models.CharField(max_length=100)

    class Meta:
        db_table = 'preview'


class File(Base):
    file = models.FileField(upload_to='file/')
    real_name = models.CharField(max_length=1023, default='')
    type = models.CharField(max_length=255, default='file')

    class Meta:
        db_table = 'file'
