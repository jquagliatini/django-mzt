from debug_toolbar.toolbar import (  # pyright: ignore[reportMissingTypeStubs]
    debug_toolbar_urls,
)
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("timers.urls")),
] + debug_toolbar_urls()
