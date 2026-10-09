from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
     path("admin/", admin.site.urls),
    path("", include("shop.urls")),
    # เสิร์ฟรูปที่อัปโหลด (ใช้ได้กับงานโชว์ ไม่เหมาะกับเว็บจริงที่คนใช้เยอะ)
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]

# เสิร์ฟรูปที่อัปโหลดตอนพัฒนา (DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
