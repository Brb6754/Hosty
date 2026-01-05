from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Room, Booking, Guest, MaintenanceTask, RoomServiceOrder, DNDSet, NotificationQueue, ActionLog, RoomWaitlist, RoomType
from .forms import RoomForm, GuestForm, BookingForm, MaintenanceForm
from datetime import date
from django.utils import timezone
from django.utils.timezone import localtime
import json



def system_notify(request, message, priority='Normal'):
    NotificationQueue.objects.create(user=request.user, message=message, priority=priority)
    ActionLog.objects.create(user=request.user, action=f"🤖 SYSTEM: {message}")

def get_room_date_info(room):
    today = timezone.localdate()
    
    if room.state == 'occupied':
        current_booking = Booking.objects.filter(
            room=room, 
            check_in_date__lte=today, 
            check_out_date__gte=today,
            checked_in=True
        ).order_by('-check_in_date').first()
        
        if current_booking:
            return f"Out: {current_booking.check_out_date.strftime('%d/%m')}"
        return "Occ."

    elif room.state == 'available':
        next_booking = Booking.objects.filter(
            room=room,
            check_in_date__gt=today,
            is_active=True
        ).order_by('check_in_date').first()
        
        if next_booking:
            return f"Next: {next_booking.check_in_date.strftime('%d/%m')}"
        return "Free"
    
    return ""



@login_required
def home(request):
    rooms = Room.objects.filter(user=request.user).order_by('number') 
    room_types = RoomType.objects.all() 
    
    for room in rooms:
        room.date_info = get_room_date_info(room)
    
    return render(request, 'dashboard.html', {
        'hotel_name': f"Hotel de {request.user.username}",
        'rooms': rooms,
        'room_types': room_types
    })

@login_required
@require_POST
def add_room(request):
    form = RoomForm(request.POST)
    if form.is_valid():
        room = form.save(commit=False)
        room.user = request.user 
        
        system_notify(request, f"New Room Added: {room.number}", "Normal")
        
        return JsonResponse({
            'success': True,
            'room': {
                'id': room.id,
                'number': room.number,
                'room_type': room.room_type.name,
                'capacity': room.room_type.capacity,
                'price': str(room.price_per_night),
                'state': room.state,
                'state_display': room.get_state_display()
            }
        })
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@login_required
@require_POST
def create_booking(request):
    guest_form = GuestForm(request.POST)
    booking_form = BookingForm(request.POST)
    
    if guest_form.is_valid() and booking_form.is_valid():
        email = guest_form.cleaned_data['email']
        guest, created = Guest.objects.update_or_create(
            user=request.user, 
            email=email,
            defaults={
                'first_name': guest_form.cleaned_data['first_name'],
                'last_name': guest_form.cleaned_data['last_name'],
                'phone_number': guest_form.cleaned_data.get('phone_number', '')
            }
        )
        
        booking = booking_form.save(commit=False)
        booking.guest = guest
        
        if booking.room.user != request.user:
             return JsonResponse({'success': False, 'errors': {'room': 'Invalid Room'}}, status=403)

        check_in = booking.check_in_date
        check_out = booking.check_out_date
        today = timezone.localdate()

        if check_out <= check_in:
            return JsonResponse({'success': False, 'errors': {'dates': 'Check-out date must be after check-in date'}}, status=400)
        
        if check_in < today:
            return JsonResponse({'success': False, 'errors': {'dates': 'Cannot create booking in the past'}}, status=400)
        
        overlapping = Booking.objects.filter(
            room=booking.room,
            is_active=True,
            check_in_date__lt=check_out,
            check_out_date__gt=check_in
        )
        if overlapping.exists():
            return JsonResponse({'success': False, 'errors': {'room': 'Room not available for selected dates'}}, status=400)
        
        nights = (check_out - check_in).days
        booking.total_price = booking.room.price_per_night * nights
        booking.save()
        
        system_notify(request, f"New Booking: {guest.first_name} (Rm {booking.room.number})", "Normal")

        return JsonResponse({
            'success': True,
            'booking': {
                'id': booking.id,
                'guest_name': f"{guest.first_name} {guest.last_name}",
                'room_number': booking.room.number,
                'total_price': str(booking.total_price),
                'nights': nights
            }
        })
    else:
        errors = {}
        if not guest_form.is_valid(): errors['guest'] = guest_form.errors
        if not booking_form.is_valid(): errors['booking'] = booking_form.errors
        return JsonResponse({'success': False, 'errors': errors}, status=400)

@login_required
@require_http_methods(["GET"])
def today_checkins(request):
    today = timezone.localdate()
    bookings = Booking.objects.filter(
        room__user=request.user, 
        check_in_date=today, 
        checked_in=False
    ).select_related('guest', 'room', 'room__room_type')
    
    data = []
    for booking in bookings:
        data.append({
            'id': booking.id,
            'guest_name': f"{booking.guest.first_name} {booking.guest.last_name}",
            'email': booking.guest.email,
            'phone': booking.guest.phone_number,
            'room_number': booking.room.number,
            'room_type': booking.room.room_type.name,
            'nights': (booking.check_out_date - booking.check_in_date).days,
            'total_price': str(booking.total_price) if booking.total_price else "0",
            'room_id': booking.room.id
        })
    return JsonResponse({'checkins': data})

@login_required
@require_POST
def update_room_status(request):
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        new_state = data.get('state')
        room = Room.objects.get(id=room_id, user=request.user)
        room.state = new_state
        room.save()
        
        date_info = get_room_date_info(room)
        
        return JsonResponse({
            'success': True, 
            'new_state': room.get_state_display(),
            'date_info': date_info
        })
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Room not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def get_all_rooms_status(request):
    rooms = Room.objects.filter(user=request.user) 
    data = []
    for room in rooms:
        data.append({
            'id': room.id,
            'state': room.state,
            'date_info': get_room_date_info(room)
        })
    return JsonResponse({'rooms': data})

@login_required
@require_POST
def process_checkin(request):
    booking_id = request.POST.get('booking_id')
    check_in_time = request.POST.get('check_in_time')
    notes = request.POST.get('notes', '')
    
    try:
        booking = Booking.objects.get(id=booking_id, room__user=request.user)
        
        booking.check_in_time = check_in_time
        booking.checked_in = True
        booking.notes = notes
        booking.save()
        
        booking.room.state = 'occupied'
        booking.room.save()
        
        date_info = f"Out: {booking.check_out_date.strftime('%d/%m')}"
        
        system_notify(request, f"Check-In: Room {booking.room.number}", "Urgent")

        return JsonResponse({
            'success': True, 
            'message': 'Check-in completed',
            'room_id': booking.room.id,
            'new_state': 'Occupied',
            'date_info': date_info
        })
    except Exception as e:
        return JsonResponse({'success': False, 'errors': {'general': str(e)}}, status=400)

def manual_priority_sort(task_list):
    n = len(task_list)
    if n <= 1: return task_list
    for i in range(n):
        for j in range(0, n - i - 1):
            current = task_list[j]
            next_t = task_list[j+1]
            
            should_swap = False
            
            if current.priority > next_t.priority:
                should_swap = True
            elif current.priority == next_t.priority:
                if current.created_at and next_t.created_at:
                    if current.created_at > next_t.created_at:
                        should_swap = True
            
            if should_swap:
                task_list[j], task_list[j+1] = task_list[j+1], task_list[j]
                
    return task_list

@login_required
@require_http_methods(["GET"])
def get_pending_tasks(request):
    tasks_queryset = MaintenanceTask.objects.filter(room__user=request.user, status='pending').select_related('room')
    tasks_list = list(tasks_queryset)
    
    sorted_tasks = manual_priority_sort(tasks_list)
    
    data = []
    for task in sorted_tasks:
        data.append({
            'id': task.id,
            'room': task.room.number,
            'description': task.description,
            'priority': task.priority,
            'priority_display': task.get_priority_display(),
            'created': localtime(task.created_at).strftime('%H:%M') if task.created_at else "--:--"
        })
    return JsonResponse({'tasks': data})

@login_required
@require_POST
def add_maintenance_task(request):
    form = MaintenanceForm(request.POST)
    if form.is_valid():
        task = form.save(commit=False)
        if task.room.user != request.user:
             return JsonResponse({'success': False, 'error': 'Invalid Room'}, status=403)
        task.save()
        
        prio = "Urgent" if task.priority == 1 else "Normal"
        system_notify(request, f"Maintenance: {task.description} ({task.room.number})", prio)
        return JsonResponse({'success': True, 'message': 'Task added'})
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)

@login_required
@require_POST
def complete_maintenance_task(request):
    task_id = request.POST.get('task_id')
    try:
        task = MaintenanceTask.objects.get(id=task_id, room__user=request.user)
        task.status = 'completed'
        task.save()
        return JsonResponse({'success': True})
    except MaintenanceTask.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)



def manual_heapify_up(heap_list, index):
    if index == 0: return
    parent_index = (index - 1) // 2
    if heap_list[index]['timestamp'] < heap_list[parent_index]['timestamp']:
        heap_list[index], heap_list[parent_index] = heap_list[parent_index], heap_list[index]
        manual_heapify_up(heap_list, parent_index)

@login_required
@require_http_methods(["GET"])
def get_room_service_heap(request):
    orders = RoomServiceOrder.objects.filter(room__user=request.user)
    
    min_heap = []
    for order in orders:
        node = {
            'id': order.id,
            'room': order.room.number,
            'item': order.item,
            'timestamp': order.timestamp.timestamp(),
            'time_display': localtime(order.timestamp).strftime('%H:%M')
        }
        min_heap.append(node)
        manual_heapify_up(min_heap, len(min_heap) - 1)
        
    return JsonResponse({'heap': min_heap})

@login_required
@require_POST
def add_service_order(request):
    room_id = request.POST.get('room_id')
    item = request.POST.get('item')
    try:
        room = Room.objects.get(id=room_id, user=request.user)
        RoomServiceOrder.objects.create(room=room, item=item)
        system_notify(request, f"Room Service: {item} (Rm {room.number})", "Normal")
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    
@login_required
@require_POST
def complete_service_order(request):
    order_id = request.POST.get('order_id')
    RoomServiceOrder.objects.filter(id=order_id, room__user=request.user).delete()
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["GET"])
def get_dnd_set(request):
    dnd_rooms = DNDSet.objects.filter(user=request.user).order_by('room_number')
    
    data = []
    for item in dnd_rooms:
        data.append({'id': item.id, 'room': item.room_number})
    return JsonResponse({'set': data})

@login_required
@require_POST
def toggle_dnd_room(request):
    room_num = request.POST.get('room_number')
    
    if not Room.objects.filter(number=room_num, user=request.user).exists():
        return JsonResponse({'success': False, 'error': 'Invalid Room'}, status=403)

    exists = DNDSet.objects.filter(room_number=room_num, user=request.user).exists()
    
    if exists:
        DNDSet.objects.filter(room_number=room_num, user=request.user).delete()
        action = "removed"
    else:
        DNDSet.objects.create(room_number=room_num, user=request.user)
        action = "added"
        system_notify(request, f"DND Activated: Room {room_num}", "Normal")
        
    return JsonResponse({'success': True, 'action': action, 'room': room_num})


@login_required
def get_notification_queue(request):
    queue = NotificationQueue.objects.filter(user=request.user).order_by('timestamp')
    data = []
    for q in queue:
        data.append({
            'id': q.id,
            'message': q.message,
            'priority': q.priority,
            'time': localtime(q.timestamp).strftime('%H:%M')
        })
    return JsonResponse({'queue': data})

@login_required
@require_POST
def add_notification(request):
    msg = request.POST.get('message')
    prio = request.POST.get('priority', 'Normal')
    system_notify(request, msg, prio)
    return JsonResponse({'success': True})

@login_required
@require_POST
def pop_notification(request):
    next_msg = NotificationQueue.objects.filter(user=request.user).order_by('timestamp').first()
    if next_msg:
        text = next_msg.message
        next_msg.delete()
        ActionLog.objects.create(user=request.user, action=f"✅ Read: '{text}'")
        return JsonResponse({'success': True, 'message': text})
    return JsonResponse({'success': False, 'message': 'No notifications'})

@login_required
def get_action_logs(request):
    logs = ActionLog.objects.filter(user=request.user).order_by('-timestamp')[:20]
    data = []
    for log in logs:
        data.append({
            'action': log.action,
            'time': localtime(log.timestamp).strftime('%H:%M:%S')
        })
    return JsonResponse({'logs': data})



@login_required
@require_http_methods(["GET"])
def get_room_waitlist(request):
    queue = RoomWaitlist.objects.filter(user=request.user).order_by('timestamp')
    data = []
    for idx, item in enumerate(queue):
        data.append({
            'pos': idx + 1,
            'id': item.id,
            'guest_name': item.guest_name,
            'room_type': item.room_type,
            'timestamp': localtime(item.timestamp).strftime('%d/%m %H:%M')
        })
    return JsonResponse({'queue': data})

@login_required
@require_POST
def add_to_room_waitlist(request):
    name = request.POST.get('guest_name')
    rtype = request.POST.get('room_type')
    
    RoomWaitlist.objects.create(user=request.user, guest_name=name, room_type=rtype)
    system_notify(request, f"Waitlist: {name} ({rtype})", "Normal")
    return JsonResponse({'success': True})

@login_required
@require_POST
def pop_waitlist(request):
    guest = RoomWaitlist.objects.filter(user=request.user).order_by('timestamp').first()
    if guest:
        name = guest.guest_name
        guest.delete()
        return JsonResponse({'success': True, 'guest': name})
    return JsonResponse({'success': False, 'message': 'Empty'})



class Node:
    def __init__(self, room_obj):
        self.val = room_obj.number
        self.id = room_obj.id
        self.next = None

@login_required
def get_cleaning_route(request):
    dirty = Room.objects.filter(user=request.user, state='cleaning').order_by('number')
    
    if not dirty: return JsonResponse({'route': []})
    
    head = Node(dirty[0])
    curr = head
    for i in range(1, len(dirty)):
        curr.next = Node(dirty[i])
        curr = curr.next
        
    route = []
    curr = head
    while curr:
        route.append({'number': curr.val, 'id': curr.id})
        curr = curr.next
        
    return JsonResponse({'route': route})

@login_required
@require_POST
def start_day_cleaning(request):
    Room.objects.filter(user=request.user).update(state='cleaning')
    return JsonResponse({'success': True})

@login_required
@require_POST
def mark_room_cleaned(request):
    room_id = request.POST.get('room_id')
    try:
        room = Room.objects.get(id=room_id, user=request.user) 
        today = timezone.localdate()
        has_guest = Booking.objects.filter(
            room=room, 
            check_in_date__lte=today, 
            check_out_date__gte=today,
            checked_in=True
        ).exists()
        
        room.state = 'occupied' if has_guest else 'available'
        room.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_POST
def reset_all_rooms(request):
    Room.objects.filter(user=request.user).update(state='available')
    return JsonResponse({'success': True})



def manual_hash_function(key, size):
    ascii_sum = sum(ord(char) for char in str(key))
    return ascii_sum % size

@login_required
@require_POST
def guest_lookup_map(request):
    target_room = request.POST.get('room_number')
    table_size = 50
    hash_table = [None] * table_size
    
    active_bookings = Booking.objects.filter(room__user=request.user, is_active=True, checked_in=True).select_related('guest', 'room')
    
    for booking in active_bookings:
        idx = manual_hash_function(booking.room.number, table_size)
        hash_table[idx] = {
            'room': booking.room.number,
            'guest': f"{booking.guest.first_name} {booking.guest.last_name}",
            'type': booking.room.room_type.name
        }
        
    search_index = manual_hash_function(target_room, table_size)
    result = hash_table[search_index]
    
    if result and result['room'] == target_room:
        return JsonResponse({'found': True, 'guest': result['guest'], 'type': result['type']})
    return JsonResponse({'found': False, 'message': 'Not found'})

def manual_string_search(text, pattern):
    text, pattern = text.lower(), pattern.lower()
    n, m = len(text), len(pattern)
    if m == 0 or m > n: return False
    for i in range(n - m + 1):
        match = True
        for j in range(m):
            if text[i + j] != pattern[j]:
                match = False; break
        if match: return True
    return False

@login_required
@require_POST
def search_guests_algo(request):
    query = request.POST.get('query', '')
    if not query: return JsonResponse({'results': []})
    
    all_bookings = Booking.objects.filter(room__user=request.user).select_related('guest', 'room').order_by('-check_in_date')
    
    results = []
    for booking in all_bookings:
        full_name = f"{booking.guest.first_name} {booking.guest.last_name}"
        if manual_string_search(full_name, query):
            status = "Past"
            if booking.is_active: status = "Active" if not booking.checked_in else "In-House"
            if booking.room.state == 'available' and booking.checked_in: status = "Checked-Out"
            
            results.append({'guest': full_name, 'room': booking.room.number, 'date': booking.check_in_date.strftime('%d/%m/%Y'), 'status': status})
            if len(results) >= 5: break
            
    return JsonResponse({'results': results})