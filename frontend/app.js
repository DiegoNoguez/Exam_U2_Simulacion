// Configuración de la API
const API_BASE_URL = 'https://exam-u2-simulacion-divdata.onrender.com/api';

// Estado de la aplicación
let currentSessionId = null;
let currentDatasetInfo = null;

// Elementos del DOM
const elements = {
    // File upload
    fileUpload: document.getElementById('file-upload'),
    fileUploadArea: document.getElementById('file-upload-area'),
    uploadLoading: document.getElementById('upload-loading'),
    
    // Dataset info
    datasetInfo: document.getElementById('dataset-info'),
    sessionId: document.getElementById('session-id'),
    totalRecords: document.getElementById('total-records'),
    columnsCount: document.getElementById('columns-count'),
    memoryUsage: document.getElementById('memory-usage'),
    categoricalColumns: document.getElementById('categorical-columns'),
    
    // Split parameters
    splitParameters: document.getElementById('split-parameters'),
    testSize: document.getElementById('test-size'),
    testSizeValue: document.getElementById('test-size-value'),
    valSize: document.getElementById('val-size'),
    valSizeValue: document.getElementById('val-size-value'),
    randomState: document.getElementById('random-state'),
    shuffle: document.getElementById('shuffle'),
    stratifyColumn: document.getElementById('stratify-column'),
    splitButton: document.getElementById('split-button'),
    splitLoading: document.getElementById('split-loading'),
    
    // Results
    results: document.getElementById('results'),
    trainSize: document.getElementById('train-size'),
    trainPercent: document.getElementById('train-percent'),
    valSizeResult: document.getElementById('val-size-result'),
    valPercent: document.getElementById('val-percent'),
    testSizeResult: document.getElementById('test-size-result'),
    testPercent: document.getElementById('test-percent'),
    distributionSection: document.getElementById('distribution-section'),
    plotsContainer: document.getElementById('plots-container'),
    
    // Error
    errorMessage: document.getElementById('error-message'),
    errorText: document.getElementById('error-text')
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

function initializeEventListeners() {
    // File upload
    elements.fileUpload.addEventListener('change', handleFileUpload);
    
    // Drag and drop
    elements.fileUploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.style.borderColor = 'var(--primary-pink)';
        this.style.backgroundColor = 'var(--light-purple)';
    });
    
    elements.fileUploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.style.borderColor = 'var(--border-color)';
        this.style.backgroundColor = 'var(--light-pink)';
    });
    
    elements.fileUploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        this.style.borderColor = 'var(--border-color)';
        this.style.backgroundColor = 'var(--light-pink)';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            elements.fileUpload.files = files;
            handleFileUpload();
        }
    });
    
    // Range inputs
    elements.testSize.addEventListener('input', function() {
        elements.testSizeValue.textContent = Math.round(this.value * 100) + '%';
    });
    
    elements.valSize.addEventListener('input', function() {
        elements.valSizeValue.textContent = Math.round(this.value * 100) + '%';
    });
}

async function handleFileUpload() {
    const file = elements.fileUpload.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.arff')) {
        showError('Por favor, selecciona un archivo .arff');
        return;
    }
    
    showLoading('upload');
    hideError();
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('use_sample', true); // Siempre usar sample del 20%
        
        const response = await fetch(`${API_BASE_URL}/datasets/upload/`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al subir el archivo');
        }
        
        const data = await response.json();
        
        currentSessionId = data.session_id;
        currentDatasetInfo = data.dataset_info;
        
        displayDatasetInfo();
        loadAvailableColumns();
        showSplitParameters();
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading('upload');
    }
}

function displayDatasetInfo() {
    elements.sessionId.value = currentSessionId;
    elements.totalRecords.value = currentDatasetInfo.total_records.toLocaleString();
    elements.columnsCount.value = currentDatasetInfo.columns_count;
    elements.memoryUsage.value = currentDatasetInfo.memory_usage_mb + ' MB';
    elements.categoricalColumns.value = currentDatasetInfo.categorical_columns.join(', ');
    
    elements.datasetInfo.style.display = 'block';
}

async function loadAvailableColumns() {
    try {
        const response = await fetch(`${API_BASE_URL}/datasets/${currentSessionId}/columns/`);
        
        if (!response.ok) {
            throw new Error('Error al cargar las columnas');
        }
        
        const data = await response.json();
        
        // Limpiar select
        elements.stratifyColumn.innerHTML = '<option value="">-- Sin estratificación --</option>';
        
        // Añadir columnas categóricas
        data.categorical_columns.forEach(column => {
            const option = document.createElement('option');
            option.value = column;
            option.textContent = column;
            elements.stratifyColumn.appendChild(option);
        });
        
    } catch (error) {
        console.error('Error loading columns:', error);
    }
}

function showSplitParameters() {
    elements.splitParameters.style.display = 'block';
}

async function splitDataset() {
    if (!currentSessionId) {
        showError('No hay dataset cargado');
        return;
    }
    
    showLoading('split');
    hideError();
    
    try {
        const parameters = {
            test_size: parseFloat(elements.testSize.value),
            val_size: parseFloat(elements.valSize.value),
            random_state: parseInt(elements.randomState.value),
            shuffle: elements.shuffle.checked,
            stratify: elements.stratifyColumn.value || null
        };
        
        const response = await fetch(`${API_BASE_URL}/datasets/split/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: currentSessionId,
                ...parameters
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al dividir el dataset');
        }
        
        const data = await response.json();
        displayResults(data);
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading('split');
    }
}

function displayResults(data) {
    // Mostrar tamaños
    elements.trainSize.textContent = data.sizes.train.toLocaleString();
    elements.valSizeResult.textContent = data.sizes.validation.toLocaleString();
    elements.testSizeResult.textContent = data.sizes.test.toLocaleString();
    
    // Mostrar porcentajes
    elements.trainPercent.textContent = data.percentages.train + '%';
    elements.valPercent.textContent = data.percentages.validation + '%';
    elements.testPercent.textContent = data.percentages.test + '%';
    
    // Mostrar distribución si existe
    if (data.distributions && data.distributions.plots) {
        displayDistributionPlots(data.distributions.plots);
        elements.distributionSection.style.display = 'block';
    } else {
        elements.distributionSection.style.display = 'none';
    }
    
    elements.results.style.display = 'block';
}

function displayDistributionPlots(plots) {
    // Limpiar contenedor previo
    elements.plotsContainer.innerHTML = '';

    // Crear gráficas para cada conjunto
    const plotTitles = {
        'original': 'Dataset Original',
        'train': 'Train Set',
        'validation': 'Validation Set',
        'test': 'Test Set'
    };

    for (const [key, plotData] of Object.entries(plots)) {
        const plotDiv = document.createElement('div');
        plotDiv.className = 'plot-container';

        const title = document.createElement('h4');
        title.className = 'plot-title';
        title.textContent = plotTitles[key];

        const img = document.createElement('img');
        img.src = 'data:image/png;base64,' + plotData;
        img.alt = plotTitles[key];
        img.className = 'distribution-plot';

        plotDiv.appendChild(title);
        plotDiv.appendChild(img);
        elements.plotsContainer.appendChild(plotDiv);
    }
}

async function clearSession() {
    if (currentSessionId) {
        try {
            await fetch(`${API_BASE_URL}/sessions/${currentSessionId}/clear/`, {
                method: 'DELETE'
            });
        } catch (error) {
            console.error('Error clearing session:', error);
        }
    }
    
    // Resetear estado
    currentSessionId = null;
    currentDatasetInfo = null;
    
    // Ocultar secciones
    elements.datasetInfo.style.display = 'none';
    elements.splitParameters.style.display = 'none';
    elements.results.style.display = 'none';
    elements.distributionSection.style.display = 'none';
    
    // Resetear formularios
    elements.fileUpload.value = '';
    elements.testSize.value = 0.4;
    elements.testSizeValue.textContent = '40%';
    elements.valSize.value = 0.5;
    elements.valSizeValue.textContent = '50%';
    elements.randomState.value = 42;
    elements.shuffle.checked = true;
    elements.stratifyColumn.value = '';
    elements.stratifyColumn.innerHTML = '<option value="">-- Sin estratificación --</option>';
}

// Utilidades
function showError(message) {
    elements.errorText.textContent = message;
    elements.errorMessage.style.display = 'flex';
}

function hideError() {
    elements.errorMessage.style.display = 'none';
}

function showLoading(type) {
    if (type === 'upload') {
        elements.uploadLoading.style.display = 'flex';
        elements.fileUploadArea.style.opacity = '0.6';
        elements.fileUploadArea.style.pointerEvents = 'none';
    } else if (type === 'split') {
        elements.splitLoading.style.display = 'flex';
        elements.splitButton.disabled = true;
    }
}

function hideLoading(type) {
    if (type === 'upload') {
        elements.uploadLoading.style.display = 'none';
        elements.fileUploadArea.style.opacity = '1';
        elements.fileUploadArea.style.pointerEvents = 'auto';
    } else if (type === 'split') {
        elements.splitLoading.style.display = 'none';
        elements.splitButton.disabled = false;
    }
}

// Función auxiliar para formatear números
function formatNumber(num) {
    return num.toLocaleString();
}