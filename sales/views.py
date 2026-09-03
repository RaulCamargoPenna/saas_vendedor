from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView

from core.mixins import PermissionCodenameRequiredMixin, TenantQuerysetMixin

from .forms import SaleForm, SaleItemFormSet
from .models import Sale
from .services import apply_sale_side_effects


class SaleListView(TenantQuerysetMixin, ListView):
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().select_related('selling_company', 'buying_company')
        company_id = self.request.GET.get('company')
        if company_id:
            queryset = queryset.filter(selling_company_id=company_id) | queryset.filter(buying_company_id=company_id)
        return queryset


class SaleDetailView(TenantQuerysetMixin, DetailView):
    model = Sale
    template_name = 'sales/sale_detail.html'
    context_object_name = 'sale'


class SaleCreateView(PermissionCodenameRequiredMixin, View):
    permission_codename = 'manage_sales'
    template_name = 'sales/sale_form.html'
    success_url = reverse_lazy('sales:list')

    def get(self, request):
        form = SaleForm(tenant=request.user.tenant)
        formset = SaleItemFormSet(form_kwargs={'tenant': request.user.tenant})
        return render(request, self.template_name, {'form': form, 'formset': formset})

    def post(self, request):
        form = SaleForm(request.POST, tenant=request.user.tenant)
        formset = SaleItemFormSet(request.POST, form_kwargs={'tenant': request.user.tenant})
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                sale = form.save(commit=False)
                sale.tenant = request.user.tenant
                sale.user = request.user
                sale.save()
                formset.instance = sale
                items = formset.save(commit=False)
                for item in items:
                    item.user = request.user
                    item.save()
                for obj in formset.deleted_objects:
                    obj.delete()
                apply_sale_side_effects(sale)
            messages.success(request, 'Venda registrada com sucesso.')
            return redirect(self.success_url)
        return render(request, self.template_name, {'form': form, 'formset': formset})


class SalePaymentConfirmView(PermissionCodenameRequiredMixin, View):
    """Lets any user with sales permission confirm that a commission was
    paid. Since sales are only ever filtered by tenant (not by the user who
    registered them), every user in the tenant can see and act on pending
    payments — satisfying the requirement that payment alerts are visible
    tenant-wide, not just to whoever created the sale.
    """

    permission_codename = 'manage_sales'

    def post(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk, tenant=request.user.tenant)
        sale.payment_confirmed = True
        sale.payment_confirmed_at = timezone.now()
        sale.save(update_fields=['payment_confirmed', 'payment_confirmed_at'])
        messages.success(request, 'Pagamento confirmado.')
        return redirect('sales:detail', pk=sale.pk)
