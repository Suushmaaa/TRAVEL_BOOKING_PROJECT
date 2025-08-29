from django import forms
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['number_of_seats']
        widgets = {
            'number_of_seats': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'placeholder': 'Number of seats'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.travel_option = kwargs.pop('travel_option', None)
        super().__init__(*args, **kwargs)
        
        if self.travel_option:
            # Dynamically restrict seat selection
            max_seats = min(10, self.travel_option.available_seats)
            self.fields['number_of_seats'].widget.attrs['max'] = max_seats
            self.fields['number_of_seats'].help_text = f'Maximum {max_seats} seats available'
    
    def clean_number_of_seats(self):
        seats = self.cleaned_data['number_of_seats']
        if self.travel_option and seats > self.travel_option.available_seats:
            raise forms.ValidationError(f'Only {self.travel_option.available_seats} seats available.')
        if seats <= 0:
            raise forms.ValidationError('Number of seats must be greater than 0.')
        return seats
