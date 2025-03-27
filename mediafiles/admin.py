from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import MediaFile

@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'file', 'uploaded_at')  # ฟิลด์ที่จะแสดงในรายการของแอดมิน
    search_fields = ('name',)  # กำหนดให้สามารถค้นหาได้จากฟิลด์ 'name'
    list_filter = ('uploaded_at',)  # เพิ่มตัวกรองวันที่อัปโหลด

    # Optional: ปรับการแสดงผลไฟล์ในแอดมินให้แสดงเป็นลิงก์หรือรูปภาพตัวอย่าง (ถ้าเป็นรูป)
    def file_preview(self, obj):
        if obj.file.name.endswith(('.jpg', '.jpeg', '.png')):
            return f'<img src="{obj.file.url}" width="100" height="100" />'
        return f'<a href="{obj.file.url}" download>{obj.file.name}</a>'
    file_preview.allow_tags = True
    file_preview.short_description = 'Preview'
