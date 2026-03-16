from django.contrib import admin
from .models import Device, Session, Measure

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'mac_address', 'user', 'created_at')
    search_fields = ('name', 'mac_address', 'user__username')
    list_filter = ('created_at',)

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'device', 'is_active', 'start_time', 'calibration_base_bpm')
    search_fields = ('user__username', 'device__name')
    list_filter = ('is_active', 'start_time')

@admin.register(Measure)
class MeasureAdmin(admin.ModelAdmin):
    list_display = ('id', 'session', 'device_mac', 'bpm', 'base_bpm', 'is_lie', 'timestamp')
    search_fields = ('device_mac', 'session__id')
    list_filter = ('is_lie', 'timestamp')
