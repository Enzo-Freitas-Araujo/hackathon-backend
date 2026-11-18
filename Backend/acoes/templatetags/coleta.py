from datetime import timedelta

from django import template
from django.db.models import Avg
from django.utils import timezone

from acoes.models import Acao, Sessao, Usuario

register = template.Library()


@register.simple_tag
def resumo_inicio():
    """Números da tela inicial do admin."""
    hoje = timezone.localdate()
    return {
        "usuarios": Usuario.objects.filter(ativo=True).count(),
        "sessoes_abertas": Sessao.objects.filter(fim__isnull=True).count(),
        "acoes_hoje": Acao.objects.filter(criado_em__date=hoje).count(),
        "acoes_7d": Acao.objects.filter(criado_em__date__gte=hoje - timedelta(days=6)).count(),
        "tr_medio": Acao.objects.aggregate(m=Avg("tempo_reacao"))["m"],
        "hoje": hoje.isoformat(),
    }


@register.simple_tag
def ultimas_acoes(n=8):
    return Acao.objects.select_related("usuario").order_by("-criado_em")[:n]
