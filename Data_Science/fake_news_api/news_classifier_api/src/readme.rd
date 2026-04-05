# Fake News Classifier

A machine learning-powered web application that classifies news articles as either "Real News" or "Fake News" using natural language processing and deep learning techniques.

## Features

- **Text Input Classification**: Directly paste news article text for instant classification
- **URL Analysis**: Input a news article URL to automatically scrape and classify the content
- **Real-time Predictions**: Get immediate feedback on whether the news is likely real or fake
- **User-Friendly Interface**: Clean, responsive web interface with tabbed navigation
- **Text Preprocessing**: Advanced NLP preprocessing using Gensim and NLTK
- **Deep Learning Model**: Uses a pre-trained neural network model for accurate predictions

## Project Structure

```
├── main.py                 # Flask backend server
├── index.html             # Frontend web interface
├── models/
│   └── model.joblib       # Pre-trained ML model (not included)
└── requirements.txt       # Python dependencies
```

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone or download the project files**

2. **Install required dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Download NLTK data** (if not automatically downloaded):
   ```python
   python -c "import nltk; nltk.download('stopwords')"
   ```

4. **Place your trained model**:
   - Ensure your trained model file (`model.joblib`) is located in the `models/` directory
   - The model should be trained with the same preprocessing pipeline used in this application

5. **Prepare the static folder**:
   - Create a `static` folder in the project root directory
   - Move `index.html` into the `static` folder:
     ```bash
     mkdir static
     mv index.html static/
     ```

## Usage

### Starting the Server

Run the Flask application:

```bash
python main.py
```

The server will start on `http://0.0.0.0:5006` by default.

### Accessing the Web Interface

1. Open your web browser
2. Navigate to `http://localhost:5006`
3. You'll see two input options:
   - **Text Input**: Paste news article text directly
   - **URL Input**: Enter a news article URL

### Using the Classifier

#### Text Input Method:
1. Click on the "Text Input" tab
2. Paste or type the news article text
3. Click "Classify News"
4. View the prediction result

#### URL Input Method:
1. Click on the "URL Input" tab
2. Enter the complete URL of a news article
3. Click "Analyze URL"
4. The system will scrape the article content and display the prediction
5. A preview of the extracted text will be shown

## API Endpoints

### POST /predict
Classifies news text directly.

**Request Body**:
```json
{
  "text": "Your news article text here..."
}
```

**Response**:
```json
{
  "prediction": "Real News" or "Fake News"
}
```

### POST /predict_url
Scrapes and classifies news from a URL.

**Request Body**:
```json
{
  "url": "https://example.com/news-article"
}
```

**Response**:
```json
{
  "prediction": "Real News" or "Fake News",
  "extracted_text_preview": "First 200 characters of the extracted text..."
}
```

## How It Works

1. **Text Preprocessing**:
   - Tokenization using Gensim's `simple_preprocess`
   - Removal of stopwords and short tokens (< 3 characters)
   - Filtering using NLTK stopwords corpus

2. **Text Vectorization**:
   - Keras Tokenizer converts text to sequences
   - Sequences are padded to uniform length (300 tokens)
   - Vocabulary size limited to 110,000 words

3. **Classification**:
   - Pre-trained neural network model makes predictions
   - Threshold of 0.95 determines Real vs Fake classification
   - Results are returned with user-friendly labels

4. **Web Scraping** (for URL input):
   - Requests library fetches the webpage
   - BeautifulSoup parses HTML content
   - Extracts text from paragraph tags
   - Cleans and formats the extracted text

## Model Requirements

The classifier expects a pre-trained model saved as `model.joblib` in the `models/` directory. The model should be:

- A Keras/TensorFlow neural network
- Trained with the same preprocessing pipeline (Gensim + NLTK)
- Compatible with input sequences of length 300
- Trained on a vocabulary size of 110,000 words

## Configuration

Key parameters in `main.py`:

- `MAX_VOCAB_SIZE = 110000`: Maximum vocabulary size
- `MAX_SEQUENCE_LENGTH = 300`: Maximum sequence length for padding
- `PORT = 5006`: Default server port
- Prediction threshold: 0.95 for classifying as "Real News"

## Troubleshooting

### Model Not Loading
- Ensure `model.joblib` exists in the `models/` directory
- Check that the model file is not corrupted
- Verify the model was saved using joblib

### URL Scraping Issues
Some websites may block scraping attempts. If this occurs:
- The system will suggest using the Text Input tab instead
- Manually copy the article text and paste it into the Text Input field

### Missing NLTK Data
If you see errors about missing stopwords:
```bash
python -c "import nltk; nltk.download('stopwords')"
```

### Port Already in Use
If port 5006 is occupied, set a different port:
```bash
PORT=8080 python main.py
```

## Security Notes

- The web scraper includes a User-Agent header to avoid being blocked
- Input validation is performed on all API endpoints
- The application uses a 10-second timeout for URL requests

## Dependencies

See `requirements.txt` for the complete list of dependencies.

## License

This project is provided as-is for educational and research purposes.

## Contributing

Contributions, issues, and feature requests are welcome!

## Contact

For questions or support, please open an issue in the project repository.