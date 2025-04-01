from django.contrib import admin
from django.utils.html import format_html
from django_summernote.admin import SummernoteModelAdmin
from .models import Category, News, Event, Image


class ImageInline(admin.TabularInline):
    model = Image
    extra = 1  # จำนวนฟอร์มว่างที่จะแสดง
    fields = ("file_path", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        if obj.file_path:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;"/>'.format(
                    obj.file_path.url
                )
            )
        return "No Image"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(News)
class NewsAdmin(SummernoteModelAdmin):
    summernote_fields = ("content",)  # ระบุ field ที่ต้องใช้ Summernote
    list_display = ("title", "category", "published_at", "created_at", "updated_at")
    search_fields = ("title", "content")
    list_filter = ("category", "published_at")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ImageInline]


@admin.register(Event)
class EventAdmin(SummernoteModelAdmin):
    summernote_fields = ("description",)  # ระบุ field ที่ต้องใช้ Summernote
    list_display = (
        "title",
        "category",
        "start_date",
        "end_date",
        "location",
        "created_at",
        "updated_at",
    )
    search_fields = ("title", "description", "location")
    list_filter = ("category", "start_date")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [ImageInline]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("file_path", "news", "event", "created_at")
    list_filter = ("news", "event")
