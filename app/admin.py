from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Slide
import os

class SlideAdmin(admin.ModelAdmin):
    list_display = ("title", "preview_image", "order", "is_active")  # แสดงตัวอย่างรูป
    list_editable = ("order", "is_active")  # ให้แก้ไขได้จากหน้า list
    search_fields = ("title",)  # ค้นหาด้วยชื่อ
    list_filter = ("is_active",)  # ตัวกรองสถานะ
    ordering = ("order",)  # เรียงตาม order

    fieldsets = (
        (
            _("Slide Information"),
            {"fields": ("title", "description", "image", "link", "order", "is_active")},
        ),
    )

    def preview_image(self, obj):
        """แสดงตัวอย่างภาพใน Django Admin"""
        if obj.image:
            return format_html(
                '<img src="{}" style="width:100px; height:auto;" />', obj.image.url
            )
        return "-"

    preview_image.short_description = _("Preview")

    def delete_model(self, request, obj):
        """ลบไฟล์ภาพออกจากเซิร์ฟเวอร์เมื่อกดลบ Slide"""
        if obj.image and os.path.isfile(obj.image.path):
            os.remove(obj.image.path)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        """ลบหลายรายการพร้อมกันและลบไฟล์ภาพ"""
        for obj in queryset:
            if obj.image and os.path.isfile(obj.image.path):
                os.remove(obj.image.path)
        super().delete_queryset(request, queryset)


admin.site.register(Slide, SlideAdmin)
