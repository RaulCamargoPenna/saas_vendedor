import pytest

from tenants.models import Tenant


@pytest.mark.django_db
def test_tenant_is_created_inactive_by_default():
    tenant = Tenant.objects.create(name='Empresa Teste', cnpj='11.111.111/0001-11')
    assert tenant.is_active is False


@pytest.mark.django_db
def test_tenant_cnpj_must_be_unique():
    Tenant.objects.create(name='Empresa A', cnpj='22.222.222/0001-22')
    with pytest.raises(Exception):
        Tenant.objects.create(name='Empresa B', cnpj='22.222.222/0001-22')
