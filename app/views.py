from django.shortcuts import render
from mediafiles.models import MediaFile
from .models import Slide


# Create your views here.
def landing_page(request):
    logo = MediaFile.objects.get(name="social_logo")  # ดึงข้อมูลรูปภาพโลโก้
    logo_text = MediaFile.objects.get(name="social_logo_text")  # ดึงข้อมูลรูปภาพข้อความโลโก้

    """ดึงข้อมูลสไลด์ที่เปิดใช้งานและเรียงลำดับ"""
    slides = Slide.objects.filter(is_active=True).order_by("order")

    return render(
        request, "index.html", {"logo": logo, "logo_text": logo_text, "slides": slides}
    )


def slide_list(request):
    """ดึงข้อมูลสไลด์ที่เปิดใช้งานและเรียงลำดับ"""
    slides = Slide.objects.filter(is_active=True).order_by("order")
    return render(request, "slide.html", {"slides": slides})
