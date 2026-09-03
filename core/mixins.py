"""Reusable mixins shared across the project's apps."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class TenantQuerysetMixin(LoginRequiredMixin):
    """Restrict any ListView/DetailView/UpdateView/DeleteView queryset to the
    logged in user's tenant, guaranteeing multitenant data isolation.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(tenant=self.request.user.tenant)


class TenantCreateMixin:
    """Automatically stamp `tenant` and `user` on any object created through
    a CreateView, so every model keeps its ownership fields consistent.
    """

    def form_valid(self, form):
        form.instance.tenant = self.request.user.tenant
        form.instance.user = self.request.user
        return super().form_valid(form)


class TenantAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only allow access to tenant administrators."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_tenant_admin


class PermissionCodenameRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow access to tenant admins or users holding a specific permission
    codename registered on the `accounts.User` model.
    """

    permission_codename = None

    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_tenant_admin:
            return True
        return self.permission_codename in user.get_feature_permissions()
