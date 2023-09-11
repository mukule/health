from django.db import models

# Create your models here.

class Hero(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    image = models.ImageField(upload_to='hero_images/', default='default/sm-3.jpg')

    def __str__(self):
        return self.title
    
class Senior(models.Model):
    name = models.CharField(max_length=255)
    profile_pic = models.ImageField(upload_to='seniors/', default='default/user.jpg')
    capacity = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    

class CompanyProfile(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company_logos/', default='default/default_logo.png')
    banner_image = models.ImageField(upload_to='company_banners/', default='default/default_banner.jpg')
    description = models.TextField()
    website = models.URLField(max_length=200)
    headquarters = models.CharField(max_length=255)
    vision = models.TextField()
    mission = models.TextField()
    # Add any additional fields you need

    def __str__(self):
        return self.name

class Event(models.Model):
    name = models.CharField(max_length=255)
    event_image = models.ImageField(upload_to='event_images/', default='default/event.png')
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField()
    location = models.CharField(max_length=255)
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE)
    # Add any additional fields you need for events

    def __str__(self):
        return self.name