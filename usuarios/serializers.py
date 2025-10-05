# usuarios/serializers.py (VERSIÓN FINAL CON RESEÑAS DE OFERENTE Y VALIDACIÓN DE CONTACTO)

from rest_framework import serializers
from django.contrib.auth import password_validation
from .models import (
    Usuario, ServicioOfrecido, VacanteEmpresa, Postulacion, Reseña,
    Conversacion, Mensaje, ImagenServicio
)

# --- SERIALIZERS PARA USUARIO Y AUTENTICACIÓN ---
# ... (Sin cambios aquí) ...
class UsuarioSerializer(serializers.ModelSerializer):
    """ Muestra la información pública de un usuario. """
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'region', 'tipo_usuario', 'cv']

class RegistroSerializer(serializers.ModelSerializer):
    """ Maneja el registro de nuevos usuarios. """
    password = serializers.CharField(write_only=True, required=True, validators=[password_validation.validate_password])
    password2 = serializers.CharField(write_only=True, required=True, label="Confirmar contraseña")

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name', 'region', 'tipo_usuario']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'region': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})
        return attrs

    def create(self, validated_data):
        usuario = Usuario.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email']
        )
        usuario.set_password(validated_data['password'])
        usuario.first_name = validated_data.get('first_name', '')
        usuario.last_name = validated_data.get('last_name', '')
        usuario.region = validated_data.get('region', '')
        usuario.tipo_usuario = validated_data.get('tipo_usuario', 'profesionista')
        usuario.save()
        return usuario

class PerfilUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'region']

class CVUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['cv']

# --- SERIALIZER PARA RESEÑAS ---
# ... (Sin cambios aquí) ...
class ReseñaSerializer(serializers.ModelSerializer):
    evaluador_username = serializers.ReadOnlyField(source='evaluador.username')
    evaluado = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(),
        write_only=True
    )
    class Meta:
        model = Reseña
        fields = [
            'id', 'evaluador_username', 'evaluado', 'comentario', 'fecha_creacion',
            'calidad_tecnica', 'solucion_problemas','cumplimiento_estandares',
            'eficiencia_tareas','atencion','manejo_instrucciones',
            'puntualidad_trabajador', 'responsabilidad','comunicacion_proactiva',
            'claridad_requerimientos', 'recursos_proporcionados', 'Soporte_tecnicoMaterial',
            'puntualidad_pago', 'inclusividad', 'transparencia_contractual', 'respeto_horarios',
            'ambiente_laboral', 'comunicacion', 'balance_vida_trabajo'
        ]

# --- SERIALIZER PARA IMÁGENES DE SERVICIO ---
# ... (Sin cambios aquí) ...
class ImagenServicioSerializer(serializers.ModelSerializer):
    imagen_url = serializers.SerializerMethodField()
    class Meta:
        model = ImagenServicio
        fields = ['id', 'imagen', 'imagen_url']
        extra_kwargs = {'imagen': {'write_only': True}}

    def get_imagen_url(self, obj):
        request = self.context.get('request')
        if request and obj.imagen and hasattr(obj.imagen, 'url'):
            return request.build_absolute_uri(obj.imagen.url)
        return None

# --- SERIALIZER PARA SERVICIOS (CORRECCIÓN APLICADA) ---
class ServicioOfrecidoSerializer(serializers.ModelSerializer):
    usuario_oferente = serializers.ReadOnlyField(source='usuario_oferente.username')
    usuario_oferente_id = serializers.ReadOnlyField(source='usuario_oferente.id')
    usuario_ha_contactado = serializers.SerializerMethodField()
    reseñas_oferente = serializers.SerializerMethodField()
    promedio_calificacion_oferente = serializers.SerializerMethodField()
    imagenes = ImagenServicioSerializer(many=True, read_only=True)
    
    # --- 1. AÑADIMOS EL CAMPO FALTANTE ---
    usuario_ha_contactado = serializers.SerializerMethodField()

    class Meta:
        model = ServicioOfrecido
        fields = [
            'id', 'usuario_oferente_id', 'usuario_oferente', 
            'titulo_servicio', 'descripcion_servicio', 'imagenes', 
            'fecha_publicacion', 'activo', 'reseñas_oferente', 
            'promedio_calificacion_oferente',
            'usuario_ha_contactado' # <-- 2. AÑADIMOS EL CAMPO A LA LISTA
        ]

    def get_reseñas_oferente(self, obj):
        # ... (Esta función no cambia)
        reseñas = Reseña.objects.filter(evaluado=obj.usuario_oferente).order_by('-fecha_creacion')
        return ReseñaSerializer(reseñas[:5], many=True, context=self.context).data

    def get_promedio_calificacion_oferente(self, obj):
        # ... (Esta función no cambia)
        reseñas = Reseña.objects.filter(evaluado=obj.usuario_oferente)
        if not reseñas.exists(): return None
        total_sum, count = 0, 0
        campos_oferente = [
            'eficiencia_tareas', 'atencion', 'manejo_instrucciones',
            'puntualidad_trabajador', 'responsabilidad', 'comunicacion_proactiva'
        ]
        for reseña in reseñas:
            for campo in campos_oferente:
                valor = getattr(reseña, campo)
                if valor is not None:
                    total_sum += valor
                    count += 1
        return round(total_sum / count, 1) if count > 0 else None

    # --- 3. AÑADIMOS LA FUNCIÓN FALTANTE ---
    def get_usuario_ha_contactado(self, obj):
        """
        Verifica si el usuario que hace la petición ya ha iniciado una conversación
        con el oferente del servicio.
        """
        request = self.context.get('request')
        # Si no hay un usuario logueado, no puede haber contactado.
        if not request or not request.user.is_authenticated:
            return False
        
        # Verificamos si existe una conversación entre el usuario actual y el oferente.
        return Conversacion.objects.filter(
            participantes=request.user,
            servicio_relacionado=obj
        ).exists()
# --- EL RESTO DE SERIALIZERS NO CAMBIA ---
# ... (PostulacionSerializer, VacanteEmpresaSerializer, etc.) ...
class PostulacionSerializer(serializers.ModelSerializer):
    profesional_username = serializers.ReadOnlyField(source='profesional.username')
    class Meta:
        model = Postulacion
        fields = ['id', 'profesional_username', 'fecha_postulacion']

class PostulacionDetalleSerializer(serializers.ModelSerializer):
    profesional_nombre = serializers.ReadOnlyField(source='profesional.get_full_name')
    profesional_email = serializers.ReadOnlyField(source='profesional.email')
    profesional_cv = serializers.SerializerMethodField()
    profesional_id = serializers.ReadOnlyField(source='profesional.id')
    class Meta:
        model = Postulacion
        fields = ['id', 'profesional_id', 'profesional_nombre', 'profesional_email', 'fecha_postulacion', 'profesional_cv', 'estado']

    def get_profesional_cv(self, obj):
        request = self.context.get('request')
        if request and obj.profesional.cv and hasattr(obj.profesional.cv, 'url'):
            return request.build_absolute_uri(obj.profesional.cv.url)
        return None

class MisPostulacionesSerializer(serializers.ModelSerializer):
    vacante = serializers.SerializerMethodField()
    estado = serializers.CharField(read_only=True)
    class Meta:
        model = Postulacion
        fields = ['id', 'vacante', 'fecha_postulacion', 'estado']
    
    def get_vacante(self, obj):
        return {
            "id": obj.vacante.id,
            "titulo_vacante": obj.vacante.titulo_vacante,
            "empresa_username": obj.vacante.empresa.username,
            "empresa_id": obj.vacante.empresa.id,
        }

class VacanteEmpresaSerializer(serializers.ModelSerializer):
    empresa_username = serializers.ReadOnlyField(source='empresa.username')
    empresa_id = serializers.ReadOnlyField(source='empresa.id')
    reseñas_empresa = serializers.SerializerMethodField()
    promedio_calificacion_empresa = serializers.SerializerMethodField()

    class Meta:
        model = VacanteEmpresa
        fields = [
            'id', 'empresa_id', 'empresa_username', 'titulo_vacante', 'descripcion_puesto',
            'requisitos', 'tipo_contrato', 'ubicacion', 'salario_ofrecido',
            'fecha_publicacion', 'activa',
            'reseñas_empresa', 'promedio_calificacion_empresa'
        ]

    def get_reseñas_empresa(self, obj):
        reseñas = Reseña.objects.filter(evaluado=obj.empresa).order_by('-fecha_creacion')
        return ReseñaSerializer(reseñas[:5], many=True, context=self.context).data

    def get_promedio_calificacion_empresa(self, obj):
        reseñas = Reseña.objects.filter(evaluado=obj.empresa)
        if not reseñas.exists(): return None
        total_sum, count = 0, 0
        campos_empresa = [
            'claridad_requerimientos', 'recursos_proporcionados', 'Soporte_tecnicoMaterial',
            'puntualidad_pago', 'inclusividad', 'transparencia_contractual', 'respeto_horarios',
            'ambiente_laboral', 'comunicacion', 'balance_vida_trabajo'
        ]
        for reseña in reseñas:
            for campo in campos_empresa:
                valor = getattr(reseña, campo)
                if valor is not None:
                    total_sum += valor
                    count += 1
        return round(total_sum / count, 1) if count > 0 else None

class VacanteConPostulantesSerializer(VacanteEmpresaSerializer):
    postulantes = PostulacionDetalleSerializer(many=True, read_only=True)
    class Meta(VacanteEmpresaSerializer.Meta):
        fields = VacanteEmpresaSerializer.Meta.fields + ['postulantes']

class PerfilPublicoSerializer(serializers.ModelSerializer):
    servicios_ofrecidos = serializers.SerializerMethodField()
    vacantes_publicadas = serializers.SerializerMethodField()
    reseñas_recibidas = ReseñaSerializer(many=True, read_only=True)
    promedio_calificacion = serializers.SerializerMethodField()
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'first_name', 'last_name', 'region', 
            'tipo_usuario', 'servicios_ofrecidos', 'vacantes_publicadas',
            'reseñas_recibidas', 'promedio_calificacion'
        ]

    def get_servicios_ofrecidos(self, obj):
        servicios_activos = ServicioOfrecido.objects.filter(usuario_oferente=obj, activo=True)
        return ServicioOfrecidoSerializer(servicios_activos, many=True, context=self.context).data

    def get_vacantes_publicadas(self, obj):
        vacantes_activas = VacanteEmpresa.objects.filter(empresa=obj, activa=True)
        return VacanteEmpresaSerializer(vacantes_activas, many=True, context=self.context).data
    
    def get_promedio_calificacion(self, obj):
        reseñas = obj.reseñas_recibidas.all()
        if not reseñas.exists(): return None
        total_sum, count = 0, 0
        if obj.tipo_usuario == 'empresa':
            campos = [
                'claridad_requerimientos', 'recursos_proporcionados', 'Soporte_tecnicoMaterial',
                'puntualidad_pago', 'inclusividad', 'transparencia_contractual', 'respeto_horarios',
                'ambiente_laboral', 'comunicacion', 'balance_vida_trabajo'
            ]
        else:
            campos = [
                'calidad_tecnica', 'solucion_problemas', 'cumplimiento_estandares',
                'eficiencia_tareas', 'atencion', 'manejo_instrucciones',
                'puntualidad_trabajador', 'responsabilidad', 'comunicacion_proactiva'
            ]
        for reseña in reseñas:
            for campo in campos:
                valor = getattr(reseña, campo)
                if valor is not None:
                    total_sum += valor
                    count += 1
        return round(total_sum / count, 1) if count > 0 else None

# --- SERIALIZERS PARA MENSAJERÍA ---
class MensajeSerializer(serializers.ModelSerializer):
    autor_username = serializers.ReadOnlyField(source='autor.username')
    class Meta:
        model = Mensaje
        fields = ['id', 'autor', 'autor_username', 'contenido', 'fecha_envio', 'leido']
        read_only_fields = ['autor']

class ConversacionSerializer(serializers.ModelSerializer):
    otro_participante = serializers.SerializerMethodField()
    ultimo_mensaje = serializers.SerializerMethodField()
    nombre_servicio_relacionado = serializers.SerializerMethodField()
    servicio_id_relacionado = serializers.SerializerMethodField()

    class Meta:
        model = Conversacion
        fields = ['id', 'otro_participante', 'ultimo_mensaje', 'fecha_modificacion',
        'nombre_servicio_relacionado', 'servicio_id_relacionado']
    
    def get_servicio_id_relacionado(self, obj):
        """Devuelve el ID del servicio si la conversación está ligada a uno."""
        if obj.servicio_relacionado:
            return obj.servicio_relacionado.id
        return None

    def get_nombre_servicio_relacionado(self, obj):
        """Devuelve el título del servicio si la conversación está ligada a uno."""
        if obj.servicio_relacionado:
            return obj.servicio_relacionado.titulo_servicio
        return None
    def get_otro_participante(self, obj):
        usuario_actual = self.context['request'].user
        otro = obj.participantes.exclude(id=usuario_actual.id).first()
        if otro:
            return {'id': otro.id, 'username': otro.username}
        return None

    def get_ultimo_mensaje(self, obj):
        ultimo = obj.mensajes.last()
        if ultimo:
            return {'contenido': ultimo.contenido[:50], 'fecha_envio': ultimo.fecha_envio}
        return None
