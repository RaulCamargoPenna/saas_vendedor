import datetime
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import models


class Sale(models.Model):
    """A sale intermediated by the tenant between a selling company and a
    buying company. `commission_percentage` is a percentage rate applied
    over `sale_value` to determine the commission the salesperson will
    receive (see `commission_amount`).
    """

    tenant = models.ForeignKey('tenants.Tenant', verbose_name='tenant', related_name='sales', on_delete=models.CASCADE)
    selling_company = models.ForeignKey('companies.Company', verbose_name='empresa vendedora', related_name='sales_as_seller', on_delete=models.PROTECT)
    buying_company = models.ForeignKey('companies.Company', verbose_name='empresa compradora', related_name='sales_as_buyer', on_delete=models.PROTECT)
    sale_value = models.DecimalField('valor da venda', max_digits=12, decimal_places=2)
    commission_percentage = models.DecimalField('comissão (%)', max_digits=5, decimal_places=2)
    sale_date = models.DateField('data da venda', default=datetime.date.today)
    payment_due_date = models.DateField('data limite para recebimento', null=True, blank=True)
    payment_confirmed = models.BooleanField('pagamento confirmado', default=False)
    payment_confirmed_at = models.DateTimeField('confirmado em', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='registrado por', on_delete=models.PROTECT, related_name='sales_created')
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'venda'
        verbose_name_plural = 'vendas'
        ordering = ['-sale_date', '-created_at']

    def __str__(self):
        return f'{self.selling_company} -> {self.buying_company}'

    @property
    def commission_amount(self):
        """Amount the salesperson will receive: sale value * commission %."""
        amount = self.sale_value * self.commission_percentage / Decimal('100')
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def is_payment_overdue(self):
        """True when the payment deadline has passed and it was not
        confirmed yet. Used to alert the whole tenant about pending
        commissions to collect.
        """
        if self.payment_confirmed or not self.payment_due_date:
            return False
        return self.payment_due_date < datetime.date.today()

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, verbose_name='venda', related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', verbose_name='produto', related_name='sale_items', on_delete=models.PROTECT)
    quantity = models.DecimalField('quantidade', max_digits=10, decimal_places=2)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='registrado por', on_delete=models.PROTECT, related_name='sale_items_created')
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'item de venda'
        verbose_name_plural = 'itens de venda'

    def __str__(self):
        return f'{self.product} x {self.quantity}'
