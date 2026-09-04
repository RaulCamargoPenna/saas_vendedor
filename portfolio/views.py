from django.views.generic import TemplateView

from .models import Projects


class LandingHomeView(TemplateView):
    template_name = 'landing/portfolio.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['projects'] = Projects.objects.all().order_by("-id")

        return context