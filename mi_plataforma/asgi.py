# mi_plataforma/asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application

# 1. Establece la variable de entorno de los settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mi_plataforma.settings')

# 2. Llama a django.setup() para cargar la configuración de Django
django.setup()

# 3. Ahora que Django está configurado, podemos importar de forma segura
import chat.routing

# 4. Define la aplicación ASGI
application = ProtocolTypeRouter({
    # El tráfico HTTP normal va a la aplicación ASGI de Django
    "http": get_asgi_application(),

    # El tráfico WebSocket va al enrutador de Channels
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})