from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(User)
admin.site.register(Group)
admin.site.register(UserGroup)
admin.site.register(Chat)
admin.site.register(Message)