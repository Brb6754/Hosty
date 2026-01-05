from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User 
from hotelconfig.models import RoomType, ExtraService
from datetime import date

class Room(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    STATES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
        ('cleaning', 'Being Cleaned'),
    ]

    number = models.CharField(max_length=10) 
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    price_per_night = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    state = models.CharField(max_length=15, choices=STATES, default='available', db_index=True)

    class Meta:
        unique_together = ('user', 'number')

    def __str__(self):
        return f'Room {self.number} ({self.user.username})'
    
    def get_room_type_display(self):
        return self.room_type.name

class Guest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField() 
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

class Booking(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.PROTECT) 
    
    check_in_date = models.DateField(db_index=True)
    check_out_date = models.DateField(db_index=True)
    
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True, db_index=True)

    check_in_time = models.TimeField(null=True, blank=True)
    checked_in = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    def clean(self):
        super().clean()
        if self.check_in_date and self.check_out_date:
            if self.check_out_date <= self.check_in_date:
                raise ValidationError('Check-out date must be after check-in date')
            if self.check_in_date < date.today():
                raise ValidationError('Cannot create booking in the past')
    
    def __str__(self):
        return f'Reserva #{self.id} - {self.guest}'
    
    class Meta:
        indexes = [
            models.Index(fields=['check_in_date', 'check_out_date']),
            models.Index(fields=['is_active', 'check_in_date']),
        ]

class ServiceCharge(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='charges')
    service = models.ForeignKey(ExtraService, on_delete=models.PROTECT)
    quantity = models.IntegerField(default=1)
    charge_date = models.DateTimeField(auto_now_add=True)
    
    charged_amount = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    def __str__(self):
        return f'{self.service.name} x{self.quantity}'

class MaintenanceTask(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Critical'),
        (2, 'High'),
        (3, 'Medium'),
        (4, 'Low'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=3, db_index=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_priority_display()}: {self.description}"

class RoomServiceOrder(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    item = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.item} -> {self.room.number}"

class DNDSet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True) 
    room_number = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'room_number')

    def __str__(self):
        return f"DND: {self.room_number}"


class NotificationQueue(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    message = models.CharField(max_length=255)
    priority = models.CharField(max_length=20, default='Normal')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

class ActionLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"LOG: {self.action}"

class RoomWaitlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) 
    guest_name = models.CharField(max_length=100)
    room_type = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.guest_name} ({self.room_type})"