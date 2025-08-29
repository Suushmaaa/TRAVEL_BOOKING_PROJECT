# booking/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from datetime import timedelta
import random

from django.core.paginator import Paginator
from django.utils import timezone
from .models import TravelOption, Booking

# Simple inline form since you might not have forms.py
from django import forms

class BookingForm(forms.Form):
    number_of_seats = forms.IntegerField(
        min_value=1, 
        max_value=10, 
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        self.travel_option = kwargs.pop('travel_option', None)
        super().__init__(*args, **kwargs)

def travel_list(request):
    """Display all available travel options with filtering"""
    travel_options = TravelOption.objects.filter(
        available_seats__gt=0,
        date__gte=timezone.now().date()
    )
    
    # Filtering
    travel_type = request.GET.get('type')
    source = request.GET.get('source')
    destination = request.GET.get('destination')
    date = request.GET.get('date')
    
    if travel_type:
        travel_options = travel_options.filter(type=travel_type)
    if source:
        travel_options = travel_options.filter(source__icontains=source)
    if destination:
        travel_options = travel_options.filter(destination__icontains=destination)
    if date:
        travel_options = travel_options.filter(date=date)
    
    # Pagination
    paginator = Paginator(travel_options, 10)  # Show 10 options per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique sources and destinations for filter dropdowns
    sources = TravelOption.objects.values_list('source', flat=True).distinct()
    destinations = TravelOption.objects.values_list('destination', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'travel_types': TravelOption.TRAVEL_TYPES,
        'sources': sources,
        'destinations': destinations,
        'current_filters': {
            'type': travel_type,
            'source': source,
            'destination': destination,
            'date': date,
        }
    }
    
    # Use your existing template name - adjust this path to match your template location
    return render(request, 'travel_list.html', context)

def travel_detail(request, travel_id):
    """Display detailed view of a travel option"""
    travel_option = get_object_or_404(TravelOption, id=travel_id)
    
    context = {
        'travel_option': travel_option,
    }
    
    # Use your existing template name
    return render(request, 'travel_detail.html', context)

@login_required
def book_travel(request, travel_id):
    """Handle travel booking"""
    travel_option = get_object_or_404(TravelOption, id=travel_id)
    
    if not travel_option.is_available:
        messages.error(request, 'This travel option is no longer available.')
        return redirect('booking:travel_list')
    
    if request.method == 'POST':
        form = BookingForm(request.POST, travel_option=travel_option)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Check if enough seats are available
                    seats_requested = form.cleaned_data['number_of_seats']
                    if seats_requested > travel_option.available_seats:
                        messages.error(request, f'Only {travel_option.available_seats} seats available.')
                        return render(request, 'book_travel.html', {'form': form, 'travel_option': travel_option})
                    
                    # Create booking
                    booking = Booking(
                        user=request.user,
                        travel_option=travel_option,
                        number_of_seats=seats_requested
                    )
                    
                    # Get passenger details from form
                    passenger_details = []
                    for i in range(seats_requested):
                        passenger_name = request.POST.get(f'passenger_name_{i}', '')
                        passenger_age = request.POST.get(f'passenger_age_{i}', '')
                        if passenger_name and passenger_age:
                            passenger_details.append({
                                'name': passenger_name,
                                'age': passenger_age
                            })
                    booking.passenger_details = passenger_details
                    
                    booking.save()
                    
                    # Update available seats
                    travel_option.available_seats -= seats_requested
                    travel_option.save()
                    
                    messages.success(request, f'Booking confirmed! Your booking ID is {booking.booking_id}')
                    return redirect('booking:my_bookings')
                    
            except Exception as e:
                messages.error(request, 'An error occurred while processing your booking. Please try again.')
                return render(request, 'book_travel.html', {'form': form, 'travel_option': travel_option})
    else:
        form = BookingForm(travel_option=travel_option)
    
    context = {
        'form': form,
        'travel_option': travel_option,
    }
    
    # Use your existing template name
    return render(request, 'book_travel.html', context)

@login_required
def my_bookings(request):
    """Display user's bookings"""
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    
    # Filter by status if requested
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_choices': Booking.STATUS_CHOICES,
        'current_status': status_filter,
    }
    
    # Use your existing template name
    return render(request, 'my_bookings.html', context)

@login_required
def cancel_booking(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    
    if booking.status != 'confirmed':
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('booking:my_bookings')
    
    if request.method == 'POST':
        if booking.cancel_booking():
            messages.success(request, f'Booking {booking.booking_id} has been cancelled successfully.')
        else:
            messages.error(request, 'Unable to cancel booking.')
        return redirect('booking:my_bookings')
    
    context = {
        'booking': booking,
    }
    
    # Use your existing template name
    return render(request, 'cancel_booking.html', context)

@login_required
def booking_detail(request, booking_id):
    """Display detailed view of a booking"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    
    context = {
        'booking': booking,
    }
    
    # Use your existing template name
    return render(request, 'booking_detail.html', context)

@login_required
def create_sample_data(request):
    """Create sample travel data - for development only"""
    if not request.user.is_superuser:
        messages.error(request, 'Only superusers can create sample data.')
        return redirect('booking:travel_list')
    
    # Check if data already exists
    existing_count = TravelOption.objects.count()
    if existing_count > 0:
        messages.warning(request, f'Travel data already exists ({existing_count} records). Clear existing data first if needed.')
        return redirect('booking:travel_list')
    
    # Sample cities
    cities = [
        'Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 
        'Hyderabad', 'Pune', 'Ahmedabad', 'Jaipur', 'Goa',
        'Kochi', 'Indore', 'Lucknow', 'Surat', 'Kanpur'
    ]
    
    travel_types = ['flight', 'train', 'bus']
    
    # Generate sample data
    created_count = 0
    for i in range(50):
        source = random.choice(cities)
        destination = random.choice([city for city in cities if city != source])
        
        travel_type = random.choice(travel_types)
        
        # Generate dates for the next 30 days
        base_date = timezone.now().date()
        travel_date = base_date + timedelta(days=random.randint(1, 30))
        
        # Generate random times
        hour = random.randint(6, 23)
        minute = random.choice([0, 15, 30, 45])
        travel_time = f"{hour:02d}:{minute:02d}"
        
        # Price based on travel type
        if travel_type == 'flight':
            price = random.randint(3000, 15000)
        elif travel_type == 'train':
            price = random.randint(500, 3000)
        else:  # bus
            price = random.randint(300, 2000)
        
        # Available seats
        available_seats = random.randint(5, 80)
        
        try:
            TravelOption.objects.create(
                travel_id=f"{travel_type.upper()[:2]}{i+1:03d}",
                type=travel_type,
                source=source,
                destination=destination,
                date=travel_date,
                time=travel_time,
                price=price,
                available_seats=available_seats
            )
            created_count += 1
        except Exception as e:
            messages.warning(request, f'Error creating travel option {i+1}: {str(e)}')
    
    messages.success(request, f'Successfully created {created_count} sample travel options!')
    return redirect('booking:travel_list')

def index(request):
    """Home page redirect to travel list"""
    return redirect('booking:travel_list')