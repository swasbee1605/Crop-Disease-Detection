from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import login,logout,authenticate
from .models import User,disease,solution
from .forms import MyUser
from django.contrib.messages import constants as message_constants
import cv2
import os
import numpy as np
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
import cv2
import joblib
from .detection import extract_features, predict_image
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required


MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'error',
}


# Create your views here.


model_path = r"C:\Users\Dell\OneDrive\Desktop\smartkheti\tomato_disease_model.joblib"
model_= joblib.load(model_path) if os.path.exists(model_path) else None


# def home(request):
#     return render(request, 'home.html')
@csrf_exempt
def predict(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        
        # Read the image from the uploaded file
        in_memory_file = np.frombuffer(file.read(), np.uint8)
        image = cv2.imdecode(in_memory_file, cv2.IMREAD_COLOR)
        if image is None:
            return JsonResponse({'error': 'Error loading image'}, status=400)
        
        # Save the image temporarily
        temp_path = 'temp_image.jpg'
        cv2.imwrite(temp_path, image)
        
        # Use your existing predict_image function
        prediction = predict_image(temp_path, model_)
        
        # Remove the temporary file
        os.remove(temp_path)
        
        return JsonResponse({'prediction': prediction})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def result_page(request):
    user=request.user
    dis=disease.objects.filter(user=user)
    context={'user':user,'diseases':dis}
    return render(request,'result.html',context)


# def disease_detection(request):
#     user = request.user
#     if request.method == 'POST':
#         image = request.FILES.get('image')
        
#         if image:
#             # Read the uploaded image file with OpenCV
#             image_data = np.fromstring(image.read(), np.uint8)
#             original_image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
            
#             if original_image is None:
#                 messages.error(request, "Error reading the uploaded image.")
#                 return redirect('disease')

#             # Process the image
#             processed_image = process_image(original_image)

#             # Convert processed image to binary data to save in the model
#             _, buffer = cv2.imencode('.png', processed_image)
#             processed_image_content = ContentFile(buffer.tobytes())

#             # Save the processed image to the file system first
#             processed_image_filename = default_storage.save(f'static/processed/{image.name}', processed_image_content)
            
#             # Create a new disease object with both the original and processed images
#             dis = disease.objects.create(
#                 user=request.user,
#                 image=image,  # Original image
#                 processed_image=processed_image_filename,  # Processed image file path
#             )
            
#             return redirect('result')
        
#     context = {'user': user}
#     return render(request, 'disease.html', context)


@login_required
def disease_detection(request):
    user=request.user
    req_state=user.state
    suggestions = crop_suggestions(req_state)

    season_suggestions = []
    for season, crops in suggestions.items():
        season_suggestions.append({
            'season': season,
            'crops': crops if crops else "None"  # If no crops are available, show 'None'
        })

    if request.method == 'POST':
        image = request.FILES.get('image')
        if image:
            disease_instance = disease.objects.create(
                user=request.user,
                image=image
            )
            # Process the image and get prediction
            temp_path = 'temp_image.jpg'
            with open(temp_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
            prediction = predict_image(temp_path, model_)
            os.remove(temp_path)
            
            disease_instance.prediction = prediction
            disease_instance.save()
            return redirect('result')
        
    context = {
        'state': req_state,
        'suggestions': suggestions
    }
    return render(request, 'disease.html',context)

@login_required
def result(request):
    diseases = disease.objects.filter(user=request.user).order_by('-id')
    disease_solutions = {}
    
    # Loop through the diseases and get the corresponding solutions
    for dis in diseases:
        try:
            # Fetch the solution for the current disease prediction
            sol = solution.objects.get(disease=dis.prediction)
            disease_solutions.append(sol.solution)  
        except:
            disease_solutions[dis.id] = "Healthy leaf."
    context = {'diseases': diseases,'disease_solutions': disease_solutions}
    return render(request, 'result.html', context)

def loginPage(request):
    if request.user.is_authenticated:
        return redirect('disease')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'User does not exist')
            return render(request, 'login.html')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('disease')
        else:
            messages.error(request, 'Username or password is incorrect')
    
    return render(request, 'login.html')

def loginPage(request):
    page = 'login'
    
    # Regular expression to match valid usernames (alphanumeric, _, #, @)
    username_pattern = r'^[\w#@]+$'
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if the username contains only valid characters
        if not re.match(username_pattern, username):
            messages.error(request, 'Username can only contain alphanumeric characters, _, #, or @.')
            return render(request, 'login.html', {'page': page})

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'Username does not exist')
            return render(request, 'login.html', {'page': page})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('disease')
        else:
            messages.error(request, 'Username or password incorrect')

    context = {'page': page}
    return render(request, 'login.html', context)

import re
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

def is_valid_email(email):
    try:
        # Use Django's built-in validation
        validate_email(email)

        # Split the email into user and domain parts
        user, domain = email.split('@')

        # Validate username
        if (len(user) < 3 or 
            not re.search(r'[a-zA-Z]', user) or 
            user[0].isdigit()):
            return False

        # Check for valid domain structure (only one TLD allowed)
        # This regex ensures that the domain ends with a valid TLD
        # and does not allow for additional segments after a valid TLD
        domain_regex = r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(domain_regex, domain):
            return False

        # Additionally, ensure no subdomains with a TLD
        # e.g., not allowing 'domain.co.uk.com'
        if domain.count('.') > 1:
            return False

        return True

    except ValidationError:
        return False

def registerPaging(request):
    page = 'register'
    form = MyUser()

    if request.method == 'POST':
        form = MyUser(request.POST)

        if form.is_valid():
            email = form.cleaned_data.get('email')
            username = form.cleaned_data.get('username')  # Assuming 'username' field exists in your form

            # Check for username length and special characters
            if len(username) < 3:
                messages.error(request, "Username must be at least 3 characters long.")
            elif not re.match(r'^[a-zA-Z0-9_]+$', username):  # Only allows alphanumeric and underscores
                messages.error(request, "Username can only contain letters, numbers, and underscores.")
            elif not is_valid_email(email):
                messages.error(request, "Please enter a valid email address.")
            else:
                user = form.save(commit=False)
                user.save()
                login(request, user)
                return redirect('disease')

        # If the form is invalid or username/email checks fail, add errors to the form
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f"{field}: {error}")

    context = {'page': page, 'form': form}
    return render(request, 'register.html', context)

def crop_suggestions(state):
    crops = {
        "Andhra Pradesh": {
            "Kharif": ["Rice", "Jowar", "Bajra", "Maize", "Tobacco"],
            "Rabi": ["Groundnut", "Sunflower"],
            "Zaid": ["Watermelon", "Cucumber"]
        },
        "Arunachal Pradesh": {
            "Kharif": ["Rice", "Maize"],
            "Rabi": ["Potato", "Wheat"],
            "Zaid": ["Pumpkin"]
        },
        "Assam": {
            "Kharif": ["Rice", "Tea"],
            "Rabi": ["Mustard", "Potato"],
            "Zaid": ["Vegetables"]
        },
        "Bihar": {
            "Kharif": ["Rice", "Maize"],
            "Rabi": ["Wheat", "Pulses"],
            "Zaid": ["Fruits"]
        },
        "Chhattisgarh": {
            "Kharif": ["Rice", "Maize"],
            "Rabi": ["Wheat", "Pulses"],
            "Zaid": []
        },
        "Goa": {
            "Kharif": ["Rice", "Coconut"],
            "Rabi": [],
            "Zaid": []
        },
        "Gujarat": {
            "Kharif": ["Cotton", "Groundnut"],
            "Rabi": ["Wheat", "Mustard"],
            "Zaid": []
        },
        "Haryana": {
            "Kharif": ["Sugarcane", "Paddy"],
            "Rabi": ["Wheat", "Sunflower"],
            "Zaid": []
        },
        "Himachal Pradesh": {
            "Kharif": ["Apple", "Peach"],
            "Rabi": [],
            "Zaid": []
        },
        "Jharkhand": {
            "Kharif": ["Rice", "Maize"],
            "Rabi": ["Wheat", "Pulses"],
            "Zaid": []
        },
        "Karnataka": {
            "Kharif": ["Rice", "Maize", "Cotton"],
            "Rabi": ["Wheat", "Sunflower"],
            "Zaid": []
        },
        "Kerala": {
            "Kharif": ["Coconut", "Rubber"],
            "Rabi": [],
            "Zaid": []
        },
        "Madhya Pradesh": {
            "Kharif": ["Maize", "Soybean"],
            "Rabi": ["Wheat", "Pulses"],
            "Zaid": ["Vegetables"]
        },
        "Maharashtra": {
            "Kharif": ["Cotton", "Jowar", "Sugarcane"],
            "Rabi": ["Wheat", "Mustard"],
            "Zaid": []
        },
        "Manipur": {
            "Kharif": ["Rice", "Maize"],
            "Rabi": ["Vegetables"],
            "Zaid": []
        },
        "Meghalaya": {
            "Kharif": ["Rice", "Maize"],
            "Rabi": ["Potato"],
            "Zaid": []
        },
        "Mizoram": {
            "Kharif": ["Rice", "Maize"],
            "Rabi": ["Potato"],
            "Zaid": []
        },
        "Nagaland": {
            "Kharif": ["Rice", "Maize"],
            "Rabi": ["Potato"],
            "Zaid": []
        },
        "Odisha": {
            "Kharif": ["Rice", "Pulses"],
            "Rabi": ["Mustard", "Wheat"],
            "Zaid": []
        },
        "Punjab": {
            "Kharif": ["Rice", "Cotton"],
            "Rabi": ["Wheat", "Barley"],
            "Zaid": []
        },
        "Rajasthan": {
            "Kharif": ["Bajra", "Jowar"],
            "Rabi": ["Wheat", "Mustard"],
            "Zaid": []
        },
        "Sikkim": {
            "Kharif": ["Cardamom", "Rice"],
            "Rabi": ["Potato"],
            "Zaid": []
        },
        "Tamil Nadu": {
            "Kharif": ["Paddy", "Groundnut"],
            "Rabi": ["Sugarcane", "Banana"],
            "Zaid": []
        },
        "Telangana": {
            "Kharif": ["Rice", "Cotton"],
            "Rabi": ["Sunflower", "Wheat"],
            "Zaid": []
        },
        "Tripura": {
            "Kharif": ["Rice", "Vegetables"],
            "Rabi": ["Mustard", "Potato"],
            "Zaid": []
        },
        "Uttar Pradesh": {
            "Kharif": ["Sugarcane", "Paddy"],
            "Rabi": ["Wheat", "Barley"],
            "Zaid": []
        },
        "Uttarakhand": {
            "Kharif": ["Rice", "Millets"],
            "Rabi": ["Wheat", "Barley"],
            "Zaid": []
        },
        "West Bengal": {
            "Kharif": ["Rice", "Jute"],
            "Rabi": ["Mustard", "Vegetables"],
            "Zaid": []
        }
    }

    return crops.get(state, {
        "Kharif": [],
        "Rabi": [],
        "Zaid": []
    })



def suggestion(request):
    user=request.user
    req_state=user.state
    suggestions = crop_suggestions(req_state)

    season_suggestions = []
    for season, crops in suggestions.items():
        season_suggestions.append({
            'season': season,
            'crops': crops if crops else "None"  # If no crops are available, show 'None'
        })

    # Pass the suggestions to the template
    context = {
        'state': req_state,
        'suggestions': suggestions
    }
    return render(request,'suggestion.html',context)

