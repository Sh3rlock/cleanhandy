from django.contrib import admin

from apps.content.models import (
    Article,
    CaseStudy,
    FAQ,
    LocationPage,
    NewsletterSubscriber,
    Review,
    ServicePage,
    SolutionPage,
)


class FAQInline(admin.TabularInline):
    model = FAQ
    extra = 0
    fk_name = "service"


@admin.register(ServicePage)
class ServicePageAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "menu", "is_bookable", "is_active", "primary_keyword")
    list_filter = ("category", "menu", "is_bookable", "is_active")
    search_fields = ("name", "slug", "primary_keyword")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ("related_services", "locations", "solutions")
    inlines = [FAQInline]

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(slug="painting")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "related_services":
            kwargs["queryset"] = ServicePage.objects.exclude(slug="painting")
        return super().formfield_for_manytomany(db_field, request, **kwargs)


@admin.register(LocationPage)
class LocationPageAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SolutionPage)
class SolutionPageAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "service", "slug")
    list_filter = ("service",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "service", "location", "show_on_homepage", "order")
    list_filter = ("show_on_homepage", "service", "location")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("customer_label", "service", "borough", "is_published")
    list_filter = ("is_published", "borough", "service")


@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ("title", "service", "borough", "is_published")
    list_filter = ("is_published", "borough")


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "subscribed_at", "unsubscribed_at")
    list_filter = ("is_active",)
    search_fields = ("email",)
    readonly_fields = ("token", "subscribed_at")
