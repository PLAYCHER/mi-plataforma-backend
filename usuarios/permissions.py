# usuarios/permissions.py (VERSIÓN CORREGIDA)
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permiso personalizado para permitir que solo los dueños de un objeto
    puedan editarlo.
    """
    def has_object_permission(self, request, view, obj):
        # Los permisos de lectura (GET, HEAD, OPTIONS) se permiten a cualquiera.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Comprobamos si el objeto tiene un atributo 'usuario_oferente' (para Servicios)
        # o un atributo 'empresa' (para Vacantes) y lo comparamos con el usuario
        # que hace la solicitud.
        
        # hasattr(obj, '...') comprueba si el atributo existe antes de intentar acceder a él.
        if hasattr(obj, 'usuario_oferente'):
            return obj.usuario_oferente == request.user
        if hasattr(obj, 'empresa'):
            return obj.empresa == request.user
            
        return False