from django.views.generic import TemplateView


class LandingHomeView(TemplateView):
    template_name = 'landing/home.html'


class RobotsView(TemplateView):
    template_name = 'landing/saas_robots.txt'
    content_type = 'text/plain'


class SitemapView(TemplateView):
    template_name = 'landing/saas_sitemap.xml'
    content_type = 'application/xml'
