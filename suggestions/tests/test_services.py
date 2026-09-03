import pytest
from django.contrib.auth import get_user_model

from companies.models import Company
from products.models import Category, CompanyProduct, Product
from suggestions.models import ConnectionSuggestion
from suggestions.services import generate_suggestions_for_tenant
from tenants.models import Tenant

User = get_user_model()


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(name='Tenant Sugestões', cnpj='30.000.000/0001-01', is_active=True)


@pytest.fixture
def user(db, tenant):
    return User.objects.create_user(email='vendedor4@example.com', password='123', tenant=tenant, is_active=True, is_tenant_admin=True)


@pytest.fixture
def category(db, tenant, user):
    return Category.objects.create(tenant=tenant, name='Insumos', user=user)


@pytest.fixture
def product(db, tenant, user, category):
    return Product.objects.create(tenant=tenant, name='Matéria-prima', category=category, unit='ton', user=user)


@pytest.mark.django_db
def test_generates_suggestion_for_matching_seller_and_buyer(tenant, user, product):
    seller = Company.objects.create(tenant=tenant, cnpj='40.000.000/0001-01', trade_name='Vende Tudo', legal_name='Vende Tudo LTDA', business_area='Atacado', user=user)
    buyer = Company.objects.create(tenant=tenant, cnpj='40.000.000/0001-02', trade_name='Compra Tudo', legal_name='Compra Tudo LTDA', business_area='Varejo', user=user)

    CompanyProduct.objects.create(company=seller, product=product, relation_type=CompanyProduct.RELATION_SELL, user=user)
    CompanyProduct.objects.create(company=buyer, product=product, relation_type=CompanyProduct.RELATION_BUY, daily_avg_consumption=20, user=user)

    created = generate_suggestions_for_tenant(tenant)

    assert len(created) == 1
    assert ConnectionSuggestion.objects.filter(selling_company=seller, buying_company=buyer, product=product).exists()


@pytest.mark.django_db
def test_does_not_duplicate_existing_suggestions(tenant, user, product):
    seller = Company.objects.create(tenant=tenant, cnpj='50.000.000/0001-01', trade_name='Seller', legal_name='Seller LTDA', business_area='Atacado', user=user)
    buyer = Company.objects.create(tenant=tenant, cnpj='50.000.000/0001-02', trade_name='Buyer', legal_name='Buyer LTDA', business_area='Varejo', user=user)
    CompanyProduct.objects.create(company=seller, product=product, relation_type=CompanyProduct.RELATION_SELL, user=user)
    CompanyProduct.objects.create(company=buyer, product=product, relation_type=CompanyProduct.RELATION_BUY, daily_avg_consumption=10, user=user)

    generate_suggestions_for_tenant(tenant)
    second_run = generate_suggestions_for_tenant(tenant)

    assert second_run == []
    assert ConnectionSuggestion.objects.count() == 1
