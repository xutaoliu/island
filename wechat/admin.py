from django.contrib import admin
from wechat.models import WechatUser, Message, TextMessage


admin.site.register([WechatUser, Message, TextMessage])
