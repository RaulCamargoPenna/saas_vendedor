"""Domain services triggered when a Sale is registered: updating the stock
replenishment reference (RF20 — last purchase date and quantity) and marking
related connection suggestions as converted.
"""


def apply_sale_side_effects(sale):
    from products.models import CompanyProduct
    from suggestions.models import ConnectionSuggestion

    for item in sale.items.all():
        CompanyProduct.objects.filter(
            company=sale.buying_company,
            product=item.product,
            relation_type=CompanyProduct.RELATION_BUY,
        ).update(
            last_movement_date=sale.sale_date,
            last_purchase_quantity=item.quantity,
        )

        ConnectionSuggestion.objects.filter(
            tenant=sale.tenant,
            selling_company=sale.selling_company,
            buying_company=sale.buying_company,
            product=item.product,
            status=ConnectionSuggestion.STATUS_PENDING,
        ).update(status=ConnectionSuggestion.STATUS_CONVERTED)
