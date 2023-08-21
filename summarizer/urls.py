from django.contrib import admin
from django.urls import path, include

from summarizer.auth_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('summarizer.extension_api.urls')),
    path('', include('summarizer.auth_app.urls')),
    path('index', views.render_index, name='home'),
]
