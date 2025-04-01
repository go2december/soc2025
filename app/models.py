import uuid
import os
from django.db import models
from django.utils.translation import gettext_lazy as _
from PIL import Image
from django.db.models.signals import post_delete
from django.dispatch import receiver


def get_slide_upload_path(instance, filename):
    """เปลี่ยนชื่อไฟล์รูปเป็น UUID"""
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("app/slides/", filename)


class Slide(models.Model):
    title = models.CharField(_("Title"), max_length=200, null=False, blank=False)
    description = models.TextField(_("Description"), blank=True, null=True)
    image = models.ImageField(
        _("Image"), upload_to=get_slide_upload_path, blank=True, null=False
    )
    link = models.URLField(_("Link"), max_length=200, blank=True, null=True)
    order = models.PositiveIntegerField(_("Order"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """ลดขนาดภาพก่อนบันทึก และลบรูปเก่าเมื่ออัปเดต"""
        try:
            old_instance = Slide.objects.get(pk=self.pk)
            if old_instance.image and old_instance.image != self.image:
                if os.path.isfile(old_instance.image.path):
                    os.remove(old_instance.image.path)
        except Slide.DoesNotExist:
            pass

        super().save(*args, **kwargs)

        # ตรวจสอบว่ามีรูปภาพหรือไม่
        if self.image:
            image_path = self.image.path
            with Image.open(image_path) as img:
                max_width = 1920  # กำหนดความกว้างสูงสุด 1920px 600px
                if img.width > max_width:
                    new_height = int((max_width / img.width) * img.height)
                    img = img.resize((max_width, new_height), Image.LANCZOS)
                    img.save(image_path, quality=85)  # ลดคุณภาพเพื่อประหยัดพื้นที่


# Signal เพื่อลบไฟล์ภาพเมื่อ Slide ถูกลบ
@receiver(post_delete, sender=Slide)
def delete_slide_image(sender, instance, **kwargs):
    """ลบไฟล์รูปภาพจริง ๆ เมื่อลบ Record"""
    if instance.image and os.path.isfile(instance.image.path):
        os.remove(instance.image.path)
