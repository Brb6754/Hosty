from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_room, name='add_room'),
    path('booking/create/', views.create_booking, name='create_booking'),
    path('today-checkins/', views.today_checkins, name='today_checkins'),
    path('checkin/process/', views.process_checkin, name='process_checkin'),
    path('bookings/api/today/', views.today_checkins, name='today_checkins'),
    path('rooms/checkin/process/', views.process_checkin, name='process_checkin'),
    path('add-room/', views.add_room, name='add_room'),
    path('create-booking/', views.create_booking, name='create_booking'),
    path('rooms/update-status/', views.update_room_status, name='update_room_status'),
    path('maintenance/api/pending/', views.get_pending_tasks, name='get_pending_tasks'),
    path('maintenance/add/', views.add_maintenance_task, name='add_maintenance_task'),
    path('maintenance/complete/', views.complete_maintenance_task, name='complete_maintenance_task'),
    path('service/api/heap/', views.get_room_service_heap, name='get_room_service_heap'),
    path('service/add/', views.add_service_order, name='add_service_order'),
    path('service/complete/', views.complete_service_order, name='complete_service_order'),
    path('dnd/api/set/', views.get_dnd_set, name='get_dnd_set'),
    path('dnd/toggle/', views.toggle_dnd_room, name='toggle_dnd_room'),
    path('notify/api/queue/', views.get_notification_queue, name='get_notification_queue'),
    path('notify/add/', views.add_notification, name='add_notification'),
    path('notify/pop/', views.pop_notification, name='pop_notification'),
    path('logs/api/', views.get_action_logs, name='get_action_logs'),
    path('map/lookup/', views.guest_lookup_map, name='guest_lookup_map'),
    path('route/api/linkedlist/', views.get_cleaning_route, name='get_cleaning_route'),
    path('route/start-day/', views.start_day_cleaning, name='start_day_cleaning'),
    path('route/clean/', views.mark_room_cleaned, name='mark_room_cleaned'),
    path('rooms/api/status/', views.get_all_rooms_status, name='get_all_rooms_status'),
    path('search/api/algo/', views.search_guests_algo, name='search_guests_algo'),
  
    
]

