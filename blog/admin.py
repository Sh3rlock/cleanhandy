from django.contrib import admin
from .models import BlogPost, Tag, Comment


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'robots_index', 'created_at', 'updated_at')
    list_filter = ('robots_index', 'robots_follow', 'created_at')
    search_fields = ('title', 'content', 'short_description', 'seo_title', 'meta_description')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'short_description', 'content', 'featured_image', 'tags'),
        }),
        ('SEO', {
            'fields': (
                'seo_title', 'meta_description', 'meta_keywords',
                'og_title', 'og_description', 'og_image',
                'canonical_url', 'robots_index', 'robots_follow', 'schema_type',
            ),
        }),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )


admin.site.register(Tag)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'post', 'created_at', 'is_approved')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('name', 'content')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Approve selected comments"
