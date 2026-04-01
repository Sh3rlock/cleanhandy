"""
SEO context builder for templates. Keeps meta/OG/Twitter/robots logic in one place.
"""
from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin

from django.conf import settings
from django.http import HttpRequest
from django.utils.html import strip_tags
from django.utils.text import Truncator
from django.utils.safestring import mark_safe

def strip_html_to_text(value: str, max_length: int = 320) -> str:
    if not value:
        return ""
    plain = strip_tags(value)
    plain = re.sub(r"\s+", " ", plain).strip()
    return Truncator(plain).chars(max_length)


def _absolute_url(request: HttpRequest, path_or_url: str) -> str:
    if not path_or_url:
        return ""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url
    base = getattr(settings, "SITE_URL", "").rstrip("/")
    if path_or_url.startswith("/"):
        return f"{base}{path_or_url}"
    return urljoin(base + "/", path_or_url)


def _default_og_image_absolute(request: HttpRequest) -> str:
    path = getattr(settings, "SEO_DEFAULT_OG_IMAGE", "") or ""
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    # static path e.g. /static/...
    return _absolute_url(request, path)


def _model_title(obj: Any) -> str:
    if obj is None:
        return ""
    for attr in ("seo_title", "title", "name"):
        v = getattr(obj, attr, None)
        if v:
            return str(v).strip()
    return ""


def _model_meta_description(obj: Any, fallback_content: str = "") -> str:
    if obj is None:
        return strip_html_to_text(fallback_content, 160)
    md = getattr(obj, "meta_description", None) or ""
    if md.strip():
        return md.strip()[:320]
    short = getattr(obj, "short_description", None) or ""
    if short and str(short).strip():
        return str(short).strip()[:320]
    content = getattr(obj, "description", None) or getattr(obj, "content", None) or fallback_content
    return strip_html_to_text(str(content or ""), 160)


def _merge_seo_field(page_row: Any, obj: Any, field: str):
    """Prefer object over site page row for overlapping SEO fields."""
    if obj is not None:
        v = getattr(obj, field, None)
        if v is not None and v != "":
            return v
    if page_row is not None:
        return getattr(page_row, field, None)
    return None


def build_seo_context(
    request: HttpRequest,
    *,
    page_key: str | None = None,
    obj: Any | None = None,
    fallback_title: str | None = None,
    fallback_description: str | None = None,
    fallback_content: str = "",
    force_noindex: bool = False,
    extra_json_ld: dict | list | None = None,
) -> dict[str, Any]:
    """
    Returns a dict with a single key 'seo' suitable for template context.
    """
    from seo.models import SitePageSEO

    page_row = None
    if page_key:
        try:
            page_row = SitePageSEO.objects.filter(page_key=page_key).first()
        except Exception:
            page_row = None

    site_name = getattr(settings, "SEO_SITE_NAME", "TheCleanHandy")
    title_suffix = getattr(settings, "SEO_TITLE_SUFFIX", "")
    default_desc = getattr(settings, "SEO_DEFAULT_META_DESCRIPTION", "")

    # Title
    raw_title = (
        (_merge_seo_field(page_row, obj, "seo_title") or "").strip()
        or fallback_title
        or _model_title(obj)
        or (page_row and getattr(page_row, "seo_title", None))
    )
    if not raw_title:
        raw_title = site_name

    full_title = raw_title
    if title_suffix and site_name and site_name not in raw_title and not raw_title.endswith(title_suffix.strip()):
        full_title = f"{raw_title}{title_suffix}"

    # Description
    meta_description = (
        (_merge_seo_field(page_row, obj, "meta_description") or "").strip()
        or fallback_description
        or _model_meta_description(obj, fallback_content)
        or (page_row and (page_row.meta_description or "").strip())
        or default_desc
    )
    meta_description = (meta_description or "")[:500]

    meta_keywords = (_merge_seo_field(page_row, obj, "meta_keywords") or "").strip()
    if page_row and not meta_keywords:
        meta_keywords = (page_row.meta_keywords or "").strip()

    # OG
    og_title = (_merge_seo_field(page_row, obj, "og_title") or "").strip() or raw_title
    og_description = (
        (_merge_seo_field(page_row, obj, "og_description") or "").strip()
        or meta_description
    )

    og_image_field = _merge_seo_field(page_row, obj, "og_image")
    og_image_url = ""
    if og_image_field:
        try:
            og_image_url = og_image_field.url
        except Exception:
            og_image_url = ""
    if not og_image_url:
        og_image_url = _default_og_image_absolute(request)

    # Robots
    ri = True
    rf = True
    if obj is not None:
        ri = getattr(obj, "robots_index", True)
        rf = getattr(obj, "robots_follow", True)
    elif page_row is not None:
        ri = page_row.robots_index
        rf = page_row.robots_follow

    if force_noindex:
        ri = False

    if ri and rf:
        robots_content = "index, follow"
    elif ri and not rf:
        robots_content = "index, nofollow"
    elif not ri and rf:
        robots_content = "noindex, follow"
    else:
        robots_content = "noindex, nofollow"

    # Canonical
    canonical = ""
    custom_canon = (_merge_seo_field(page_row, obj, "canonical_url") or "").strip()
    if custom_canon:
        canonical = custom_canon
    else:
        canonical = request.build_absolute_uri(request.path)

    schema_type = SEOSchemaType_value(obj, page_row)

    # Twitter
    twitter_card = getattr(settings, "SEO_TWITTER_CARD", "summary_large_image")

    og_type = "website"
    if obj is not None and obj.__class__.__name__ == "BlogPost":
        og_type = "article"

    seo_dict: dict[str, Any] = {
        "title": full_title,
        "meta_description": meta_description,
        "meta_keywords": meta_keywords,
        "og_title": og_title,
        "og_description": og_description,
        "og_image": og_image_url,
        "og_url": canonical,
        "og_type": og_type,
        "canonical_url": canonical,
        "robots": robots_content,
        "schema_type": schema_type,
        "twitter_card": twitter_card,
        "twitter_title": og_title,
        "twitter_description": og_description,
        "twitter_image": og_image_url,
        "json_ld_extra": extra_json_ld,
    }

    # JSON-LD graph built in template from seo + business settings
    seo_dict["json_ld"] = build_json_ld_bundle(
        request,
        seo_dict,
        obj=obj,
        page_key=page_key,
        extra=extra_json_ld,
    )
    seo_dict["json_ld_script"] = seo_json_ld_script(seo_dict)

    return {"seo": seo_dict}


def SEOSchemaType_value(obj: Any, page_row: Any) -> str:
    from seo.models import SEOSchemaType

    if obj is not None and getattr(obj, "schema_type", None):
        return obj.schema_type
    if page_row is not None:
        return page_row.schema_type or SEOSchemaType.WEB_PAGE
    return SEOSchemaType.WEB_PAGE


def build_json_ld_bundle(
    request: HttpRequest,
    seo: dict[str, Any],
    *,
    obj: Any | None = None,
    page_key: str | None = None,
    extra: dict | list | None = None,
) -> list[dict[str, Any]]:
    """Returns a list of JSON-LD objects for script type=application/ld+json."""
    from seo.models import SEOSchemaType

    graph: list[dict[str, Any]] = []
    base_url = getattr(settings, "SITE_URL", "").rstrip("/") or request.build_absolute_uri("/").rstrip("/")
    st = seo.get("schema_type") or SEOSchemaType.WEB_PAGE

    if st == SEOSchemaType.BLOG_POSTING and obj is not None:
        graph.append(_blog_posting_schema(request, obj, seo, base_url))
    elif st == SEOSchemaType.SERVICE and obj is not None:
        graph.append(_service_schema(obj, seo, base_url))
    elif st == SEOSchemaType.ARTICLE and obj is not None:
        graph.append(_article_schema(request, obj, seo, base_url))
    elif st == SEOSchemaType.LOCAL_BUSINESS:
        lb = _local_business_schema(base_url, seo)
        if lb:
            graph.append(lb)
    else:
        graph.append(
            {
                "@context": "https://schema.org",
                "@type": st if st in dict(SEOSchemaType.choices) else "WebPage",
                "name": seo.get("og_title") or seo.get("title"),
                "description": seo.get("meta_description"),
                "url": seo.get("canonical_url"),
            }
        )

    # Extra LocalBusiness for marketing pages without a dedicated model instance
    if page_key in {"home", "contact"}:
        lb = _local_business_schema(base_url, seo)
        if lb and not any(g.get("@type") == "LocalBusiness" for g in graph):
            graph.append(lb)

    if page_key == "faq":
        graph.append(
            {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "url": seo.get("canonical_url"),
            }
        )

    if isinstance(extra, dict):
        graph.append(extra)
    elif isinstance(extra, list):
        graph.extend(extra)

    return [g for g in graph if g]


def _local_business_schema(base_url: str, seo: dict[str, Any]) -> dict[str, Any] | None:
    name = getattr(settings, "SEO_BUSINESS_NAME", "") or getattr(settings, "SEO_SITE_NAME", "")
    if not name:
        return None
    data: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": name,
        "url": base_url,
        "description": seo.get("meta_description"),
    }
    phone = getattr(settings, "SEO_BUSINESS_PHONE", "")
    email = getattr(settings, "SEO_BUSINESS_EMAIL", "")
    if phone:
        data["telephone"] = phone
    if email:
        data["email"] = email
    logo = getattr(settings, "SEO_BUSINESS_LOGO_URL", "")
    if logo:
        if not logo.startswith("http"):
            logo = urljoin(base_url + "/", logo.lstrip("/"))
        data["image"] = logo
    street = getattr(settings, "SEO_BUSINESS_STREET", "")
    city = getattr(settings, "SEO_BUSINESS_CITY", "")
    region = getattr(settings, "SEO_BUSINESS_REGION", "")
    postal = getattr(settings, "SEO_BUSINESS_POSTAL", "")
    country = getattr(settings, "SEO_BUSINESS_COUNTRY", "")
    if any([street, city]):
        data["address"] = {
            "@type": "PostalAddress",
            "streetAddress": street or None,
            "addressLocality": city or None,
            "addressRegion": region or None,
            "postalCode": postal or None,
            "addressCountry": country or None,
        }
    return data


def _service_schema(obj: Any, seo: dict[str, Any], base_url: str) -> dict[str, Any]:
    name = getattr(obj, "name", None) or seo.get("og_title")
    desc = getattr(obj, "description", None) or seo.get("meta_description")
    out = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": name,
        "description": strip_html_to_text(str(desc or ""), 500),
        "url": seo.get("canonical_url"),
    }
    img = getattr(obj, "service_image", None)
    if img:
        try:
            out["image"] = _absolute_url_from_file(img, base_url)
        except Exception:
            pass
    return out


def _absolute_url_from_file(field_file, base_url: str) -> str:
    url = field_file.url
    if url.startswith("http"):
        return url
    return urljoin(base_url + "/", url.lstrip("/"))


def _blog_posting_schema(request: HttpRequest, post: Any, seo: dict[str, Any], base_url: str) -> dict[str, Any]:
    from django.urls import reverse

    url = seo.get("canonical_url")
    if not url and getattr(post, "slug", None):
        try:
            path = reverse("blog_detail", kwargs={"slug": post.slug})
        except Exception:
            path = "/blog/"
        url = request.build_absolute_uri(path)
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": getattr(post, "title", "") or seo.get("title"),
        "description": seo.get("meta_description"),
        "url": url,
        "datePublished": post.created_at.isoformat() if getattr(post, "created_at", None) else None,
    }
    if hasattr(post, "updated_at") and post.updated_at:
        data["dateModified"] = post.updated_at.isoformat()
    if getattr(post, "featured_image", None):
        try:
            data["image"] = _absolute_url_from_file(post.featured_image, base_url)
        except Exception:
            pass
    return data


def _article_schema(request: HttpRequest, obj: Any, seo: dict[str, Any], base_url: str) -> dict[str, Any]:
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": getattr(obj, "title", None) or seo.get("title"),
        "description": seo.get("meta_description"),
        "url": seo.get("canonical_url"),
    }
    if getattr(obj, "created_at", None):
        data["datePublished"] = obj.created_at.isoformat()
    return data


def seo_json_ld_script(seo: dict[str, Any]) -> str:
    """Safe JSON-LD for embedding in templates."""
    graph = seo.get("json_ld") or []
    if not graph:
        return ""
    payload = {"@context": "https://schema.org", "@graph": graph}
    return mark_safe(json.dumps(payload, ensure_ascii=False))
