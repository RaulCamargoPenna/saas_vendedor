# SaaS Vendedor

SaaS multitenant para vendedores gerenciarem as empresas que atendem, os
produtos que essas empresas compram/vendem, alertas de reposição de estoque,
sugestões de conexão comercial e vendas com comissão.

Implementado seguindo o PRD do projeto (`prd-saas-vendedor.md`), com Django 5+
(Class Based Views), Django Template Language + TailwindCSS (via CDN) e
SQLite.

## Stack

- Python 3.12+
- Django 6.1 (atende ao requisito "Django 5+")
- TailwindCSS via CDN (Play CDN) — não é necessário Node/npm para rodar o projeto
- pytest + pytest-django para os testes automatizados
- SQLite (banco padrão do Django)

## Como rodar o projeto

1. Crie e ative o ambiente virtual:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Gere as migrations e aplique no banco (o projeto é entregue **sem**
   migrations geradas, propositalmente, para você criar as suas):

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. Crie um superusuário (necessário para ativar tenants pelo Django Admin):

   ```bash
   python manage.py createsuperuser
   ```

   O comando vai pedir e-mail e senha (o login é feito por e-mail, não por
   username).

5. Rode o servidor de desenvolvimento:

   ```bash
   python manage.py runserver
   ```

6. Acesse:
   - Site institucional: http://localhost:8000/
   - Login: http://localhost:8000/conta/login/
   - Cadastro de novo tenant: http://localhost:8000/conta/cadastro/
   - Django Admin (ativação de tenants): http://localhost:8000/admin/

## Fluxo de teste manual sugerido

1. Acesse `/conta/cadastro/` e cadastre uma nova empresa (tenant) + usuário
   administrador.
2. O e-mail de ativação é impresso no **console** onde o `runserver` está
   rodando (backend de e-mail configurado como `console` em desenvolvimento).
   Copie o link e acesse-o para ativar a conta do usuário.
3. Entre no Django Admin com o superusuário criado no passo 4 acima, vá em
   **Tenants** e ative o tenant recém-criado (ação "Ativar tenants
   selecionados").
4. Volte para `/conta/login/` e faça login com o e-mail/senha cadastrados.
5. No dashboard, cadastre empresas (`Empresas`), produtos (`Produtos`),
   vincule produtos às empresas informando se compram ou vendem, registre
   vendas (`Vendas`) e veja as sugestões de conexão (`Sugestões`).

## Rodando os testes automatizados

```bash
python -m pytest
```

Todos os models, views e regras de negócio principais (isolamento
multitenant, ativação de conta, cálculo de previsão de reposição de estoque,
geração de sugestões de conexão e efeitos colaterais do registro de uma
venda) possuem testes em `<app>/tests/`.

## Estrutura de apps

| App | Responsabilidade |
|---|---|
| `core` | Mixins reutilizáveis de isolamento multitenant e permissões |
| `tenants` | Model `Tenant` e ativação pelo Django Admin |
| `accounts` | Usuário customizado (login por e-mail), ativação de conta, funcionários |
| `companies` | Cadastro de empresas clientes |
| `products` | Cadastro de produtos e vínculo empresa-produto (compra/venda) |
| `sales` | Registro de vendas, itens de venda e comissões |
| `suggestions` | Sugestões de conexão comercial entre empresas |
| `dashboard` | Painel principal pós-login com indicadores e alertas |
| `landing` | Site institucional público |

## Observações importantes

- O projeto está configurado com `EMAIL_BACKEND` de console (os e-mails de
  ativação aparecem no terminal). Para produção, configure um backend SMTP
  real em `config/settings.py`.
- `DEBUG = True` e `SECRET_KEY` de desenvolvimento estão no `settings.py`;
  troque ambos antes de qualquer deploy.
- Docker foi propositalmente deixado de fora desta entrega, conforme
  definido no PRD (previsto apenas para as sprints finais).
- O TailwindCSS é carregado via CDN (Play CDN) para manter o setup simples,
  sem exigir Node/npm. Caso queira migrar para um build local do Tailwind
  no futuro, isso pode ser adicionado sem alterar a estrutura dos templates.
