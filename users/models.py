import os
from django.db import models
from django.contrib.auth.models import AbstractUser  # สำหรับ Custom User Model
from datetime import date
from django.dispatch import receiver
from django.db.models.signals import (
    pre_delete,
    pre_save,
)  # สำหรับ Signal การลบ/เปลี่ยนรูปภาพ


# --- ฟังก์ชันสำหรับกำหนด path การเก็บรูปภาพของ CustomUser ---
def user_photo_upload_path(instance, filename):
    """กำหนด path การอัปโหลดรูปภาพโปรไฟล์ของผู้ใช้งาน"""
    extension = os.path.splitext(filename)[1]  # นามสกุลไฟล์ เช่น .jpg, .png
    # ใช้ PK (Primary Key) ของ User เป็นชื่อไฟล์เพื่อไม่ให้ชื่อซ้ำกัน
    if instance.pk:
        return f"photos/users/{instance.pk}{extension}"
    # กรณีที่เพิ่งสร้าง User และยังไม่มี PK, ใช้ email เป็นชื่อชั่วคราว
    # (ควรถูกเปลี่ยนเมื่อ User ถูกบันทึกและมี PK)
    return f'photos/users/temp_{instance.email.split("@")[0]}{extension}'


# --- 1. โครงสร้างองค์กรและตำแหน่ง (Shared Models) ---
# Models เหล่านี้เป็นข้อมูลหลักที่ทุกประเภทผู้ใช้งานอาจต้องอ้างอิงถึง


class Faculty(models.Model):
    FacultyID = models.AutoField(primary_key=True)
    FacultyName = models.CharField(max_length=255, unique=True, verbose_name="ชื่อคณะ")
    Description = models.TextField(blank=True, null=True, verbose_name="คำอธิบาย")

    class Meta:
        verbose_name = "คณะ"
        verbose_name_plural = "คณะ"

    def __str__(self):
        return self.FacultyName


class Department(models.Model):
    DepartmentID = models.AutoField(primary_key=True)
    Faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, verbose_name="คณะ")
    DepartmentName = models.CharField(max_length=255, verbose_name="ชื่อสาขาวิชา")
    Description = models.TextField(blank=True, null=True, verbose_name="คำอธิบาย")

    class Meta:
        verbose_name = "สาขาวิชา"
        verbose_name_plural = "สาขาวิชา"
        unique_together = ("Faculty", "DepartmentName")  # ห้ามชื่อสาขาซ้ำกันในคณะเดียวกัน

    def __str__(self):
        return f"{self.DepartmentName} ({self.Faculty.FacultyName})"


class GenericDepartmentPosition(models.Model):
    GenericDeptPosID = models.AutoField(primary_key=True)
    PositionName = models.CharField(
        max_length=255, unique=True, verbose_name="ชื่อตำแหน่งประจำสาขา/บทบาททั่วไป"
    )
    Description = models.TextField(blank=True, null=True, verbose_name="คำอธิบาย")

    class Meta:
        verbose_name = "ตำแหน่งประจำสาขา (ทั่วไป)"
        verbose_name_plural = "ตำแหน่งประจำสาขา (ทั่วไป)"

    def __str__(self):
        return self.PositionName


class AdministrativePosition(models.Model):
    AdminPosID = models.AutoField(primary_key=True)
    Faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="สังกัดคณะ (ถ้ามี)",
    )
    PositionName = models.CharField(max_length=255, verbose_name="ชื่อตำแหน่งทางผู้บริหาร")
    Description = models.TextField(blank=True, null=True, verbose_name="คำอธิบาย")

    class Meta:
        verbose_name = "ตำแหน่งทางผู้บริหาร"
        verbose_name_plural = "ตำแหน่งทางผู้บริหาร"
        unique_together = ("Faculty", "PositionName")  # ห้ามชื่อตำแหน่งซ้ำกันในคณะเดียวกัน

    def __str__(self):
        if self.Faculty:
            return f"{self.PositionName} ({self.Faculty.FacultyName})"
        return self.PositionName


class PersonnelType(models.Model):
    PersonnelTypeID = models.AutoField(primary_key=True)
    TypeName = models.CharField(
        max_length=50, unique=True, verbose_name="ชื่อประเภทบุคลากร"
    )
    Description = models.TextField(blank=True, null=True, verbose_name="คำอธิบาย")

    class Meta:
        verbose_name = "ประเภทบุคลากร"
        verbose_name_plural = "ประเภทบุคลากร"

    def __str__(self):
        return self.TypeName


# --- 2. Custom User Model (บัญชีผู้ใช้งานหลัก) ---
# CustomUser จะเก็บข้อมูลพื้นฐานที่ผู้ใช้ทุกคนมี รวมถึงประเภทผู้ใช้
class CustomUser(AbstractUser):
    # AbstractUser มี fields พื้นฐานของ User อยู่แล้ว เช่น:
    # username, email, first_name, last_name, password, is_staff, is_active, is_superuser, date_joined, last_login

    # เพิ่มฟิลด์สำหรับระบุประเภทผู้ใช้
    USER_TYPE_CHOICES = (
        ("STAFF", "บุคลากร"),
        ("STUDENT", "นักศึกษา"),
        ("SPEAKER", "วิทยากร"),
        ("OTHER", "อื่นๆ"),  # สำหรับ User ที่ไม่ได้จัดอยู่ใน 3 ประเภทหลัก
    )
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default="OTHER",
        verbose_name="ประเภทผู้ใช้",
    )

    # เพิ่มฟิลด์ข้อมูลส่วนตัวทั่วไปที่ผู้ใช้ทุกคนอาจมี
    Prefix = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="คำนำหน้าชื่อ"
    )
    EnglishFirstName = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ชื่อภาษาอังกฤษ"
    )
    EnglishLastName = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="นามสกุลภาษาอังกฤษ"
    )
    DateOfBirth = models.DateField(blank=True, null=True, verbose_name="วันเกิด")
    NationalID = models.CharField(
        max_length=13, unique=True, blank=True, null=True, verbose_name="เลขบัตรประชาชน"
    )
    Address = models.TextField(blank=True, null=True, verbose_name="ที่อยู่")
    PhoneNumber = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="เบอร์โทรศัพท์"
    )
    Photo = models.ImageField(
        upload_to=user_photo_upload_path,
        blank=True,
        null=True,
        verbose_name="รูปภาพประจำตัว",
    )

    class Meta:
        verbose_name = "ผู้ใช้งาน"
        verbose_name_plural = "ผู้ใช้งาน"

    def __str__(self):
        # ใช้ first_name, last_name จาก AbstractUser
        full_name = f"{self.Prefix or ''} {self.first_name} {self.last_name}".strip()
        if not full_name:  # ถ้าไม่มีชื่อ/นามสกุล ให้ใช้อีเมล
            return self.email
        return f"{full_name} ({self.get_user_type_display()})"


# --- Signals สำหรับจัดการรูปภาพของ CustomUser ---
# เมื่อมีการเปลี่ยนรูปภาพเก่าจะถูกลบออก
@receiver(pre_save, sender=CustomUser)
def auto_delete_photo_on_change(sender, instance, **kwargs):
    if not instance.pk:  # ถ้าเป็นการสร้างใหม่ ไม่ต้องทำอะไร
        return False

    try:
        # ดึงรูปภาพเก่าจากฐานข้อมูล
        old_photo = sender.objects.get(pk=instance.pk).Photo
    except sender.DoesNotExist:
        return False  # ถ้าหาไม่เจอ ก็ไม่ต้องทำอะไร

    new_photo = instance.Photo
    # ถ้ามีการเปลี่ยนรูปภาพ และไฟล์เก่ามีอยู่จริง ให้ลบไฟล์เก่า
    if old_photo and old_photo.url != new_photo.url:
        if os.path.isfile(old_photo.path):
            os.remove(old_photo.path)


# เมื่อ User ถูกลบ รูปภาพที่เกี่ยวข้องจะถูกลบออกด้วย
@receiver(pre_delete, sender=CustomUser)
def auto_delete_photo_on_delete(sender, instance, **kwargs):
    if instance.Photo:
        if os.path.isfile(instance.Photo.path):
            os.remove(instance.Photo.path)


# --- 3. Profile Models สำหรับแต่ละประเภทผู้ใช้ (One-to-One Link กับ CustomUser) ---


class PersonnelProfile(models.Model):
    User = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="personnel_profile",
        verbose_name="ผู้ใช้งาน",
    )
    StartDate = models.DateField(blank=True, null=True, verbose_name="วันที่เริ่มงาน")
    EmploymentStatus = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="สถานะการทำงาน"
    )  # เช่น "ทำงานอยู่", "ลาออก", "เกษียณ"

    # Foreign Keys ที่เกี่ยวข้องกับบุคลากร
    PersonnelType = models.ForeignKey(
        "PersonnelType",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="ประเภทบุคลากร",
    )
    Faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="สังกัดคณะ",
    )
    Department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="สังกัดสาขาวิชา",
    )
    GenericDepartmentPosition = models.ForeignKey(
        GenericDepartmentPosition,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="ตำแหน่งประจำสาขา/บทบาท",
    )
    AdministrativePosition = models.ForeignKey(
        AdministrativePosition,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="ตำแหน่งทางผู้บริหาร",
    )

    class Meta:
        verbose_name = "ข้อมูลบุคลากร"
        verbose_name_plural = "ข้อมูลบุคลากร"

    def __str__(self):
        return f"Profile: {self.User.first_name} {self.User.last_name} (บุคลากร)"


class StudentProfile(models.Model):
    User = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="student_profile",
        verbose_name="ผู้ใช้งาน",
    )
    StudentID = models.CharField(
        max_length=20, unique=True, blank=True, null=True, verbose_name="รหัสนักศึกษา"
    )
    Faculty = models.ForeignKey(
        Faculty, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="คณะ"
    )
    Department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="สาขาวิชา",
    )
    AdmissionYear = models.IntegerField(blank=True, null=True, verbose_name="ปีที่เข้าศึกษา")
    StudentStatus = models.CharField(
        max_length=50, default="กำลังศึกษา", verbose_name="สถานะนักศึกษา"
    )  # เช่น กำลังศึกษา, สำเร็จการศึกษา, พักการเรียน

    class Meta:
        verbose_name = "ข้อมูลนักศึกษา"
        verbose_name_plural = "ข้อมูลนักศึกษา"

    def __str__(self):
        return f"Profile: {self.StudentID} - {self.User.first_name} {self.User.last_name} (นักศึกษา)"


class SpeakerProfile(models.Model):
    User = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="speaker_profile",
        verbose_name="ผู้ใช้งาน",
    )
    Organization = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="องค์กร/หน่วยงาน"
    )
    Bio = models.TextField(blank=True, null=True, verbose_name="ประวัติโดยย่อ")
    ExpertiseAreas = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="สาขาความเชี่ยวชาญ (คั่นด้วยคอมมา)",
    )  # เก็บเป็น String หรือเชื่อมกับ Expertise/Tag ถ้าต้องการละเอียด
    # สามารถเพิ่มฟิลด์อื่น ๆ เช่น ประวัติการบรรยาย, ค่าตอบแทน ฯลฯ

    class Meta:
        verbose_name = "ข้อมูลวิทยากร"
        verbose_name_plural = "ข้อมูลวิทยากร"

    def __str__(self):
        return f"Profile: {self.User.first_name} {self.User.last_name} (วิทยากร)"


# --- 4. ข้อมูลคุณสมบัติอื่นๆ (เชื่อมโยงกับ CustomUser) ---
# Models เหล่านี้เป็นข้อมูลที่ User ทุกประเภทสามารถมีได้


class Education(models.Model):
    EducationID = models.AutoField(primary_key=True)
    User = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="education_records",
        verbose_name="ผู้ใช้งาน",
    )
    DegreeLevel = models.CharField(
        max_length=100, verbose_name="ระดับการศึกษา"
    )  # เช่น ปริญญาตรี, โท, เอก
    Major = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="สาขาวิชา"
    )
    Institution = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="สถาบันการศึกษา"
    )
    Country = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="ประเทศ"
    )
    GraduationYear = models.IntegerField(
        blank=True, null=True, verbose_name="ปีที่จบการศึกษา"
    )

    class Meta:
        verbose_name = "การศึกษา"
        verbose_name_plural = "การศึกษา"

    def __str__(self):
        return (
            f"{self.DegreeLevel} ({self.Major or 'N/A'}) - {self.Institution or 'N/A'}"
        )


class AcademicPosition(models.Model):
    AcademicPositionID = models.AutoField(primary_key=True)
    User = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="academic_positions",
        verbose_name="ผู้ใช้งาน",
    )
    PositionName = models.CharField(
        max_length=100, verbose_name="ตำแหน่งทางวิชาการ"
    )  # เช่น ผู้ช่วยศาสตราจารย์, รองศาสตราจารย์
    EffectiveDate = models.DateField(verbose_name="วันที่มีผลบังคับใช้")
    EndDate = models.DateField(blank=True, null=True, verbose_name="วันที่สิ้นสุด")

    class Meta:
        verbose_name = "ตำแหน่งทางวิชาการ"
        verbose_name_plural = "ตำแหน่งทางวิชาการ"

    def __str__(self):
        return f"{self.PositionName} ({self.EffectiveDate.year})"


# --- 5. ความเชี่ยวชาญและระบบ Knowledge Management (KM) ---


class Expertise(models.Model):
    ExpertiseID = models.AutoField(primary_key=True)
    User = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="expertises",
        verbose_name="ผู้ใช้งาน",
    )
    ExpertiseArea = models.CharField(max_length=255, verbose_name="หัวข้อความเชี่ยวชาญ")
    ProficiencyLevel = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="ระดับความเชี่ยวชาญ"
    )  # เช่น Beginner, Intermediate, Advanced
    Description = models.TextField(blank=True, null=True, verbose_name="คำอธิบาย")

    class Meta:
        verbose_name = "ความเชี่ยวชาญ"
        verbose_name_plural = "ความเชี่ยวชาญ"

    def __str__(self):
        return self.ExpertiseArea


class Tag(models.Model):
    TagID = models.AutoField(primary_key=True)
    TagName = models.CharField(max_length=100, unique=True, verbose_name="ชื่อแท็ก")
    TagDescription = models.TextField(blank=True, null=True, verbose_name="คำอธิบายแท็ก")

    class Meta:
        verbose_name = "แท็ก"
        verbose_name_plural = "แท็ก"  # แก้ไขให้ถูกต้องตามหลักภาษาไทย

    def __str__(self):
        return self.TagName


class ExpertiseTag(models.Model):
    Expertise = models.ForeignKey(
        Expertise, on_delete=models.CASCADE, verbose_name="ความเชี่ยวชาญ"
    )
    Tag = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name="แท็ก")

    class Meta:
        unique_together = ("Expertise", "Tag")  # ห้ามซ้ำกันระหว่างความเชี่ยวชาญและแท็ก
        verbose_name = "ความเชี่ยวชาญกับแท็ก"
        verbose_name_plural = "ความเชี่ยวชาญกับแท็ก"  # แก้ไขให้ถูกต้องตามหลักภาษาไทย

    def __str__(self):
        return f"{self.Expertise.ExpertiseArea} - {self.Tag.TagName}"
