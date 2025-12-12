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
#  Helper para publicidad
# ==========================
def get_ads_context():
# ... (rest of get_ads_context) ...
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


def team_login(request):
    """
    Vista para validar acceso al registro de jugadores.
    Requiere Teléfono del Delegado y PIN.
    """
    if request.method == "POST":
        form = TeamAccessForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["delegate_phone"]
            pin = form.cleaned_data["access_pin"]

            # Buscar equipo que coincida
            # OJO: como el teléfono no es único en estricto sentido (pudiera repetirse),
            # lo ideal es buscar por teléfono y verificar PIN.
            # O si el usuario viene de un link con folio, podríamos pre-filtrar.
            # Aquí buscaremos por teléfono y PIN.
            # Si hay varios equipos con mismo teléfono/PIN, logueamos al más reciente o pedimos folio?
            # Asumamos que el PIN + Teléfono es "suficiente" credencial.
            # Pero para editar SPECIFICAMENTE un equipo, necesitamos saber CUAL.
            # Vamos a asumir que el usuario tiene que elegir a cual entrar si hay multiples?
            # SIMPLIFICACION: Buscamos un match. Si hay varios, tomamos el último.

            teams = Team.objects.filter(access_pin=pin)
            # Filtramos en python para normalizar el telefono de la base si es necesario,
            # pero mejor intentamos filter directo si el formato es consistente.
            # Dado que guardamos texto libre, es riesgoso.
            # Mejor estrategia: iterar y comparar normalizado.

            valid_team = None
            for team in teams:
                db_phone = ''.join(filter(str.isdigit, team.delegate_phone))
                if db_phone == phone:
                    valid_team = team
                    break

            if valid_team:
                # Login exitoso
                request.session['active_team_folio'] = valid_team.folio
                return redirect('registrar_jugadores', folio=valid_team.folio)
            else:
                form.add_error(None, "Credenciales inválidas (Teléfono o PIN incorrectos).")

    else:
        form = TeamAccessForm()

    context = {"form": form}
    context.update(get_ads_context())
    return render(request, "inscripciones/team_login.html", context)


def redirect_to_inscripcion(request):
    return redirect("inscripcion")


def inscripcion(request):
# ... (existing inscripcion view logic) ...
    """
    Devuelve el banner activo (si existe) para cada zona:
    - ad_top
    - ad_sidebar
    - ad_bottom
    """
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


def redirect_to_inscripcion(request):
    return redirect("inscripcion")


def inscripcion(request):
    open_tournaments = Tournament.objects.filter(is_open=True)

    if not open_tournaments.exists():
        context = get_ads_context()
        return render(request, "inscripciones/inscripcion_cerrada.html", context)

    if request.method == "POST":
        form = TeamForm(request.POST, request.FILES)
        form.fields["tournament"].queryset = open_tournaments
        if form.is_valid():
            # No guardamos todavía, para poder llenar folio y fecha límite
            team = form.save(commit=False)

            # Fecha límite de pago: 7 días naturales a partir de hoy
            team.payment_deadline = timezone.now().date() + timedelta(days=7)

            # Generar folio tipo LIFE-<id_torneo>-<consecutivo>
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


def subir_comprobante(request):
    """
    Vista pública para subir el comprobante de pago usando el folio del equipo.
    Cada envío crea un NUEVO PaymentProof para tener historial.
    """
    if request.method == "POST":
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            folio = form.cleaned_data["folio"].strip().upper()

            team = get_object_or_404(Team, folio=folio)

            payment = form.save(commit=False)
            payment.team = team
            payment.save()

            # Actualizar status del equipo cuando envían comprobante
            team.status = "COMPROBANTE_ENVIADO"
            team.save(update_fields=["status"])

            context = {"team": team}
            context.update(get_ads_context())

            return render(
                request,
                "inscripciones/comprobante_enviado.html",
                context,
            )
    else:
        initial = {}
        folio = request.GET.get("folio")
        if folio:
            initial["folio"] = folio
        form = PaymentProofForm(initial=initial)

    context = {"form": form}
    context.update(get_ads_context())

    return render(request, "inscripciones/subir_comprobante.html", context)


def registrar_jugadores(request, folio):
    """
    Registro de jugadores para un equipo específico.

    - Si el equipo NO está aprobado => muestra pantalla de 'pendiente de aprobación'.
    - Si está aprobado => permite capturar / editar jugadores con un formset.
    """
    # Seguridad: Validar sesión
    if request.session.get('active_team_folio') != folio:
        return redirect('team_login')

    team = get_object_or_404(Team, folio=folio)

    # Si no está aprobado, bloqueamos el registro
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
            # recargamos formset con los datos ya guardados
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


def descargar_credenciales(request, folio):
    """
    Genera y devuelve el PDF de credenciales para el equipo con ese folio.
    (Aquí no usamos base.html ni zonas de publicidad: solo se sirve el PDF.)
    """
    equipo = get_object_or_404(Team, folio=folio)
    # Ordenados por número de playera
    jugadores = Player.objects.filter(team=equipo).order_by("jersey_number")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        generar_credenciales_pdf(equipo, jugadores, tmp.name)
        tmp.seek(0)

        return FileResponse(
            open(tmp.name, "rb"),
            content_type="application/pdf",
            filename=f"credenciales_{equipo.folio}.pdf",
        )
