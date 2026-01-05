from django.db import models
from django.core.validators import MinValueValidator

class HotelConfig(models.Model):
    hotel_name = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()

    def __str__(self):
        return self.hotel_name
    
class RoomType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    capacity = models.IntegerField(validators=[MinValueValidator(1)])

    def __str__(self):
        return self.name

class ExtraService(models.Model):    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    def __str__(self):
        return self.name