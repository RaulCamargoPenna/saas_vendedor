import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import DecimalField, ExpressionWrapper, F, Q, Sum
from django.views.generic import TemplateView

from companies.models import Company
from products.models import CompanyProduct
from sales.models import Sale
from suggestions.models import ConnectionSuggestion


ALERT_THRESHOLD_DAYS = 7


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_date_range(self):
        today = datetime.date.today()

        start_date_param = self.request.GET.get('start_date')
        end_date_param = self.request.GET.get('end_date')

        try:
            start_date = (
                datetime.date.fromisoformat(start_date_param)
                if start_date_param
                else today.replace(day=1)
            )
        except (TypeError, ValueError):
            start_date = today.replace(day=1)

        try:
            end_date = (
                datetime.date.fromisoformat(end_date_param)
                if end_date_param
                else today
            )
        except (TypeError, ValueError):
            end_date = today

        if start_date > end_date:
            start_date, end_date = end_date, start_date

        return start_date, end_date

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tenant = self.request.user.tenant
        today = datetime.date.today()

        start_date, end_date = self.get_date_range()
        end_datetime = end_date + datetime.timedelta(days=1)

        context['start_date'] = start_date
        context['end_date'] = end_date

        context['companies_count'] = Company.objects.filter(
            tenant=tenant,
            created_at__gte=start_date,
            created_at__lt=end_datetime,
        ).count()

        sales_period = Sale.objects.filter(
            tenant=tenant,
            sale_date__range=(start_date, end_date),
        )

        commission_expression = ExpressionWrapper(
            F('sale_value') * F('commission_percentage') / 100,
            output_field=DecimalField(
                max_digits=14,
                decimal_places=2,
            ),
        )

        sales_summary = sales_period.aggregate(
            total_sale_value=Sum('sale_value'),

            total_commission=Sum(
                commission_expression,
                filter=Q(payment_confirmed=True),
            ),

            total_pending_commission=Sum(
                commission_expression,
                filter=Q(payment_confirmed=False),
            ),
        )

        context['sales_period_count'] = sales_period.count()

        context['total_sale_value_period'] = float(
            sales_summary['total_sale_value'] or 0
        )

        context['total_commission_period'] = float(
            (sales_summary['total_commission']) or 0
        )

        context['total_pending_commission_period'] = float(
            sales_summary['total_pending_commission'] or 0
        )

        context['pending_suggestions_count'] = (
            ConnectionSuggestion.objects.filter(
                tenant=tenant,
                status=ConnectionSuggestion.STATUS_PENDING,
            ).count()
        )

        context['recent_suggestions'] = (
            ConnectionSuggestion.objects.filter(
                tenant=tenant,
                status=ConnectionSuggestion.STATUS_PENDING,
            )
            .select_related(
                'selling_company',
                'buying_company',
                'product',
            )
            .order_by('-created_at')[:5]
        )

        buy_relations = (
            CompanyProduct.objects.filter(
                company__tenant=tenant,
                relation_type=CompanyProduct.RELATION_BUY,
                last_movement_date__isnull=False,
                last_purchase_quantity__isnull=False,
                daily_avg_consumption__isnull=False,
            )
            .select_related('company', 'product')
        )

        stock_alerts = []

        for relation in buy_relations:
            days_left = relation.days_until_depletion()

            if (
                days_left is not None
                and days_left <= ALERT_THRESHOLD_DAYS
            ):
                stock_alerts.append({
                    'relation': relation,
                    'days_left': days_left,
                })

        stock_alerts.sort(
            key=lambda item: item['days_left']
        )

        context['stock_alerts'] = stock_alerts[:10]

        pending_payments = (
            Sale.objects.filter(
                tenant=tenant,
                payment_confirmed=False,
                payment_due_date__isnull=False,
                payment_due_date__lt=today,
            )
            .select_related(
                'selling_company',
                'buying_company',
            )
            .order_by('payment_due_date')
        )

        context['pending_payments'] = pending_payments[:10]
        context['pending_payments_count'] = pending_payments.count()

        return context