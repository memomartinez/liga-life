from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
import qrcode
from io import BytesIO
from django.conf import settings
from reportlab.lib.utils import ImageReader
import os


def generar_credenciales_pdf(team, jugadores, ruta_salida):

    # Hoja tamaño carta
    PAGE_WIDTH, PAGE_HEIGHT = letter

    # Dimensiones de cada credencial
    CARD_WIDTH = 85 * mm
    CARD_HEIGHT = 55 * mm

    # Márgenes y separación entre credenciales
    X_MARGIN = 15 * mm
    Y_MARGIN = 15 * mm
    X_GAP = 8 * mm
    Y_GAP = 8 * mm

    # Fondos disponibles
    fondos = {
        "EMP": os.path.join(settings.BASE_DIR, "static", "fondos", "empresarial_bg.png"),
        "LIB": os.path.join(settings.BASE_DIR, "static", "fondos", "empresarial_bg.png"),
        "VET": os.path.join(settings.BASE_DIR, "static", "fondos", "veteranos_bg.png"),
        "REF": os.path.join(settings.BASE_DIR, "static", "fondos", "refuerzo_bg.png"),
    }

    # Cache de imágenes
    fondos_img = {
        key: ImageReader(path)
        for key, path in fondos.items()
        if os.path.exists(path)
    }

    # ---- helpers de categoría ----
    def es_refuerzo(j):
        """Detecta si el jugador es refuerzo según varios posibles campos."""
        for campo in ("refuerzo", "es_refuerzo", "is_refuerzo", "is_reinforcement", "tipo"):
            if not hasattr(j, campo):
                continue
            val = getattr(j, campo)
            if isinstance(val, bool):
                if val:
                    return True
            elif isinstance(val, int):
                if val != 0:
                    return True
            elif isinstance(val, str):
                if val.strip().lower() in (
                    "ref",
                    "refuerzo",
                    "true",
                    "1",
                    "sí",
                    "si",
                    "y",
                ):
                    return True
        return False

    def categoria_para(j):
        """
        Regla:
        - Si es refuerzo -> REF (credencial de refuerzo).
        - Si no, usamos la categoría del equipo (EMP, VET, LIB, ...).
        - Si falla algo, caemos a EMP.
        """
        if es_refuerzo(j):
            return "REF"

        base = getattr(team, "category", "EMP") or "EMP"
        base = str(base).upper()
        if base in fondos:
            return base
        return "EMP"

    c = canvas.Canvas(ruta_salida, pagesize=letter)

    col_count = 2  # 2 credenciales por fila
    row_count = 4  # 4 filas por página

    jugador_index = 0
    total = len(jugadores)

    while jugador_index < total:
        for fila in range(row_count):
            for col in range(col_count):

                if jugador_index >= total:
                    break

                jugador = jugadores[jugador_index]

                # Esquina inferior izquierda de la credencial
                x = X_MARGIN + col * (CARD_WIDTH + X_GAP)
                y = PAGE_HEIGHT - Y_MARGIN - (fila + 1) * CARD_HEIGHT - fila * Y_GAP

                # ===== FONDO (por jugador) =====
                cat = categoria_para(jugador)
                fondo_img = fondos_img.get(cat, fondos_img.get("EMP"))
                c.drawImage(fondo_img, x, y, CARD_WIDTH, CARD_HEIGHT, mask="auto")

                # ===== LÍNEA PUNTEADA =====
                c.setDash(2, 2)
                c.rect(x, y, CARD_WIDTH, CARD_HEIGHT)
                c.setDash()

                # ===== FOTO =====
                # un poquito más ABAJO (vs el último ajuste)
                if jugador.photo:
                    try:
                        c.drawImage(
                            jugador.photo.path,
                            x + 9.5 * mm,      # misma X
                            y + 15.5 * mm,     # antes 15.5 mm → medio mm más abajo
                            width=15 * mm,
                            height=24 * mm,
                            preserveAspectRatio=True,
                            mask="auto",
                        )
                    except Exception:
                        pass

                # ===== TEXTOS =====
                valor_x = x + 39.5 * mm

                nombre_y   = y + 34.0 * mm   # NOMBRE
                equipo_y   = y + 29.5 * mm   # EQUIPO
                grupo_y    = y + 25.5 * mm   # GRUPO
                curp_y     = y + 21.0 * mm

                servicio_x = x + 47.0 * mm   # SERVICIO MÉDICO
                servicio_y = y + 16.5 * mm

                nombre = f"{jugador.first_name} {jugador.last_name}"
                equipo = team.name
                grupo = (
                    team.get_category_display()
                    if hasattr(team, "get_category_display")
                    else team.category
                )
                curp = getattr(jugador, "curp", "") or ""
                servicio = getattr(jugador, "imss_number", "") or ""

                c.setFont("Helvetica-Bold", 8.5)
                c.drawString(valor_x, nombre_y, nombre)

                c.setFont("Helvetica", 7.5)
                c.drawString(valor_x, equipo_y, equipo)
                c.drawString(valor_x, grupo_y, grupo)

                if curp:
                    c.drawString(valor_x, curp_y, curp)

                if servicio:
                    c.drawString(servicio_x, servicio_y, servicio)

                # ===== FOLIO =====
                words = team.name.split()
                if len(words) >= 2:
                    initials = (words[0][0] + words[1][0]).upper()
                else:
                    initials = team.name[:2].upper()
                folio_jugador = f"{initials}-{jugador.jersey_number:02d}"

                c.saveState()
                # un puntito más pequeño
                c.setFont("Helvetica-Bold", 6)

                # → un poquito MÁS A LA DERECHA y MÁS ARRIBA
                folio_x = x + CARD_WIDTH - 4.5* mm   # se acerca al centro del recuadro blanco
                folio_y = y + CARD_HEIGHT - 7.5 * mm  # sube un poco dentro del recuadro

                c.translate(folio_x, folio_y)
                c.rotate(90)  # se lee al derecho
                c.drawCentredString(0, 0, folio_jugador)
                c.restoreState()

                # ===== QR =====
                qr_data = f"https://liga-life.onrender.com/equipo/{team.folio}/jugadores/"
                qr_img = qrcode.make(qr_data)
                buffer = BytesIO()
                qr_img.save(buffer, "PNG")
                buffer.seek(0)

                QR_SIZE = 9 * mm
                qr_x = x + (CARD_WIDTH - QR_SIZE) / 2 - 5 * mm
                qr_y = y + 5 * mm

                c.drawImage(
                    ImageReader(buffer),
                    qr_x,
                    qr_y,
                    width=QR_SIZE,
                    height=QR_SIZE,
                    mask="auto",
                )

                jugador_index += 1

        c.showPage()

    c.save()
