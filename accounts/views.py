from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.generic import FormView, ListView, TemplateView, UpdateView

from core.mixins import TenantAdminRequiredMixin, PermissionCodenameRequiredMixin
from tenants.models import Tenant

from .forms import EmailLoginForm, EmployeeCreationForm, SignUpForm, EmployeeForm
from .signals import build_activation_link, send_activation_email
from .tokens import account_activation_token

User = get_user_model()

def demo_login(request):
    demo_user = User.objects.get(
        email='demo-user@saasvendedor.com.br'
    )

    login(request, demo_user, backend='django.contrib.auth.backends.ModelBackend',)

    return redirect('dashboard:home')

class SignUpView(FormView):
    """Public sign up: creates an inactive Tenant plus its admin user, and
    sends the activation e-mail to the new administrator.
    """

    template_name = 'accounts/signup.html'
    form_class = SignUpForm
    success_url = reverse_lazy('accounts:signup_done')

    @transaction.atomic
    def form_valid(self, form):
        data = form.cleaned_data
        tenant = Tenant.objects.create(
            name=data['tenant_name'],
            cnpj=data['tenant_cnpj'],
            is_active=False,
        )
        user = User.objects.create_user(
            email=data['email'],
            password=data['password1'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            tenant=tenant,
            is_tenant_admin=True,
            is_active=False,
        )
        activation_link = build_activation_link(self.request, user)
        send_activation_email(user, activation_link)
        return super().form_valid(form)


class SignUpDoneView(TemplateView):
    template_name = 'accounts/signup_done.html'


class ActivateAccountView(View):
    """Confirms the activation link sent by e-mail. Note the tenant itself
    still needs to be activated by the platform's superuser before the user
    can actually log in.
    """

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save(update_fields=['is_active'])
            messages.success(request, 'Conta ativada com sucesso. Assim que seu tenant for aprovado você poderá fazer login.')
        else:
            messages.error(request, 'Link de ativação inválido ou expirado.')
        return redirect('accounts:login')


class EmailLoginView(FormView):
    template_name = 'accounts/login.html'
    form_class = EmailLoginForm
    success_url = reverse_lazy('dashboard:home')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(self.request, email=email, password=password)

        if user is None:
            form.add_error(None, 'E-mail ou senha inválidos.')
            return self.form_invalid(form)

        if not user.is_active:
            form.add_error(None, 'Sua conta ainda não foi ativada. Verifique seu e-mail.')
            return self.form_invalid(form)

        if user.tenant_id and not user.tenant.is_active:
            form.add_error(None, 'O tenant da sua empresa ainda não foi ativado pela administração do sistema.')
            return self.form_invalid(form)

        login(self.request, user)
        return super().form_valid(form)


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('landing:home')

    def get(self, request):
        return self.post(request)


class EmployeeListView(TenantAdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/employee_list.html'
    context_object_name = 'employees'

    def get_queryset(self):
        return User.objects.filter(tenant=self.request.user.tenant).order_by('-created_at')


class EmployeeCreateView(TenantAdminRequiredMixin, FormView):
    template_name = 'accounts/employee_form.html'
    form_class = EmployeeCreationForm
    success_url = reverse_lazy('accounts:employee_list')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.tenant = self.request.user.tenant
        user.is_active = False
        user.set_unusable_password()
        user.feature_permissions = form.cleaned_data['feature_permissions']
        user.save()
        activation_link = build_activation_link(self.request, user)
        send_activation_email(user, activation_link)
        messages.success(self.request, f'Funcionário {user.email} cadastrado. Um e-mail de ativação foi enviado.')
        return super().form_valid(form)

class EmployeeUpdateView(PermissionCodenameRequiredMixin, UpdateView):
    model = User
    form_class = EmployeeForm
    template_name = 'accounts/employee_detail.html'
    permission_codename = 'manage_employees'

    def get_queryset(self):
        return User.objects.filter(
            tenant=self.request.user.tenant
        )

    def form_valid(self, form):
        response = super().form_valid(form)

        messages.success(
            self.request,
            'Funcionário atualizado com sucesso.'
        )

        return response

    def get_success_url(self):
        return reverse(
            'accounts:employee_update',
            kwargs={'pk': self.object.pk}
        )