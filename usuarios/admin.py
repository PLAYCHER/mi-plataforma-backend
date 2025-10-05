from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario # Importa tu modelo Usuario personalizado
from rest_framework.authtoken.models import Token # Importa el modelo Token

# Si quieres usar la configuración por defecto del admin para usuarios,
# pero con tu modelo personalizado, puedes hacer algo simple como:
# admin.site.register(Usuario, UserAdmin)

# O, si quieres personalizar más cómo se muestra el Usuario en el admin:
class CustomUserAdmin(UserAdmin):
    # Aquí puedes añadir personalizaciones si lo deseas en el futuro
    # Por ejemplo, para mostrar tus campos personalizados en la lista de usuarios:
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'tipo_usuario')
    # Para añadir campos al formulario de creación/edición:
    # fieldsets = UserAdmin.fieldsets + (
    #     (None, {'fields': ('fecha_nacimiento', 'region', 'tipo_usuario')}),
    # )
    # add_fieldsets = UserAdmin.add_fieldsets + (
    #     (None, {'fields': ('fecha_nacimiento', 'region', 'tipo_usuario', 'email', 'first_name', 'last_name')}),
    # )
    pass

admin.site.register(Usuario, CustomUserAdmin) # Registra tu modelo Usuario con la clase admin personalizada (o UserAdmin directamente)

# También es útil poder ver los tokens en el admin (opcional pero recomendado)
# Puedes crear una clase admin simple para Token o registrarlo directamente
class TokenAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'created')
    readonly_fields = ('key', 'user', 'created') # Generalmente no querrás editar tokens directamente

admin.site.register(Token, TokenAdmin)