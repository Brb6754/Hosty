from django.contrib import admin
from django.urls import path, include
from hotelconfig.views import inicio, login_view, home , signup_view, initial_hotel_setup

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', inicio, name='inicio'),
    path('login/', login_view, name='login'),
    path('home/', home, name='home'),
    path('signup/', signup_view, name='signup'),
    path('initial_setup/', initial_hotel_setup, name='initial_setup'),
    path('', include('rooms.urls')),
]
