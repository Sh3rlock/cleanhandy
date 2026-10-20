from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.booking.models import PricingGuideRow
from apps.company.models import get_company
from apps.content.models import Article, CaseStudy, FAQ, LocationPage, Review, ServicePage, SolutionPage
from apps.content.schema import (
    absolute_url,
    breadcrumb_node,
    faq_node,
    graph,
    local_business_node,
    organization_node,
    render_json_ld,
    service_node,
    website_node,
)


def _seo(request, company, *, title, description, path, og_title="", og_description="", og_image="", noindex=False):
    canonical = absolute_url(request, path, company)
    return {
        "seo_title": title,
        "meta_description": description,
        "canonical_url": canonical,
        "og_title": og_title or title,
        "og_description": og_description or description,
        "og_image": og_image,
        "og_url": canonical,
        "noindex": noindex,
    }


def _model_seo(request, company, obj, fallback_title, fallback_description):
    return _seo(
        request,
        company,
        title=obj.seo_title or fallback_title,
        description=obj.meta_description or fallback_description,
        path=obj.public_path(),
        og_title=obj.og_title,
        og_description=obj.og_description,
        og_image=obj.og_image,
        noindex=obj.noindex,
    )


def _json(company, request, *extra):
    return render_json_ld(
        graph(
            organization_node(company, request),
            website_node(company, request),
            local_business_node(company, request),
            *extra,
        )
    )


def home(request):
    company = get_company()
    services = ServicePage.objects.filter(is_active=True)
    hubs = {service.slug: service for service in services}
    faqs = FAQ.objects.filter(show_on_homepage=True)
    areas = LocationPage.objects.all()
    crumbs = [{"name": "Home", "url": "/"}]
    context = {
        "hubs": hubs,
        "moving_hub": hubs.get("moving-services-nyc"),
        "cleaning_hub": hubs.get("move-in-out-cleaning-nyc"),
        "commercial_hub": hubs.get("commercial-cleaning-nyc"),
        "faqs": faqs,
        "areas": areas,
        "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request), faq_node(faqs)),
        **_seo(
            request,
            company,
            title="Moving & Cleaning Services NYC | TheCleanHandy",
            description="Professional moving, move-in and move-out cleaning, and commercial cleaning services in New York City. Get a personalized quote from TheCleanHandy.",
            path="/",
        ),
    }
    return render(request, "home.html", context)


def service_page(request, slug):
    company = get_company()
    service = get_object_or_404(ServicePage, slug=slug, is_active=True)
    faqs = service.faqs.all()
    section = {
        "moving": ("Moving", reverse("home") + "#moving"),
        "move_cleaning": ("Cleaning", reverse("home") + "#cleaning"),
        "commercial": ("Commercial", reverse("home") + "#commercial"),
        "additional": ("Additional services", reverse("service_page", kwargs={"slug": "additional-services"})),
    }.get(service.category, ("Services", "/"))
    crumbs = [
        {"name": "Home", "url": "/"},
        {"name": section[0], "url": section[1] if service.slug != "additional-services" else ""},
        {"name": service.name, "url": service.get_absolute_url()},
    ]
    if service.slug == "additional-services":
        crumbs = [{"name": "Home", "url": "/"}, {"name": service.name, "url": service.get_absolute_url()}]
    return render(
        request,
        "content/service.html",
        {
            "service": service,
            "faqs": faqs,
            "related_services": service.related_services.filter(is_active=True),
            "locations": service.locations.all(),
            "solutions": service.solutions.all(),
            "articles": service.articles.all(),
            "breadcrumbs": crumbs,
            "json_ld": _json(
                company,
                request,
                service_node(service, company, request),
                breadcrumb_node(crumbs, company, request),
                faq_node(faqs),
            ),
            **_model_seo(request, company, service, service.name, service.short_description[:160]),
        },
    )


def location_index(request):
    company = get_company()
    areas = LocationPage.objects.all()
    crumbs = [{"name": "Home", "url": "/"}, {"name": "Areas we serve", "url": "/areas/"}]
    return render(
        request,
        "content/location_index.html",
        {
            "areas": areas,
            "breadcrumbs": crumbs,
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request)),
            **_seo(
                request,
                company,
                title="Areas We Serve | TheCleanHandy",
                description="TheCleanHandy serves Manhattan, Brooklyn, Queens, the Bronx, Staten Island, Astoria, Long Island, and New Jersey.",
                path="/areas/",
            ),
        },
    )


def location_page(request, slug):
    company = get_company()
    area = get_object_or_404(LocationPage, slug=slug)
    faqs = area.faqs.all()
    crumbs = [
        {"name": "Home", "url": "/"},
        {"name": "Areas we serve", "url": "/areas/"},
        {"name": area.name, "url": area.get_absolute_url()},
    ]
    return render(
        request,
        "content/location.html",
        {
            "area": area,
            "area_region": "New Jersey" if area.slug == "new-jersey" else "Long Island" if area.slug == "long-island" else "New York City",
            "services": area.services.filter(is_active=True),
            "faqs": faqs,
            "breadcrumbs": crumbs,
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request), faq_node(faqs)),
            **_model_seo(request, company, area, f"Moving & Cleaning in {area.name} | TheCleanHandy", area.introduction[:160]),
        },
    )


def solution_page(request, slug):
    company = get_company()
    solution = get_object_or_404(SolutionPage, slug=slug)
    faqs = solution.faqs.all()
    crumbs = [{"name": "Home", "url": "/"}, {"name": solution.name, "url": solution.get_absolute_url()}]
    return render(
        request,
        "content/solution.html",
        {
            "solution": solution,
            "services": solution.services.filter(is_active=True),
            "faqs": faqs,
            "breadcrumbs": crumbs,
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request), faq_node(faqs)),
            **_model_seo(request, company, solution, f"{solution.name} | TheCleanHandy", solution.introduction[:160]),
        },
    )


def article_index(request):
    company = get_company()
    articles = Article.objects.select_related("service")
    crumbs = [{"name": "Home", "url": "/"}, {"name": "Resources", "url": "/resources/"}]
    return render(
        request,
        "content/article_index.html",
        {
            "articles": articles,
            "breadcrumbs": crumbs,
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request)),
            **_seo(
                request,
                company,
                title="Moving & Cleaning Guides | TheCleanHandy",
                description="Practical NYC guides for move-out cleaning, move-in cleaning, and office cleaning from TheCleanHandy.",
                path="/resources/",
            ),
        },
    )


def article_page(request, slug):
    company = get_company()
    article = get_object_or_404(Article.objects.select_related("service"), slug=slug)
    crumbs = [
        {"name": "Home", "url": "/"},
        {"name": "Resources", "url": "/resources/"},
        {"name": article.title, "url": article.get_absolute_url()},
    ]
    return render(
        request,
        "content/article.html",
        {
            "article": article,
            "breadcrumbs": crumbs,
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request)),
            **_model_seo(request, company, article, f"{article.title} | TheCleanHandy", article.introduction[:160]),
        },
    )


def about(request):
    company = get_company()
    crumbs = [{"name": "Home", "url": "/"}, {"name": "About", "url": "/about/"}]
    return render(
        request,
        "content/about.html",
        {
            "breadcrumbs": crumbs,
            "services": ServicePage.objects.filter(is_active=True, is_bookable=True).order_by("category", "name"),
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request)),
            **_seo(
                request,
                company,
                title="About TheCleanHandy | NYC Moving & Cleaning",
                description="TheCleanHandy is a New York City company for move-in and move-out cleaning, moving, and commercial cleaning.",
                path="/about/",
            ),
        },
    )


def pricing(request):
    company = get_company()
    rows = PricingGuideRow.objects.select_related("service")
    crumbs = [{"name": "Home", "url": "/"}, {"name": "Pricing", "url": "/pricing/"}]
    return render(
        request,
        "content/pricing.html",
        {
            "rows": rows,
            "breadcrumbs": crumbs,
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request)),
            **_seo(
                request,
                company,
                title="Cleaning Time Guide & Quotes | TheCleanHandy",
                description="See TheCleanHandy's published cleaning time guide by apartment size. Final prices are quoted after you describe the job.",
                path="/pricing/",
            ),
        },
    )


def faq_page(request):
    company = get_company()
    faqs = FAQ.objects.select_related("service", "location")
    crumbs = [{"name": "Home", "url": "/"}, {"name": "FAQ", "url": "/faq/"}]
    return render(
        request,
        "content/faq.html",
        {
            "faqs": faqs,
            "breadcrumbs": crumbs,
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request), faq_node(faqs)),
            **_seo(
                request,
                company,
                title="Moving & Cleaning FAQ | TheCleanHandy",
                description="Answers about NYC move-out cleaning, move-in cleaning, moving help, and commercial cleaning from TheCleanHandy.",
                path="/faq/",
            ),
        },
    )


def reviews_page(request):
    company = get_company()
    reviews = Review.objects.filter(is_published=True).select_related("service")
    crumbs = [{"name": "Home", "url": "/"}, {"name": "Reviews", "url": "/reviews/"}]
    return render(
        request,
        "content/reviews.html",
        {
            "reviews": reviews,
            "breadcrumbs": crumbs,
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request)),
            **_seo(
                request,
                company,
                title="Customer Stories | TheCleanHandy",
                description="Published stories from TheCleanHandy customers, with the job, the situation, and the result. No manufactured ratings.",
                path="/reviews/",
            ),
        },
    )


def our_work(request):
    company = get_company()
    studies = CaseStudy.objects.filter(is_published=True).select_related("service")
    crumbs = [{"name": "Home", "url": "/"}, {"name": "Our work", "url": "/our-work/"}]
    return render(
        request,
        "content/our_work.html",
        {
            "studies": studies,
            "breadcrumbs": crumbs,
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request)),
            **_seo(
                request,
                company,
                title="Our Work | TheCleanHandy",
                description="Case notes from TheCleanHandy moving, turnover, and commercial cleaning jobs in New York City.",
                path="/our-work/",
            ),
        },
    )


def contact(request):
    company = get_company()
    crumbs = [{"name": "Home", "url": "/"}, {"name": "Contact", "url": "/contact/"}]
    return render(
        request,
        "content/contact.html",
        {
            "breadcrumbs": crumbs,
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request)),
            **_seo(
                request,
                company,
                title="Contact TheCleanHandy | NYC Moving & Cleaning",
                description="Call, email, or request a quote from TheCleanHandy for moving, move-in/out cleaning, and commercial cleaning in NYC.",
                path="/contact/",
            ),
        },
    )


def terms(request):
    company = get_company()
    crumbs = [{"name": "Home", "url": "/"}, {"name": "Terms", "url": "/terms/"}]
    return render(
        request,
        "content/terms.html",
        {
            "breadcrumbs": crumbs,
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request)),
            **_seo(
                request,
                company,
                title="Terms and Conditions | TheCleanHandy",
                description="Terms for quotes, deposits, moving, cleaning, and related work from TheCleanHandy in New York City, Long Island, and New Jersey.",
                path="/terms/",
            ),
        },
    )


def privacy(request):
    company = get_company()
    crumbs = [{"name": "Home", "url": "/"}, {"name": "Privacy", "url": "/privacy/"}]
    return render(
        request,
        "content/privacy.html",
        {
            "breadcrumbs": crumbs,
            "json_ld": _json(company, request, breadcrumb_node(crumbs, company, request)),
            **_seo(
                request,
                company,
                title="Privacy Policy | TheCleanHandy",
                description="How TheCleanHandy collects and uses contact, property, quote, and payment information for moving and cleaning services.",
                path="/privacy/",
            ),
        },
    )


def robots(request):
    sitemap = request.build_absolute_uri("/sitemap.xml")
    body = "\n".join(
        [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin/",
            "Disallow: /account/",
            "Disallow: /get-a-quote/property/",
            "Disallow: /get-a-quote/contact/",
            "",
            f"Sitemap: {sitemap}",
            "",
        ]
    )
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


def llms_txt(request):
    company = get_company()
    lines = [
        f"# {company.legal_name}",
        "",
        f"> {company.about}",
        "",
        "## Company",
        f"- Name: {company.legal_name}",
        f"- Service area: {company.service_area}",
        f"- Phone: {company.phone}",
        f"- Email: {company.public_email}",
        f"- Website: {company.website}",
        f"- Headquarters city: {company.city}, {company.region} {company.postal_code}",
    ]
    if company.has_street_address:
        lines.append(f"- Street address: {company.street_address}")
    lines.append(f"- Hours: {company.hours or 'By appointment'}")
    for link in company.social_links():
        lines.append(f"- {link['label']}: {link['url']}")
    lines.extend(["", "## Services"])
    for service in ServicePage.objects.filter(is_active=True):
        url = absolute_url(request, service.get_absolute_url(), company)
        lines.append(f"- [{service.name}]({url}): {service.short_description}")
    lines.extend(["", "## Service areas"])
    for area in LocationPage.objects.all():
        url = absolute_url(request, area.get_absolute_url(), company)
        lines.append(f"- [{area.name}]({url}): {area.introduction}")
    lines.extend(
        [
            "",
            "## Legal",
            f"- [Terms and Conditions]({absolute_url(request, '/terms/', company)})",
            f"- [Privacy Policy]({absolute_url(request, '/privacy/', company)})",
            "",
            "## Frequently asked questions",
        ]
    )
    for faq in FAQ.objects.all():
        lines.append(f"### {faq.question}")
        lines.append(faq.answer)
        lines.append("")
    return HttpResponse("\n".join(lines).strip() + "\n", content_type="text/plain; charset=utf-8")


def page_not_found(request, exception):
    company = get_company()
    return render(
        request,
        "404.html",
        {
            **_seo(
                request,
                company,
                title="Page not found | TheCleanHandy",
                description="That page is not on TheCleanHandy.",
                path=request.path,
                noindex=True,
            )
        },
        status=404,
    )
