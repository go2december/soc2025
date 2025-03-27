from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage

# Create your models here.
class MediaFile(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='mediafiles/')  # หรือใช้ ImageField หากเป็นไฟล์รูปภาพ
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):       
         
        # ตรวจสอบว่ามีการเปลี่ยนรูปภาพใหม่หรือไม่
        if self.pk:  # ถ้าโมเดลมีอยู่แล้ว (ไม่ใช่โมเดลใหม่)
            old_file = MediaFile.objects.get(pk=self.pk)  # ดึงโมเดลเดิม
            if old_file.file != self.file:  # ถ้ารูปภาพเปลี่ยน
                if old_file.file:  # ถ้ามีรูปภาพเดิม
                    default_storage.delete(old_file.file.name)  # ลบรูปภาพเดิม
        super().save(*args, **kwargs)  # บันทึกโมเดล
    
# สัญญาณสำหรับลบไฟล์เมื่อข้อมูลถูกลบ
@receiver(post_delete, sender=MediaFile)
def delete_file_on_record_delete(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)  # ลบไฟล์จริงในระบบไฟล์