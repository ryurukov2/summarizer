from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.render_login, name='login'),
    path('login/google/', views.google_login, name='google_login'),
    path('api/login/google/', views.google_login_api, name='google_login_api'),
    path('google_logout/', views.google_logout, name='google_logout'),
]