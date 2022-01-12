from django.urls import path
from . import views

urlpatterns = [
        
        path('', views.dashboard, name='dashboard'),
        path('login/', views.login, name='login'),
        path('logout/', views.logout, name='logout'),
        path('register/', views.register, name='register'),
        path('goods/', views.goods, name='goods'),
        path('search/', views.goods, name='search'),

        path('login/user', views.loginUser, name='loginUser'),
        path('add/user', views.addUser, name='addUser'),
        path('add/url', views.addUrl, name='addUrl'),
        path('get/url', views.getUrl, name='getUrl'),
        path('del/url', views.delUrl, name='delUrl'),

        path('start', views.scrapStart, name='start'),
        path('stop', views.scrapStop, name='stop'),

]
