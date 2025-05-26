from django.urls import path
from .views import ScrapePersonAPIView

urlpatterns = [
    path('scrape-person/', ScrapePersonAPIView.as_view(), name='scrape-person-api'),
]