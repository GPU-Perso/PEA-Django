"""
URL configuration for PEAWeb project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from stocks.views import stocks_list, stock_update, show_stock, show_alerts, acknowledge_alert

urlpatterns = [
    path('', stocks_list),
    path('online/<str:online>', stocks_list),
    path('update/code/<str:code>', stock_update),
    path('stock_detail/', show_stock),
    path('alerts/', show_alerts),
    path('acknowledge_alert/id/<int:id>', acknowledge_alert),
    path('admin/', admin.site.urls),
]
