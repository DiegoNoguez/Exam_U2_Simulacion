from django_restframework import status
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.cache import cache
import pandas as pd
import gc

from .serializers import (
    DatasetUploadSerializer, 
    SplitParametersSerializer,
    DatasetInfoSerializer
)
from .utils import (
    load_kdd_dataset, 
    train_val_test_split, 
    get_dataset_info, 
    create_lightweight_distribution_plot,
    cleanup_memory
)

@api_view(['POST'])
def upload_dataset(request):
    """Endpoint para cargar un dataset NSL-KDD (20% del original)"""
    serializer = DatasetUploadSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    uploaded_file = serializer.validated_data['file']
    use_sample = serializer.validated_data.get('use_sample', False)
    
    # Validar que sea un archivo ARFF
    if not uploaded_file.name.endswith('.arff'):
        return Response(
            {'error': 'Solo se permiten archivos .arff'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Leer contenido del archivo
        file_content = uploaded_file.read().decode('utf-8')
        
        # Si se solicita sample, tomar solo una parte del dataset
        if use_sample:
            lines = file_content.split('\n')
            # Tomar aproximadamente el 20% del dataset
            sample_size = max(1, len(lines) // 5)
            file_content = '\n'.join(lines[:sample_size])
        
        # Cargar dataset en memoria
        df = load_kdd_dataset(file_content)
        dataset_info = get_dataset_info(df)
        
        # Generar ID único para la sesión
        import uuid
        session_id = str(uuid.uuid4())
        
        # Almacenar dataset en cache (expira en 1 hora)
        cache_data = {
            'dataset_info': dataset_info,
            'file_content': file_content,
            'created_at': pd.Timestamp.now().isoformat()
        }
        cache.set(session_id, cache_data, timeout=3600)  # 1 hora
        
        # Limpiar memoria
        cleanup_memory(df, file_content)
        
        response_data = {
            'session_id': session_id,
            'dataset_info': dataset_info,
            'message': 'Dataset cargado exitosamente'
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'error': f'Error al procesar el dataset: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def split_dataset(request):
    """Endpoint para dividir un dataset cargado en sesión"""
    session_id = request.data.get('session_id')
    
    if not session_id:
        return Response(
            {'error': 'Se requiere session_id'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Recuperar datos de la sesión
    cache_data = cache.get(session_id)
    if not cache_data:
        return Response(
            {'error': 'Sesión no encontrada o expirada'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Validar parámetros de división
    param_serializer = SplitParametersSerializer(data=request.data)
    if not param_serializer.is_valid():
        return Response(
            param_serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    params = param_serializer.validated_data
    
    try:
        # Recargar dataset desde cache
        file_content = cache_data['file_content']
        df = load_kdd_dataset(file_content)
        
        # Realizar la división
        train_set, val_set, test_set = train_val_test_split(
            df,
            rstate=params['random_state'],
            shuffle=params['shuffle'],
            stratify=params.get('stratify')
        )
        
        # Preparar respuesta
        response_data = {
            'sizes': {
                'train': len(train_set),
                'validation': len(val_set),
                'test': len(test_set),
                'total': len(df)
            },
            'percentages': {
                'train': round(len(train_set) / len(df) * 100, 2),
                'validation': round(len(val_set) / len(df) * 100, 2),
                'test': round(len(test_set) / len(df) * 100, 2)
            },
            'parameters': params
        }
        
        # Si se especificó una columna para estratificar, incluir distribuciones
        if params.get('stratify'):
            stratify_col = params['stratify']
            if stratify_col in df.columns:
                distribution_plot = create_lightweight_distribution_plot(df, stratify_col)
                
                response_data['distributions'] = {
                    'original': df[stratify_col].value_counts().to_dict(),
                    'train': train_set[stratify_col].value_counts().to_dict(),
                    'validation': val_set[stratify_col].value_counts().to_dict(),
                    'test': test_set[stratify_col].value_counts().to_dict(),
                    'plot': distribution_plot
                }
        
        # Actualizar cache con información de la división
        cache_data['last_split'] = {
            'parameters': params,
            'sizes': response_data['sizes'],
            'timestamp': pd.Timestamp.now().isoformat()
        }
        cache.set(session_id, cache_data, timeout=3600)
        
        # Limpiar memoria
        cleanup_memory(df, train_set, val_set, test_set, file_content)
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'Error al dividir el dataset: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def get_dataset_info_view(request, session_id):
    """Obtiene información del dataset en sesión"""
    cache_data = cache.get(session_id)
    if not cache_data:
        return Response(
            {'error': 'Sesión no encontrada o expirada'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    dataset_info = cache_data['dataset_info']
    serializer = DatasetInfoSerializer(dataset_info)
    
    response_data = {
        'session_id': session_id,
        'dataset_info': serializer.data,
        'last_split': cache_data.get('last_split')
    }
    
    return Response(response_data)

@api_view(['GET'])
def get_available_columns(request, session_id):
    """Obtiene las columnas disponibles para estratificación"""
    cache_data = cache.get(session_id)
    if not cache_data:
        return Response(
            {'error': 'Sesión no encontrada o expirada'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    dataset_info = cache_data['dataset_info']
    
    return Response({
        'categorical_columns': dataset_info.get('categorical_columns', []),
        'numeric_columns': dataset_info.get('numeric_columns', []),
        'all_columns': dataset_info.get('columns', [])
    })

@api_view(['DELETE'])
def clear_session(request, session_id):
    """Limpia una sesión específica"""
    cache.delete(session_id)
    return Response(
        {'message': 'Sesión limpiada exitosamente'}, 
        status=status.HTTP_200_OK
    )

@api_view(['GET'])
def health_check(request):
    """Endpoint de salud del API"""
    return Response({
        'status': 'healthy',
        'message': 'API de división de datasets NSL-KDD funcionando correctamente'
    })