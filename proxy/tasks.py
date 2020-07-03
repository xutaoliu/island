from celery import shared_task
from proxy.models import Proxy
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import requests
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
                Proxy.objects.get_or_create(ip=item['ip'], port=item['port'], protocol=item['protocol'],
                                            anonymity=item['anonymity'], site=item['site'], location=item['location'],
                                            delay=result.elapsed.total_seconds())
                schedule, created = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.MINUTES)
                PeriodicTask.objects.get_or_create(name=f'proxy-{item["ip"]}:{item["port"]}',
                                                   defaults={
                                                       'interval': schedule,
                                                       'task': 'proxy.tasks.check_proxy',
                                                       'kwargs': json.dumps({'ip': item['ip'], 'port': item['port']})})
        except requests.exceptions.RequestException:
            pass
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=2)
    channel.basic_consume(queue='proxy', on_message_callback=item_scraped)
    channel.start_consuming()


@shared_task
def check_proxy(ip, port):
    try:
        proxy = Proxy.objects.get(ip=ip, port=port)
    except Proxy.DoesNotExist:
        PeriodicTask.objects.filter(name=f'proxy-{ip}:{port}').delete()
    else:
        try:
            result = requests.get(settings.PROXY_CHECK_URL, proxies={
                'http': f'{proxy.protocol}://{proxy.ip}:{proxy.port}',
                'https': f'{proxy.protocol}://{proxy.ip}:{proxy.port}'
            }, timeout=5)
            if result.status_code == 200:
                proxy.delay = result.elapsed.total_seconds()
                proxy.save()
            else:
                raise requests.exceptions.RequestException(response=result)
        except requests.exceptions.RequestException:
            proxy.delay = -1
            proxy.save()
            PeriodicTask.objects.filter(name=f'proxy-{ip}:{port}').delete()
