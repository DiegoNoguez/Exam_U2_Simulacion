import arff
import pandas as pd
from sklearn.model_selection import train_test_split
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo para ahorrar RAM
import matplotlib.pyplot as plt
import io
import base64
import gc

def load_kdd_dataset(file_content):
    """Lectura del DataSet NSL-KDD desde contenido en memoria"""
    try:
        # Convertir bytes a string si es necesario
        if isinstance(file_content, bytes):
            file_content = file_content.decode('utf-8')
        
        dataset = arff.loads(file_content)
        attributes = [attr[0] for attr in dataset['attributes']]
        df = pd.DataFrame(dataset['data'], columns=attributes)
        return df
    except Exception as e:
        raise Exception(f"Error loading dataset: {str(e)}")

def train_val_test_split(df, rstate=42, shuffle=True, stratify=None): #Recordando que usamos el 42 como semilla
    """Función para dividir el dataset en train, validation y test"""
    strat = df[stratify] if stratify else None
    train_set, test_set = train_test_split(
        df, test_size=0.4, random_state=rstate, shuffle=shuffle, stratify=strat)

    strat = test_set[stratify] if stratify else None
    val_set, test_set = train_test_split(
        test_set, test_size=0.5, random_state=rstate, shuffle=shuffle, stratify=strat)
    
    return train_set, val_set, test_set

def get_dataset_info(df):
    """Obtiene información del dataset optimizada para memoria"""
    info = {
        'total_records': len(df),
        'columns_count': len(df.columns),
        'columns': list(df.columns),
        'column_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
    }
    
    # Información de tipos de datos
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    info['numeric_columns'] = numeric_cols
    info['categorical_columns'] = categorical_cols
    
    return info

def create_lightweight_distribution_plot(df, column, max_categories=20):
    """Crea un gráfico de distribución optimizado para memoria"""
    # Configurar figura pequeña
    plt.figure(figsize=(6, 4), dpi=80)  # Reducir tamaño y DPI
    
    # Para columnas categóricas, limitar el número de categorías mostradas
    if df[column].dtype == 'object':
        value_counts = df[column].value_counts()
        if len(value_counts) > max_categories:
            # Mostrar solo las top categorías
            top_categories = value_counts.head(max_categories)
            top_categories.plot(kind='bar')
            plt.title(f'Top {max_categories} categorías de {column}')
        else:
            value_counts.plot(kind='bar')
            plt.title(f'Distribución de {column}')
    else:
        # Para columnas numéricas
        df[column].hist(bins=30, alpha=0.7)
        plt.title(f'Distribución de {column}')
    
    plt.xlabel(column)
    plt.ylabel('Frecuencia')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Convertir gráfico a base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=80, bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()
    
    graphic = base64.b64encode(image_png).decode('utf-8')
    
    # Limpiar memoria de matplotlib
    plt.close('all')
    gc.collect()
    
    return graphic

def cleanup_memory(*objects):
    """Función auxiliar para limpiar memoria"""
    for obj in objects:
        del obj
    gc.collect()