# SaaS Vendedor

A multitenant SaaS platform that enables salespeople to manage the companies
they serve, the products those companies buy and sell, inventory replenishment
alerts, business connection suggestions, and commission-based sales.

Implemented according to the project PRD (`prd-saas-vendedor.md`) using Django
5+ (Class-Based Views), Django Template Language, Tailwind CSS (via CDN), and
SQLite.

Live at: https://saas.raulcamargo.com.br/

## Stack

- Python 3.12+
- Django 6.1 (meets the "Django 5+" requirement)
- Tailwind CSS via CDN (Play CDN) — Node/npm is not required to run the project
- pytest + pytest-django for automated tests
- SQLite (Django's default database)

## Running the project

1. Create and activate the virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Generate the migrations and apply them to the database (the project is
   intentionally delivered **without** generated migrations so that you can
   create them yourself):

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. Create a superuser (required to activate tenants through Django Admin):

   ```bash
   python manage.py createsuperuser
   ```

   The command will ask for an email address and password (authentication uses
   the email address rather than a username).

5. Start the development server:

   ```bash
   python manage.py runserver
   ```

6. Open:
   - Public website: http://localhost:8000/
   - Login: http://localhost:8000/conta/login/
   - New tenant registration: http://localhost:8000/conta/cadastro/
   - Django Admin (tenant activation): http://localhost:8000/admin/

## Suggested manual testing flow

1. Open `/conta/cadastro/` and register a new company (tenant) and its
   administrator user.
2. The activation email is printed in the **console** where `runserver` is
   running (the email backend is configured as `console` in development).
   Copy the link and open it to activate the user account.
3. Sign in to Django Admin with the superuser created in step 4 above, open
   **Tenants**, and activate the newly created tenant (the "Activate selected
   tenants" action).
4. Return to `/conta/login/` and sign in with the registered email address and
   password.
5. From the dashboard, register companies (`Companies`) and products
   (`Products`), associate products with companies by specifying whether they
   buy or sell them, record sales (`Sales`), and review connection suggestions
   (`Suggestions`).

## Running the automated tests

```bash
python -m pytest
```

All models, views, and main business rules (multitenant isolation, account
activation, inventory replenishment forecast calculation, connection suggestion
generation, and sale registration side effects) have tests under
`<app>/tests/`.

## App structure

| App | Responsibility |
|---|---|
| `core` | Reusable mixins for multitenant isolation and permissions |
| `tenants` | `Tenant` model and activation through Django Admin |
| `accounts` | Custom user, email-based login, account activation, and employee management |
| `companies` | Customer company management |
| `products` | Product management and company-product buy/sell relationships |
| `sales` | Sales, sale items, and commission management |
| `suggestions` | Business connection suggestions between companies |
| `dashboard` | Main authenticated dashboard with indicators and alerts |
| `landing` | Public institutional website |

## Important notes

- The project uses the console `EMAIL_BACKEND` (activation emails are displayed
  in the terminal). Configure a real SMTP backend in `config/settings.py` for
  production.
- Development values for `DEBUG = True` and `SECRET_KEY` are stored in
  `settings.py`; replace both before any deployment.
- Docker was intentionally left out of this delivery, as defined in the PRD
  (it is planned only for the final sprints).
- Tailwind CSS is loaded through the CDN (Play CDN) to keep setup simple and
  avoid requiring Node/npm. A local Tailwind build can be added later without
  changing the template structure.
- `core.middlewares.SaaSDomainMiddleware` handles requests made through the
  `saas.raulcamargo.com.br` subdomain. When a request from that host does not
  already start with `/saas/`, the middleware prefixes its internal path with
  `/saas`, allowing the subdomain to reuse the same URL routes defined under
  the `/saas/` prefix without issuing a client-side redirect.
