import json

from django.utils.safestring import mark_safe


def absolute_url(request, path, company):
    if company and company.website:
        return company.website.rstrip("/") + path
    return request.build_absolute_uri(path)


def organization_node(company, request):
    if not company.organization_ready():
        return None
    node = {
        "@type": "Organization",
        "@id": absolute_url(request, "/#organization", company),
        "name": company.legal_name,
        "url": company.website,
        "telephone": company.phone,
        "email": company.public_email,
        "areaServed": company.service_area,
        "description": company.about,
    }
    social = [link["url"] for link in company.social_links()]
    if social:
        node["sameAs"] = social
    if company.has_street_address:
        node["address"] = {
            "@type": "PostalAddress",
            "streetAddress": company.street_address,
            "addressLocality": company.city,
            "addressRegion": company.region,
            "postalCode": company.postal_code,
            "addressCountry": "US",
        }
    return node


def local_business_node(company, request):
    if not (company.organization_ready() and company.has_street_address):
        return None
    return {
        "@type": "LocalBusiness",
        "@id": absolute_url(request, "/#localbusiness", company),
        "name": company.legal_name,
        "url": company.website,
        "telephone": company.phone,
        "email": company.public_email,
        "image": company.website,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": company.street_address,
            "addressLocality": company.city,
            "addressRegion": company.region,
            "postalCode": company.postal_code,
            "addressCountry": "US",
        },
        "areaServed": company.service_area,
        "parentOrganization": {"@id": absolute_url(request, "/#organization", company)},
    }


def website_node(company, request):
    if not company.organization_ready():
        return None
    return {
        "@type": "WebSite",
        "@id": absolute_url(request, "/#website", company),
        "url": company.website,
        "name": company.legal_name,
        "publisher": {"@id": absolute_url(request, "/#organization", company)},
    }


def service_node(service, company, request):
    node = {
        "@type": "Service",
        "name": service.name,
        "description": service.short_description,
        "url": absolute_url(request, service.get_absolute_url(), company),
        "areaServed": {
            "@type": "City",
            "name": "New York",
        },
    }
    if company.organization_ready():
        node["provider"] = {"@id": absolute_url(request, "/#organization", company)}
    return node


def breadcrumb_node(crumbs, company, request):
    items = []
    for index, crumb in enumerate(crumbs, start=1):
        entry = {"@type": "ListItem", "position": index, "name": crumb["name"]}
        if crumb.get("url"):
            entry["item"] = absolute_url(request, crumb["url"], company)
        items.append(entry)
    return {"@type": "BreadcrumbList", "itemListElement": items}


def faq_node(faqs):
    if not faqs:
        return None
    return {
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": faq.question,
                "acceptedAnswer": {"@type": "Answer", "text": faq.answer},
            }
            for faq in faqs
        ],
    }


def graph(*nodes):
    present = [node for node in nodes if node]
    if not present:
        return None
    return {"@context": "https://schema.org", "@graph": present}


def render_json_ld(data):
    if not data:
        return ""
    payload = json.dumps(data, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')
