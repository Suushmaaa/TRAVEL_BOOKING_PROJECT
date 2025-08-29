from django.contrib import admin
# booking/admin.py
from django.contrib import admin
from .models import TravelOption, Booking

@admin.register(TravelOption)
class TravelOptionAdmin(admin.ModelAdmin):
    list_display = ['travel_id', 'type', 'source', 'destination', 'date', 'time', 'price', 'available_seats']
    list_filter = ['type', 'date', 'source', 'destination']
    search_fields = ['travel_id', 'source', 'destination']
    list_editable = ['price', 'available_seats']
    ordering = ['date', 'time']
    
    # Add action to create sample data
    actions = ['create_sample_data']
    
    def create_sample_data(self, request, queryset):
        # This will be called from admin actions
        from datetime import timedelta
        from django.utils import timezone
        import random
        
        cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune']
        travel_types = ['flight', 'train', 'bus']
        
        for i in range(20):
            source = random.choice(cities)
            destination = random.choice([city for city in cities if city != source])
            travel_type = random.choice(travel_types)
            
            base_date = timezone.now().date()
            travel_date = base_date + timedelta(days=random.randint(1, 30))
            
            hour = random.randint(6, 23)
            minute = random.choice([0, 15, 30, 45])
            travel_time = f"{hour:02d}:{minute:02d}"
            
            if travel_type == 'flight':
                price = random.randint(3000, 15000)
            elif travel_type == 'train':
                price = random.randint(500, 3000)
            else:
                price = random.randint(300, 2000)
            
            available_seats = random.randint(5, 80)
            
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
        
        self.message_user(request, f"Created 20 sample travel options successfully!")
    
    create_sample_data.short_description = "Create sample travel data"

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_id', 'user', 'travel_option', 'number_of_seats', 'total_price', 'status', 'booking_date']
    list_filter = ['status', 'booking_date']
    search_fields = ['booking_id', 'user__username']
    readonly_fields = ['booking_id', 'total_price', 'booking_date']
# Register your models here.
