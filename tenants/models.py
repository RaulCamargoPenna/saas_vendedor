from django.db import models


class Tenant(models.Model):
    """A tenant represents a company subscribed to the SaaS platform.
    Every other entity in the system belongs to exactly one tenant.
    """

    name = models.CharField('nome', max_length=255)
    cnpj = models.CharField('CNPJ', max_length=18, unique=True)
    is_active = models.BooleanField('ativo', default=False)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'tenant'
        verbose_name_plural = 'tenants'
        ordering = ['-created_at']

    def __str__(self):
        return self.name
