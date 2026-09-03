from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView

from core.mixins import PermissionCodenameRequiredMixin, TenantQuerysetMixin

from .models import ConnectionSuggestion
from .services import generate_suggestions_for_tenant


class ConnectionSuggestionListView(TenantQuerysetMixin, ListView):
    model = ConnectionSuggestion
    template_name = 'suggestions/suggestion_list.html'
    context_object_name = 'suggestions'

    def get_queryset(self):
        return super().get_queryset().filter(status=ConnectionSuggestion.STATUS_PENDING).select_related(
            'selling_company', 'buying_company', 'product',
        )


class ConnectionSuggestionRefreshView(PermissionCodenameRequiredMixin, View):
    permission_codename = 'manage_suggestions'

    def post(self, request):
        created = generate_suggestions_for_tenant(request.user.tenant)
        messages.success(request, f'{len(created)} nova(s) sugestão(ões) de conexão encontrada(s).')
        return redirect('suggestions:list')


class ConnectionSuggestionDiscardView(PermissionCodenameRequiredMixin, View):
    permission_codename = 'manage_suggestions'

    def post(self, request, pk):
        suggestion = get_object_or_404(ConnectionSuggestion, pk=pk, tenant=request.user.tenant)
        suggestion.status = ConnectionSuggestion.STATUS_DISCARDED
        suggestion.save(update_fields=['status'])
        messages.info(request, 'Sugestão descartada.')
        return redirect('suggestions:list')
