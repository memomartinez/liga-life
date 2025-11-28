from django.contrib import admin
from django import forms

from .models import Tournament, Team, Player, PaymentProof


# ===========================
#  INLINE DE JUGADORES
# ===========================
class PlayerInlineForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = (
            "jersey_number",
            "last_name",
            "first_name",
            "imss_number",
            "curp",
            "age_years",
            "age_months",
            "is_reinforcement",
            "photo",
        )
        widgets = {
            "jersey_number": forms.NumberInput(
                attrs={"style": "width: 60px;"}
            ),
            "last_name": forms.TextInput(
                attrs={"style": "width: 140px;"}
            ),
            "first_name": forms.TextInput(
                attrs={"style": "width: 140px;"}
            ),
            "imss_number": forms.TextInput(
                attrs={"style": "width: 120px;"}
            ),
            "curp": forms.TextInput(
                attrs={"style": "width: 180px;"}
            ),
            "age_years": forms.NumberInput(
                attrs={"style": "width: 60px;"}
            ),
            "age_months": forms.NumberInput(
                attrs={"style": "width: 60px;"}
            ),
            "photo": forms.ClearableFileInput(
                attrs={"style": "width: 220px;"}
            ),
        }


class PlayerInline(admin.TabularInline):
    model = Player
    form = PlayerInlineForm
    extra = 0
    fields = (
        "jersey_number",
        "last_name",
        "first_name",
        "imss_number",
        "curp",
        "age_years",
        "age_months",
        "is_reinforcement",
        "photo",
    )


# ===========================
#  INLINE DE COMPROBANTES
# ===========================
class PaymentProofInline(admin.TabularInline):
    model = PaymentProof
    extra = 0
    readonly_fields = ("file", "uploaded_at")
    can_delete = False


# ===========================
#  TOURNAMENT
# ===========================
@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name", "season", "is_open", "start_date", "end_date")
    list_filter = ("is_open",)


# ===========================
#  TEAM
# ===========================
@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    inlines = [PlayerInline, PaymentProofInline]

    # botones de guardar también arriba
    save_on_top = True

    # usamos template propio para mover Historia + Recargar
    change_form_template = "inscripciones/team/change_form.html"

    fieldsets = (
        ("Datos del equipo", {
            "fields": (
                ("tournament", "category"),
                ("name", "company_name"),
                "employer_number_imss",
            )
        }),
        ("Delegado titular", {
            "fields": (
                ("delegate_name", "delegate_email"),
                ("delegate_phone", "delegate_office_phone"),
                "delegate_ine",
            )
        }),
        ("Delegado suplente", {
            "classes": ("collapse",),
            "fields": (
                "alternate_delegate_name",
                ("alternate_delegate_phone", "alternate_delegate_office_phone"),
                "alternate_delegate_ine",
            ),
        }),
        ("Control interno de la liga", {
            "fields": (
                "status",
                "folio",
                "payment_deadline",
                "preferred_days",
            )
        }),
    )

    class Media:
        css = {
            "all": ("css/admin_team.css",)
        }
        js = ("js/admin_team.js",)


# ===========================
#  PAYMENT PROOF
# ===========================
@admin.register(PaymentProof)
class PaymentProofAdmin(admin.ModelAdmin):
    list_display = ("team", "uploaded_at", "file")
    readonly_fields = ("uploaded_at",)
    search_fields = ("team__name", "team__folio")
    list_filter = ("uploaded_at",)
