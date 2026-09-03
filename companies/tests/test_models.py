import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from companies.models import Company
from tenants.models import Tenant

User = get_user_model()


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(name='Tenant Teste', cnpj='10.000.000/0001-00', is_active=True)


@pytest.fixture
def user(db, tenant):
    return User.objects.create_user(email='vendedor@example.com', password='123', tenant=tenant, is_active=True, is_tenant_admin=True)


@pytest.mark.django_db
def test_cnpj_unique_per_tenant(tenant, user):
    Company.objects.create(tenant=tenant, cnpj='99.999.999/0001-99', trade_name='A', legal_name='A LTDA', business_area='Varejo', user=user)
    with pytest.raises(IntegrityError):
        Company.objects.create(tenant=tenant, cnpj='99.999.999/0001-99', trade_name='B', legal_name='B LTDA', business_area='Varejo', user=user)
