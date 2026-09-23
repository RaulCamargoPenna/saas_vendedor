import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_portfolio_exposes_search_metadata(client):
    response = client.get(reverse('portfolio:home'))

    assert response.status_code == 200
    content = response.content.decode()
    assert '<link rel="canonical" href="https://raulcamargo.com.br/"' in content
    assert '<meta name="robots" content="index, follow' in content
    assert 'application/ld+json' in content
    assert 'Desenvolvedor Python e Django' in content


def test_portfolio_exposes_robots_and_sitemap(client):
    robots = client.get(reverse('portfolio:robots'))
    sitemap = client.get(reverse('portfolio:sitemap'))

    assert robots.status_code == 200
    assert robots['Content-Type'].startswith('text/plain')
    assert 'Sitemap: https://raulcamargo.com.br/sitemap.xml' in robots.content.decode()
    assert sitemap.status_code == 200
    assert sitemap['Content-Type'].startswith('application/xml')
    assert '<loc>https://raulcamargo.com.br/</loc>' in sitemap.content.decode()
