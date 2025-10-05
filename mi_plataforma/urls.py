# mi_plataforma/urls.py (VERSIÓN FINAL Y LIMPIA)

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/usuarios/', include('usuarios.urls')), # <-- Esta es la única ruta principal de la API
]

# Esto permite a Django servir los archivos subidos (media) en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
