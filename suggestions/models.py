from django.db import models


class ConnectionSuggestion(models.Model):
    """Suggests a commercial connection between a company that sells a
    product and another that buys the same product, within the same tenant.
    """

    STATUS_PENDING = 'pending'
    STATUS_DISCARDED = 'discarded'
    STATUS_CONVERTED = 'converted'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pendente'),
        (STATUS_DISCARDED, 'Descartada'),
        (STATUS_CONVERTED, 'Convertida em venda'),
    )

    tenant = models.ForeignKey('tenants.Tenant', verbose_name='tenant', related_name='connection_suggestions', on_delete=models.CASCADE)
    selling_company = models.ForeignKey('companies.Company', verbose_name='empresa vendedora', related_name='suggestions_as_seller', on_delete=models.CASCADE)
    buying_company = models.ForeignKey('companies.Company', verbose_name='empresa compradora', related_name='suggestions_as_buyer', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', verbose_name='produto', related_name='connection_suggestions', on_delete=models.CASCADE)
    status = models.CharField('status', max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'sugestão de conexão'
        verbose_name_plural = 'sugestões de conexão'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['selling_company', 'buying_company', 'product'],
                name='unique_suggestion_per_pair_and_product',
            ),
        ]

    def __str__(self):
        return f'{self.selling_company} pode vender {self.product} para {self.buying_company}'
