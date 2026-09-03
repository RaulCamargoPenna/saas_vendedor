from django import forms
from django.contrib.auth import get_user_model

from tenants.models import Tenant
from .models import FEATURE_PERMISSIONS

User = get_user_model()

INPUT_CLASSES = (
    'w-full rounded-md border border-zinc-200 px-3 py-2 text-sm '
    'focus:outline-none focus:ring-2 focus:ring-zinc-900 '
    'placeholder:text-zinc-400'
)


class SignUpForm(forms.Form):
    """Public form to register a new tenant along with its admin user."""

    tenant_name = forms.CharField(
        label='Nome da empresa',
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES}),
    )
    tenant_cnpj = forms.CharField(
        label='CNPJ da empresa',
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': '00.000.000/0000-00'}),
    )
    first_name = forms.CharField(
        label='Seu nome',
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES}),
    )
    last_name = forms.CharField(
        label='Seu sobrenome',
        required=False,
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES}),
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASSES}),
    )
    password1 = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASSES}),
    )
    password2 = forms.CharField(
        label='Confirme a senha',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASSES}),
    )

    def clean_tenant_cnpj(self):
        cnpj = self.cleaned_data['tenant_cnpj']
        if Tenant.objects.filter(cnpj=cnpj).exists():
            raise forms.ValidationError('Já existe uma empresa cadastrada com este CNPJ.')
        return cnpj

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Já existe uma conta com este e-mail.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('As senhas informadas não coincidem.')
        return cleaned_data


class EmailLoginForm(forms.Form):
    """Login form authenticating by e-mail and password."""

    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': INPUT_CLASSES, 'autofocus': True}),
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': INPUT_CLASSES}),
    )


class EmployeeCreationForm(forms.ModelForm):
    """Form used by a tenant admin to register a new employee."""

    feature_permissions = forms.MultipleChoiceField(
        label='Permissões',
        choices=FEATURE_PERMISSIONS,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'role', 'feature_permissions']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'last_name': forms.TextInput(attrs={'class': INPUT_CLASSES}),
            'email': forms.EmailInput(attrs={'class': INPUT_CLASSES}),
            'role': forms.TextInput(attrs={'class': INPUT_CLASSES}),
        }
