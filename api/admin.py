from django.contrib import admin
from api.models import User, Hostel, Room, Asset


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'created_at']
    list_filter = ['created_at', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name']


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ['name', 'rooms_count', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']

    def rooms_count(self, obj):
        return obj.rooms.count()
    rooms_count.short_description = 'Number of Rooms'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'hostel', 'floor', 'capacity', 'assets_count', 'created_at']
    list_filter = ['hostel', 'floor', 'created_at']
    search_fields = ['room_number', 'hostel__name']
    readonly_fields = ['created_at']

    def assets_count(self, obj):
        return obj.assets.count()
    assets_count.short_description = 'Number of Assets'


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'asset_type', 'condition', 'quantity', 'room', 'updated_at']
    list_filter = ['condition', 'asset_type', 'created_at', 'updated_at']
    search_fields = ['name', 'asset_type', 'room__room_number', 'room__hostel__name']
    readonly_fields = ['created_at', 'updated_at']
