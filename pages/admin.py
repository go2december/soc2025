from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.models import Group
from .models import Category, Page, ContentSection, PageImage, PageFile


# Register your models here.
class ContentSectionInline(admin.TabularInline):
    model = ContentSection
    extra = 1
    fields = ("order", "title", "content", "images")
    ordering = ("order",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(page__author=request.user)
        return qs


class PageImageInline(admin.TabularInline):
    model = PageImage
    extra = 1
    fields = ("order", "image_preview", "image", "caption")
    readonly_fields = ("image_preview",)
    ordering = ("order",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(page__author=request.user)
        return qs

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.image.url,
            )
        return "-"

    image_preview.short_description = "Preview"


class PageFileInline(admin.TabularInline):
    model = PageFile
    extra = 1
    fields = ("order", "title", "file", "description")
    ordering = ("order",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(page__author=request.user)
        return qs


class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "page_count",
    )
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(page__author=request.user).distinct()
        return qs

    def page_count(self, obj):
        if not hasattr(obj, "page_count"):
            obj._page_count = obj.pages.count()
        return obj._page_count

    page_count.short_description = "จำนวนหน้า"

    def save_model(self, request, obj, form, change):
        if not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    readonly_fields = ("created_at", "updated_at", "author_display")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                )
            },
        ),
        (
            "ผู้สร้าง",
            {
                "fields": ("author_display",),
                "classes": ("collapse",),
            },
        ),
        (
            "วันที่",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def author_display(self, obj):
        if obj.created_by:
            return f"{obj.created_by.get_full_name()} ({obj.created_by.username})"
        return "-"

    author_display.short_description = "ผู้สร้าง"


class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "get_category", "author", "is_published", "created_at")
    list_filter = ("category", "is_published", "created_at")
    search_fields = (
        "title",
        "content_sections__content",
    )  # ค้นหาจากเนื้อหาใน ContentSection
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "author_display")
    inlines = [ContentSectionInline, PageImageInline, PageFileInline]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "is_published",
                )
            },
        ),
        (
            "ผู้เขียน",
            {
                "fields": ("author_display",),
                "classes": ("collapse",),
            },
        ),
        (
            "วันที่",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def get_category(self, obj):
        return obj.category.name if obj.category else "-"

    get_category.admin_order_field = "หมวดหมู่"

    get_category.short_description = "หมวดหมู่"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(author=request.user)
        return qs

    def author_display(self, obj):
        if obj.author:
            return f"{obj.author.get_full_name()} ({obj.author.author.username()})"
        return "-"

    author_display.short_description = "ผู้เขียน"

    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

    def get_list_filter(self, request):
        if request.user.is_superuser:
            return ("category", "is_published", "created_at", "author")
        return ("category", "is_published", "created_at")


class ContentSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "page", "order")
    list_filter = ("page",)
    search_fields = ("title", "content")
    ordering = ("page", "order")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(page__author=request.user)
        return qs


class PageImageAdmin(admin.ModelAdmin):
    list_display = ("page", "order", "caption")
    search_fields = ("page__category",)
    ordering = ("page", "order")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(page__author=request.user)
        return qs


class PageFileAdmin(admin.ModelAdmin):
    list_display = ("title", "page", "file", "file_type", "download_link")
    list_filter = ("page__category",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(page__author=request.user)
        return qs

    def file_type(self, obj):
        return obj.get_file_extension().upper()

    def download_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" download>ดาว์นโหลด</a>', obj.file.url)
        return "-"

    download_link.short_description = "ไฟล์"


# ยกเลิกการลงทะเบียน Group ถ้าไม่ต้องการให้แสดงใน Admin
admin.site.unregister(Group)

# ลงทะเบียนโมเดลที่ต้องการให้แสดงใน Admin
admin.site.register(Category, CategoryAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(ContentSection, ContentSectionAdmin)
admin.site.register(PageImage, PageImageAdmin)
admin.site.register(PageFile, PageFileAdmin)
