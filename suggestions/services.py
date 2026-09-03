"""Business logic that scans a tenant's CompanyProduct records to find
selling/buying pairs for the same product, creating ConnectionSuggestion
entries when a new opportunity is found (RF17/RF18).
"""
from products.models import CompanyProduct

from .models import ConnectionSuggestion


def generate_suggestions_for_tenant(tenant):
    """Create pending ConnectionSuggestion objects for every product a
    company sells that another company in the same tenant buys. Returns the
    list of newly created suggestions.
    """
    sellers = CompanyProduct.objects.filter(
        company__tenant=tenant,
        relation_type=CompanyProduct.RELATION_SELL,
    ).select_related('company', 'product')

    buyers = CompanyProduct.objects.filter(
        company__tenant=tenant,
        relation_type=CompanyProduct.RELATION_BUY,
    ).select_related('company', 'product')

    buyers_by_product = {}
    for buyer in buyers:
        buyers_by_product.setdefault(buyer.product_id, []).append(buyer.company)

    created = []
    for seller in sellers:
        for buying_company in buyers_by_product.get(seller.product_id, []):
            if buying_company.pk == seller.company_id:
                continue
            suggestion, was_created = ConnectionSuggestion.objects.get_or_create(
                tenant=tenant,
                selling_company=seller.company,
                buying_company=buying_company,
                product=seller.product,
                defaults={'status': ConnectionSuggestion.STATUS_PENDING},
            )
            if was_created:
                created.append(suggestion)
    return created
