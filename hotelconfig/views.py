from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .forms import HotelConfigForm, RoomTypeForm, ExtraServiceForm
from .models import HotelConfig, RoomType, ExtraService
from rooms.models import Room, MaintenanceTask
from rooms.forms import MaintenanceForm
import logging

logger = logging.getLogger(__name__)

def inicio(request):
    return render(request, 'base.html')

@login_required
def home(request):
    hotel_config = HotelConfig.objects.first()
    room_types = RoomType.objects.all()
    extra_services = ExtraService.objects.all()
    rooms = Room.objects.all()
    available_rooms = Room.objects.filter(state='available')
    
    context = {
        'hotel_name': hotel_config.hotel_name if hotel_config else "Mi Hotel",
        'room_types': room_types,
        'extra_services': extra_services,
        'rooms': rooms,
        'available_rooms': available_rooms,
    }
    return render(request, 'home.html', context)

def new_hotel_form(request):
    return render(request, 'new_hotel_form.html')

def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('initial_setup')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home') 
        else:
            messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, 'login.html')

@login_required
def initial_hotel_setup(request):
    
    # Si la configuración principal ya existe, redirigir o mostrar un formulario de edición
    # if HotelConfig.objects.exists() and not request.GET.get('edit'):
        # Podrías redirigir a una página de administración
        # return redirect('home') 
        
    config_form = HotelConfigForm(instance=HotelConfig.objects.first() if HotelConfig.objects.exists() else None)
    # Usar prefijos para evitar colisiones de nombres y permitir que el JS funcione correctamente
    room_form = RoomTypeForm(prefix='room_type')
    service_form = ExtraServiceForm(prefix='extra_service')

    if request.method == 'POST':
        logger.debug("POST keys: %s", list(request.POST.keys()))
        config_form = HotelConfigForm(request.POST, instance=HotelConfig.objects.first() if HotelConfig.objects.exists() else None)
        # Inicializar formularios principales con prefijos
        room_form = RoomTypeForm(request.POST, prefix='room_type')
        service_form = ExtraServiceForm(request.POST, prefix='extra_service')
        
        if not (config_form.is_valid() and room_form.is_valid() and service_form.is_valid()):
            logger.warning("Config Errors: %s", config_form.errors)
            logger.warning("Room Errors: %s", room_form.errors)
            logger.warning("Service Errors: %s", service_form.errors)

        with transaction.atomic():
            if config_form.is_valid() and room_form.is_valid() and service_form.is_valid():
                logger.info("Forms are valid. Saving configuration...")
                
                # Only delete if this is a fresh setup (no existing config)
                if not HotelConfig.objects.exists():
                    RoomType.objects.all().delete()
                    ExtraService.objects.all().delete()

                config_form.save()
                
                # Guardar el primer tipo de habitación (el del formulario principal)
                room_form.save()
                
                # Guardar tipos de habitación adicionales (dinámicos)
                # El JS genera nombres como room_type-2-name, room_type-3-name, etc.
                counter = 2
                while True:
                    prefix = f'room_type-{counter}'
                    if f'{prefix}-name' not in request.POST:
                        break
                    
                    # Crear un formulario temporal para validar y guardar
                    dynamic_room_form = RoomTypeForm(request.POST, prefix=prefix)
                    if dynamic_room_form.is_valid():
                        dynamic_room_form.save()
                    counter += 1
                
                # Guardar el primer servicio extra
                service_form.save()
                
                # Guardar servicios extra adicionales
                counter = 2
                while True:
                    prefix = f'extra_service-{counter}'
                    if f'{prefix}-name' not in request.POST:
                        break
                    
                    dynamic_service_form = ExtraServiceForm(request.POST, prefix=prefix)
                    if dynamic_service_form.is_valid():
                        dynamic_service_form.save()
                    counter += 1
                
                return redirect('home') 

    context = {
        'config_form': config_form,
        'room_form': room_form,
        'service_form': service_form,
    }
    return render(request, 'initial_setup.html', context)