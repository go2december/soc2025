from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Tag, Article, ArticleImage, ArticleAttachment


# Register your models here.
class ArticleImageInline(admin.TabularInline):
    model = ArticleImage
    extra = 1
    fields = ("image", "caption", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: auto;" />', obj.image.url
            )
        return "-"

    preview.short_description = "Preview"


class ArticleAttachmentInline(admin.TabularInline):
    model = ArticleAttachment
    extra = 1
    fields = ("file", "name", "file_type", "download_link")
    readonly_fields = ("download_link",)

    def download_link(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">Download</a>', obj.file.url
            )
        return "-"

    download_link.short_description = "Link"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "article_count")
    serch_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def article_count(self, obj):
        return obj.articles.count()

    article_count.short_description = "จำนวนข่าว"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "article_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def article_count(self, obj):
        return obj.articles.count()

    article_count.short_description = "จำนวนข่าว"


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author_username", "status", "created_at")
    search_fields = ("title", "content")
    list_filter = ("status", "category", "tags", "publish_date")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "publish_date"
    filter_horizontal = ("tags",)
    ordering = ("-created_at",)
    inlines = [ArticleImageInline, ArticleAttachmentInline]
    readonly_fields = ("view_count", "cover_preview", "author_username")
    fieldsets = (
        (None, {"fields": ("title", "slug", "author_username", "category", "tags")}),
        (
            "เนื้อหา",
            {
                "fields": (
                    "content",
                    "excerpt",
                    "cover_image",
                    "cover_preview",
                )
            },
        ),
        (
            "การเผยแพร่",
            {
                "fields": (
                    "status",
                    "publish_date",
                    "view_count",
                )
            },
        ),
    )

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="width: 100px; height: auto;" />',
                obj.cover_image.url,
            )
        return "-"

    cover_preview.short_description = "ภาพปก"

    def view_count(self, obj):
        return obj.views

    view_count.short_description = "จำนวนการเข้าชม"

    def author_username(self, obj):
        return obj.author.username if obj.author else "-"

    author_username.short_description = "ผู้เขียน"
    author_username.admin_order_field = "author__username"

    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(ArticleImage)
class ArticleImageAdmin(admin.ModelAdmin):
    list_display = ("article", "image_preview", "caption")
    list_filter = ("article__category",)
    search_fields = ("article__title", "caption")
    readonly_fields = ("image_preview",)

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 100px; height: auto;" />', obj.image.url
            )
        return "-"

    image_preview.short_description = "Preview"


@admin.register(ArticleAttachment)
class ArticleAttachmentAdmin(admin.ModelAdmin):
    list_display = ("article", "file_name", "file_type", "download_link")
    list_filter = (
        "file_type",
        "article__category",
    )
    search_fields = ("article__title", "name")
    readonly_fields = ("download_link",)

    def file_name(self, obj):
        return obj.file.name.split("/")[-1]

    file_name.short_description = "ชื่อไฟล์"

    def download_link(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">Download</a>', obj.file.url
            )
        return "-"

    download_link.short_description = "ดาว์นโหลด"
