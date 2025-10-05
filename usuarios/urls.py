# usuarios/urls.py (VERSIÓN CORREGIDA Y LIMPIA)
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import (
    RegistroAPIView,LoginAPIView,
    PerfilUsuarioAPIView,ServicioListCreateAPIView,
    ServicioDetailAPIView,VacanteListCreateAPIView,
    VacanteDetailAPIView,PostulacionCreateAPIView,
    MisVacantesAPIView,CVUploadAPIView,
    MisPostulacionesAPIView,MisServiciosAPIView,
    ServicioToggleActiveAPIView,VacanteToggleActiveAPIView,
    PostulacionUpdateStatusAPIView, PerfilPublicoAPIView,
    ReseñaCreateAPIView,PostulacionMarcarRevisionAPIView,
    ConversacionListAPIView,MensajeListCreateAPIView,
    IniciarConversacionAPIView,ImagenServicioDeleteAPIView,
)

urlpatterns = [
    # Rutas de Autenticación y Perfil
    path('registro/', RegistroAPIView.as_view(), name='api_registro'),
    path('login/', LoginAPIView.as_view(), name='api_login'),
    path('perfil/', PerfilUsuarioAPIView.as_view(), name='api_perfil_usuario'),
    path('perfil/subir-cv/', CVUploadAPIView.as_view(), name='api_subir_cv'),
    path('perfil-publico/<str:username>/', PerfilPublicoAPIView.as_view(), name='api_perfil_publico'),
    path('reseñas/crear/', ReseñaCreateAPIView.as_view(), name='api_reseña_crear'),
    
    # Rutas para Servicios Ofrecidos
    path('servicios/', ServicioListCreateAPIView.as_view(), name='api_servicios_lista'),
    path('servicios/<int:pk>/', ServicioDetailAPIView.as_view(), name='api_servicio_detalle'),
    path('mis-servicios/', MisServiciosAPIView.as_view(), name='api_mis_servicios'),
    path('servicios/<int:pk>/toggle-active/', ServicioToggleActiveAPIView.as_view(), name='api_servicio_toggle_active'),
    path('servicios/imagenes/<int:pk>/', ImagenServicioDeleteAPIView.as_view(), name='api_imagen_servicio_delete'),
    
    # Rutas para Vacantes y Postulaciones
    path('vacantes/', VacanteListCreateAPIView.as_view(), name='api_vacantes_lista'),
    path('vacantes/<int:pk>/', VacanteDetailAPIView.as_view(), name='api_vacante_detalle'), # <-- Nombre corregido
    path('vacantes/<int:pk>/postularse/', PostulacionCreateAPIView.as_view(), name='api_vacante_postularse'),
    path('mis-vacantes/', MisVacantesAPIView.as_view(), name='api_mis_vacantes'),
    path('mis-postulaciones/', MisPostulacionesAPIView.as_view(), name='api_mis_postulaciones'),
    path('vacantes/<int:pk>/toggle-active/', VacanteToggleActiveAPIView.as_view(), name='api_vacante_toggle_active'),
    path('postulaciones/<int:pk>/actualizar-estado/', PostulacionUpdateStatusAPIView.as_view(), name='api_postulacion_update_status'),
    path('postulaciones/<int:pk>/marcar-revision/', PostulacionMarcarRevisionAPIView.as_view(), name='api_postulacion_marcar_revision'),

    # --- Rutas para Mensajería ---
    path('conversaciones/', ConversacionListAPIView.as_view(), name='api_conversaciones_lista'),
    path('conversaciones/<int:conversacion_id>/mensajes/', MensajeListCreateAPIView.as_view(), name='api_mensajes_lista_crea'),
    path('conversaciones/iniciar/', IniciarConversacionAPIView.as_view(), name='api_iniciar_conversacion'),

]

