from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


class User(AbstractUser):
    """Custom user model for JWT authentication."""
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username


class Hostel(models.Model):
    """Represents a hostel building/block."""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Hostel"
        verbose_name_plural = "Hostels"

    def __str__(self):
        return self.name


class Room(models.Model):
    """Represents a room in a hostel."""
    room_number = models.CharField(max_length=50)
    floor = models.IntegerField()
    capacity = models.IntegerField()
    hostel = models.ForeignKey(
        Hostel,
        on_delete=models.CASCADE,
        related_name='rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('hostel', 'room_number')
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

    def __str__(self):
        return f"Room {self.room_number} - {self.hostel.name}"


class Asset(models.Model):
    """Represents an asset/item in a room."""
    CONDITION_CHOICES = (
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Poor', 'Poor'),
        ('Damaged', 'Damaged'),
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    asset_type = models.CharField(max_length=100)
    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='Good'
    )
    image = models.CharField(max_length=500, blank=True, null=True)
    quantity = models.IntegerField(default=0)
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='assets'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Asset"
        verbose_name_plural = "Assets"

    def __str__(self):
        return f"{self.name} - {self.asset_type} (Qty: {self.quantity})"


class MaintenanceRequest(models.Model):
    """Represents a maintenance request for an asset or room."""
    STATUS_CHOICES = (
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed'),
    )

    PRIORITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Open'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='Medium'
    )
    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='maintenance_requests',
        null=True,
        blank=True
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='maintenance_requests',
        null=True,
        blank=True
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='maintenance_requests_created',
        null=True,
        blank=True
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='maintenance_requests_assigned',
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Maintenance Request"
        verbose_name_plural = "Maintenance Requests"

    def __str__(self):
        return f"{self.title} - {self.status} ({self.priority})"
