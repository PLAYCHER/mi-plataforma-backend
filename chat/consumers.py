# chat/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from usuarios.models import Mensaje, Conversacion, Usuario
from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs
# --- Funciones asíncronas para interactuar con la base de datos ---
# Es una buena práctica separar la lógica de la base de datos del consumer.

@sync_to_async
def get_user_from_token(token_key):
    """Obtiene un usuario a partir de un token de autenticación."""
    try:
        token = Token.objects.select_related('user').get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return AnonymousUser()

@sync_to_async
def user_is_participant(user, conversacion_id):
    """Verifica si un usuario es participante de una conversación."""
    if user.is_anonymous:
        return False
    try:
        conversacion = Conversacion.objects.get(id=conversacion_id)
        return conversacion.participantes.filter(id=user.id).exists()
    except Conversacion.DoesNotExist:
        return False

@sync_to_async
def save_message(user, conversacion_id, content):
    """Guarda un nuevo mensaje en la base de datos."""
    conversacion = Conversacion.objects.get(id=conversacion_id)
    mensaje = Mensaje.objects.create(
        conversacion=conversacion,
        autor=user,
        contenido=content
    )
    # Devolvemos un diccionario simple y serializable para enviarlo como JSON
    return {
        'id': mensaje.id,
        'autor': mensaje.autor.id,
        'autor_username': mensaje.autor.username,
        'contenido': mensaje.contenido,
        'fecha_envio': mensaje.fecha_envio.isoformat(),
    }

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversacion_id = self.scope['url_route']['kwargs']['conversacion_id']
        self.room_group_name = f'chat_{self.conversacion_id}'

        # Extraer token de los query parameters de la URL
        query_string = self.scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token_key = query_params.get('token', [None])[0]

        if not token_key:
            await self.close()
            return

        # Autenticar al usuario
        self.user = await get_user_from_token(token_key)
        is_participant = await user_is_participant(self.user, self.conversacion_id)

        if self.user.is_anonymous or not is_participant:
            await self.close()
            return

        # Si todo es válido, unirse al grupo y aceptar la conexión
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_content = text_data_json['message']

            # Guardar el nuevo mensaje (el usuario ya está autenticado)
            new_message = await save_message(self.user, self.conversacion_id, message_content)

            # Enviar el mensaje al grupo de la sala
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': new_message
                }
            )
        except Exception as e:
            print(f"Error en el consumer al recibir mensaje: {e}")

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))
