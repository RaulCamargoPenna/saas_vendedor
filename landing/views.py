from django.views.generic import TemplateView


class LandingHomeView(TemplateView):
    template_name = 'landing/home.html'
