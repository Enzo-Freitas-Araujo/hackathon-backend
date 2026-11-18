import csv

from django.contrib import admin
from django.db.models import Avg, Count, Max
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .models import Acao, Sessao, Usuario

admin.site.site_header = "Coleta de Ações"
admin.site.site_title = "Coleta de Ações"
admin.site.index_title = "Início"


def _link(url_name, filtro, pk, texto):
    return format_html('<a href="{}?{}={}">{}</a>', reverse(url_name), filtro, pk, texto)


def _duracao(inicio, fim):
    if not fim:
        return None
    s = int((fim - inicio).total_seconds())
    return f"{s // 3600}h {s % 3600 // 60}m" if s >= 3600 else f"{s // 60}m {s % 60}s"


def acoes_csv(queryset):
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="acoes_{timezone.now():%Y%m%d_%H%M}.csv"'
    resp.write("﻿")  # acentos corretos no Excel
    w = csv.writer(resp, delimiter=";")
    w.writerow(["id", "usuario_id", "usuario", "sessao_id", "tipo", "jogo", "fase", "resposta",
                "tempo_reacao", "tempo_resposta", "extra", "criado_em"])
    num = lambda v: "" if v is None else str(v).replace(".", ",")  # noqa: E731
    for a in queryset.select_related("usuario").order_by("criado_em").iterator():
        w.writerow([a.id, a.usuario_id, a.usuario.nome, a.sessao_id or "", a.tipo, a.jogo, a.fase, a.resposta,
                    num(a.tempo_reacao), num(a.tempo_resposta), a.extra or "",
                    timezone.localtime(a.criado_em).strftime("%Y-%m-%d %H:%M:%S")])
    return resp


# ------------------------------------------------------------------ Usuário
class SessaoInline(admin.TabularInline):
    model = Sessao
    extra = 0
    fields = ["inicio", "fim", "duracao", "total_acoes"]
    readonly_fields = fields
    show_change_link = True
    can_delete = False
    verbose_name_plural = "sessões recentes"

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_n=Count("acoes"))

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="duração")
    def duracao(self, obj):
        return _duracao(obj.inicio, obj.fim) or "Em andamento"

    @admin.display(description="ações")
    def total_acoes(self, obj):
        return obj._n


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ["nome", "idade", "instituicao", "ativo", "n_sessoes", "n_acoes", "ultima_atividade", "criado_em"]
    list_filter = ["ativo", "instituicao", "criado_em"]
    search_fields = ["nome", "email", "instituicao"]
    list_editable = ["ativo"]
    date_hierarchy = "criado_em"
    readonly_fields = ["criado_em"]
    fieldsets = [
        (None, {"fields": ["nome", "idade", "email", "instituicao"]}),
        ("Situação", {"fields": ["ativo", "criado_em"]}),
    ]
    inlines = [SessaoInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _sessoes=Count("sessoes", distinct=True),
            _acoes=Count("acoes", distinct=True),
            _ultima=Max("acoes__criado_em"),
        )

    @admin.display(description="sessões", ordering="_sessoes")
    def n_sessoes(self, obj):
        return _link("admin:acoes_sessao_changelist", "usuario__id__exact", obj.pk, obj._sessoes)

    @admin.display(description="ações", ordering="_acoes")
    def n_acoes(self, obj):
        return _link("admin:acoes_acao_changelist", "usuario__id__exact", obj.pk, obj._acoes)

    @admin.display(description="última atividade", ordering="_ultima")
    def ultima_atividade(self, obj):
        return obj._ultima


# ------------------------------------------------------------------ Sessão
class AcaoInline(admin.TabularInline):
    model = Acao
    extra = 0
    fields = ["criado_em", "tipo", "jogo", "fase", "resposta", "tempo_reacao", "tempo_resposta"]
    readonly_fields = fields
    can_delete = False
    ordering = ["criado_em"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Sessao)
class SessaoAdmin(admin.ModelAdmin):
    list_display = ["__str__", "usuario", "inicio_fmt", "situacao", "duracao", "n_acoes"]
    list_filter = ["inicio", "usuario"]
    search_fields = ["usuario__nome"]
    date_hierarchy = "inicio"
    list_select_related = ["usuario"]
    autocomplete_fields = ["usuario"]
    readonly_fields = ["inicio"]
    actions = ["finalizar_sessoes"]
    inlines = [AcaoInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_n=Count("acoes"))

    @admin.display(description="início", ordering="inicio")
    def inicio_fmt(self, obj):
        return timezone.localtime(obj.inicio).strftime("%d/%m/%Y %H:%M")

    @admin.display(description="situação")
    def situacao(self, obj):
        if obj.fim:
            return format_html('<span class="selo">{}</span>', "Finalizada")
        return format_html('<span class="selo selo-ativo">{}</span>', "Em andamento")

    @admin.display(description="duração")
    def duracao(self, obj):
        return _duracao(obj.inicio, obj.fim) or "—"

    @admin.display(description="ações", ordering="_n")
    def n_acoes(self, obj):
        return _link("admin:acoes_acao_changelist", "sessao__id__exact", obj.pk, obj._n)

    @admin.action(description="Finalizar sessões selecionadas")
    def finalizar_sessoes(self, request, queryset):
        n = queryset.filter(fim__isnull=True).update(fim=timezone.now())
        self.message_user(request, f"{n} sessão(ões) finalizada(s).")


# ------------------------------------------------------------------ Ação
@admin.register(Acao)
class AcaoAdmin(admin.ModelAdmin):
    list_display = ["data_hora", "usuario", "sessao_link", "tipo_selo", "jogo", "fase", "resposta_curta",
                    "tr", "tresp"]
    list_display_links = ["data_hora"]
    list_filter = ["tipo", "jogo", "fase", "criado_em", "usuario"]
    search_fields = ["usuario__nome", "fase", "resposta"]
    date_hierarchy = "criado_em"
    list_select_related = ["usuario", "sessao"]
    autocomplete_fields = ["usuario", "sessao"]
    readonly_fields = ["criado_em"]
    list_per_page = 50
    actions = ["exportar_csv"]
    fieldsets = [
        ("Quem", {"fields": ["usuario", "sessao", "criado_em"]}),
        ("O quê", {"fields": ["tipo", "jogo", "fase", "resposta"]}),
        ("Tempos", {"fields": ["tempo_reacao", "tempo_resposta"]}),
        ("Dados extras", {"fields": ["extra"], "classes": ["collapse"]}),
    ]

    @admin.display(description="data/hora", ordering="criado_em")
    def data_hora(self, obj):
        return timezone.localtime(obj.criado_em).strftime("%d/%m/%Y %H:%M:%S")

    @admin.display(description="sessão", ordering="sessao")
    def sessao_link(self, obj):
        if not obj.sessao_id:
            return "—"
        url = reverse("admin:acoes_sessao_change", args=[obj.sessao_id])
        return format_html('<a href="{}">#{}</a>', url, obj.sessao_id)

    @admin.display(description="tipo", ordering="tipo")
    def tipo_selo(self, obj):
        return format_html('<span class="selo">{}</span>', obj.get_tipo_display())

    @admin.display(description="resposta")
    def resposta_curta(self, obj):
        r = obj.resposta or "—"
        return r if len(r) <= 40 else r[:40] + "…"

    @admin.display(description="t. reação", ordering="tempo_reacao")
    def tr(self, obj):
        return f"{obj.tempo_reacao:.2f} s" if obj.tempo_reacao is not None else "—"

    @admin.display(description="t. resposta", ordering="tempo_resposta")
    def tresp(self, obj):
        return f"{obj.tempo_resposta:.2f} s" if obj.tempo_resposta is not None else "—"

    @admin.action(description="Exportar selecionadas (CSV)")
    def exportar_csv(self, request, queryset):
        return acoes_csv(queryset)

    def changelist_view(self, request, extra_context=None):
        """Calcula o resumo do que está filtrado para mostrar acima da tabela."""
        resp = super().changelist_view(request, extra_context)
        cl = getattr(resp, "context_data", {}).get("cl") if hasattr(resp, "context_data") else None
        if cl is not None:
            qs = cl.queryset
            agg = qs.aggregate(total=Count("id"), usuarios=Count("usuario", distinct=True),
                               sessoes=Count("sessao", distinct=True),
                               tr=Avg("tempo_reacao"), tresp=Avg("tempo_resposta"))
            nomes = dict(Acao.Tipo.choices)
            por_tipo = list(qs.values("tipo").annotate(n=Count("id")).order_by("-n"))
            maior = max((t["n"] for t in por_tipo), default=0)
            resp.context_data["resumo"] = {
                **agg,
                "por_tipo": [
                    {"nome": nomes.get(t["tipo"], t["tipo"]), "n": t["n"],
                     "pct": round(t["n"] / maior * 100) if maior else 0}
                    for t in por_tipo
                ],
            }
        return resp
