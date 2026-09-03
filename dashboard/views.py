import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from companies.models import Company
from products.models import CompanyProduct
from sales.models import Sale
from suggestions.models import ConnectionSuggestion

ALERT_THRESHOLD_DAYS = 7


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.request.user.tenant
        today = datetime.date.today()
        first_day_of_month = today.replace(day=1)

        context['companies_count'] = Company.objects.filter(tenant=tenant).count()

        sales_this_month = Sale.objects.filter(tenant=tenant, sale_date__gte=first_day_of_month)
        context['sales_this_month_count'] = len(sales_this_month)
        context['total_sale_value_month'] = sum((sale.sale_value for sale in sales_this_month), start=0)
        context['total_commission_month'] = sum((sale.commission_amount for sale in sales_this_month.filter(payment_confirmed=True)), start=0)
        context['total__pending_commission_month'] = sum((sale.commission_amount for sale in sales_this_month.filter(payment_confirmed=False)), start=0)

        context['pending_suggestions_count'] = ConnectionSuggestion.objects.filter(
            tenant=tenant, status=ConnectionSuggestion.STATUS_PENDING,
        ).count()

        # Alertas de reposição de estoque (RF16)
        buy_relations = CompanyProduct.objects.filter(
            company__tenant=tenant,
            relation_type=CompanyProduct.RELATION_BUY,
            last_movement_date__isnull=False,
            last_purchase_quantity__isnull=False,
            daily_avg_consumption__isnull=False,
        ).select_related('company', 'product')

        stock_alerts = []
        for relation in buy_relations:
            days_left = relation.days_until_depletion()
            if days_left is not None and days_left <= ALERT_THRESHOLD_DAYS:
                stock_alerts.append({'relation': relation, 'days_left': days_left})
        stock_alerts.sort(key=lambda item: item['days_left'])
        context['stock_alerts'] = stock_alerts[:10]

        context['recent_suggestions'] = ConnectionSuggestion.objects.filter(
            tenant=tenant, status=ConnectionSuggestion.STATUS_PENDING,
        ).select_related('selling_company', 'buying_company', 'product').order_by('-created_at')[:5]

        # Alertas de pagamento (comissão) pendente, visíveis a todo o tenant.
        pending_payments = Sale.objects.filter(
            tenant=tenant,
            payment_confirmed=False,
            payment_due_date__isnull=False,
            payment_due_date__lt=today,
        ).select_related('selling_company', 'buying_company').order_by('payment_due_date')
        context['pending_payments'] = pending_payments[:10]
        context['pending_payments_count'] = pending_payments.count()

        return context
