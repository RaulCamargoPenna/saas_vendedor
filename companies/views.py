from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from django.db.models import ProtectedError
from django.shortcuts import redirect

from core.mixins import PermissionCodenameRequiredMixin, TenantCreateMixin, TenantQuerysetMixin

from .forms import CompanyForm
from .models import Company


class CompanyListView(TenantQuerysetMixin, ListView):
    model = Company
    template_name = 'companies/company_list.html'
    context_object_name = 'companies'
    paginate_by = 20


class CompanyDetailView(TenantQuerysetMixin, DetailView):
    model = Company
    template_name = 'companies/company_detail.html'
    context_object_name = 'company'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company_products'] = self.object.company_products.select_related('product')
        return context


class CompanyCreateView(PermissionCodenameRequiredMixin, TenantCreateMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = 'companies/company_form.html'
    success_url = reverse_lazy('companies:list')
    permission_codename = 'manage_companies'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Empresa cadastrada com sucesso.')
        return response


class CompanyUpdateView(PermissionCodenameRequiredMixin, TenantQuerysetMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'companies/company_form.html'
    success_url = reverse_lazy('companies:list')
    permission_codename = 'manage_companies'


class CompanyDeleteView(PermissionCodenameRequiredMixin, TenantQuerysetMixin, DeleteView):
    model = Company
    template_name = 'companies/company_confirm_delete.html'
    success_url = reverse_lazy('companies:list')
    permission_codename = 'manage_companies'
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            self.object.delete()
        except ProtectedError:
            messages.error(
                request,
                'Não é possível excluir esta empresa porque existem '
                'registros vinculados a ela.'
            )
            return redirect(
                'companies:detail',
                pk=self.object.pk
            )

        messages.success(
            request,
            'Empresa excluída com sucesso.'
        )
        return redirect(self.success_url)
