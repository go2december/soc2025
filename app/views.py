from django.shortcuts import render
from mediafiles.models import MediaFile

# Create your views here.
def landing_page(request):
    logo = MediaFile.objects.get(name='social_logo')  # ดึงข้อมูลรูปภาพโลโก้
    logo_text = MediaFile.objects.get(name='social_logo_text')  # ดึงข้อมูลรูปภาพข้อความโลโก้
    return render(request, 'index.html', {'logo': logo, 'logo_text': logo_text}) 