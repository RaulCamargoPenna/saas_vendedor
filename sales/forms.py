import datetime

from django import forms
from django.forms import inlineformset_factory

from .models import Sale, SaleItem

INPUT_CLASSES = (
    'w-full rounded-md border border-zinc-200 px-3 py-2 text-sm '
    'focus:outline-none focus:ring-2 focus:ring-zinc-900'
)


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = [
            'selling_company', 'buying_company', 'sale_value', 'commission_percentage',
            'sale_date', 'payment_due_date',
        ]
        widgets = {
            'selling_company': forms.Select(attrs={'class': INPUT_CLASSES}),
            'buying_company': forms.Select(attrs={'class': INPUT_CLASSES}),
            'sale_value': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'step': '0.01'}),
            'commission_percentage': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'step': '0.01', 'placeholder': 'Ex.: 5.00'}),
            'sale_date': forms.DateInput(attrs={'class': INPUT_CLASSES, 'type': 'date'}),
            'payment_due_date': forms.DateInput(attrs={'class': INPUT_CLASSES, 'type': 'date'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            from companies.models import Company
            queryset = Company.objects.filter(tenant=tenant)
            self.fields['selling_company'].queryset = queryset
            self.fields['buying_company'].queryset = queryset
        if not self.is_bound and not self.initial.get('sale_date'):
            self.initial['sale_date'] = datetime.date.today()

    def clean(self):
        cleaned_data = super().clean()
        selling_company = cleaned_data.get('selling_company')
        buying_company = cleaned_data.get('buying_company')
        if selling_company and buying_company and selling_company == buying_company:
            raise forms.ValidationError('A empresa vendedora e a compradora não podem ser a mesma.')
        return cleaned_data


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['product', 'quantity']
        widgets = {
            'product': forms.Select(attrs={'class': INPUT_CLASSES}),
            'quantity': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'step': '0.01'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            from products.models import Product
            self.fields['product'].queryset = Product.objects.filter(tenant=tenant)


# `extra=3` gives the user a few empty rows to start with, and the "add
# product" button in the template clones new rows client-side (updating
# `items-TOTAL_FORMS`), so any number of products (N) can be added to a sale.
SaleItemFormSet = inlineformset_factory(
    Sale,
    SaleItem,
    form=SaleItemForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
