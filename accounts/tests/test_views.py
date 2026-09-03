import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from tenants.models import Tenant

User = get_user_model()


@pytest.mark.django_db
def test_signup_creates_inactive_tenant_and_admin(client):
    url = reverse('accounts:signup')
    response = client.post(url, {
        'tenant_name': 'Minha Empresa',
        'tenant_cnpj': '44.444.444/0001-44',
        'first_name': 'Ana',
        'last_name': 'Silva',
        'email': 'ana@example.com',
        'password1': 'senha-super-forte',
        'password2': 'senha-super-forte',
    })
    assert response.status_code == 302
    tenant = Tenant.objects.get(cnpj='44.444.444/0001-44')
    assert tenant.is_active is False
    user = User.objects.get(email='ana@example.com')
    assert user.is_tenant_admin is True
    assert user.is_active is False


@pytest.mark.django_db
def test_login_blocked_for_inactive_tenant(client):
    tenant = Tenant.objects.create(name='Empresa Y', cnpj='55.555.555/0001-55', is_active=False)
    User.objects.create_user(email='user2@example.com', password='senha123', tenant=tenant, is_active=True)
    url = reverse('accounts:login')
    response = client.post(url, {'email': 'user2@example.com', 'password': 'senha123'})
    assert response.status_code == 200
    assert b'tenant' in response.content.lower() or b'ativado' in response.content.lower()


@pytest.mark.django_db
def test_login_success_for_active_user_and_tenant(client):
    tenant = Tenant.objects.create(name='Empresa Z', cnpj='66.666.666/0001-66', is_active=True)
    User.objects.create_user(email='user3@example.com', password='senha123', tenant=tenant, is_active=True)
    url = reverse('accounts:login')
    response = client.post(url, {'email': 'user3@example.com', 'password': 'senha123'})
    assert response.status_code == 302
