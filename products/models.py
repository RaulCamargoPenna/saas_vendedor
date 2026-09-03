import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Category(models.Model):
    """Product category, modeled as its own entity (instead of free text) to
    avoid duplicated categories caused by typos.
    """

    tenant = models.ForeignKey('tenants.Tenant', verbose_name='tenant', related_name='categories', on_delete=models.CASCADE)
    name = models.CharField('nome', max_length=150)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='cadastrado por', on_delete=models.PROTECT, related_name='categories_created')
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'name'], name='unique_category_name_per_tenant'),
        ]

    def __str__(self):
        return self.name


class Product(models.Model):
    tenant = models.ForeignKey('tenants.Tenant', verbose_name='tenant', related_name='products', on_delete=models.CASCADE)
    name = models.CharField('nome', max_length=255)
    category = models.ForeignKey(Category, verbose_name='categoria', related_name='products', on_delete=models.PROTECT)
    unit = models.CharField('unidade', max_length=50)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='cadastrado por', on_delete=models.PROTECT, related_name='products_created')
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'produto'
        verbose_name_plural = 'produtos'
        ordering = ['name']
        unique_together = ['tenant', 'name']

    def __str__(self):
        return self.name


class CompanyProduct(models.Model):
    """Links a Company to a Product, telling whether the company buys or
    sells it. When the relation is 'buy', the daily average consumption is
    used together with the quantity purchased last time to forecast stock
    replenishment alerts.
    """

    RELATION_BUY = 'buy'
    RELATION_SELL = 'sell'
    RELATION_TYPE_CHOICES = (
        (RELATION_BUY, 'Compra'),
        (RELATION_SELL, 'Venda'),
    )

    company = models.ForeignKey('companies.Company', verbose_name='empresa', related_name='company_products', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name='produto', related_name='company_products', on_delete=models.CASCADE)
    relation_type = models.CharField('tipo de relação', max_length=4, choices=RELATION_TYPE_CHOICES)
    daily_avg_consumption = models.DecimalField('consumo médio diário', max_digits=10, decimal_places=2, null=True, blank=True)
    last_purchase_quantity = models.DecimalField('quantidade da última compra', max_digits=10, decimal_places=2, null=True, blank=True)
    last_movement_date = models.DateField('última movimentação', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='cadastrado por', on_delete=models.PROTECT, related_name='company_products_created')
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'vínculo empresa-produto'
        verbose_name_plural = 'vínculos empresa-produto'
        constraints = [
            models.UniqueConstraint(fields=['company', 'product', 'relation_type'], name='unique_company_product_relation'),
        ]

    def __str__(self):
        return f'{self.company} - {self.product} ({self.get_relation_type_display()})'

    def clean(self):
        if self.relation_type == self.RELATION_BUY and not self.daily_avg_consumption:
            raise ValidationError({'daily_avg_consumption': 'Informe o consumo médio diário para produtos comprados.'})

    @property
    def estimated_depletion_date(self):
        """Estimated date the company will run out of stock, based on the
        quantity purchased last time and the daily average consumption.
        """
        if self.relation_type != self.RELATION_BUY:
            return None
        if not self.last_movement_date or not self.last_purchase_quantity or not self.daily_avg_consumption:
            return None
        if self.daily_avg_consumption <= 0:
            return None
        days_of_stock = int(self.last_purchase_quantity // self.daily_avg_consumption)
        return self.last_movement_date + datetime.timedelta(days=days_of_stock)

    def days_until_depletion(self, reference_date=None):
        depletion = self.estimated_depletion_date
        if not depletion:
            return None
        reference_date = reference_date or datetime.date.today()
        return (depletion - reference_date).days
