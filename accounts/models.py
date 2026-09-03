from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

FEATURE_PERMISSIONS = (
    ('manage_companies', 'Gerenciar empresas'),
    ('manage_products', 'Gerenciar produtos'),
    ('manage_sales', 'Gerenciar vendas'),
    ('manage_suggestions', 'Gerenciar sugestões de conexão'),
)


class CustomUserManager(BaseUserManager):
    """Manager that creates users identified by e-mail instead of username."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_tenant_admin', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário precisa ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário precisa ter is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model authenticated by e-mail, always bound to a tenant
    (except for the platform's own superusers, who manage tenant activation).
    """

    email = models.EmailField('e-mail', unique=True)
    first_name = models.CharField('nome', max_length=150, blank=True)
    last_name = models.CharField('sobrenome', max_length=150, blank=True)
    role = models.CharField('função', max_length=100, blank=True)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        verbose_name='tenant',
        related_name='users',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_tenant_admin = models.BooleanField('administrador do tenant', default=False)
    is_active = models.BooleanField('ativo', default=False)
    is_staff = models.BooleanField('equipe interna', default=False)
    feature_permissions = models.JSONField('permissões de funcionalidades', default=list, blank=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.email

    def get_short_name(self):
        return self.first_name or self.email

    def get_feature_permissions(self):
        return self.feature_permissions or []
