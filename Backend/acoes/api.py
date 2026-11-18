from django.shortcuts import get_object_or_404
from rest_framework import generics, serializers, status
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Acao, Sessao, Usuario


# ---------------------------------------------------------------- permissões
class GravarLivreLerComLogin(BasePermission):
    """API aberta: qualquer um pode ler (GET) e gravar (POST)."""

    def has_permission(self, request, view):
        return request.method in ("GET", "HEAD", "OPTIONS", "POST")


# ---------------------------------------------------------------- serializers
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "nome", "idade", "email", "instituicao", "ativo", "criado_em"]
        read_only_fields = ["ativo", "criado_em"]


class SessaoSerializer(serializers.ModelSerializer):
    usuario_id = serializers.PrimaryKeyRelatedField(source="usuario", queryset=Usuario.objects.filter(ativo=True))
    usuario_nome = serializers.CharField(source="usuario.nome", read_only=True)

    class Meta:
        model = Sessao
        fields = ["id", "usuario_id", "usuario_nome", "inicio", "fim"]
        read_only_fields = ["inicio", "fim"]


class AcaoSerializer(serializers.ModelSerializer):
    usuario_id = serializers.PrimaryKeyRelatedField(source="usuario", queryset=Usuario.objects.all())
    sessao_id = serializers.PrimaryKeyRelatedField(
        source="sessao", queryset=Sessao.objects.all(), required=False, allow_null=True
    )
    tempo_reacao = serializers.DecimalField(
        max_digits=8, decimal_places=3, min_value=0, required=False, allow_null=True, coerce_to_string=False
    )
    tempo_resposta = serializers.DecimalField(
        max_digits=8, decimal_places=3, min_value=0, required=False, allow_null=True, coerce_to_string=False
    )

    class Meta:
        model = Acao
        fields = ["id", "usuario_id", "sessao_id", "tipo", "jogo", "fase", "resposta",
                  "tempo_reacao", "tempo_resposta", "extra", "criado_em"]
        read_only_fields = ["criado_em"]

    def validate(self, attrs):
        sessao = attrs.get("sessao")
        if sessao:
            if sessao.usuario_id != attrs["usuario"].pk:
                raise serializers.ValidationError({"sessao_id": "Esta sessão é de outro usuário."})
            if sessao.fim:
                raise serializers.ValidationError({"sessao_id": "Esta sessão já foi finalizada."})
        return attrs


# ---------------------------------------------------------------- views
class FiltroMixin:
    FILTROS = {}

    def get_queryset(self):
        qs = super().get_queryset()
        for param, campo in self.FILTROS.items():
            valor = self.request.query_params.get(param)
            if valor:
                qs = qs.filter(**{campo: valor})
        return qs


class UsuarioView(FiltroMixin, generics.ListCreateAPIView):
    """POST /api/usuarios/ cadastra · GET lista (?nome= &instituicao=)"""

    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [GravarLivreLerComLogin]
    FILTROS = {"nome": "nome__icontains", "instituicao": "instituicao"}


class UsuarioDetalheView(generics.RetrieveAPIView):
    """GET /api/usuarios/{id}/"""

    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [GravarLivreLerComLogin]


class SessaoView(FiltroMixin, generics.ListCreateAPIView):
    """POST /api/sessoes/ inicia {"usuario_id": 1} · GET lista (?usuario=)"""

    queryset = Sessao.objects.select_related("usuario")
    serializer_class = SessaoSerializer
    permission_classes = [GravarLivreLerComLogin]
    FILTROS = {"usuario": "usuario_id"}


class FinalizarSessaoView(APIView):
    """POST /api/sessoes/{id}/finalizar/"""

    permission_classes = [GravarLivreLerComLogin]

    def post(self, request, pk):
        sessao = get_object_or_404(Sessao.objects.select_related("usuario"), pk=pk)
        sessao.finalizar()
        return Response(SessaoSerializer(sessao).data)


class AcaoView(FiltroMixin, generics.ListCreateAPIView):
    """
    POST /api/acoes/  registra uma ação ou uma lista
    GET  /api/acoes/  ?usuario= &sessao= &tipo= &jogo= &fase= &de=AAAA-MM-DD &ate=AAAA-MM-DD
    """

    queryset = Acao.objects.all()
    serializer_class = AcaoSerializer
    permission_classes = [GravarLivreLerComLogin]
    FILTROS = {"usuario": "usuario_id", "sessao": "sessao_id", "tipo": "tipo", "jogo": "jogo", "fase": "fase",
               "de": "criado_em__date__gte", "ate": "criado_em__date__lte"}

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data, many=isinstance(request.data, list))
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=status.HTTP_201_CREATED)
