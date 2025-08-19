from django.contrib import admin
from .models import User,disease,solution

# Register your models here.

admin.site.register(User)
admin.site.register(disease)
admin.site.register(solution)