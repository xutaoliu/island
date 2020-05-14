from django.db import transaction
from wechatpy.utils import check_signature
from island import settings
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from django.http import HttpResponse, HttpResponseBadRequest, Http404
from wechatpy import parse_message
from wechatpy.crypto import WeChatCrypto
from wechatpy.crypto.cryptography import WeChatCipher
from wechatpy.crypto.pkcs7 import PKCS7Encoder
from wechatpy.utils import to_text
from wechatpy.replies import EmptyReply
from django.views.decorators.csrf import csrf_exempt
from wechat.models import WechatUser, Message, TextMessage
from twitter_image.models import ImageData
import logging
import base64
from django.core.cache import cache
from django.shortcuts import render, reverse
from wechat import actions

logger = logging.getLogger('wechat')
crypto = WeChatCrypto(settings.WECHAT_TOKEN, settings.WECHAT_AES_KEY, settings.WECHAT_APPID)
imgs_cipher = WeChatCipher(crypto.key)


def serve_imgs(request, imgs):
    if request.method == 'GET':
        try:
            plain_imgs = imgs_cipher.decrypt(base64.b64decode(imgs))
            content = to_text(PKCS7Encoder.decode(plain_imgs))
            token = content[:len(settings.WECHAT_TOKEN)]
            if token != settings.WECHAT_TOKEN:
                raise Exception('Invalid token.')
            img_ids = list(map(int, content[len(settings.WECHAT_TOKEN):].split(',')))
        except:
            return HttpResponseBadRequest()
        paths = ImageData.objects.filter(id__in=img_ids).values_list('image', flat=True)
        if paths.exists():
            urls = [reverse('media', kwargs={'path': path}) for path in paths]
            return render(request, 'imgs.html', {'imgs': urls})
        else:
            return Http404()
    else:
        return HttpResponseBadRequest()


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
            reply = process_text(request, msg)
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


def process_text(request, msg):
    user = WechatUser.objects.get(openid=msg.source)
    with transaction.atomic():
        message = Message.objects.create(id=msg.id, user=user, time=msg.create_time, type='text')
        TextMessage.objects.create(message=message, content=msg.content)
    if msg.content in actions.state_functions:
        reply, data = actions.state_functions[msg.content](request, user, msg, {}, 0)
        if data is not None:
            cache.set(f'wechat/{msg.source}/state', {'name': msg.content, 'step': 1, 'data': data},
                      timeout=settings.WECHAT_STATE_TIMEOUT)
        else:
            cache.delete(f'wechat/{msg.source}/state')
        return reply
    else:
        state = cache.get(f'wechat/{msg.source}/state')
        if state is not None:
            reply, data = actions.state_functions[state['name']](request, user, msg, state['data'], state['step'])
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
