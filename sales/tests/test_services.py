import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from companies.models import Company
from products.models import Category, CompanyProduct, Product
from sales.models import Sale, SaleItem
from sales.services import apply_sale_side_effects
from suggestions.models import ConnectionSuggestion
from tenants.models import Tenant

User = get_user_model()


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(name='Tenant Vendas', cnpj='20.000.000/0001-01', is_active=True)


@pytest.fixture
def user(db, tenant):
    return User.objects.create_user(email='vendedor3@example.com', password='123', tenant=tenant, is_active=True, is_tenant_admin=True)


@pytest.fixture
def seller_company(db, tenant, user):
    return Company.objects.create(tenant=tenant, cnpj='01.000.000/0001-01', trade_name='Fornecedora', legal_name='Fornecedora LTDA', business_area='Indústria', user=user)


@pytest.fixture
def buyer_company(db, tenant, user):
    return Company.objects.create(tenant=tenant, cnpj='02.000.000/0001-02', trade_name='Compradora', legal_name='Compradora LTDA', business_area='Comércio', user=user)


@pytest.fixture
def category(db, tenant, user):
    return Category.objects.create(tenant=tenant, name='Geral', user=user)


@pytest.fixture
def product(db, tenant, user, category):
    return Product.objects.create(tenant=tenant, name='Insumo', category=category, unit='kg', user=user)


@pytest.mark.django_db
def test_commission_amount_is_calculated_from_percentage(tenant, user, seller_company, buyer_company):
    sale = Sale.objects.create(
        tenant=tenant, selling_company=seller_company, buying_company=buyer_company,
        sale_value=Decimal('1000.00'), commission_percentage=Decimal('5.00'), user=user,
    )
    assert sale.commission_amount == Decimal('50.00')


@pytest.mark.django_db
def test_payment_is_overdue_when_due_date_passed_and_not_confirmed(tenant, user, seller_company, buyer_company):
    sale = Sale.objects.create(
        tenant=tenant, selling_company=seller_company, buying_company=buyer_company,
        sale_value=Decimal('500.00'), commission_percentage=Decimal('10.00'),
        payment_due_date=datetime.date.today() - datetime.timedelta(days=1), user=user,
    )
    assert sale.is_payment_overdue is True


@pytest.mark.django_db
def test_payment_is_not_overdue_when_confirmed(tenant, user, seller_company, buyer_company):
    sale = Sale.objects.create(
        tenant=tenant, selling_company=seller_company, buying_company=buyer_company,
        sale_value=Decimal('500.00'), commission_percentage=Decimal('10.00'),
        payment_due_date=datetime.date.today() - datetime.timedelta(days=1),
        payment_confirmed=True, user=user,
    )
    assert sale.is_payment_overdue is False


@pytest.mark.django_db
def test_sale_updates_last_purchase_quantity_and_movement_date(tenant, user, seller_company, buyer_company, product):
    CompanyProduct.objects.create(
        company=buyer_company,
        product=product,
        relation_type=CompanyProduct.RELATION_BUY,
        daily_avg_consumption=Decimal('2.00'),
        last_purchase_quantity=Decimal('5.00'),
        last_movement_date=datetime.date(2025, 1, 1),
        user=user,
    )
    sale_date = datetime.date(2026, 3, 10)
    sale = Sale.objects.create(
        tenant=tenant, selling_company=seller_company, buying_company=buyer_company,
        sale_value=Decimal('300.00'), commission_percentage=Decimal('5.00'), sale_date=sale_date, user=user,
    )
    SaleItem.objects.create(sale=sale, product=product, quantity=Decimal('10.00'), user=user)

    apply_sale_side_effects(sale)

    company_product = CompanyProduct.objects.get(company=buyer_company, product=product)
    assert company_product.last_movement_date == sale_date
    assert company_product.last_purchase_quantity == Decimal('10.00')


@pytest.mark.django_db
def test_sale_converts_matching_pending_suggestion(tenant, user, seller_company, buyer_company, product):
    suggestion = ConnectionSuggestion.objects.create(
        tenant=tenant,
        selling_company=seller_company,
        buying_company=buyer_company,
        product=product,
        status=ConnectionSuggestion.STATUS_PENDING,
    )
    sale = Sale.objects.create(
        tenant=tenant, selling_company=seller_company, buying_company=buyer_company,
        sale_value=Decimal('200.00'), commission_percentage=Decimal('5.00'), user=user,
    )
    SaleItem.objects.create(sale=sale, product=product, quantity=Decimal('5.00'), user=user)

    apply_sale_side_effects(sale)

    suggestion.refresh_from_db()
    assert suggestion.status == ConnectionSuggestion.STATUS_CONVERTED
