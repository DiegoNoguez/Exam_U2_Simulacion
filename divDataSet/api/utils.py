import os
import arff
import pandas as pd
from sklearn.model_selection import train_test_split

# CONFIGURACIÓN CRÍTICA PARA RENDER - DEBE IR ANTES de importar matplotlib
import matplotlib
matplotlib.use('Agg')  # Backend no interactivo
# Evita que matplotlib busque fuentes del sistema
os.environ['MPLBACKEND'] = 'Agg'
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

# Ahora importamos matplotlib después de la configuración
import matplotlib.pyplot as plt
import io
import base64
import gc

# Crear directorio temporal para matplotlib si no existe
try:
    os.makedirs('/tmp/matplotlib', exist_ok=True)
except:
    pass

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

def train_val_test_split(df, rstate=42, shuffle=True, stratify=None):
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

def create_lightweight_distribution_plot(df, column, title, max_categories=20):
    """Crea un gráfico de distribución optimizado para memoria"""
    try:
        # Configurar figura pequeña
        plt.figure(figsize=(12, 8), dpi=100) 
        
        # Para columnas categóricas, limitar el número de categorías mostradas
        if df[column].dtype == 'object':
            value_counts = df[column].value_counts()
            if len(value_counts) > max_categories:
                # Mostrar solo las top categorías
                top_categories = value_counts.head(max_categories)
                top_categories.plot(kind='bar')
                plt.title(f'{title} - Top {max_categories} categorías')
            else:
                value_counts.plot(kind='bar')
                plt.title(f'{title}')
        else:
            # Para columnas numéricas
            df[column].hist(bins=30, alpha=0.7)
            plt.title(f'{title}')
        
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
        
        return graphic
        
    except Exception as e:
        print(f"Error creando gráfica: {e}")
        return None
    finally:
        # Limpiar memoria de matplotlib
        plt.close('all')
        gc.collect()

def cleanup_memory(*objects):
    """Función auxiliar para limpiar memoria"""
    for obj in objects:
        del obj
    gc.collect()