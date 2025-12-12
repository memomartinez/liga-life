import random
import string
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class Tournament(models.Model):
    name = models.CharField(max_length=150)
    season = models.CharField(max_length=50, blank=True)
    is_open = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date', 'name']

    def __str__(self):
        return self.name if not self.season else f"{self.name} - {self.season}"


class Team(models.Model):
    CATEGORY_CHOICES = [
        ('EMP', 'Empresarial'),
        ('LIB', 'Libre'),
        ('VET', 'Veteranos'),
    ]
    STATUS_CHOICES = [
        ('PRE_REGISTRADO', 'Pre-registrado (sin comprobante)'),
        ('COMPROBANTE_ENVIADO', 'Comprobante enviado'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
        ('EXPIRADO', 'Expirado'),
    ]

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.PROTECT,
        related_name='teams',
    )
    name = models.CharField('Nombre del equipo', max_length=150)
    company_name = models.CharField('Empresa/Patrocinador', max_length=150, blank=True)

    employer_number_imss = models.CharField(
        'Número patronal IMSS',
        max_length=20,
        blank=True,
        help_text='Número patronal registrado ante el IMSS (opcional).',
    )

    # Responsable principal
    category = models.CharField(max_length=3, choices=CATEGORY_CHOICES)
    delegate_name = models.CharField('Nombre del delegado', max_length=150)
    delegate_phone = models.CharField('Teléfono del delegado', max_length=30)
    delegate_office_phone = models.CharField(
        'Teléfono de oficina del delegado',
        max_length=30,
        blank=True,
    )
    delegate_email = models.EmailField('Correo del delegado', blank=True)

    # Responsable suplente
    alternate_delegate_name = models.CharField(
        'Nombre del responsable suplente',
        max_length=150,
        blank=True,
    )
    alternate_delegate_phone = models.CharField(
        'Teléfono del suplente',
        max_length=30,
        blank=True,
    )
    alternate_delegate_office_phone = models.CharField(
        'Teléfono de oficina del suplente',
        max_length=30,
        blank=True,
    )

    # Preferencias de juego (guardamos códigos separados por coma, ej. "LUN,MIE")
    preferred_days = models.CharField(
        'Días preferentes de juego',
        max_length=50,
        blank=True,
    )

    # Documentos (INEs)
    delegate_ine = models.FileField(
        'INE del delegado',
        upload_to='ines/',
        null=True,
        blank=True,
    )
    alternate_delegate_ine = models.FileField(
        'INE del suplente',
        upload_to='ines/',
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PRE_REGISTRADO',
    )
    folio = models.CharField(max_length=30, unique=True, blank=True)
    access_pin = models.CharField(
        'PIN de acceso',
        max_length=4,
        blank=True,
        help_text='PIN de 4 dígitos para editar jugadores.',
    )
    payment_deadline = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['tournament', 'name']

    def __str__(self):
        return f"{self.name} ({self.tournament})"

    def save(self, *args, **kwargs):
        creating = self.pk is None

        # Fecha límite de pago automática (7 días)
        if creating and self.payment_deadline is None:
            self.payment_deadline = timezone.now().date() + timedelta(days=7)

        super().save(*args, **kwargs)

        # Generación de folio LIFE-<torneo>-<consecutivo>
        if creating and not self.folio:
            self.folio = f"LIFE-{self.tournament.id:02d}-{self.id:04d}"
            super().save(update_fields=['folio'])

        # Generar PIN de 4 dígitos si no existe (siempre)
        if creating and not self.access_pin:
            self.access_pin = ''.join(random.choices(string.digits, k=4))
            super().save(update_fields=['access_pin'])


class Player(models.Model):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='players',
    )

    jersey_number = models.PositiveIntegerField(
        'Número',
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )
    last_name = models.CharField('Apellido', max_length=150)
    first_name = models.CharField('Nombre', max_length=150)

    imss_number = models.CharField(
        'Número IMSS',
        max_length=20,
        blank=True,
        help_text='Si es refuerzo y no tiene IMSS, deja en blanco.',
    )
    age_years = models.PositiveIntegerField(
        'Edad (años)',
        null=True,
        blank=True,
    )
    age_months = models.PositiveIntegerField(
        'Edad (meses)',
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(12)],
        help_text='Meses adicionales (0–12).',
    )
    curp = models.CharField(
        'CURP',
        max_length=18,
        blank=True,
        help_text='CURP del jugador (opcional).',
    )
    is_reinforcement = models.BooleanField(
        'Es refuerzo',
        default=False,
        help_text='Marca esta casilla si el jugador es refuerzo.',
    )

    # Foto opcional del jugador
    photo = models.ImageField(
        'Foto del jugador (opcional)',
        upload_to='jugadores_fotos/',
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['team', 'jersey_number']
        unique_together = [
            ('team', 'jersey_number'),
            ('team', 'last_name', 'first_name'),
        ]

    def __str__(self):
        ref = " (REF)" if self.is_reinforcement else ""
        return f"{self.jersey_number} - {self.last_name} {self.first_name}{ref}"


class PaymentProof(models.Model):
    # ahora es ForeignKey, no OneToOne
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='payment_proofs',
    )
    file = models.FileField(upload_to='comprobantes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Comprobante {self.team.folio}"


# =============================
#  PUBLICIDAD / BANNERS
# =============================
class AdBanner(models.Model):
    POSITION_CHOICES = [
        ('TOP', 'Banner superior'),
        ('SIDEBAR', 'Banner lateral'),
        ('BOTTOM', 'Banner inferior'),
    ]

    name = models.CharField(
        'Nombre interno',
        max_length=100,
    )
    position = models.CharField(
        'Posición',
        max_length=10,
        choices=POSITION_CHOICES,
    )
    image = models.ImageField(
        'Imagen del banner',
        upload_to='publicidad/',
        blank=True,
        null=True,
    )
    image_url = models.URLField(
        'URL de imagen externa',
        blank=True,
        help_text='Opcional. Si se especifica, se usará en lugar de la imagen subida.',
    )
    link_url = models.URLField(
        'URL de destino',
        blank=True,
        help_text='Opcional. Link al hacer clic en el banner.',
    )
    is_active = models.BooleanField(
        'Activo',
        default=True,
    )
    order = models.PositiveIntegerField(
        'Orden',
        default=0,
        help_text='Se usa para ordenar los banners dentro de la misma posición.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'order', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_position_display()})"

    @property
    def get_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        if self.image_url:
            return self.image_url
        return ""
