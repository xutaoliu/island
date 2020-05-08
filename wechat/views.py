from twitter_image.models import Task
from django.db import transaction
from wechatpy.utils import check_signature
from island import settings
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from django.http import HttpResponse, HttpResponseBadRequest
from wechatpy import parse_message
from wechatpy.crypto import WeChatCrypto
from wechatpy.replies import TextReply, EmptyReply
from django.views.decorators.csrf import csrf_exempt
from wechat.models import User, WechatUser, Message, TextMessage
from django.contrib.auth.models import Group
import logging
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger('wechat')
crypto = WeChatCrypto(settings.WECHAT_TOKEN, settings.WECHAT_AES_KEY, settings.WECHAT_APPID)
state_functions = {}


@csrf_exempt
def serve(request):
    timestamp = request.GET.get('timestamp', '')
    nonce = request.GET.get('nonce', '')
    if request.method == 'GET':
        signature = request.GET.get('signature', '')
        echo_str = request.GET.get('echostr', '')
        try:
            check_signature(settings.WECHAT_TOKEN, signature, timestamp, nonce)
            logger.info('Wechat signature validated.')
            return HttpResponse(echo_str)
        except InvalidSignatureException:
            logger.warning('Invalid wechat signature.')
            return HttpResponseBadRequest()
    elif request.method == 'POST':
        signature = request.GET.get('msg_signature', '')
        try:
            decrypted_xml = crypto.decrypt_message(request.body, signature, timestamp, nonce)
        except (InvalidAppIdException, InvalidSignatureException):
            logger.warning('Invalid wechat message signature.')
            return HttpResponseBadRequest()
        msg = parse_message(decrypted_xml)
        if msg.type == 'text':
            reply = process_text(msg)
            if reply is None:
                return HttpResponse(EmptyReply().render())
            xml = reply.render()
            encrypted_xml = crypto.encrypt_message(xml, nonce, timestamp)
            return HttpResponse(encrypted_xml)
        elif msg.type == 'event':
            if msg.event == 'subscribe':
                subscribe(msg)
            elif msg.event == 'unsubscribe':
                unsubscribe(msg)
            else:
                pass
        else:
            pass
        return HttpResponse(EmptyReply().render())
    return HttpResponseBadRequest()


def subscribe(msg):
    with transaction.atomic():
        if User.objects.filter(username=msg.source).exists():
            user = User.objects.get(username=msg.source)
        else:
            user = User.objects.create_user(username=msg.source)
            user.groups.set([Group.objects.get(name='wechat')])
            user.save()
        WechatUser.objects.create(user=user, openid=msg.source, subscribe_time=msg.create_time)


def unsubscribe(msg):
    WechatUser.objects.filter(openid=msg.source).delete()


def process_text(msg):
    user = WechatUser.objects.get(openid=msg.source)
    with transaction.atomic():
        message = Message.objects.create(id=msg.id, user=user, time=msg.create_time, type='text')
        TextMessage.objects.create(message=message, content=msg.content)
    if msg.content == '@help':
        return TextReply(content='\n'.join(state_functions.keys()), message=msg)
    else:
        if msg.content in state_functions:
            reply, data = state_functions[msg.content](user, msg, {}, 0)
            if data is not None:
                cache.set(f'wechat/{msg.source}/state', {'name': msg.content, 'step': 1, 'data': data}, timeout=settings.WECHAT_STATE_TIMEOUT)
            return reply
        elif msg.content == '@cancel':
            cache.delete(f'wechat/{msg.source}/state')
            return TextReply(content='Canceled.', message=msg)
        else:
            state = cache.get(f'wechat/{msg.source}/state')
            if state is not None:
                reply, data = state_functions[state['name']](user, msg, state['data'], state['step'])
                if data is not None:
                    cache.set(f'wechat/{msg.source}/state', {'name': state['name'], 'step': state['step'] + 1, 'data': data}, timeout=settings.WECHAT_STATE_TIMEOUT)
                else:
                    cache.delete(f'wechat/{msg.source}/state')
                return reply
    return None


def for_state(state):
    def decorator(func):
        state_functions[state] = func
        return func
    return decorator


@for_state('@bind')
def state_bind(user, msg, data, step):
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
