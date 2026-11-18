from django.db import models
from django.utils import timezone


class Usuario(models.Model):
    """Quem joga/usa o app (não é o login do admin)."""

    nome = models.CharField(max_length=150)
    idade = models.PositiveSmallIntegerField(null=True, blank=True)
    email = models.EmailField("e-mail", blank=True, default="")
    instituicao = models.CharField("instituição", max_length=200, blank=True, default="")
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField("cadastrado em", auto_now_add=True)

    class Meta:
        verbose_name = "cadastro"
        verbose_name_plural = "cadastros"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class Sessao(models.Model):
    """Um período de uso: começa quando o usuário entra e termina ao finalizar."""

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="sessoes", verbose_name="usuário")
    inicio = models.DateTimeField("início", auto_now_add=True)
    fim = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "sessão"
        verbose_name_plural = "sessões"
        ordering = ["-inicio"]

    def __str__(self):
        return f"Sessão #{self.pk} · {self.usuario}"

    @property
    def em_andamento(self):
        return self.fim is None

    def finalizar(self):
        if self.fim is None:
            self.fim = timezone.now()
            self.save(update_fields=["fim"])


class Acao(models.Model):
    """Uma ação feita por um usuário, opcionalmente dentro de uma sessão."""

    class Tipo(models.TextChoices):
        CLICK = "click", "Clique"
        DRAG = "drag", "Arrastar"
        TYPE = "type", "Digitar"
        SELECT = "select", "Selecionar"
        SUBMIT = "submit", "Enviar"
        NEXT = "next", "Avançar"
        BACK = "back", "Voltar"
        HINT = "hint", "Pedir dica"
        SKIP = "skip", "Pular"

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="acoes", verbose_name="usuário")
    sessao = models.ForeignKey(
        Sessao, on_delete=models.CASCADE, related_name="acoes", null=True, blank=True, verbose_name="sessão"
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    jogo = models.CharField(max_length=50, blank=True, default="")
    fase = models.CharField(max_length=100, blank=True, default="")
    resposta = models.TextField(blank=True, default="")
    tempo_reacao = models.DecimalField("tempo de reação (s)", max_digits=8, decimal_places=3, null=True, blank=True)
    tempo_resposta = models.DecimalField(
        "tempo de resposta (s)", max_digits=8, decimal_places=3, null=True, blank=True
    )
    extra = models.JSONField(default=dict, blank=True, help_text="Qualquer dado adicional, em JSON.")
    criado_em = models.DateTimeField("data/hora", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "ação"
        verbose_name_plural = "ações"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.usuario} · {self.get_tipo_display()} · {self.fase}"
