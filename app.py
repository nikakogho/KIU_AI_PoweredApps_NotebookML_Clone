import os
import logging
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from rag_processor import RAGProcessor # We will create this class in rag_processor.py

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables (especially OpenAI API key)
load_dotenv()

# --- Configuration ---
UPLOAD_FOLDER = 'data/uploads' # Store uploaded files here
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
# Ensure data directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('data/vector_store', exist_ok=True) # For FAISS index etc.

# --- Initialize Flask App ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Initialize RAG Processor ---
# This object will hold the logic for processing, embedding, storing, and querying
try:
    rag_processor = RAGProcessor(
        embedding_model_name='all-MiniLM-L6-v2', # A popular sentence-transformer model
        vector_store_path='data/vector_store'
    )
    logging.info("RAG Processor initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize RAG Processor: {e}", exc_info=True)
    # Depending on the desired behavior, you might want to exit or run in a limited mode.
    # For now, we'll let it potentially fail later if used.
    rag_processor = None

# --- Helper Function ---
def allowed_file(filename):
    """Checks if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    """
    Simple health check endpoint to verify the server is running.
    """
    return jsonify({"status": "ok"}), 200

# --- API Endpoints ---
@app.route('/upload', methods=['POST'])
def upload_document():
    """
    API endpoint to upload a document (txt or pdf).
    Processes the document and adds it to the vector store.
    """
    if rag_processor is None:
         return jsonify({"error": "RAG Processor not initialized"}), 500

    if request.files['file'] is None:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        try:
            # Save the uploaded file temporarily
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            logging.info(f"File '{filename}' uploaded successfully.")

            # Process the document using the RAG Processor
            rag_processor.add_document(filename)
            logging.info(f"Document '{filename}' processed and added to vector store.")

            # Optional: Remove the temp file after processing if desired
            # os.remove(filename)

            return jsonify({"message": f"Document '{file.filename}' uploaded and processed successfully."}), 200

        except Exception as e:
            logging.error(f"Error processing file {file.filename}: {e}", exc_info=True)
            return jsonify({"error": f"Failed to process file: {str(e)}"}), 500
    else:
        return jsonify({"error": "File type not allowed. Please upload .txt or .pdf"}), 400

@app.route('/query', methods=['POST'])
def query_documents():
    """
    API endpoint to ask a question based on the uploaded documents.
    Retrieves relevant context and generates an answer using OpenAI.
    """
    if rag_processor is None:
         return jsonify({"error": "RAG Processor not initialized"}), 500

    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    query_text = data['query']
    logging.info(f"Received query: '{query_text}'")

    try:
        # Get the answer from the RAG processor
        answer = rag_processor.answer_query(query_text)
        logging.info(f"Generated answer: '{answer}'")
        return jsonify({"answer": answer}), 200

    except Exception as e:
        logging.error(f"Error answering query '{query_text}': {e}", exc_info=True)
        return jsonify({"error": f"Failed to answer query: {str(e)}"}), 500

# --- Main Execution ---
if __name__ == '__main__':
    # Make sure the OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        logging.error("FATAL ERROR: OPENAI_API_KEY environment variable not set.")
        # Exit if the key is essential for startup, or handle appropriately
    else:
        logging.info("OpenAI API key found.")

    # Run the Flask app
    # Use host='0.0.0.0' to make it accessible on your network
    # Use debug=True for development (auto-reloads), but turn off for production
    app.run(host='0.0.0.0', port=5000, debug=True)
