import pytest
from django.contrib.auth import get_user_model

from tenants.models import Tenant

User = get_user_model()


@pytest.mark.django_db
def test_create_user_with_email():
    tenant = Tenant.objects.create(name='Empresa X', cnpj='33.333.333/0001-33')
    user = User.objects.create_user(email='user@example.com', password='senha123', tenant=tenant)
    assert user.email == 'user@example.com'
    assert user.check_password('senha123')
    assert user.is_active is False


@pytest.mark.django_db
def test_create_superuser():
    admin = User.objects.create_superuser(email='admin@example.com', password='senha123')
    assert admin.is_staff is True
    assert admin.is_superuser is True
