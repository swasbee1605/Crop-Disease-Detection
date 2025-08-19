from django.contrib import admin
from django.urls import path,include
from . import views

urlpatterns = [
    path('disease/',views.disease_detection,name="disease"),
    path('result/',views.result,name="result"),
    path('login/',views.loginPage,name="loginPage"),
    path('logout/',views.logoutPage,name="logoutPage"),
    path('',views.registerPaging,name="registerPage"),
    path('predict/', views.predict, name='predict'),
    path('suggest/',views.suggestion,name="suggestion")
    
]