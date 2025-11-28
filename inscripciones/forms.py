from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.forms.forms import NON_FIELD_ERRORS
from .models import Team, PaymentProof, Player


# -----------------------------
# Equipo
# -----------------------------
class TeamForm(forms.ModelForm):
    PREFERRED_DAY_CHOICES = [
        ('LUN', 'Lunes'),
        ('MAR', 'Martes'),
        ('MIE', 'Miércoles'),
        ('JUE', 'Jueves'),
        ('VIE', 'Viernes'),
    ]

    # Campo especial para checkboxes (hasta 2 días)
    preferred_days = forms.MultipleChoiceField(
        choices=PREFERRED_DAY_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Días preferentes de juego (elige hasta 2)',
    )

    class Meta:
        model = Team
        fields = [
            'tournament',
            'category',
            'name',
            'company_name',
            'employer_number_imss',
            'delegate_name',
            'delegate_phone',
            'delegate_office_phone',
            'delegate_email',

            'alternate_delegate_name',
            'alternate_delegate_phone',
            'alternate_delegate_office_phone',

            'preferred_days',
            'delegate_ine',
            'alternate_delegate_ine',
        ]
        labels = {
            'tournament': 'Torneo',
            'category': 'Categoría',
            'name': 'Nombre del equipo',
            'company_name': 'Empresa / Patrocinador',
            'employer_number_imss': 'Número patronal IMSS de la empresa',
            'delegate_name': 'Nombre del delegado',
            'delegate_phone': 'Teléfono del delegado',
            'delegate_office_phone': 'Teléfono de oficina del delegado',
            'delegate_email': 'Correo del delegado',

            'alternate_delegate_name': 'Nombre del responsable suplente',
            'alternate_delegate_phone': 'Teléfono del suplente',
            'alternate_delegate_office_phone': 'Teléfono de oficina del suplente',

            'delegate_ine': 'INE del delegado (foto/scan)',
            'alternate_delegate_ine': 'INE del suplente (foto/scan)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Estilos Bootstrap
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxSelectMultiple):
                field.widget.attrs.update({})
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-control'})

        # Cuando editamos un equipo, precargar días preferentes
        if self.instance and self.instance.pk and self.instance.preferred_days:
            self.fields['preferred_days'].initial = self.instance.preferred_days.split(',')

    def clean_preferred_days(self):
        days = self.cleaned_data.get('preferred_days') or []
        if len(days) > 2:
            raise forms.ValidationError('Selecciona máximo 2 días de juego.')
        return days

    def save(self, commit=True):
        # convertimos lista de días en cadena "LUN,MIE"
        instance = super().save(commit=False)
        days = self.cleaned_data.get('preferred_days') or []
        instance.preferred_days = ','.join(days)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


# -----------------------------
# Comprobante de pago
# -----------------------------
class PaymentProofForm(forms.ModelForm):
    folio = forms.CharField(
        label="Folio del equipo",
        max_length=30,
        help_text="Ingresa el folio tal como aparece en tu ficha de preinscripción.",
    )
    delegate_phone = forms.CharField(
        label="Teléfono del delegado",
        max_length=30,
        help_text="Ingresa el teléfono del delegado que registraste en la preinscripción.",
    )

    class Meta:
        model = PaymentProof
        fields = ['file', 'folio', 'delegate_phone']

    def clean(self):
        cleaned_data = super().clean()
        folio = cleaned_data.get('folio')
        delegate_phone = cleaned_data.get('delegate_phone')

        if folio and delegate_phone:

            def normalize(phone: str) -> str:
                # Nos quedamos solo con dígitos: quita espacios, guiones, etc.
                return ''.join(ch for ch in phone if ch.isdigit())

            try:
                team = Team.objects.get(folio=folio.strip().upper())
            except Team.DoesNotExist:
                raise forms.ValidationError(
                    "No existe ningún equipo con ese folio. Revisa que esté bien escrito."
                )

            db_phone = normalize(team.delegate_phone or "")
            entered_phone = normalize(delegate_phone)

            if not db_phone or db_phone != entered_phone:
                raise forms.ValidationError(
                    "El teléfono del delegado no coincide con el registrado para ese folio. "
                    "Verifica tus datos o contacta a la liga."
                )

            # Guardamos el team para usarlo en la vista
            self.team = team

        return cleaned_data


# -----------------------------
# Jugadores
# -----------------------------
class PlayerForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = [
            'jersey_number',      # Número
            'first_name',         # Nombre
            'last_name',          # Apellido
            'imss_number',        # NSS / IMSS del jugador
            'curp',               # CURP
            'age_years',          # Edad (años)
            'age_months',         # Edad (meses)
            'is_reinforcement',   # Es refuerzo
            'photo',              # Foto (opcional)
        ]
        widgets = {
            'jersey_number': forms.NumberInput(
                attrs={'class': 'form-control form-control-sm'}
            ),
            'first_name': forms.TextInput(
                attrs={'class': 'form-control form-control-sm'}
            ),
            'last_name': forms.TextInput(
                attrs={'class': 'form-control form-control-sm'}
            ),
            'imss_number': forms.TextInput(
                attrs={'class': 'form-control form-control-sm'}
            ),
            'curp': forms.TextInput(   # 👈 nuevo widget
                attrs={
                    'class': 'form-control form-control-sm',
                    'maxlength': 18,
                    'style': 'text-transform:uppercase;',
                    'placeholder': 'CURP (18 caracteres)',
                }
            ),
            'age_years': forms.NumberInput(
                attrs={'class': 'form-control form-control-sm', 'min': 0}
            ),
            'age_months': forms.NumberInput(
                attrs={'class': 'form-control form-control-sm', 'min': 0, 'max': 11}
            ),
            'is_reinforcement': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
            'photo': forms.FileInput(
                attrs={'class': 'form-control form-control-sm'}
            ),
        }

    def clean_curp(self):
        """
        Normaliza y valida la CURP si se captura.
        No la hacemos obligatoria; solo validamos formato básico.
        """
        curp = (self.cleaned_data.get('curp') or '').strip().upper()
        if not curp:
            return curp

        if len(curp) != 18:
            raise forms.ValidationError("La CURP debe tener exactamente 18 caracteres.")

        # Si quieres algo más estricto, aquí podrías meter un regex de CURP real.
        return curp

    def clean(self):
        cleaned = super().clean()

        # ¿Fila completamente en blanco? (para filas extra)
        is_blank = (
            not cleaned.get('jersey_number')
            and not cleaned.get('first_name')
            and not cleaned.get('last_name')
            and not cleaned.get('imss_number')
            and not cleaned.get('curp')           # 👈 añadimos curp a la comprobación
            and not cleaned.get('age_years')
            and not cleaned.get('age_months')
            and not cleaned.get('photo')
            and not cleaned.get('is_reinforcement')
        )

        # Para las filas nuevas se permite que estén totalmente vacías
        if self.empty_permitted and is_blank:
            return cleaned

        # Si NO es refuerzo, el NSS es obligatorio -> error en el campo
        if not cleaned.get('is_reinforcement') and not cleaned.get('imss_number'):
            self.add_error(
                'imss_number',
                "Para jugadores que no son refuerzo, el NSS (IMSS) es obligatorio."
            )

        # 🔹 Hacemos más entendibles los errores de duplicados (unique_together)
        if NON_FIELD_ERRORS in self._errors:
            nuevos = []
            for msg in self._errors[NON_FIELD_ERRORS]:
                if "Team y Número ya existe" in msg or "Team and Number already exists" in msg:
                    nuevos.append(
                        "Ya existe un jugador en este equipo con ese número. "
                        "Verifica que el número de camiseta no esté repetido."
                    )
                elif "Team,Apellido y Nombre ya existe" in msg or "Team, Last name and First name already exists" in msg:
                    nuevos.append(
                        "Ya existe un jugador en este equipo con ese nombre y apellido. "
                        "Revisa que no tengas al mismo jugador registrado dos veces."
                    )
                else:
                    nuevos.append(msg)

            self._errors[NON_FIELD_ERRORS] = nuevos

        return cleaned


class BasePlayerFormSet(BaseInlineFormSet):
    """
    Reglas del equipo:
    - Máx. 20 jugadores.
    - Máx. 2 refuerzos.
    - No se puede repetir número de playera en el mismo equipo.
    - No se puede repetir Nombre + Apellido en el mismo equipo.
    """
    def clean(self):
        super().clean()

        total_players = 0
        reinforcements = 0

        numeros_vistos = {}   # {numero: índice_form}
        nombres_vistos = {}   # {(nombre, apellido): índice_form}

        for index, form in enumerate(self.forms):
            if not hasattr(form, "cleaned_data"):
                continue

            cd = form.cleaned_data

            if cd.get("DELETE"):
                continue

            # Fila completamente vacía -> ignorar
            is_blank = (
                not cd.get('jersey_number')
                and not cd.get('first_name')
                and not cd.get('last_name')
                and not cd.get('imss_number')
                and not cd.get('curp')
                and not cd.get('age_years')
                and not cd.get('age_months')
                and not cd.get('photo')
                and not cd.get('is_reinforcement')
            )
            if is_blank:
                continue

            total_players += 1
            if cd.get('is_reinforcement'):
                reinforcements += 1

            # --- Validar número repetido ---
            num = cd.get('jersey_number')
            if num:
                if num in numeros_vistos:
                    # jugador actual
                    form.add_error(
                        'jersey_number',
                        "Ya existe otro jugador con este número en este equipo."
                    )
                    # jugador anterior con el mismo número
                    self.forms[numeros_vistos[num]].add_error(
                        'jersey_number',
                        "Este número está repetido en la lista de jugadores."
                    )
                else:
                    numeros_vistos[num] = index

            # --- Validar nombre+apellido repetido ---
            first = (cd.get('first_name') or '').strip()
            last = (cd.get('last_name') or '').strip()
            if first and last:
                key = (first.lower(), last.lower())
                if key in nombres_vistos:
                    msg = "Ya existe otro jugador con este nombre y apellido en este equipo."
                    form.add_error('first_name', msg)
                    form.add_error('last_name', msg)

                    # también marcamos el primero
                    prev_index = nombres_vistos[key]
                    self.forms[prev_index].add_error(
                        'first_name', "Nombre y apellido repetidos en la lista."
                    )
                    self.forms[prev_index].add_error(
                        'last_name', "Nombre y apellido repetidos en la lista."
                    )
                else:
                    nombres_vistos[key] = index

        # Máx. 20 jugadores en total
        if total_players > 20:
            raise forms.ValidationError(
                "No puedes registrar más de 20 jugadores por equipo "
                "(18 con NSS + hasta 2 refuerzos)."
            )

        # Máx. 2 refuerzos
        if reinforcements > 2:
            raise forms.ValidationError(
                "Solo puedes registrar hasta 2 jugadores como refuerzo."
            )


PlayerFormSet = inlineformset_factory(
    Team,
    Player,
    form=PlayerForm,
    formset=BasePlayerFormSet,
    extra=20,          # siempre verás hasta 20 filas
    max_num=20,        # nunca más de 20 guardados
    validate_max=True,
    can_delete=True,   # el delegado puede marcar para eliminar
)

# --- Formulario SOLO para el admin ---
class PlayerAdminForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = "__all__"
