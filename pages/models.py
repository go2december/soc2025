import os
import uuid
from django.db import models
from django.utils.text import slugify
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_delete
from django.conf import settings
from django.core.files.storage import default_storage
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


# Create your models here.
class Category(models.Model):
    """
    หมวดหมู่สำหรับจัดกลุ่มหน้าเนื้อหา
    """

    name = models.CharField(max_length=100, unique=True, verbose_name="ชื่อหมวดหมู่")
    slug = models.SlugField(
        max_length=100, unique=True, blank=True, verbose_name="Slug"
    )
    description = models.TextField(blank=True, null=True, verbose_name="คำอธิบาย")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไข")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="categories_created",
        null=True,
        verbose_name="ผู้สร้าง",
    )

    class Meta:
        verbose_name = "หมวดหมู่"
        verbose_name_plural = "หมวดหมู่"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("page_list_by_category", kwargs={"category_slug": self.slug})

    @property
    def published_pages_count(self):
        return self.pages.filter(is_published=True).count()


class Page(models.Model):
    """
    โมเดลสำหรับหน้าเนื้อหา
    """

    title = models.CharField(max_length=200, verbose_name="หัวเรื่อง")
    slug = models.SlugField(
        max_length=200, unique=True, blank=True, verbose_name="Slug"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pages",
        verbose_name="หมวดหมู่",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="pages_created",
        verbose_name="ผู้เขียน",
    )
    is_published = models.BooleanField(default=True, verbose_name="เผยแพร่")
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        null=True,
        verbose_name="คำอธิบายสำหรับ SEO",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไข")

    class Meta:
        verbose_name = "หน้า"
        verbose_name_plural = "หน้า"
        ordering = ["-created_at"]
        permissions = [
            ("can_publish_page", "สามารถเผยแพร่หน้าได้"),
            ("can_edit_page", "สามารถแก้ไขหน้าได้"),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("page_detail", kwargs={"page_slug": self.slug})

    @property
    def main_image(self):
        """รูปภาพหลักของหน้า (รูปแรกที่ถูกอัปโหลด)"""
        return self.images.first()


def get_upload_path(instance, filename):
    """
    สร้าง path สำหรับเก็บไฟล์
    โครงสร้าง: media/pages/<page_id>/<file_type>/<uuid>_<original_filename>.<ext>
    """
    ext = os.path.splitext(filename)[1].lower()
    original_filename = os.path.splitext(filename)[0]
    new_filename = f"{uuid.uuid4()}_{original_filename}{ext}"
    return f"pages/{instance.page.id}/{instance.file_type}/{new_filename}"


class ContentSection(models.Model):
    """
    เนื้อหาย่อยของหน้า
    """

    page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name="sections", verbose_name="หน้า"
    )
    title = models.CharField(
        max_length=200, blank=True, null=True, verbose_name="หัวเรื่องส่วน"
    )
    content = models.TextField(blank=True, null=True, verbose_name="เนื้อหา")
    order = models.PositiveIntegerField(default=0, verbose_name="ลำดับ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไข")
    images = models.ManyToManyField(
        "PageImage",
        blank=True,
        related_name="sections",
        verbose_name="รูปภาพประกอบส่วนเนื้อหา",
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "ส่วนเนื้อหา"
        verbose_name_plural = "ส่วนเนื้อหา"

    def __str__(self):
        return f"{self.page.title} - ส่วนที่ {self.order}"


class PageImage(models.Model):
    """
    รูปภาพที่เกี่ยวข้องกับหน้า
    """

    page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name="images", verbose_name="หน้า"
    )
    image = models.ImageField(
        upload_to=get_upload_path,
        verbose_name="รูปภาพ",
        help_text="รองรับไฟล์ .jpg, .png, .gif เท่านั้น",
    )
    original_filename = models.CharField(max_length=255, editable=False, blank=True, null=True)
    caption = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="คำบรรยายภาพ"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="ลำดับ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    file_type = models.CharField(
        max_length=50, default="image", editable=False, verbose_name="ประเภทไฟล์"
    )

    class Meta:
        verbose_name = "รูปภาพหน้า"
        verbose_name_plural = "รูปภาพหน้า"
        ordering = ["order"]

    def __str__(self):
        return f"ภาพสำหรับ {self.page.title} - {self.caption or 'ไม่มีคำบรรยาย'}"

    def save(self, *args, **kwargs):
        # บันทึกชื่อไฟล์เดิมเมื่อสร้าง หรือ อัปเดตรูปภาพ
        if self.image and not self.original_filename:
            self.original_filename = os.path.basename(self.image.name)

        # ตรวจสอบว่ามีการเปลี่ยนแปลงไฟล์หรือไม่
        if self.pk:
            old_instance = PageImage.objects.get(pk=self.pk)
            if old_instance.image != self.image:
                self.delete_file(old_instance.image)

        self.file_type = "image"
        super().save(*args, **kwargs)

    def delete_file(self, file_field):
        """ลบไฟล์ออกจากระบบไฟล์"""
        if file_field and default_storage.exists(file_field.name):
            default_storage.delete(file_field.name)

    @property
    def filename(self):
        """ชื่อไฟล์ที่แสดง + นามสกลุ"""
        return os.path.basename(self.image.name)

    @property
    def display_name(self):
        """ชื่อไฟล์ที่แสดงใน UI"""
        if self.original_filename:
            return self.original_filename
        return os.path.basename(self.image.name)


class PageFile(models.Model):
    """
    ไฟล์แนบของหน้า (สำหรับดาวน์โหลด)
    """

    page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name="files", verbose_name="หน้า"
    )
    file = models.FileField(
        upload_to=get_upload_path,
        verbose_name="ไฟล์",
        help_text="รองรับไฟล์ .PDF, .DOCX, .XLSX เท่านั้น",
    )
    original_filename = models.CharField(max_length=255, editable=False, blank=True, null=True)
    title = models.CharField(
        max_length=200, verbose_name="ชื่อไฟล์", help_text="ชื่อไฟล์ที่จะแสดง"
    )
    description = models.TextField(blank=True, null=True, verbose_name="คำบรรยายไฟล์")
    download_count = models.PositiveIntegerField(
        default=0, verbose_name="จำนวนดาวน์โหลด"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="ลำดับ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    file_type = models.CharField(
        max_length=50, default="file", editable=False, verbose_name="ประเภทไฟล์"
    )

    class Meta:
        verbose_name = "ไฟล์ดาว์นโหลด"
        verbose_name_plural = "ไฟล์ดาว์นโหลด"
        ordering = ["order"]

    def __str__(self):
        return f"{self.page.title} - {self.title or 'ไม่มีชื่อไฟล์'}"

    def save(self, *args, **kwargs):
        # บันทึกชื่อไฟล์เดิมเมื่อสร้าง หรือ อัปเดตไฟล์
        if self.file and not self.original_filename:
            self.original_filename = os.path.basename(self.file.name)

        # ตรวจสอบว่ามีการเปลี่ยนแปลงไฟล์หรือไม่
        if self.pk:
            old_instance = PageFile.objects.get(pk=self.pk)
            if old_instance.file != self.file:
                self.delete_file(old_instance.file)

        self.file_type = "file"
        super().save(*args, **kwargs)

    def delete_file(self, file_field):
        """ลบไฟล์ออกจากระบบไฟล์"""
        if file_field and default_storage.exists(file_field.name):
            default_storage.delete(file_field.name)

    def get_file_extension(self):
        """ดึงนามสกุลไฟล์"""
        return os.path.splitext(self.file.name)[1][1:].lower()

    @property
    def filename(self):
        """ชื่อไฟล์ที่แสดง + นามสกุล"""
        return os.path.basename(self.file.name)

    @property
    def display_name(self):
        """ชื่อไฟล์ที่แสดงให้ผู้ใช้เห็น"""
        if self.original_filename:
            return self.original_filename
        return os.path.basename(self.file.name)

    def increment_download_count(self):
        """เพิ่มจำนวนดาวน์โหลดเมื่อมีการดาวน์โหลดไฟล์"""
        self.download_count += 1
        self.save(update_fields=["download_count"])


# Signal handlers to delete files when model instances are deleted


@receiver(pre_save, sender=PageImage)
def page_image_pre_save(sender, instance, **kwargs):
    """
    ตรวจสอบการเปลี่ยนไฟล์รูปก่อนบันทึก PageImage
    """
    if instance.pk:
        try:
            old_instance = PageImage.objects.get(pk=instance.pk)
            if old_instance.image != instance.image:
                old_instance.delete_file(old_instance.image)
        except PageImage.DoesNotExist:
            pass


@receiver(pre_save, sender=PageFile)
def page_file_pre_save(sender, instance, **kwargs):
    """
    ตรวจสอบการเปลี่ยนไฟล์ก่อนบันทึก PageFile
    """
    if instance.pk:
        try:
            old_instance = PageFile.objects.get(pk=instance.pk)
            if old_instance.file != instance.file:
                old_instance.delete_file(old_instance.file)
        except PageFile.DoesNotExist:
            pass


@receiver(post_delete, sender=PageImage)
def page_image_post_delete(sender, instance, **kwargs):
    """
    ลบไฟล์เมื่อ PageImage ถูกลบ
    """
    instance.delete_file(instance.image)


@receiver(post_delete, sender=PageFile)
def page_file_post_delete(sender, instance, **kwargs):
    """
    ลบไฟล์เมื่อ PageFile ถูกลบ
    """
    instance.delete_file(instance.file)


@receiver(post_delete, sender=Page)
def page_post_delete(sender, instance, **kwargs):
    """
    ลบไฟล์และรูปภาพที่เกี่ยวข้องเมื่อ Page ถูกลบ
    """
    # ลบรูปภาพที่เกี่ยวข้อง
    for image in instance.images.all():
        image.delete_file(image.image)

    # ลบไฟล์ที่เกี่ยวข้อง
    for file in instance.files.all():
        file.delete_file(file.file)
