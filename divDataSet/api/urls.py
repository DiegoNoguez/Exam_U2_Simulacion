# Archivo para configurar las rutas o urls de mi app 
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('datasets/upload/', views.upload_dataset, name='upload-dataset'),
    path('datasets/split/', views.split_dataset, name='split-dataset'),
    path('datasets/<str:session_id>/info/', views.get_dataset_info_view, name='dataset-info'),
    path('datasets/<str:session_id>/columns/', views.get_available_columns, name='available-columns'),
    path('sessions/<str:session_id>/clear/', views.clear_session, name='clear-session'),
]