from django import forms

from .models import Company

INPUT_CLASSES = (
    'w-full rounded-md border border-zinc-200 px-3 py-2 text-sm '
    'focus:outline-none focus:ring-2 focus:ring-zinc-900'
)


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['cnpj', 'trade_name', 'legal_name', 'business_area', 'email', 'phone']
        widgets = {
            'cnpj': forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': '00.000.000/0000-00'}),
            'trade_name': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'legal_name': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'business_area': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASSES, "placeholder": "example@example.com"}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASSES, "placeholder": "11996523322"}),
        }

    def clean_cnpj(self):
        cnpj = self.cleaned_data['cnpj']
        cnpj = cnpj.replace("-", "").replace(".", "").replace("/", "")

        if len(cnpj) != 14:
            raise forms.ValidationError(
                'O CNPJ deve conter 14 dígitos.'
            )

        queryset = Company.objects.filter(cnpj=cnpj)

        # Na edição, ignora a própria empresa
        if self.instance.pk:
            if self.instance.cnpj != cnpj:
                raise forms.ValidationError(
                    'Não é possível fazer alteração no CNPJ da empresa.'
                )
            
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(
                'Já existe uma empresa cadastrada com este CNPJ.'
            )

        return cnpj