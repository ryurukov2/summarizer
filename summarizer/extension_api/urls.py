from django.urls import path
from . import views

urlpatterns = [
    path('submit-text/', views.submit_text, name='submit_text'),
    path('check-daily-usage/', views.check_daily_usage, name='check_daily_usage'),
    path('submit-text-adv/', views.submit_text_adv, name='submit_text_adv'),
    path('history/', views.SummaryListView.as_view(), name='summary history'),
    path('history/details/<int:pk>', views.SummaryDetailView.as_view(), name='summary detail'),
]
