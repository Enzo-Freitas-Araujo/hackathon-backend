# API de Coleta de Ações

Cadastro de usuários, sessões e ações, com Django REST Framework e o Django Admin com tema próprio (preto e azul).

## Rodar

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
DEBUG=True python manage.py runserver
```

Admin: http://127.0.0.1:8000/admin/

## Endpoints

| Método | URL | Uso |
|---|---|---|
| POST | `/api/usuarios/` | cadastra `{"nome": "Ana", "idade": 8, "email": "", "instituicao": ""}` |
| POST | `/api/sessoes/` | inicia `{"usuario_id": 1}` |
| POST | `/api/sessoes/<id>/finalizar/` | finaliza |
| POST | `/api/acoes/` | registra uma ação ou uma lista (veja abaixo) |
| GET | `/api/usuarios/`, `/api/usuarios/<id>/`, `/api/sessoes/`, `/api/acoes/` | leitura, **exige login** |
| POST | `/api/token/` | `username` + `password` → token (header `Authorization: Token <token>`) |

Ação:

```json
{
  "usuario_id": 1, "sessao_id": 3,
  "tipo": "submit", "jogo": "piaget", "fase": "capitulo_1", "resposta": "B",
  "tempo_reacao": 1.42, "tempo_resposta": 2.10, "extra": {"qualquer": "coisa"}
}
```

Tipos: `click, drag, type, select, submit, next, back, hint, skip`.
Filtros de `/api/acoes/`: `?usuario= &sessao= &tipo= &jogo= &fase= &de=AAAA-MM-DD &ate=AAAA-MM-DD`.

## Telas

- `/admin/`: tema preto e azul; início com resumo; tela de ações com totais e ações por tipo; exportação CSV.
- `/`: página inicial de exemplo usando o mesmo tema.

## Tema

- Cores: variáveis no topo de `static/css/tema.css`.
- Admin: `templates/admin/` (base_site.html, index.html, acoes/acao/change_list.html).
- Outras páginas: estenda `templates/base.html` (exemplo em `templates/inicio.html`).

## Deploy (Render)

Variáveis: `DJANGO_SECRET_KEY`, `DATABASE_URL`, `CORS_ALLOWED_ORIGINS` (URL do front), `CSRF_TRUSTED_ORIGINS`.

```
Build: pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
Start: gunicorn mysite.wsgi
```
