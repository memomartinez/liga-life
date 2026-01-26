# inscripciones/views.py
from datetime import timedelta
import tempfile

from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import TeamForm, PaymentProofForm, PlayerFormSet, TeamAccessForm
from .models import Tournament, Team, PaymentProof, Player, AdBanner
from .utils import generar_credenciales_pdf


# ==========================
# Helper para publicidad
# ==========================
def get_ads_context():
    return {
        "ad_top": AdBanner.objects.filter(
            position="TOP", is_active=True
        ).order_by("order", "-created_at").first(),
        "ad_sidebar": AdBanner.objects.filter(
            position="SIDEBAR", is_active=True
        ).order_by("order", "-created_at").first(),
        "ad_bottom": AdBanner.objects.filter(
            position="BOTTOM", is_active=True
        ).order_by("order", "-created_at").first(),
    }


# ==========================
# Login de equipo
# ==========================
def team_login(request):
    """
    Acceso al registro de jugadores mediante:
    - Teléfono del delegado
    - PIN del equipo
    """
    if request.method == "POST":
        form = TeamAccessForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["delegate_phone"]
            pin = form.cleaned_data["access_pin"]

            teams = Team.objects.filter(access_pin=pin)
            valid_team = None

            for team in teams:
                db_phone = "".join(filter(str.isdigit, team.delegate_phone))
                if db_phone == phone:
                    valid_team = team
                    break

            if valid_team:
                request.session["active_team_folio"] = valid_team.folio
                return redirect("registrar_jugadores", folio=valid_team.folio)
            else:
                form.add_error(
                    None, "Credenciales inválidas (Teléfono o PIN incorrectos)."
                )
    else:
        form = TeamAccessForm()

    context = {"form": form}
    context.update(get_ads_context())
    return render(request, "inscripciones/team_login.html", context)


def redirect_to_inscripcion(request):
    return redirect("inscripcion")


# ==========================
# Inscripción de equipo
# ==========================
def inscripcion(request):
    open_tournaments = Tournament.objects.filter(is_open=True)

    if not open_tournaments.exists():
        context = get_ads_context()
        return render(request, "inscripciones/inscripcion_cerrada.html", context)

    if request.method == "POST":
        form = TeamForm(request.POST, request.FILES)
        form.fields["tournament"].queryset = open_tournaments

        if form.is_valid():
            team = form.save(commit=False)

            # Fecha límite de pago: 7 días naturales
            team.payment_deadline = timezone.now().date() + timedelta(days=7)

            # Generar folio
            if not team.folio:
                consecutivo = (
                    Team.objects.filter(tournament=team.tournament).count() + 1
                )
                team.folio = f"LIFE-{team.tournament.id:02d}-{consecutivo:04d}"

            team.save()

            context = {"team": team}
            context.update(get_ads_context())

            return render(
                request,
                "inscripciones/inscripcion_exitosa.html",
                context,
            )
    else:
        form = TeamForm()
        form.fields["tournament"].queryset = open_tournaments

    context = {"form": form}
    context.update(get_ads_context())

    return render(request, "inscripciones/inscripcion.html", context)


# ==========================
# Subir comprobante
# ==========================
def subir_comprobante(request):
    """
    Subida pública de comprobante usando folio + teléfono del delegado.
    Cada envío crea un PaymentProof nuevo.
    """
    if request.method == "POST":
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            # IMPORTANTE: usar el Team validado por el form (folio + teléfono)
            team = getattr(form, "team", None)
            if team is None:
                # Fallback defensivo (no debería pasar si el form valida bien)
                folio = (form.cleaned_data.get("folio") or "").strip().upper()
                team = get_object_or_404(Team, folio=folio)

            payment = form.save(commit=False)
            payment.team = team
            payment.save()

            team.status = "COMPROBANTE_ENVIADO"
            team.save(update_fields=["status"])

            context = {"team": team}
            context.update(get_ads_context())
            return render(request, "inscripciones/comprobante_enviado.html", context)
    else:
        initial = {}
        folio = request.GET.get("folio")
        if folio:
            initial["folio"] = folio
        form = PaymentProofForm(initial=initial)

    context = {"form": form}
    context.update(get_ads_context())
    return render(request, "inscripciones/subir_comprobante.html", context)

# ==========================
# Registro de jugadores
# ==========================
def registrar_jugadores(request, folio):
    """
    Registro / edición de jugadores.
    Solo equipos aprobados y con sesión válida.
    """
    if request.session.get("active_team_folio") != folio:
        return redirect("team_login")

    team = get_object_or_404(Team, folio=folio)

    if team.status != "APROBADO":
        context = {"team": team}
        context.update(get_ads_context())
        return render(
            request,
            "inscripciones/registro_jugadores_pendiente.html",
            context,
        )

    guardado = False

    if request.method == "POST":
        formset = PlayerFormSet(request.POST, request.FILES, instance=team)
        if formset.is_valid():
            formset.save()
            guardado = True
            formset = PlayerFormSet(instance=team)
    else:
        formset = PlayerFormSet(instance=team)

    context = {
        "team": team,
        "formset": formset,
        "guardado": guardado,
    }
    context.update(get_ads_context())

    return render(
        request,
        "inscripciones/registro_jugadores.html",
        context,
    )


# ==========================
# Descargar credenciales
# ==========================
def descargar_credenciales(request, folio):
    """
    Genera y devuelve el PDF de credenciales.
    Protegido por sesión y status APROBADO.
    """
    if request.session.get("active_team_folio") != folio:
        return redirect("team_login")

    equipo = get_object_or_404(Team, folio=folio)
    if equipo.status != "APROBADO":
        return redirect("team_login")

    jugadores = Player.objects.filter(team=equipo).order_by("jersey_number")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        generar_credenciales_pdf(equipo, jugadores, tmp.name)
        tmp.seek(0)

        return FileResponse(
            open(tmp.name, "rb"),
            content_type="application/pdf",
            filename=f"credenciales_{equipo.folio}.pdf",
        )
