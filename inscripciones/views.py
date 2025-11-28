# inscripciones/views.py
from datetime import timedelta
import tempfile

from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import TeamForm, PaymentProofForm, PlayerFormSet
from .models import Tournament, Team, PaymentProof, Player
from .utils import generar_credenciales_pdf


def redirect_to_inscripcion(request):
    return redirect('inscripcion')


def inscripcion(request):
    open_tournaments = Tournament.objects.filter(is_open=True)

    if not open_tournaments.exists():
        return render(request, 'inscripciones/inscripcion_cerrada.html')

    if request.method == 'POST':
        form = TeamForm(request.POST, request.FILES)
        form.fields['tournament'].queryset = open_tournaments
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
            return render(
                request,
                'inscripciones/inscripcion_exitosa.html',
                {'team': team},
            )
    else:
        form = TeamForm()
        form.fields['tournament'].queryset = open_tournaments

    return render(request, 'inscripciones/inscripcion.html', {'form': form})


def subir_comprobante(request):
    """
    Vista pública para subir el comprobante de pago usando el folio del equipo.
    Cada envío crea un NUEVO PaymentProof para tener historial.
    """
    if request.method == 'POST':
        form = PaymentProofForm(request.POST, request.FILES)
        if form.is_valid():
            folio = form.cleaned_data['folio'].strip().upper()

            team = get_object_or_404(Team, folio=folio)

            payment = form.save(commit=False)
            payment.team = team
            payment.save()

            # Actualizar status del equipo cuando envían comprobante
            team.status = 'COMPROBANTE_ENVIADO'
            team.save(update_fields=['status'])

            return render(
                request,
                'inscripciones/comprobante_enviado.html',
                {'team': team},
            )
    else:
        initial = {}
        folio = request.GET.get('folio')
        if folio:
            initial['folio'] = folio
        form = PaymentProofForm(initial=initial)

    return render(request, 'inscripciones/subir_comprobante.html', {'form': form})


def registrar_jugadores(request, folio):
    """
    Registro de jugadores para un equipo específico.

    - Si el equipo NO está aprobado => muestra pantalla de 'pendiente de aprobación'.
    - Si está aprobado => permite capturar / editar jugadores con un formset.
    """
    team = get_object_or_404(Team, folio=folio)

    # Si no está aprobado, bloqueamos el registro
    if team.status != 'APROBADO':
        return render(
            request,
            'inscripciones/registro_jugadores_pendiente.html',
            {'team': team},
        )

    guardado = False

    if request.method == 'POST':
        formset = PlayerFormSet(request.POST, request.FILES, instance=team)
        if formset.is_valid():
            formset.save()
            guardado = True
            # recargamos formset con los datos ya guardados
            formset = PlayerFormSet(instance=team)
    else:
        formset = PlayerFormSet(instance=team)

    return render(
        request,
        'inscripciones/registro_jugadores.html',
        {
            'team': team,
            'formset': formset,
            'guardado': guardado,
        },
    )


def descargar_credenciales(request, folio):
    """
    Genera y devuelve el PDF de credenciales para el equipo con ese folio.
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
