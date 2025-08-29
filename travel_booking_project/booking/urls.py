from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.travel_list, name='travel_list'),  # /booking/ -> booking travel list
    path('travel/<int:travel_id>/', views.travel_detail, name='travel_detail'),
    path('book/<int:travel_id>/', views.book_travel, name='book_travel'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('cancel/<str:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('booking/<str:booking_id>/', views.booking_detail, name='booking_detail'),
    path('create-sample-data/', views.create_sample_data, name='create_sample_data'),
]
