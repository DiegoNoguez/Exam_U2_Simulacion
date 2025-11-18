from django.contrib import admin
from django.urls import path, include

#configuracion de las rutas de las apis
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]