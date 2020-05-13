from django.utils import timezone
from wechat.models import User, WechatUser
from wechatpy.replies import TextReply
from twitter_image.models import Task, TaskTweet
from django.shortcuts import reverse
from django.contrib.auth.models import Group
from django.db import transaction
import logging

logger = logging.getLogger('wechat')
state_functions = {}


def for_state(state, desc):
    def decorator(func):
        func.desc = desc
        state_functions[state] = func
        return func
    return decorator


def subscribe(msg):
    with transaction.atomic():
        if User.objects.filter(username=msg.source).exists():
            user = User.objects.get(username=msg.source)
        else:
            user = User.objects.create_user(username=msg.source)
            user.groups.set([Group.objects.get(name='wechat')])
            user.save()
        WechatUser.objects.create(user=user, openid=msg.source, subscribe_time=msg.create_time)
    return TextReply(content='\n'.join([f'{state} - {func.desc}' for state, func in state_functions.items()]), message=msg)


def unsubscribe(msg):
    WechatUser.objects.filter(openid=msg.source).delete()


@for_state('--help', '显示指令帮助')
def state_help(request, user, msg, data, step):
    return TextReply(content='\n'.join([f'{state} - {func.desc}' for state, func in state_functions.items()]), message=msg), None


@for_state('--cancel', '取消当前指令')
def state_cancel(request, user, msg, data, step):
    return TextReply(content='已取消.', message=msg), None


@for_state('--bind', '绑定推特账号')
def state_bind(request, user, msg, data, step):
    if step == 0:
        return TextReply(content='Twitter ID:', message=msg), data
    elif step == 1:
        data['twitter_id'] = msg.content
        return TextReply(content='Tag (e.g. #NintendoSwitch):', message=msg), data
    elif step == 2:
        data['tag'] = msg.content
        if 'twitter_id' not in data:
            logger.error(f'twitter_id not found in state @bind at step: {step}, {msg}, {data}')
            return None, None
        with transaction.atomic():
            tasks = Task.objects.select_for_update().filter(owner=user.user)
            if tasks.exists():
                tasks.update(username=data['twitter_id'], tag=msg.content, last_update=timezone.make_aware(timezone.datetime.utcfromtimestamp(0), timezone=timezone.utc))
            else:
                Task.objects.create(username=data['twitter_id'], tag=msg.content, owner=user.user)
        return TextReply(content='Bind success.', message=msg), None
    else:
        logger.error(f'Unknown step for state @bind: {step}, {msg}, {data}')
    return None, None


@for_state('--update', '更新照片')
def state_update(request, user, msg, data, step):
    with transaction.atomic():
        tasks = Task.objects.select_for_update(skip_locked=True).filter(owner=user.user)
        with timezone.override(None):
            for task in tasks:
                task.update(auto_flush_new=False)
                task.last_update = timezone.now()
                task.save()
    return TextReply(content='更新中...\n请使用--imgs获取新照片', message=msg), None


@for_state('--imgs', '获取新的照片')
def state_imgs(request, user, msg, data, step):
    with transaction.atomic():
        tweets = TaskTweet.objects.select_for_update().filter(task__owner=user.user, new=True)
        if tweets.exists():
            paths = tweets.values_list('images__image', flat=True)
            urls = []
            for path in paths:
                urls.append(request.build_absolute_uri(reverse('media', kwargs={'path': path})))
            tweets.update(new=False)
            return TextReply(content='\n'.join(urls), message=msg), None
        else:
            return TextReply(content='还没有获取到照片，请稍后再试', message=msg), None
