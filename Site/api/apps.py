from django.apps import AppConfig

class MyapiConfig(AppConfig):
    name = 'api'

    def ready(self):
        import api.signals
