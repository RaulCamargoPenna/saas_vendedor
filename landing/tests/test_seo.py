from django.urls import reverse


def test_saas_landing_exposes_search_metadata(client):
    response = client.get(reverse('landing:home'))

    assert response.status_code == 200
    content = response.content.decode()
    assert '<link rel="canonical" href="https://saas.raulcamargo.com.br/"' in content
    assert '<meta name="robots" content="index, follow' in content
    assert '"@type": "SoftwareApplication"' in content
    assert '"@type": "FAQPage"' in content
    assert 'Perguntas frequentes' in content


def test_saas_exposes_robots_and_sitemap(client):
    robots = client.get(reverse('landing:robots'))
    sitemap = client.get(reverse('landing:sitemap'))

    assert robots.status_code == 200
    assert robots['Content-Type'].startswith('text/plain')
    assert 'Sitemap: https://saas.raulcamargo.com.br/sitemap.xml' in robots.content.decode()
    assert sitemap.status_code == 200
    assert sitemap['Content-Type'].startswith('application/xml')
    assert '<loc>https://saas.raulcamargo.com.br/</loc>' in sitemap.content.decode()


def test_saas_subdomain_routes_root_seo_files(client):
    response = client.get('/sitemap.xml', HTTP_HOST='saas.raulcamargo.com.br')

    assert response.status_code == 200
    assert '<loc>https://saas.raulcamargo.com.br/</loc>' in response.content.decode()


def test_account_pages_are_not_indexable(client):
    response = client.get(reverse('accounts:login'))

    assert response.status_code == 200
    assert '<meta name="robots" content="noindex, nofollow"' in response.content.decode()
