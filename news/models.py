import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.dispatch import receiver
from django.db.models.signals import pre_save, pre_delete


# Create your models here.
def get_file_upload_path(instance, filename):
    """สร้าง Path สำหรับการอัปโหลดไฟล์"""
    ext = filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"

    if isinstance(instance, Article):
        return os.path.join("news/covers", new_filename)
    elif isinstance(instance, ArticleImage):
        return os.path.join("news/images", new_filename)
    elif isinstance(instance, ArticleAttachment):
        return os.path.join("news/attachments", new_filename)
    return os.path.join("news", new_filename)


def delete_file_if_exists(file_path):
    """ลบไฟล์ถ้ามีอยู่ในระบบ"""
    if file_path and os.path.isfile(file_path):
        try:
            os.remove(file_path)
        except:
            pass


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="ชื่อหมวดหมู่")
    slug = models.SlugField(
        max_length=100, unique=True, blank=True, null=True, verbose_name="Slug"
    )
    description = models.TextField(blank=True, verbose_name="คำอธิบายหมวดหมู่")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไขล่าสุด")

    class Meta:
        verbose_name = "หมวดหมู่"
        verbose_name_plural = "หมวดหมู่ข่าว"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("news:category_detail", args={self.slug})


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="ชื่อแท็ก")
    slug = models.SlugField(
        max_length=100, unique=True, blank=True, null=True, verbose_name="Slug"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไขล่าสุด")

    class Meta:
        verbose_name = "แท็ก"
        verbose_name_plural = "แท็กข่าว"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Article(models.Model):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

    STATUS_CHOICES = [
        (DRAFT, "แบบร่าง"),
        (PUBLISHED, "เผยแพร่"),
        (ARCHIVED, "จัดเก็บ"),
    ]

    title = models.CharField(max_length=200, verbose_name="หัวข้อข่าว")
    slug = models.SlugField(
        max_length=200, unique_for_date="publish_date", verbose_name="Slug"
    )
    content = models.TextField(verbose_name="เนื้อหาข่าว")
    excerpt = models.TextField(blank=True, verbose_name="บทคัดย่อ")
    cover_image = models.ImageField(
        upload_to=get_file_upload_path, blank=True, null=True, verbose_name="ภาพปก"
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=DRAFT, verbose_name="สถานะ"
    )
    views = models.PositiveIntegerField(default=0, verbose_name="จำนวนการเข้าชม")
    publish_date = models.DateTimeField(default=timezone.now, verbose_name="วันที่เผยแพร่")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="วันที่แก้ไขล่าสุด")

    # relationships
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="news_articles",
        verbose_name="ผู้เขียน",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="articles",
        verbose_name="หมวดหมู่",
    )
    tags = models.ManyToManyField(
        Tag, blank=True, related_name="articles", verbose_name="แท็ก"
    )

    class Meta:
        verbose_name = "ข่าว"
        verbose_name_plural = "ข่าวทั้งหมด"
        ordering = ["-publish_date"]
        indexes = [models.Index(fields=["-publish_date"])]

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        """Override delete method to remove cover image file."""
        if self.cover_image:
            delete_file_if_exists(self.cover_image.path)

        # Remove all related images
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse(
            "news:article_detail",
            args=[
                self.publisth_date.year,
                self.publish_date.month,
                self.publish_date.day,
                self.slug,
            ],
        )


class ArticleImage(models.Model):
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="ข่าว",
    )
    image = models.ImageField(upload_to=get_file_upload_path, verbose_name="ภาพประกอบ")
    caption = models.CharField(max_length=255, blank=True, verbose_name="คำบรรยายภาพ")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")

    class Meta:
        verbose_name = "ภาพข่าว"
        verbose_name_plural = "ภาพข่าว"
        ordering = ["created_at"]

    def __str__(self):
        return f"ภาพประกอบสำหรับ {self.article.title}"

    def delete(self, *args, **kwargs):
        """Override delete method to remove image file."""
        if self.image:
            delete_file_if_exists(self.image.path)
        super().delete(*args, **kwargs)


class ArticleAttachment(models.Model):
    ARCICLE_FILE = "file"
    ARCICLE_VIDEO = "video"
    ARCTICLE_AUDIO = "audio"
    ARCTICLE_DOCUMENT = "document"

    ATTACHMENT_TYPE = [
        (ARCICLE_FILE, "ไฟล์"),
        (ARCICLE_VIDEO, "วิดีโอ"),
        (ARCTICLE_AUDIO, "เสียง"),
        (ARCTICLE_DOCUMENT, "เอกสาร"),
    ]

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name="ข่าว",
    )
    file = models.FileField(upload_to=get_file_upload_path, verbose_name="ไฟล์แนบ")
    name = models.CharField(max_length=255, blank=True, verbose_name="=ชื่อไฟล์")
    file_type = models.CharField(
        max_length=10,
        choices=ATTACHMENT_TYPE,
        default=ARCICLE_FILE,
        verbose_name="ประเภทไฟล์",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="วันที่สร้าง")

    class Meta:
        verbose_name = "ไฟล์แนบ"
        verbose_name_plural = "ไฟล์แนบ"
        ordering = ["created_at"]

    def __str__(self):
        return f"ไฟล์แนบสำหรับ {self.article.title}"

    def delete(self, *args, **kwargs):
        """Override delete method to remove file."""
        if self.file:
            delete_file_if_exists(self.file.path)
        super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.file.name.split("/")[-1]
        super().save(*args, **kwargs)


# ใช้ Django signals เพื่อจัดการการลบไฟล์เมื่อมีการอัปเดตหรือลบ record
@receiver(pre_delete, sender=Article)
def article_delete(sender, instance, **kwargs):
    """Signal สำหรับลบไฟล์เมื่อมีการลบ Article"""
    # ลบไฟล์ภาพปก
    if instance.cover_image:
        delete_file_if_exists(instance.cover_image.path)

    # ลบรูปที่เกี่ยวจข้อง
    for image in instance.images.all():
        image.delete()  # จะเรียกใช้ method delete ของ ArticleImage ซึ่งจะลบไฟล์ภาพด้วย

    # ลบไฟล์แนบที่เกียวข้อง
    for attachment in instance.attachments.all():
        attachment.delete()  # จะเรียกใช้ method delete ของ ArticleAttachment ซึ่งจะลบไฟล์แนบด้วย


@receiver(pre_save, sender=Article)
def article_update(sender, instance, **kwargs):
    """Signal สำหรับลบไฟล์เมื่อมีการอัปเดต Article"""
    # ตรวจสอบว่ามีการเปลี่ยนแปลง cover_image หรือไม่
    if not instance.pk:
        return False

    try:
        old_cover = Article.objects.get(pk=instance.pk).cover_image
    except Article.DoesNotExist:
        return False

    new_cover = instance.cover_image
    if old_cover and old_cover != new_cover:
        delete_file_if_exists(old_cover.path)


@receiver(pre_save, sender=ArticleImage)
def article_image_update(sender, instance, **kwargs):
    """Signal สำหรับลบไฟล์เมื่อมีการอัปเดต ArticleImage"""
    # ตรวจสอบว่ามีการเปลี่ยนแปลง image หรือไม่
    if not instance.pk:
        return False

    try:
        old_image = ArticleImage.objects.get(pk=instance.pk).image
    except ArticleImage.DoesNotExist:
        return False

    new_image = instance.image
    if old_image and old_image != new_image:
        delete_file_if_exists(old_image.path)


@receiver(pre_save, sender=ArticleAttachment)
def article_attachment_update(sender, instance, **kwargs):
    """Signal สำหรับลบไฟล์เมื่อมีการอัปเดต ArticleAttachment"""
    # ตรวจสอบว่ามีการเปลี่ยนแปลง file หรือไม่
    if not instance.pk:
        return False

    try:
        old_file = ArticleAttachment.objects.get(pk=instance.pk).file
    except ArticleAttachment.DoesNotExist:
        return False

    new_file = instance.file
    if old_file and old_file != new_file:
        delete_file_if_exists(old_file.path)
