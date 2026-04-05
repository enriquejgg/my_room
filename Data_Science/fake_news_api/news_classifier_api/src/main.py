# Importar módulos necesarios
import sys
import os

# Añadir el directorio padre al path de Python para permitir importaciones relativas
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # NO CAMBIAR ESTO !!!

# Importar módulos de Flask y otras bibliotecas necesarias
from flask import Flask, request, jsonify, send_from_directory
import joblib
import gensim
# from gensim.utils import simple_preprocess
# from gensim.parsing.preprocessing import STOPWORDS
import nltk
from nltk.corpus import stopwords
# import numpy as np
# import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import requests
from bs4 import BeautifulSoup
import re

# Descargar recursos NLTK si no están ya disponibles

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

# Crear una instancia de la aplicación Flask
app = Flask(__name__, static_folder='static')

# --- Cargamos el modelo ---
# Ruta al modelo guardado
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "model.joblib")
model = None

# Definir stopwords para preprocesamiento

try:
    stop_words = stopwords.words('english')
    stop_words.extend(['from', 'subject', 're', 'edu', 'use'])
except:
    # Fallback si datos NLTK no están disponibles
    stop_words = ['from', 'subject', 're', 'edu', 'use', 'the', 'and', 'in', 'to', 'of', 'a', 'for', 'with', 'on', 'at',
                  'this', 'that', 'by']


# Función de preprocesamiento idéntica a la utilizada en el entrenamiento
def preprocess(text):
    """Tokeniza y filtra el texto usando el mismo proceso que en el entrenamiento del modelo."""
    result = []
    for token in gensim.utils.simple_preprocess(text):
        if token not in gensim.parsing.preprocessing.STOPWORDS and len(token) > 3 and token not in stop_words:
            result.append(token)
    return result


# Configuración del Tokenizer - debe coincidir con la configuración del entrenamiento
# Crearemos un nuevo tokenizer y lo ajustaremos en la primera solicitud de predicción
MAX_VOCAB_SIZE = 110000  # Debe coincidir con total_words del training
MAX_SEQUENCE_LENGTH = 300  # Debe coincidir con max_length del training
tokenizer = None

# Definir las etiquetas de salida para ser user-friendly
LABEL_MAPPING = {
    0: "Fake News",
    1: "Real News"
}


def load_model():
    """Carga el modelo pre-entrenado desde el disco."""
    global model
    try:
        if os.path.exists(MODEL_PATH):
            model = joblib.load(MODEL_PATH)
            print(f"Model loaded successfully from {MODEL_PATH}")
        else:
            print(f"Error: Model file not found at {MODEL_PATH}")
            model = None
    except Exception as e:
        print(f"Error loading model: {e}")
        model = None


def predict_news(text_input):
    """Predice si la noticia es falsa o real basada en el texto de entrada."""
    global tokenizer

    if model is None:
        return "Model not loaded. Please check server logs."

    try:
        # Procesamos el input exactamente como en el training notebook
        if isinstance(text_input, str):
            # 1. Aplicamos preprocesamiento (tokenización y filtrado)
            tokens = preprocess(text_input)
            # 2. Unimos los tokens en una variable string
            processed_text = " ".join(tokens)
            # 3. Creamos una lista para texto procesado para una predicción
            processed_input = [processed_text]
        elif isinstance(text_input, list) and all(isinstance(item, str) for item in text_input):
            # Procesado de cada string de la lista
            processed_input = []
            for item in text_input:
                tokens = preprocess(item)
                processed_text = " ".join(tokens)
                processed_input.append(processed_text)
        else:
            return "Invalid input format. Please provide a string or a list of strings."

        # Inicializar tokenizer si no se había hecho
        if tokenizer is None:
            tokenizer = Tokenizer(num_words=MAX_VOCAB_SIZE)
            # Ajustamos el tokenizer al formato del input
            tokenizer.fit_on_texts(processed_input)

        # Convertimos secuencias de texto a integers
        sequences = tokenizer.texts_to_sequences(processed_input)

        # Hacemos el Padding de las secuencias para uniformar la longitud
        padded_sequences = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)

        # Hacer la predicción
        predictions = model.predict(padded_sequences)

        # Convertir las predicciones a 0 o 1.
        # Usamos el mismo límite que en el training (0.95)
        binary_predictions = []
        for pred in predictions:
            if pred.item() > 0.95:
                binary_predictions.append(1)  # Real news
            else:
                binary_predictions.append(0)  # Fake news

        # Mapeo a etiquetas legibles
        text_predictions = []
        for pred in binary_predictions:
            text_predictions.append(LABEL_MAPPING[pred])

        return text_predictions[0] if isinstance(text_input, str) and len(text_predictions) > 0 else text_predictions
    except Exception as e:
        return f"Error during prediction: {e}"


def scrape_article_text(url):
    """Extrae el contenido principal de texto de una URL de artículo de noticias."""
    try:
        # Los scrapers suelen configurar sus solicitudes HTTP con un User-Agent que imite el de un navegador web común.
        # Esto hace que las solicitudes parezcan legítimas y reduce la probabilidad de ser bloqueado.
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Request
        response = requests.get(url, headers=headers, timeout=10)

        # Verificar si el request tuvo éxito
        if response.status_code != 200:
            return None, f"Failed to access the URL: HTTP {response.status_code}"

        # Analizar el contenido HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Borramos el contenido de los scripts y elementos de estilo
        for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav']):
            script_or_style.decompose()

        # Extraer texto de los párrafos
        paragraphs = soup.find_all('p')

        # Si no hay párrafos obtenemos la totalidad del texto
        if not paragraphs:
            article_text = soup.get_text()
        else:
            article_text = ' '.join([p.get_text() for p in paragraphs])

        # Limpiado del texto
        # Borramos espacio en blanco adicional
        article_text = re.sub(r'\s+', ' ', article_text).strip()

        # Si el texto es demasiado corto puede no ser contenido válido
        if len(article_text) < 100:
            # Seleccionamos la totalidad del texto
            article_text = soup.body.get_text() if soup.body else soup.get_text()
            article_text = re.sub(r'\s+', ' ', article_text).strip()

        if len(article_text) < 50:
            return None, "Could not extract sufficient text from the URL"

        return article_text, None
    except requests.exceptions.RequestException as e:
        return None, f"Request error: {str(e)}"
    except Exception as e:
        return None, f"Error scraping article: {str(e)}"

# Cargar el modelo al iniciar la aplicación
load_model()


# --- Serve Frontend ---
# Esta ruta sirve el archivo index.html desde la carpeta estática cuando se accede a la raíz del sitio.
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')


# --- REST API Endpoint for Text Prediction ---
# Este endpoint maneja las solicitudes POST para hacer predicciones basadas en texto.
@app.route("/predict", methods=["POST"])
def handle_predict():
    # Maneja las solicitudes de predicción al endpoint /predict
    # Verifica si la solicitud es JSON
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    # Verifica si el campo 'text' está presente en los datos JSON
    if "text" not in data:
        return jsonify({"error": "Missing 'text' field in JSON payload"}), 400

    # Extrae el texto de los datos JSON
    text_input = data["text"]

    # Verifica si el texto es una cadena o una lista de cadenas
    if not (isinstance(text_input, str) or \
            (isinstance(text_input, list) and all(isinstance(item, str) for item in text_input))):
        return jsonify({"error": "'text' field must be a string or a list of strings"}), 400

    # Carga el modelo si no está cargado
    if model is None:
        load_model()
        if model is None:
            return jsonify({"error": "Model is not loaded. Cannot perform prediction."}), 503

    # Realiza la predicción con el texto proporcionado
    prediction_result = predict_news(text_input)

    # Verifica si hubo un error en la predicción
    if isinstance(prediction_result, str) and ("Error" in prediction_result or "Model not loaded" in prediction_result):
        return jsonify({"error": prediction_result}), 500

    # Devuelve el resultado de la predicción
    return jsonify({"prediction": prediction_result}), 200


# --- REST API Endpoint for URL Prediction ---
# Este endpoint maneja las solicitudes POST para hacer predicciones basadas en el contenido de una URL.
@app.route("/predict_url", methods=["POST"])
def handle_predict_url():
    # Maneja las solicitudes de predicción para URLs al endpoint /predict_url.
    # Verifica si la solicitud es JSON
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    # Obtiene los datos JSON de la solicitud
    data = request.get_json()
    # Verifica si el campo 'url' está presente en los datos JSON
    if "url" not in data:
        return jsonify({"error": "Missing 'url' field in JSON payload"}), 400

    # Extrae la URL de los datos JSON
    url = data["url"]

    # Verifica si la URL es una cadena
    if not isinstance(url, str):
        return jsonify({"error": "'url' field must be a string"}), 400

    # Extrae el texto del artículo de la URL
    article_text, error_message = scrape_article_text(url)

    # Verifica si hubo un error al extraer el texto del artículo
    if article_text is None:
        return jsonify({
            "error": error_message,
            "suggestion": "This website may be protected against scraping. Try copying the text manually and using the Text Input tab instead."
        }), 400

    # Usa la función de predicción existente con el texto extraído
    if model is None:
        load_model()
        if model is None:
            return jsonify({"error": "Model is not loaded. Cannot perform prediction."}), 503

    # Realiza la predicción con el texto extraído
    prediction_result = predict_news(article_text)

    # Verifica si hubo un error en la predicción
    if isinstance(prediction_result, str) and ("Error" in prediction_result or "Model not loaded" in prediction_result):
        return jsonify({"error": prediction_result}), 500

    # Devuelve el resultado de la predicción junto con una vista previa del texto extraído
    return jsonify({
        "prediction": prediction_result,
        "extracted_text_preview": article_text[:200] + "..." if len(article_text) > 200 else article_text
    }), 200


# --- End of REST API Endpoint ---

# Este bloque se ejecuta solo si el script se ejecuta directamente (no si se importa como módulo)
if __name__ == '__main__':
    print("Starting Flask server...")
    if model is None:
        print("Warning: Model was not loaded successfully. API might not work as expected.")
    # Inicia el servidor Flask en el host y puerto especificados
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5006)), debug=False)


