# usuarios/views.py (VERSIÓN FINAL, COMPLETA Y CORREGIDA)

# --- Imports ---
from django.contrib.auth import authenticate
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework import filters
from django.db.models import Q
from .permissions import IsOwnerOrReadOnly
from .models import Usuario, ServicioOfrecido, VacanteEmpresa, Postulacion,Reseña
from .serializers import (
    UsuarioSerializer, RegistroSerializer, ServicioOfrecidoSerializer,
    VacanteEmpresaSerializer, PostulacionSerializer, VacanteConPostulantesSerializer,
    CVUploadSerializer, PerfilUpdateSerializer, MisPostulacionesSerializer,PostulacionDetalleSerializer,
    PerfilPublicoSerializer,ReseñaSerializer,Postulacion,ConversacionSerializer,MensajeSerializer,
    Conversacion,ImagenServicio,Mensaje,
)

# --- Vistas de Autenticación y Perfil ---

class RegistroAPIView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]

class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        usuario = authenticate(username=username, password=password)
        if usuario:
            token, created = Token.objects.get_or_create(user=usuario)
            usuario_serializer = UsuarioSerializer(usuario, context={'request': request})
            return Response({
                "token": token.key,
                "usuario": usuario_serializer.data
            }, status=status.HTTP_200_OK)
        return Response({"error": "Credenciales inválidas"}, status=status.HTTP_400_BAD_REQUEST)

class PerfilUsuarioAPIView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PerfilUpdateSerializer
        return UsuarioSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        read_serializer = UsuarioSerializer(instance, context={'request': request})
        return Response(read_serializer.data)

class CVUploadAPIView(generics.UpdateAPIView):
    serializer_class = CVUploadSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_object(self):
        return self.request.user

    # --- ¡AQUÍ ESTÁ LA LÓGICA QUE FALTABA! ---
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Después de subir el CV, devolvemos el perfil completo del usuario
        read_serializer = UsuarioSerializer(instance, context={'request': request})
        return Response(read_serializer.data)

# --- Vistas para Servicios Ofrecidos ---
class ServicioListCreateAPIView(generics.ListCreateAPIView):
    queryset = ServicioOfrecido.objects.filter(activo=True).order_by('-fecha_publicacion')
    serializer_class = ServicioOfrecidoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['titulo_servicio', 'descripcion_servicio', 'usuario_oferente__username']
    parser_classes = (MultiPartParser, FormParser)

    def perform_create(self, serializer):
        servicio = serializer.save(usuario_oferente=self.request.user)
        
        # Luego, obtenemos la lista de archivos de imagen de la petición
        imagenes = self.request.FILES.getlist('imagenes')
        
        # Iteramos sobre cada archivo y creamos un objeto ImagenServicio asociado
        for imagen in imagenes:
            ImagenServicio.objects.create(servicio=servicio, imagen=imagen)

class ImagenServicioDeleteAPIView(generics.DestroyAPIView):
    """
    Vista para eliminar una imagen específica de un servicio.
    """
    queryset = ImagenServicio.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Asegurarnos de que el usuario que borra la imagen es el dueño del servicio
        obj = super().get_object()
        if obj.servicio.usuario_oferente != self.request.user:
            raise permissions.PermissionDenied("No tienes permiso para borrar esta imagen.")
        return obj
    
class ServicioDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ServicioOfrecido.objects.all()
    serializer_class = ServicioOfrecidoSerializer
    permission_classes = [IsOwnerOrReadOnly]
    parser_classes = (MultiPartParser, FormParser)

    # --- ¡CORRECCIÓN APLICADA AQUÍ! ---
    # Sobrescribimos el método 'retrieve' para pasar el contexto explícitamente.
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Creamos el serializer y le pasamos el 'request' en el contexto.
        serializer = self.get_serializer(instance, context={'request': request})
        return Response(serializer.data)

    def perform_update(self, serializer):
        servicio = serializer.save()
        imagenes = self.request.FILES.getlist('imagenes')
        for imagen in imagenes:
            ImagenServicio.objects.create(servicio=servicio, imagen=imagen)

class ServicioToggleActiveAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    def post(self, request, pk=None):
        try:
            servicio = ServicioOfrecido.objects.get(pk=pk)
        except ServicioOfrecido.DoesNotExist:
            return Response({'error': 'El servicio no existe.'}, status=status.HTTP_404_NOT_FOUND)
        if servicio.usuario_oferente != request.user:
            return Response({'error': 'No tienes permiso para modificar este servicio.'}, status=status.HTTP_403_FORBIDDEN)
        servicio.activo = not servicio.activo
        servicio.save()
        serializer = ServicioOfrecidoSerializer(servicio, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class MisServiciosAPIView(generics.ListAPIView):
    serializer_class = ServicioOfrecidoSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return ServicioOfrecido.objects.filter(usuario_oferente=self.request.user).order_by('-fecha_publicacion')

# --- Vistas para Vacantes ---

class VacanteListCreateAPIView(generics.ListCreateAPIView):
    queryset = VacanteEmpresa.objects.filter(activa=True).order_by('-fecha_publicacion')
    serializer_class = VacanteEmpresaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['titulo_vacante', 'descripcion_puesto', 'ubicacion', 'empresa__username']

    def perform_create(self, serializer):
        if self.request.user.tipo_usuario != 'empresa':
            raise permissions.PermissionDenied("Solo las empresas pueden publicar vacantes.")
        serializer.save(empresa=self.request.user)

class VacanteToggleActiveAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    def post(self, request, pk=None):
        try:
            vacante = VacanteEmpresa.objects.get(pk=pk)
        except VacanteEmpresa.DoesNotExist:
            return Response({'error': 'La vacante no existe.'}, status=status.HTTP_404_NOT_FOUND)
        if vacante.empresa != request.user:
            return Response({'error': 'No tienes permiso para modificar esta vacante.'}, status=status.HTTP_403_FORBIDDEN)
        vacante.activa = not vacante.activa
        vacante.save()
        serializer = VacanteEmpresaSerializer(vacante)
        return Response(serializer.data, status=status.HTTP_200_OK)

class VacanteDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = VacanteEmpresa.objects.all()
    serializer_class = VacanteConPostulantesSerializer
    permission_classes = [IsOwnerOrReadOnly]

# --- Vistas para Postulaciones ---

class PostulacionCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    def post(self, request, pk=None):
        try:
            vacante = VacanteEmpresa.objects.get(pk=pk, activa=True)
        except VacanteEmpresa.DoesNotExist:
            return Response({'error': 'La vacante no existe o ya no está activa.'}, status=status.HTTP_404_NOT_FOUND)
        profesional = request.user
        if profesional.tipo_usuario != 'profesionista':
            return Response({'error': 'Solo los profesionales pueden postularse.'}, status=status.HTTP_403_FORBIDDEN)
        if Postulacion.objects.filter(vacante=vacante, profesional=profesional).exists():
            return Response({'error': 'Ya te has postulado a esta vacante.'}, status=status.HTTP_400_BAD_REQUEST)
        Postulacion.objects.create(vacante=vacante, profesional=profesional)
        return Response({'status': '¡Postulación exitosa!'}, status=status.HTTP_201_CREATED)

class PostulacionUpdateStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    def patch(self, request, pk=None):
        try:
            postulacion = Postulacion.objects.get(pk=pk)
        except Postulacion.DoesNotExist:
            return Response({'error': 'La postulación no existe.'}, status=status.HTTP_404_NOT_FOUND)
        if postulacion.vacante.empresa != request.user:
            return Response({'error': 'No tienes permiso para modificar esta postulación.'}, status=status.HTTP_403_FORBIDDEN)
        nuevo_estado = request.data.get('estado')
        if not nuevo_estado:
            return Response({'error': 'El campo "estado" es requerido.'}, status=status.HTTP_400_BAD_REQUEST)
        postulacion.estado = nuevo_estado
        postulacion.save()
        serializer = PostulacionDetalleSerializer(postulacion, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

# --- Vistas de Dashboards ---

class MisVacantesAPIView(generics.ListAPIView):
    serializer_class = VacanteEmpresaSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return VacanteEmpresa.objects.filter(empresa=self.request.user).order_by('-fecha_publicacion')

class MisPostulacionesAPIView(generics.ListAPIView):
    """
    Devuelve una lista de las postulaciones hechas por el
    usuario (profesional) autenticado.
    """
    serializer_class = MisPostulacionesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # --- ¡ESTA ES LA CORRECCIÓN! ---
        # Cambiamos 'fecha_publicacion' a 'fecha_postulacion'
        return Postulacion.objects.filter(profesional=self.request.user).order_by('-fecha_postulacion')
        # --------------------------------

class PerfilPublicoAPIView(generics.RetrieveAPIView):
    """
    Vista para obtener el perfil público de cualquier usuario por su username.
    """
    queryset = Usuario.objects.all()
    serializer_class = PerfilPublicoSerializer
    permission_classes = [permissions.AllowAny] # Cualquiera puede ver un perfil público
    lookup_field = 'username' # Le decimos a Django que busque por username en lugar de ID

class ReseñaCreateAPIView(generics.CreateAPIView):
    """
    Vista para que un usuario autenticado cree una reseña para otro usuario.
    """
    queryset = Reseña.objects.all()
    serializer_class = ReseñaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        evaluador = self.request.user
        evaluado = serializer.validated_data['evaluado']

        # --- ¡VALIDACIÓN CLAVE! ---
        # Verificamos si existe una conversación entre el evaluador y el evaluado.
        ha_contactado = Conversacion.objects.filter(
            participantes=evaluador
        ).filter(
            participantes=evaluado
        ).exists()

        if not ha_contactado:
            # Si no existe una conversación, denegamos el permiso.
            raise permissions.PermissionDenied("Solo puedes dejar una reseña a usuarios con los que has contactado.")
        
        # Si la validación pasa, guardamos la reseña.
        serializer.save(evaluador=evaluador)

class PostulacionMarcarRevisionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request, pk=None):
        try:
            postulacion = Postulacion.objects.get(pk=pk)
        except Postulacion.DoesNotExist:
            return Response({'error': 'La postulación no existe.'}, status=status.HTTP_404_NOT_FOUND)

        # Verificamos que quien hace la petición es el dueño de la vacante
        if postulacion.vacante.empresa != request.user:
            return Response({'error': 'No tienes permiso para modificar esta postulación.'}, status=status.HTTP_403_FORBIDDEN)

        # IMPORTANTE: Solo cambiamos el estado si actualmente es 'recibida'
        # para no sobrescribir estados más avanzados como 'contactado' o 'rechazado'.
        if postulacion.estado == 'recibida':
            postulacion.estado = 'en_revision'
            postulacion.save()

        serializer = PostulacionDetalleSerializer(postulacion, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ConversacionListAPIView(generics.ListAPIView):
    """ Devuelve la lista de conversaciones del usuario autenticado. """
    serializer_class = ConversacionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Filtra las conversaciones donde el usuario actual es un participante
        return self.request.user.conversaciones.all().order_by('-fecha_modificacion')


class MensajeListCreateAPIView(generics.ListCreateAPIView):
    """ Devuelve los mensajes de una conversación o crea un nuevo mensaje. """
    serializer_class = MensajeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Obtenemos el ID de la conversación desde la URL
        conversacion_id = self.kwargs['conversacion_id']
        # Filtramos los mensajes de esa conversación
        mensajes = Mensaje.objects.filter(conversacion_id=conversacion_id)
        
        # Marcar mensajes como leídos
        # Obtenemos los mensajes que no son del usuario actual y no están leídos
        mensajes_no_leidos = mensajes.filter(leido=False).exclude(autor=self.request.user)
        mensajes_no_leidos.update(leido=True)

        return mensajes

    def perform_create(self, serializer):
        # Asignamos el autor y la conversación automáticamente
        conversacion_id = self.kwargs['conversacion_id']
        conversacion = Conversacion.objects.get(id=conversacion_id)
        serializer.save(autor=self.request.user, conversacion=conversacion)


# usuarios/views.py

class IniciarConversacionAPIView(APIView):
    """
    Encuentra una conversación existente o crea una nueva,
    opcionalmente ligada a un servicio.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        usuario_actual = request.user
        otro_usuario_id = request.data.get('usuario_id')
        servicio_id = request.data.get('servicio_id')

        if not otro_usuario_id:
            return Response({'error': 'Se requiere el ID del usuario.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            otro_usuario = Usuario.objects.get(id=otro_usuario_id)
        except Usuario.DoesNotExist:
            return Response({'error': 'El usuario no existe.'}, status=status.HTTP_404_NOT_FOUND)

        # --- LÓGICA CORREGIDA ---
        if servicio_id:
            # Buscamos encadenando los filtros
            conversacion = Conversacion.objects.filter(
                participantes=usuario_actual
            ).filter(
                participantes=otro_usuario
            ).filter(
                servicio_relacionado_id=servicio_id
            )
        else:
            # Hacemos lo mismo para la búsqueda genérica
            conversacion = Conversacion.objects.filter(
                participantes=usuario_actual
            ).filter(
                participantes=otro_usuario
            ).filter(
                servicio_relacionado__isnull=True
            )
        
        if conversacion.exists():
            conv = conversacion.first()
        else:
            conv = Conversacion.objects.create()
            conv.participantes.add(usuario_actual, otro_usuario)
            
            if servicio_id:
                try:
                    servicio = ServicioOfrecido.objects.get(id=servicio_id)
                    conv.servicio_relacionado = servicio
                    conv.save()
                except ServicioOfrecido.DoesNotExist:
                    pass 

        return Response({'conversacion_id': conv.id}, status=status.HTTP_200_OK)