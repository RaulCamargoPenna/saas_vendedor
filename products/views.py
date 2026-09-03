from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView
from django.db.models import ProtectedError
from django.shortcuts import redirect

from companies.models import Company
from core.mixins import PermissionCodenameRequiredMixin, TenantCreateMixin, TenantQuerysetMixin

from .forms import CategoryForm, CompanyProductForm, ProductForm
from .models import Category, CompanyProduct, Product


class CategoryListView(TenantQuerysetMixin, ListView):
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'


class CategoryCreateView(PermissionCodenameRequiredMixin, TenantCreateMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category_list')
    permission_codename = 'manage_products'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Categoria cadastrada com sucesso.')
        return response


class CategoryUpdateView(PermissionCodenameRequiredMixin, TenantQuerysetMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category_list')
    permission_codename = 'manage_products'


class CategoryDeleteView(PermissionCodenameRequiredMixin, TenantQuerysetMixin, DeleteView):
    model = Category
    template_name = 'products/category_confirm_delete.html'
    success_url = reverse_lazy('products:category_list')
    permission_codename = 'manage_products'
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            self.object.delete()
        except ProtectedError:
            messages.error(
                request,
                'Não é possível excluir esta categoria pois existem vínculos a ele.'
            )
            return redirect(
                'products:category_list',
            )

        messages.success(
            request,
            'Categoria excluída com sucesso.'
        )
        return redirect(self.success_url)


class ProductListView(TenantQuerysetMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related('category')


class ProductCreateView(PermissionCodenameRequiredMixin, TenantCreateMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:list')
    permission_codename = 'manage_products'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Produto cadastrado com sucesso.')
        return response


class ProductUpdateView(PermissionCodenameRequiredMixin, TenantQuerysetMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:list')
    permission_codename = 'manage_products'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs


class ProductDeleteView(PermissionCodenameRequiredMixin, TenantQuerysetMixin, DeleteView):
    model = Product
    template_name = 'products/product_confirm_delete.html'
    success_url = reverse_lazy('products:list')
    permission_codename = 'manage_products'
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        try:
            self.object.delete()
        except ProtectedError:
            messages.error(
                request,
                'Não é possível excluir este produto pois existem vínculos a ele.'
            )
            return redirect(
                'products:list',
            )

        messages.success(
            request,
            'Empresa excluída com sucesso.'
        )
        return redirect(self.success_url)


class CompanyProductCreateView(PermissionCodenameRequiredMixin, View):
    """Links a product to a company directly from the company's detail page."""

    permission_codename = 'manage_products'
    template_name = 'products/company_product_form.html'

    def get_company(self):
        return get_object_or_404(Company, pk=self.kwargs['company_pk'], tenant=self.request.user.tenant)

    def get(self, request, company_pk):
        company = self.get_company()
        form = CompanyProductForm(tenant=request.user.tenant)
        return render(request, self.template_name, {'company': company, 'form': form})

    def post(self, request, company_pk):
        company = self.get_company()
        form = CompanyProductForm(request.POST, tenant=request.user.tenant)
        if form.is_valid():
            company_product = form.save(commit=False)
            company_product.company = company
            company_product.user = request.user
            company_product.full_clean()
            company_product.save()
            messages.success(request, 'Produto vinculado à empresa com sucesso.')
            return redirect(reverse('companies:detail', kwargs={'pk': company.pk}))
        return render(request, self.template_name, {'company': company, 'form': form})
    
class CompanyProductUpdateView(PermissionCodenameRequiredMixin, UpdateView):
    model = CompanyProduct
    form_class = CompanyProductForm
    template_name = 'products/company_product_form.html'
    permission_codename = 'manage_products'

    def get_company(self):
        return get_object_or_404(
            Company,
            pk=self.kwargs['company_pk'],
            tenant=self.request.user.tenant
        )

    def get_object(self, queryset=None):
        return get_object_or_404(
            CompanyProduct,
            pk=self.kwargs['pk'],
            company=self.get_company()
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['tenant'] = self.request.user.tenant
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company'] = self.get_company()
        return context

    def form_valid(self, form):
        company = self.get_company()

        company_product = form.save(commit=False)
        company_product.company = company
        company_product.user = self.request.user
        company_product.full_clean()
        company_product.save()

        messages.success(
            self.request,
            'Produto atualizado com sucesso.'
        )

        return redirect(
            'companies:detail',
            pk=company.pk
        )

class CompanyProductDeleteView(PermissionCodenameRequiredMixin, DeleteView):
    model = CompanyProduct
    template_name = 'products/company_product_confirm_delete.html'
    permission_codename = 'manage_products'

    def get_queryset(self):
        return CompanyProduct.objects.filter(company__tenant=self.request.user.tenant)

    def get_success_url(self):
        return reverse('companies:detail', kwargs={'pk': self.object.company_id})
