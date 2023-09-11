from django import forms
from .models import *

class HeroForm(forms.ModelForm):
    title = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    content = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))
    image = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}))

    class Meta:
        model = Hero
        fields = ['title', 'content', 'image']


class SeniorForm(forms.ModelForm):
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter name'}),
        label='Name'
    )

    profile_pic = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        label='Profile Picture'
    )

    capacity = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter capacity'}),
        label='Capacity'
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter description'}),
        label='Description'
    )

    class Meta:
        model = Senior
        fields = ['name', 'profile_pic', 'capacity', 'description']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the profile_pic field not required
        self.fields['profile_pic'].required = False

class CompanyProfileForm(forms.ModelForm):
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter name'}),
        label='Name'
    )

    logo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        label='Logo'
    )

    banner_image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        label='Banner Image'
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter description'}),
        label='Description'
    )

    website = forms.URLField(
        max_length=200,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter website URL'}),
        label='Website'
    )

    headquarters = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter headquarters'}),
        label='Headquarters'
    )

    vision = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter vision'}),
        label='Vision'
    )

    mission = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter mission'}),
        label='Mission'
    )

    class Meta:
        model = CompanyProfile
        fields = ['name', 'logo', 'banner_image', 'description', 'website', 'headquarters', 'vision', 'mission']


class EventForm(forms.ModelForm):
    company = forms.ModelChoiceField(
        queryset=CompanyProfile.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control', 'placeholder': 'Select company'}),
        label='Associated Company'
    )

    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter event name'}),
        label='Event Name'
    )

    event_image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        label='Event Image'
    )

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'Date Started', 'type': 'date'}),
        label='Date Started', required=False
    )

    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'Select end date', 'type': 'date'}),
        label='Event End Date'
    )

    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter event description'}),
        label='Event Description'
    )

    location = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter event location'}),
        label='Event Location'
    )

    class Meta:
        model = Event
        fields = ['company', 'name', 'event_image', 'start_date', 'end_date', 'description', 'location']
