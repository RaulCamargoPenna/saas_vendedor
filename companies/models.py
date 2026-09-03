from django.conf import settings
from django.db import models


class Company(models.Model):
    """A client company followed up by the tenant's sales team."""

    tenant = models.ForeignKey('tenants.Tenant', verbose_name='tenant', related_name='companies', on_delete=models.CASCADE)
    cnpj = models.CharField('CNPJ', max_length=14)
    trade_name = models.CharField('nome fantasia', max_length=255)
    legal_name = models.CharField('razão social', max_length=255)
    business_area = models.CharField('área de atuação', max_length=150)
    email = models.EmailField(null=True)
    phone = models.CharField(max_length=11, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='cadastrado por', on_delete=models.PROTECT, related_name='companies_created')
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'empresa'
        verbose_name_plural = 'empresas'
        ordering = ['trade_name']
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'cnpj'], name='unique_cnpj_per_tenant'),
        ]

    def __str__(self):
        return self.trade_name
