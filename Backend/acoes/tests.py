from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Acao, Sessao, Usuario


class APITests(TestCase):
    def setUp(self):
        self.c = APIClient()
        self.admin = get_user_model().objects.create_superuser("admin", "a@a.com", "senha-forte-123")

    def test_fluxo_completo(self):
        r = self.c.post("/api/usuarios/", {"nome": "Ana", "idade": 8, "instituicao": "Escola X"}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        uid = r.data["id"]

        r = self.c.post("/api/sessoes/", {"usuario_id": uid}, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        sid = r.data["id"]

        r = self.c.post("/api/acoes/", [
            {"usuario_id": uid, "sessao_id": sid, "tipo": "click", "fase": "f1"},
            {"usuario_id": uid, "sessao_id": sid, "tipo": "submit", "fase": "f1", "tempo_reacao": 1.25},
        ], format="json")
        self.assertEqual(r.status_code, 201, r.data)

        r = self.c.post(f"/api/sessoes/{sid}/finalizar/")
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(r.data["fim"])
        self.assertEqual(Sessao.objects.get().acoes.count(), 2)

    def test_validacoes(self):
        ana = Usuario.objects.create(nome="Ana")
        bia = Usuario.objects.create(nome="Bia")
        s_bia = Sessao.objects.create(usuario=bia)
        fechada = Sessao.objects.create(usuario=ana)
        fechada.finalizar()
        casos = [
            ({"usuario_id": 999, "tipo": "click"}, "usuario_id"),
            ({"usuario_id": ana.pk, "tipo": "voar"}, "tipo"),
            ({"usuario_id": ana.pk, "tipo": "click", "tempo_reacao": -1}, "tempo_reacao"),
            ({"usuario_id": ana.pk, "tipo": "click", "sessao_id": s_bia.pk}, "sessao_id"),
            ({"usuario_id": ana.pk, "tipo": "click", "sessao_id": fechada.pk}, "sessao_id"),
        ]
        for corpo, campo in casos:
            r = self.c.post("/api/acoes/", corpo, format="json")
            self.assertEqual(r.status_code, 400, corpo)
            self.assertIn(campo, r.data)
        self.assertEqual(self.c.post("/api/usuarios/", {}, format="json").status_code, 400)

    def test_usuario_inativo_nao_abre_sessao(self):
        u = Usuario.objects.create(nome="Ana", ativo=False)
        self.assertEqual(self.c.post("/api/sessoes/", {"usuario_id": u.pk}, format="json").status_code, 400)

    def test_leitura_exige_login_e_filtros(self):
        u1, u2 = Usuario.objects.create(nome="Ana"), Usuario.objects.create(nome="Bia")
        Acao.objects.create(usuario=u1, tipo="click")
        Acao.objects.create(usuario=u2, tipo="submit")
        for url in ["/api/usuarios/", "/api/sessoes/", "/api/acoes/", f"/api/usuarios/{u1.pk}/"]:
            self.assertEqual(self.c.get(url).status_code, 401, url)
        token = self.c.post("/api/token/", {"username": "admin", "password": "senha-forte-123"}).data["token"]
        self.c.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(self.c.get("/api/acoes/").data["count"], 2)
        self.assertEqual(self.c.get(f"/api/acoes/?usuario={u1.pk}").data["count"], 1)
        self.assertEqual(self.c.get("/api/usuarios/?nome=bi").data["count"], 1)


class TelasTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser("admin", "a@a.com", "senha-forte-123")
        self.u = Usuario.objects.create(nome="Ana", idade=8)
        self.s = Sessao.objects.create(usuario=self.u)
        self.a = Acao.objects.create(usuario=self.u, sessao=self.s, tipo="submit", tempo_reacao=Decimal("1.5"))
        Acao.objects.create(usuario=self.u, tipo="click")

    def test_paginas_admin(self):
        self.client.force_login(self.admin)
        for url in [
            "/admin/", "/admin/acoes/usuario/", f"/admin/acoes/usuario/{self.u.pk}/change/", "/admin/acoes/usuario/add/",
            "/admin/acoes/sessao/", f"/admin/acoes/sessao/{self.s.pk}/change/",
            "/admin/acoes/acao/", f"/admin/acoes/acao/{self.a.pk}/change/",
        ]:
            r = self.client.get(url)
            self.assertEqual(r.status_code, 200, url)
            self.assertContains(r, "css/tema.css")

    def test_resumo_da_lista_de_acoes(self):
        self.client.force_login(self.admin)
        r = self.client.get("/admin/acoes/acao/")
        self.assertEqual(r.context["resumo"]["total"], 2)
        r = self.client.get("/admin/acoes/acao/?tipo__exact=submit")
        self.assertEqual(r.context["resumo"]["total"], 1)
        self.assertContains(r, "Ações por tipo")

    def test_exportar_csv_e_finalizar(self):
        self.client.force_login(self.admin)
        r = self.client.post("/admin/acoes/acao/", {"action": "exportar_csv", "_selected_action": [self.a.pk]})
        self.assertIn("Ana", r.content.decode("utf-8-sig"))
        self.client.post("/admin/acoes/sessao/", {"action": "finalizar_sessoes", "_selected_action": [self.s.pk]})
        self.s.refresh_from_db()
        self.assertIsNotNone(self.s.fim)

    def test_pagina_inicial_usa_o_mesmo_tema(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "css/tema.css")
