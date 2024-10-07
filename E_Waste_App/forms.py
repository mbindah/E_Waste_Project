# forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import *

# User Registration Form
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

# Vendor Registration Form
class VendorRegistrationForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = '__all__'  # Adjust based on your Vendor model fields

# Client Registration Form
class ClientRegistrationForm(UserCreationForm):
    # Add fields from the Client model
    address = forms.CharField(widget=forms.Textarea, required=True)
    contact_number = forms.CharField(max_length=15, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        # Save the User instance
        user = super().save(commit=False)
        if commit:
            user.save()
        
        # Create the Client instance
        Client.objects.create(
            user=user,
            address=self.cleaned_data['address'],
            contact_number=self.cleaned_data['contact_number']
        )

        return user

# Product Posting Form
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'image']  # Adjust based on your Product model fields

# Message Form
class MessageForm(forms.Form):
    content = forms.CharField(widget=forms.Textarea, label="Message")
    recipient = forms.ChoiceField(label="Select Recipient")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(MessageForm, self).__init__(*args, **kwargs)

        if hasattr(user, 'client'):
            # If user is a client, show vendors
            vendors = Vendor.objects.all()
            self.fields['recipient'].choices = [(vendor.id, vendor.company_name) for vendor in vendors]
        elif hasattr(user, 'vendor'):
            # If user is a vendor, show clients
            clients = Client.objects.all()
            self.fields['recipient'].choices = [(client.id, client.email) for client in clients]

# Rating Form
class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['vendor', 'score', 'comment']  # Adjust based on your Rating model fields

    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score < 0 or score > 10:
            raise forms.ValidationError('Score must be between 0 and 10.')
        return score

# Update User Details
class UpdateUserForm(forms.ModelForm):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter your password'}),
        required=False,  # Make it optional
    )

    class Meta:
        model = User
        fields = ['email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'readonly': 'readonly'}),  # If you don't want users to update the username
        }
