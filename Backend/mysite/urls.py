from django.contrib import admin
from django.urls import path, re_path
from django.views.generic import TemplateView
from rest_framework.authtoken.views import obtain_auth_token

from acoes import api

urlpatterns = [
    path("", TemplateView.as_view(template_name="inicio.html"), name="inicio"),
    path("admin/", admin.site.urls),
    re_path(r"^api/usuarios/?$", api.UsuarioView.as_view()),
    re_path(r"^api/usuarios/(?P<pk>\d+)/?$", api.UsuarioDetalheView.as_view()),
    re_path(r"^api/sessoes/?$", api.SessaoView.as_view()),
    re_path(r"^api/sessoes/(?P<pk>\d+)/finalizar/?$", api.FinalizarSessaoView.as_view()),
    re_path(r"^api/acoes/?$", api.AcaoView.as_view()),
]
