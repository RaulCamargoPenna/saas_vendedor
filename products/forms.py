from django import forms

from .models import Category, CompanyProduct, Product

INPUT_CLASSES = (
    'w-full rounded-md border border-zinc-200 px-3 py-2 text-sm '
    'focus:outline-none focus:ring-2 focus:ring-zinc-900'
)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASSES}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'unit']
        widgets = {
            'name': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'category': forms.Select(attrs={'class': INPUT_CLASSES}),
            'unit': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'kg, unidade, litro...'}),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = tenant
        if tenant is not None:
            self.fields['category'].queryset = Category.objects.filter(tenant=tenant)

    def clean_name(self):
        name = self.cleaned_data['name']
        
        queryset = Product.objects.filter(tenant=self.tenant, name=name)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError(
                'Já existe um produto cadastrado com este nome.'
            )

        return name


class CompanyProductForm(forms.ModelForm):
    class Meta:
        model = CompanyProduct
        fields = ['product', 'relation_type', 'daily_avg_consumption', 'last_purchase_quantity', 'last_movement_date']
        widgets = {
            'product': forms.Select(attrs={'class': INPUT_CLASSES}),
            'relation_type': forms.Select(attrs={'class': INPUT_CLASSES}),
            'daily_avg_consumption': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'step': '0.01'}),
            'last_purchase_quantity': forms.NumberInput(attrs={'class': INPUT_CLASSES, 'step': '0.01'}),
            'last_movement_date': forms.DateInput(attrs={'class': INPUT_CLASSES, 'type': 'date'}, format='%Y-%m-%d'),
        }

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        if tenant is not None:
            self.fields['product'].queryset = Product.objects.filter(tenant=tenant)

    def clean(self):
        cleaned_data = super().clean()
        relation_type = cleaned_data.get('relation_type')
        daily_avg_consumption = cleaned_data.get('daily_avg_consumption')
        if relation_type == CompanyProduct.RELATION_BUY and not daily_avg_consumption:
            self.add_error('daily_avg_consumption', 'Obrigatório quando a empresa compra este produto.')
        return cleaned_data
