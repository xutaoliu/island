from django.db import transaction
from wechatpy.utils import check_signature
from island import settings
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from django.http import HttpResponse, HttpResponseBadRequest
from wechatpy import parse_message
from wechatpy.crypto import WeChatCrypto
from wechatpy.replies import EmptyReply
from django.views.decorators.csrf import csrf_exempt
from wechat.models import WechatUser, Message, TextMessage
import logging
from django.core.cache import cache
from wechat import actions

logger = logging.getLogger('wechat')
crypto = WeChatCrypto(settings.WECHAT_TOKEN, settings.WECHAT_AES_KEY, settings.WECHAT_APPID)


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
        reply = None
        if msg.type == 'text':
            reply = process_text(msg)
        elif msg.type == 'event':
            if msg.event == 'subscribe':
                reply = actions.subscribe(msg)
            elif msg.event == 'unsubscribe':
                reply = actions.unsubscribe(msg)
        if reply is None:
            return HttpResponse(EmptyReply().render())
        else:
            xml = reply.render()
            encrypted_xml = crypto.encrypt_message(xml, nonce, timestamp)
            return HttpResponse(encrypted_xml)
    else:
        return HttpResponseBadRequest()


def process_text(msg):
    user = WechatUser.objects.get(openid=msg.source)
    with transaction.atomic():
        message = Message.objects.create(id=msg.id, user=user, time=msg.create_time, type='text')
        TextMessage.objects.create(message=message, content=msg.content)
    if msg.content in actions.state_functions:
        reply, data = actions.state_functions[msg.content](user, msg, {}, 0)
        if data is not None:
            cache.set(f'wechat/{msg.source}/state', {'name': msg.content, 'step': 1, 'data': data},
                      timeout=settings.WECHAT_STATE_TIMEOUT)
        else:
            cache.delete(f'wechat/{msg.source}/state')
        return reply
    else:
        state = cache.get(f'wechat/{msg.source}/state')
        if state is not None:
            reply, data = actions.state_functions[state['name']](user, msg, state['data'], state['step'])
            if data is not None:
                cache.set(f'wechat/{msg.source}/state',
                          {'name': state['name'], 'step': state['step'] + 1, 'data': data},
                          timeout=settings.WECHAT_STATE_TIMEOUT)
            else:
                cache.delete(f'wechat/{msg.source}/state')
            return reply
        else:
            # other message
            return None
