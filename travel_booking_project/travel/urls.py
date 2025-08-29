# travel/urls.py - COMPLETE URL PATTERNS
from django.urls import path
from . import views

app_name = 'travel'

urlpatterns = [
    # Main pages
    path('', views.travel_list, name='travel_list'),
    path('home/', views.home, name='home'),
    
    # Travel details and booking
    path('detail/<int:pk>/', views.travel_detail, name='travel_detail'),
    path('book/<int:pk>/', views.book_travel, name='book_travel'),
    path('quick-book/<int:pk>/', views.quick_book, name='quick_book'),
    
    # User bookings
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('cancel-booking/<int:pk>/', views.cancel_booking, name='cancel_booking'),
    path('booking-confirmation/<str:booking_id>/', views.booking_confirmation, name='booking_confirmation'),
    
    # Search functionality
    path('search/', views.travel_search, name='travel_search'),
    
    # AJAX endpoints
    path('availability/<int:pk>/', views.travel_availability, name='travel_availability'),
    
    # Debug and utility
    path('debug/', views.debug_auth, name='debug_auth'),
]