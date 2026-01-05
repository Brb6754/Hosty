# hotelconfig/forms.py
from django import forms
from .models import HotelConfig , RoomType, ExtraService

class HotelConfigForm(forms.ModelForm):
    class Meta:
        model = HotelConfig
        fields = ['hotel_name', 'address', 'phone_number', 'email']

class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['name', 'description', 'capacity']

class ExtraServiceForm(forms.ModelForm):
    class Meta:
        model = ExtraService
        fields = ['name', 'description', 'price']