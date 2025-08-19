from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
STATES = [
        ('', 'Select a State'),  # Placeholder option
        ('AP', 'Andhra Pradesh'),
        ('AR', 'Arunachal Pradesh'),
        ('AS', 'Assam'),
        ('BR', 'Bihar'),
        ('CT', 'Chhattisgarh'),
        ('GA', 'Goa'),
        ('GJ', 'Gujarat'),
        ('HR', 'Haryana'),
        ('HP', 'Himachal Pradesh'),
        ('JH', 'Jharkhand'),
        ('KA', 'Karnataka'),
        ('KL', 'Kerala'),
        ('MP', 'Madhya Pradesh'),
        ('MH', 'Maharashtra'),
        ('MN', 'Manipur'),
        ('ML', 'Meghalaya'),
        ('MZ', 'Mizoram'),
        ('NL', 'Nagaland'),
        ('OD', 'Odisha'),
        ('PB', 'Punjab'),
        ('RJ', 'Rajasthan'),
        ('SK', 'Sikkim'),
        ('TN', 'Tamil Nadu'),
        ('TG', 'Telangana'),
        ('TR', 'Tripura'),
        ('UP', 'Uttar Pradesh'),
        ('UK', 'Uttarakhand'),
        ('WB', 'West Bengal'),
    ]


class User(AbstractUser):
    name=models.CharField(max_length=200,null=True)
    username=models.TextField(max_length=50,unique=True,null=True)
    email=models.EmailField(unique=True,null=True)
    state=models.TextField(max_length=25,null=True)


    USERNAME_FIELD='username'
    REQUIRED_FIELDS=[]

class disease(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    image=models.ImageField(null=True,upload_to="static/images")
    processed_image=models.ImageField(null=True,upload_to="static/processed")
    prediction = models.CharField(max_length=255, blank=True, null=True)  # Field for storing predictions

    def __str__(self):
        return f"{self.user.username} - {self.prediction if self.prediction else 'No Prediction'}"
    

class solution(models.Model):
    disease=models.CharField(max_length=200,null=True)
    cuase=models.CharField(max_length=200,null=True)
    solutions=models.CharField(max_length=1000,null=True)
