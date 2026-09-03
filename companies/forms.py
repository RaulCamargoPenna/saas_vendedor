from django import forms

from .models import Company

INPUT_CLASSES = (
    'w-full rounded-xl border border-zinc-200/80 bg-white/70 px-3.5 py-2.5 text-sm text-zinc-900 '
    'shadow-sm outline-none transition-all placeholder:text-zinc-400 focus:border-zinc-400 focus:bg-white focus:ring-4 focus:ring-zinc-900/5'
)


class CompanyForm(forms.ModelForm):
    def __init__(self, *args, tenant=None, **kwargs):
        self.tenant = tenant
        super().__init__(*args, **kwargs)
        
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

        if not self.tenant:
            raise forms.ValidationError(
                'Não foi possível identificar o tenant.'
            )

        queryset = Company.objects.filter(
            tenant = self.tenant,
            cnpj=cnpj,
        )

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