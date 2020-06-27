from celery import shared_task
from proxy.models import Proxy
import requests
from django.db import IntegrityError
import json
from island import settings
import logging
import pika

logger = logging.getLogger('proxy')


@shared_task
def process_proxy():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', virtual_host='crawler',
                                                                   credentials=pika.PlainCredentials(
                                                                       settings.RABBITMQ_USER,
                                                                       settings.RABBITMQ_PASS)))
    channel = connection.channel()
    channel.queue_declare(queue='proxy', durable=True, arguments={'x-max-length': 1000})

    def item_scraped(ch, method, properties, body):
        item = json.loads(body)['payload']
        try:
            result = requests.get(settings.PROXY_CHECK_URL, proxies={
                'http': f'{item["protocol"]}://{item["ip"]}:{item["port"]}',
                'https': f'{item["protocol"]}://{item["ip"]}:{item["port"]}'
            }, timeout=5)
            if result.status_code == 200:
                Proxy.objects.create(ip=item['ip'], port=item['port'], protocol=item['protocol'], anonymity=item['anonymity'], site=item['site'], location=item['location'], delay=result.elapsed.total_seconds())
        except (requests.exceptions.RequestException, IntegrityError):
            pass
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=2)
    channel.basic_consume(queue='proxy', on_message_callback=item_scraped)
    channel.start_consuming()
