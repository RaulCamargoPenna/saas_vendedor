import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from companies.models import Company
from products.models import Category, CompanyProduct, Product
from tenants.models import Tenant

User = get_user_model()


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(name='Tenant Teste', cnpj='10.000.000/0001-01', is_active=True)


@pytest.fixture
def user(db, tenant):
    return User.objects.create_user(email='vendedor2@example.com', password='123', tenant=tenant, is_active=True, is_tenant_admin=True)


@pytest.fixture
def category(db, tenant, user):
    return Category.objects.create(tenant=tenant, name='Ferragens', user=user)


@pytest.fixture
def company(db, tenant, user):
    return Company.objects.create(tenant=tenant, cnpj='12.345.678/0001-99', trade_name='Cliente A', legal_name='Cliente A LTDA', business_area='Indústria', user=user)


@pytest.fixture
def product(db, tenant, user, category):
    return Product.objects.create(tenant=tenant, name='Parafuso', category=category, unit='caixa', user=user)


@pytest.mark.django_db
def test_category_name_unique_per_tenant(tenant, user):
    Category.objects.create(tenant=tenant, name='Insumos', user=user)
    with pytest.raises(IntegrityError):
        Category.objects.create(tenant=tenant, name='Insumos', user=user)


@pytest.mark.django_db
def test_buy_relation_requires_daily_avg_consumption(company, product, user):
    company_product = CompanyProduct(
        company=company,
        product=product,
        relation_type=CompanyProduct.RELATION_BUY,
        user=user,
    )
    with pytest.raises(ValidationError):
        company_product.full_clean()


@pytest.mark.django_db
def test_estimated_depletion_date_is_calculated_from_daily_consumption(company, product, user):
    company_product = CompanyProduct.objects.create(
        company=company,
        product=product,
        relation_type=CompanyProduct.RELATION_BUY,
        daily_avg_consumption=Decimal('2.00'),
        last_purchase_quantity=Decimal('30.00'),
        last_movement_date=datetime.date(2026, 1, 1),
        user=user,
    )
    # 30 units purchased / 2 units per day = 15 days of stock.
    assert company_product.estimated_depletion_date == datetime.date(2026, 1, 16)


@pytest.mark.django_db
def test_estimated_depletion_date_is_none_without_last_purchase_quantity(company, product, user):
    company_product = CompanyProduct.objects.create(
        company=company,
        product=product,
        relation_type=CompanyProduct.RELATION_BUY,
        daily_avg_consumption=Decimal('2.00'),
        last_movement_date=datetime.date(2026, 1, 1),
        user=user,
    )
    assert company_product.estimated_depletion_date is None


@pytest.mark.django_db
def test_sell_relation_has_no_depletion_date(company, product, user):
    company_product = CompanyProduct.objects.create(
        company=company,
        product=product,
        relation_type=CompanyProduct.RELATION_SELL,
        user=user,
    )
    assert company_product.estimated_depletion_date is None
