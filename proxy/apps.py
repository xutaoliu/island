from django.apps import AppConfig


class ProxyConfig(AppConfig):
    name = 'proxy'

    def ready(self):
        from proxy import tasks
        tasks.process_proxy.delay()
