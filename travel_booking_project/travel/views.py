# travel/views.py - COMPLETE VERSION WITH YOUR MODIFICATIONS
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from datetime import datetime
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re

from booking.models import TravelOption, Booking  # Import from booking app

def home(request):
    """Landing page - redirects authenticated users to travel list"""
    print(f"Home view - User authenticated: {request.user.is_authenticated}")
    print(f"Home view - User: {request.user}")
    
    if request.user.is_authenticated:
        return redirect('travel:travel_list')
    return render(request, 'home.html')

def travel_list(request):
    """Travel list - NO LOGIN REQUIRED, with filters"""
    # Get all travel options
    travels = TravelOption.objects.all().order_by('date', 'time')
    
    # Get filter parameters
    travel_type = request.GET.get('type', '').strip()
    source = request.GET.get('source', '').strip()
    destination = request.GET.get('destination', '').strip()
    date = request.GET.get('date', '').strip()
    
    # Apply filters
    if travel_type:
        travels = travels.filter(type=travel_type)
    
    if source:
        travels = travels.filter(source__icontains=source)
    
    if destination:
        travels = travels.filter(destination__icontains=destination)
    
    if date:
        try:
            filter_date = datetime.strptime(date, '%Y-%m-%d').date()
            travels = travels.filter(date=filter_date)
        except ValueError:
            pass  # Invalid date format, ignore filter
    
    # Get unique sources and destinations for autocomplete
    all_travels = TravelOption.objects.all()
    sources = list(all_travels.values_list('source', flat=True).distinct().order_by('source'))
    destinations = list(all_travels.values_list('destination', flat=True).distinct().order_by('destination'))
    
    # Travel types for dropdown
    travel_types = TravelOption.TRAVEL_TYPES
    
    # Current filters for template
    current_filters = {
        'type': travel_type,
        'source': source,
        'destination': destination,
        'date': date,
    }
    
    # Pagination
    paginator = Paginator(travels, 12)  # Show 12 travels per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    print(f"Total travels found: {travels.count()}")
    print(f"Filters applied: {current_filters}")
    
    context = {
        'travels': travels,
        'page_obj': page_obj,
        'travel_types': travel_types,
        'sources': sources,
        'destinations': destinations,
        'current_filters': current_filters,
    }
    
    return render(request, "travel_list.html", context)

def travel_detail(request, pk):
    """Travel detail - NO LOGIN REQUIRED"""
    travel = get_object_or_404(TravelOption, pk=pk)
    return render(request, "travel_detail.html", {"travel": travel})

@login_required
def book_travel(request, pk):
    """Book travel - LOGIN REQUIRED with passenger details"""
    travel = get_object_or_404(TravelOption, pk=pk)

    if not travel.is_available:
        messages.error(request, "This travel option is no longer available.")
        return redirect('travel:travel_detail', pk=pk)

    if request.method == "POST":
        try:
            # Get form data
            num_seats = int(request.POST.get("number_of_seats", 1))
            passenger_name = request.POST.get('passenger_name', '').strip()
            contact_number = request.POST.get('contact_number', '').strip()
            email = request.POST.get('email', '').strip()
            
            # Validation
            errors = []
            
            if num_seats < 1:
                errors.append("Number of seats must be at least 1.")
            elif num_seats > travel.available_seats:
                errors.append(f"Only {travel.available_seats} seats available.")
            
            if not passenger_name:
                errors.append("Passenger name is required.")
            elif len(passenger_name) < 2:
                errors.append("Passenger name must be at least 2 characters long.")
            
            if not contact_number:
                errors.append("Contact number is required.")
            elif not re.match(r'^\+?[\d\s\-\(\)]{10,15}$', contact_number):
                errors.append("Please enter a valid contact number.")
            
            if not email:
                errors.append("Email is required.")
            else:
                try:
                    validate_email(email)
                except ValidationError:
                    errors.append("Please enter a valid email address.")
            
            if errors:
                for error in errors:
                    messages.error(request, error)
                return render(request, "book_travel.html", {
                    "travel": travel,
                    "form_data": {
                        'number_of_seats': num_seats,
                        'passenger_name': passenger_name,
                        'contact_number': contact_number,
                        'email': email,
                    }
                })
            
            # Create booking with passenger details
            booking = Booking.objects.create(
                user=request.user,
                travel_option=travel,
                number_of_seats=num_seats,
                passenger_details=[{
                    'name': passenger_name,
                    'contact': contact_number,
                    'email': email
                }]
            )
            
            # Update available seats
            travel.available_seats -= num_seats
            travel.save()
            
            messages.success(request, f"Booking confirmed! Your booking ID is {booking.booking_id}")
            
            # Redirect to booking detail if the URL exists, otherwise to my_bookings
            try:
                return redirect('booking:booking_detail', booking_id=booking.booking_id)
            except:
                return redirect("travel:my_bookings")
                
        except ValueError:
            messages.error(request, "Invalid number of seats.")
        except Exception as e:
            messages.error(request, f"An error occurred while processing your booking: {str(e)}")

    return render(request, "book_travel.html", {"travel": travel})

@login_required
def my_bookings(request):
    """User's bookings - LOGIN REQUIRED"""
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    return render(request, "my_bookings.html", {"bookings": bookings})

@login_required
def cancel_booking(request, pk):
    """Cancel booking - LOGIN REQUIRED"""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    
    if booking.status == 'confirmed':
        # Cancel the booking using the model method
        if booking.cancel_booking():
            messages.success(request, f"Booking {booking.booking_id} has been cancelled.")
        else:
            messages.error(request, "Unable to cancel this booking.")
    else:
        messages.error(request, "This booking cannot be cancelled.")
    
    return redirect("travel:my_bookings")

def travel_search(request):
    """Search travel options"""
    q = (request.GET.get("q") or "").strip()
    date = (request.GET.get("date") or "").strip()
    
    results = TravelOption.objects.all().order_by('date', 'time')

    if q:
        results = results.filter(
            Q(source__icontains=q) |
            Q(destination__icontains=q) |
            Q(type__icontains=q)
        )
    
    if date:
        try:
            filter_date = datetime.strptime(date, '%Y-%m-%d').date()
            results = results.filter(date=filter_date)
        except ValueError:
            pass
    
    print(f"Search query: '{q}', Date: '{date}'")
    print(f"Search results: {results.count()}")

    return render(request, "travel_search.html", {
        "results": results, 
        "q": q,
        "date": date
    })

def debug_auth(request):
    """Debug view to check authentication status"""
    from django.conf import settings
    
    # Check if we have any travel data
    travel_count = TravelOption.objects.count()
    
    return HttpResponse(f"""
    <h2>Debug Info</h2>
    <p>User authenticated: {request.user.is_authenticated}</p>
    <p>User: {request.user}</p>
    <p>LOGIN_URL from settings: {getattr(settings, 'LOGIN_URL', 'Not set')}</p>
    <p>LOGIN_REDIRECT_URL from settings: {getattr(settings, 'LOGIN_REDIRECT_URL', 'Not set')}</p>
    
    <h3>Database Info</h3>
    <p>Total travel options: {travel_count}</p>
    <p>Sample travel options:</p>
    <ul>
        {''.join([f'<li>{travel}</li>' for travel in TravelOption.objects.all()[:5]])}
    </ul>
    
    <hr>
    <h3>Navigation Links</h3>
    <p><a href="/">Home (travel:travel_list)</a></p>
    <p><a href="/booking/">Booking App</a></p>
    <p><a href="/accounts/login/">Login</a></p>
    <p><a href="/accounts/logout/">Logout</a></p>
    <p><a href="/search/">Search</a></p>
    <hr>
    <p>Check your Django terminal/console for print statements when you click the links above.</p>
    """)

# Additional utility views

@login_required
def booking_confirmation(request, booking_id):
    """Show booking confirmation details"""
    booking = get_object_or_404(Booking, booking_id=booking_id, user=request.user)
    return render(request, "booking_confirmation.html", {"booking": booking})

def travel_availability(request, pk):
    """AJAX endpoint to check travel availability"""
    travel = get_object_or_404(TravelOption, pk=pk)
    return JsonResponse({
        'available_seats': travel.available_seats,
        'is_available': travel.is_available,
        'price': float(travel.price),
    })

# Quick booking view for faster booking process
@login_required
def quick_book(request, pk):
    """Quick booking with minimal form"""
    travel = get_object_or_404(TravelOption, pk=pk)
    
    if request.method == "POST":
        try:
            num_seats = int(request.POST.get("seats", 1))
            
            if num_seats <= travel.available_seats and num_seats > 0:
                # Create quick booking with user's existing info
                booking = Booking.objects.create(
                    user=request.user,
                    travel_option=travel,
                    number_of_seats=num_seats,
                    passenger_details=[{
                        'name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                        'contact': '',  # Can be filled later
                        'email': request.user.email,
                    }]
                )
                
                travel.available_seats -= num_seats
                travel.save()
                
                messages.success(request, f"Quick booking successful! Booking ID: {booking.booking_id}")
                return redirect("travel:my_bookings")
            else:
                messages.error(request, "Invalid number of seats or not enough seats available.")
                
        except ValueError:
            messages.error(request, "Invalid seat number.")
    
    return render(request, "quick_book.html", {"travel": travel})