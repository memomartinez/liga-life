from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from inscripciones import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.redirect_to_inscripcion, name='home'),
    path('inscripcion/', views.inscripcion, name='inscripcion'),
    path('comprobante/', views.subir_comprobante, name='subir_comprobante'),
    path('login-equipo/', views.team_login, name='team_login'),
    path('equipo/<str:folio>/jugadores/', views.registrar_jugadores, name='registrar_jugadores'),
    path("equipo/<str:folio>/credenciales/pdf/", views.descargar_credenciales, name="credenciales_pdf"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
