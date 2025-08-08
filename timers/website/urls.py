from debug_toolbar.toolbar import debug_toolbar_urls  # pyright: ignore[reportMissingTypeStubs]
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("timers.urls")),
] + debug_toolbar_urls()
