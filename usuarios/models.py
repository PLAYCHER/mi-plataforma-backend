from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    # Campos que ya vienen con AbstractUser:
    # username, first_name, last_name, email, password, groups, user_permissions,
    # is_staff, is_active, is_superuser, last_login, date_joined
    cv = models.FileField(upload_to='cvs/', null=True, blank=True)
    TIPO_USUARIO_CHOICES = [
        ('oferente', 'Oferente de Servicio'),
        ('profesionista', 'Profesionista Postulante'),
        ('empresa', 'Empresa Reclutadora'),
        # Podrías añadir más si es necesario
    ]

    # Tus campos adicionales
    # email ya está en AbstractUser y será usado para login, asegúrate que sea único
    fecha_nacimiento = models.DateField(null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='profesionista', # O el que consideres más común
    )

    # Para usar email como nombre de usuario principal para login
    # USERNAME_FIELD = 'email' # Descomenta si quieres usar email para login en vez de username
    # REQUIRED_FIELDS = ['username'] # Si usas email como USERNAME_FIELD, username podría no ser requerido o viceversa. Ajusta según tu necesidad.

    def __str__(self):
        return self.username # O self.email si lo prefieres
    
# usuarios/models.py

# ... (tu clase Usuario existente está aquí arriba) ...

class ServicioOfrecido(models.Model):
    usuario_oferente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='servicios_ofrecidos')
    titulo_servicio = models.CharField(max_length=200)
    descripcion_servicio = models.TextField()
    #imagen_servicio = models.ImageField(upload_to='servicios/', null=True, blank=True)
    # Podríamos añadir más campos en el futuro, como categoría, precio, etc.
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"'{self.titulo_servicio}' ofrecido por {self.usuario_oferente.username}"
    
class ImagenServicio(models.Model):
    """ Un modelo para almacenar cada imagen asociada a un servicio. """
    servicio = models.ForeignKey(ServicioOfrecido, related_name='imagenes', on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='servicios_galeria/')

    def __str__(self):
        return f"Imagen para {self.servicio.titulo_servicio}"

class VacanteEmpresa(models.Model):
    # Asumimos que un usuario tipo 'empresa' publica la vacante
    empresa = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='vacantes_publicadas')
    titulo_vacante = models.CharField(max_length=255)
    descripcion_puesto = models.TextField()
    requisitos = models.TextField(help_text="Lista de requisitos, separados por líneas.")
    tipo_contrato = models.CharField(max_length=50, choices=[('tiempo_completo', 'Tiempo Completo'), ('medio_tiempo', 'Medio Tiempo'), ('freelance', 'Freelance/Proyecto')])
    ubicacion = models.CharField(max_length=150)
    salario_ofrecido = models.CharField(max_length=100, blank=True, null=True, help_text="Ej: $30,000 - $40,000 MXN mensuales")
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.titulo_vacante} en {self.empresa.username}"

class Postulacion(models.Model):
    ESTADO_CHOICES = [
        ('recibida', 'Recibida'),
        ('en_revision', 'En Revisión'),
        ('contactado', 'Contactado'),
        ('rechazado', 'Rechazado'),
    ]
    # El profesional que se postula
    profesional = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='mis_postulaciones')
    # La vacante a la que se postula
    vacante = models.ForeignKey(VacanteEmpresa, on_delete=models.CASCADE, related_name='postulantes')
    
    # Podríamos añadir más campos, como una carta de presentación o la fecha del CV.
    # Por ahora, lo mantenemos simple.

    #Estado de las vacantes como, conctactado, revicion o rechazado 
    fecha_postulacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='recibida'
    )

    # Para evitar que un usuario se postule varias veces a la misma vacante
    class Meta:
        unique_together = ('profesional', 'vacante')

    def __str__(self):
        return f"{self.profesional.username} se postuló a {self.vacante.titulo_vacante}"
    
class Reseña(models.Model):
    # --- Relaciones Clave ---
    evaluador = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reseñas_hechas')
    evaluado = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reseñas_recibidas')

    # --- Campo Común ---
    comentario = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # --- Calificaciones para TRABAJADORES con profesion(calificados por empresas) ---
    calidad_tecnica = models.PositiveSmallIntegerField(null=True, blank=True) # Calidad técnica / Eficiencia
    solucion_problemas = models.PositiveSmallIntegerField(null=True, blank=True)
    cumplimiento_estandares = models.PositiveSmallIntegerField(null=True, blank=True)

     # --- Calificaciones para TRABAJADORES oferentes(calificados por empresas) ---
    eficiencia_tareas = models.PositiveSmallIntegerField(null=True, blank=True) # Calidad técnica / Eficiencia
    atencion = models.PositiveSmallIntegerField(null=True, blank=True)
    manejo_instrucciones = models.PositiveSmallIntegerField(null=True, blank=True)

    # --- Calificaciones de valores para TRABAJADORES(calificados por empresas) ---
    honestidad = models.PositiveSmallIntegerField(null=True, blank=True)
    comunicacion_proactiva = models.PositiveSmallIntegerField(null=True, blank=True)
    puntualidad_trabajador = models.PositiveSmallIntegerField(null=True, blank=True)
    responsabilidad = models.PositiveSmallIntegerField(null=True, blank=True)

    # --- Calificaciones para EMPRESAS (calificadas por trabajadores) ---
    claridad_requerimientos = models.PositiveSmallIntegerField(null=True, blank=True)
    recursos_proporcionados = models.PositiveSmallIntegerField(null=True, blank=True)
    Soporte_tecnicoMaterial = models.PositiveSmallIntegerField(null=True, blank=True)

    puntualidad_pago = models.PositiveSmallIntegerField(null=True, blank=True)
    inclusividad = models.PositiveSmallIntegerField(null=True, blank=True)
    transparencia_contractual = models.PositiveSmallIntegerField(null=True, blank=True)
    respeto_horarios = models.PositiveSmallIntegerField(null=True, blank=True)

    ambiente_laboral = models.PositiveSmallIntegerField(null=True, blank=True)
    comunicacion = models.PositiveSmallIntegerField(null=True, blank=True)
    balance_vida_trabajo = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        return f"Reseña de {self.evaluador.username} para {self.evaluado.username}"
    
class Conversacion(models.Model):
    """ Representa una conversación entre dos usuarios. """
    participantes = models.ManyToManyField(Usuario, related_name='conversaciones')
    servicio_relacionado = models.ForeignKey(
        ServicioOfrecido, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='conversaciones_servicio'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Devuelve los nombres de los participantes, por ejemplo: "sergio - tech"
        return " - ".join([user.username for user in self.participantes.all()])

class Mensaje(models.Model):
    """ Representa un mensaje individual dentro de una conversación. """
    conversacion = models.ForeignKey(Conversacion, on_delete=models.CASCADE, related_name='mensajes')
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='mensajes_enviados')
    contenido = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    class Meta:
        # Ordena los mensajes del más antiguo al más reciente por defecto
        ordering = ['fecha_envio']

    def __str__(self):
        return f"De {self.autor.username} en conversacion {self.conversacion.id}"

