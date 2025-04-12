import os
import logging
import numpy as np
import faiss
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import pickle # To save/load Python objects (like the doc list)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RAGProcessor:
    """
    Handles document processing, embedding, vector storage, retrieval,
    and interaction with OpenAI for RAG-based question answering.
    """
    def __init__(self, embedding_model_name='all-MiniLM-L6-v2', vector_store_path='data/vector_store'):
        """
        Initializes the RAG Processor.

        Args:
            embedding_model_name (str): Name of the Sentence Transformer model to use.
            vector_store_path (str): Directory to save/load the FAISS index and document chunks.
        """
        self.vector_store_path = vector_store_path
        self.index_file = os.path.join(vector_store_path, 'faiss_index.idx')
        self.doc_chunks_file = os.path.join(vector_store_path, 'doc_chunks.pkl')

        logging.info(f"Loading embedding model: {embedding_model_name}")
        try:
            self.embedding_model = SentenceTransformer(embedding_model_name)
            # Get embedding dimension dynamically
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            logging.info(f"Embedding model loaded. Dimension: {self.embedding_dim}")
        except Exception as e:
            logging.error(f"Failed to load SentenceTransformer model '{embedding_model_name}': {e}", exc_info=True)
            raise # Re-raise the exception to be caught by the caller (app.py)

        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        if not self.openai_client.api_key:
             logging.warning("OpenAI API key not found in environment variables. Querying will fail.")
             # Consider raising an error if OpenAI is essential for initialization

        # Load existing vector store or initialize a new one
        self.index = None
        self.doc_chunks = [] # List to store {'text': chunk_text, 'source': filename}
        self._load_vector_store()

    def _load_vector_store(self):
        """Loads the FAISS index and document chunks from disk if they exist."""
        try:
            if os.path.exists(self.index_file) and os.path.exists(self.doc_chunks_file):
                logging.info(f"Loading FAISS index from {self.index_file}")
                self.index = faiss.read_index(self.index_file)
                logging.info(f"Loading document chunks from {self.doc_chunks_file}")
                with open(self.doc_chunks_file, 'rb') as f:
                    self.doc_chunks = pickle.load(f)
                logging.info(f"Loaded {self.index.ntotal} vectors and {len(self.doc_chunks)} document chunks.")
                # Sanity check
                if self.index.ntotal != len(self.doc_chunks):
                    logging.warning("Mismatch between index size and number of document chunks. Re-indexing might be needed.")
                    # Handle this mismatch? For now, log a warning.
                if self.index.d != self.embedding_dim:
                    logging.warning(f"Index dimension ({self.index.d}) does not match model dimension ({self.embedding_dim}). Re-initializing.")
                    self._initialize_vector_store() # Re-initialize if dimensions mismatch

            else:
                logging.info("No existing vector store found. Initializing a new one.")
                self._initialize_vector_store()
        except Exception as e:
            logging.error(f"Error loading vector store from {self.vector_store_path}: {e}", exc_info=True)
            logging.info("Initializing a new vector store due to loading error.")
            self._initialize_vector_store()


    def _initialize_vector_store(self):
        """Initializes an empty FAISS index."""
        logging.info(f"Creating a new FAISS index with dimension {self.embedding_dim}.")
        # Using IndexFlatL2 - simple L2 distance search.
        # For larger datasets, consider more advanced index types like IndexIVFFlat.
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.doc_chunks = []


    def _save_vector_store(self):
        """Saves the FAISS index and document chunks to disk."""
        try:
            logging.info(f"Saving FAISS index to {self.index_file}")
            faiss.write_index(self.index, self.index_file)
            logging.info(f"Saving document chunks to {self.doc_chunks_file}")
            with open(self.doc_chunks_file, 'wb') as f:
                pickle.dump(self.doc_chunks, f)
            logging.info("Vector store saved successfully.")
        except Exception as e:
            logging.error(f"Error saving vector store to {self.vector_store_path}: {e}", exc_info=True)


    def _extract_text_from_pdf(self, file_path):
        """Extracts text from a PDF file."""
        logging.info(f"Extracting text from PDF: {file_path}")
        text = ""
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n" # Add newline between pages
            logging.info(f"Successfully extracted text from {len(reader.pages)} pages in {file_path}")
            return text
        except Exception as e:
            logging.error(f"Failed to extract text from PDF {file_path}: {e}", exc_info=True)
            return "" # Return empty string on failure

    def _extract_text_from_txt(self, file_path):
        """Extracts text from a TXT file."""
        logging.info(f"Extracting text from TXT: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            logging.info(f"Successfully extracted text from {file_path}")
            return text
        except Exception as e:
            logging.error(f"Failed to read text file {file_path}: {e}", exc_info=True)
            return "" # Return empty string on failure

    def _split_text_into_chunks(self, text, chunk_size=500, chunk_overlap=50):
        """
        Splits text into overlapping chunks.
        A simple implementation, more sophisticated methods exist (e.g., LangChain's splitters).
        """
        # Basic splitting by characters - consider splitting by paragraphs or sentences
        # for potentially better semantic coherence within chunks.
        if not text:
            return []

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - chunk_overlap # Move start forward, considering overlap
            if start < 0: # Prevent infinite loop if overlap >= size
                 start = end
        logging.info(f"Split text into {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap}).")
        return chunks


    def add_document(self, file_path):
        """
        Loads a document, extracts text, splits into chunks,
        embeds chunks, and adds them to the vector store.
        """
        logging.info(f"Processing document: {file_path}")
        filename = os.path.basename(file_path)
        text = ""
        if filename.lower().endswith('.pdf'):
            text = self._extract_text_from_pdf(file_path)
        elif filename.lower().endswith('.txt'):
            text = self._extract_text_from_txt(file_path)
        else:
            logging.warning(f"Unsupported file type skipped: {filename}")
            return # Or raise an error

        if not text:
            logging.warning(f"No text extracted from {filename}. Skipping.")
            return

        # Split text into manageable chunks
        chunks = self._split_text_into_chunks(text)
        if not chunks:
            logging.warning(f"No chunks generated for {filename}. Skipping.")
            return

        # Generate embeddings for the chunks
        logging.info(f"Generating embeddings for {len(chunks)} chunks from {filename}...")
        try:
            chunk_embeddings = self.embedding_model.encode(chunks, show_progress_bar=True)
            # Ensure embeddings are float32, FAISS requirement
            chunk_embeddings = np.array(chunk_embeddings).astype('float32')
            logging.info(f"Generated {chunk_embeddings.shape[0]} embeddings.")
        except Exception as e:
            logging.error(f"Failed to generate embeddings for {filename}: {e}", exc_info=True)
            return # Skip adding this document if embedding fails

        # Add embeddings to FAISS index
        if chunk_embeddings.shape[0] > 0:
            self.index.add(chunk_embeddings)
            # Store the corresponding text chunks and their source
            for i, chunk in enumerate(chunks):
                self.doc_chunks.append({'text': chunk, 'source': filename})
            logging.info(f"Added {chunk_embeddings.shape[0]} vectors to FAISS index. Total vectors: {self.index.ntotal}")

            # Save the updated index and chunks
            self._save_vector_store()
        else:
            logging.warning(f"No embeddings were generated or added for {filename}.")


    def retrieve_relevant_chunks(self, query, k=5):
        """
        Embeds the query and retrieves the top k relevant chunks from the vector store.
        """
        if not query:
            return []

        logging.info(f"Embedding query: '{query}'")
        try:
            query_embedding = self.embedding_model.encode([query])
            query_embedding = np.array(query_embedding).astype('float32')
            logging.info("Query embedded successfully.")
        except Exception as e:
            logging.error(f"Failed to embed query '{query}': {e}", exc_info=True)
            return [] # Return empty list if embedding fails

        if self.index is None or self.index.ntotal == 0:
            logging.warning("Vector store is empty or not initialized. Cannot retrieve chunks.")
            return []

        # Search the FAISS index
        logging.info(f"Searching index for {k} nearest neighbors...")
        try:
            # D: distances, I: indices of neighbors
            distances, indices = self.index.search(query_embedding, k)
            logging.info(f"Search complete. Found indices: {indices}")

            # Retrieve the actual text chunks using the indices
            # indices[0] because we searched for a single query vector
            relevant_chunks = [self.doc_chunks[i] for i in indices[0] if 0 <= i < len(self.doc_chunks)]

            # Optional: Filter by distance threshold if needed
            # threshold = 1.0 # Example threshold for L2 distance (lower is better)
            # relevant_chunks = [self.doc_chunks[indices[0][j]] for j, dist in enumerate(distances[0]) if dist < threshold and 0 <= indices[0][j] < len(self.doc_chunks)]

            logging.info(f"Retrieved {len(relevant_chunks)} relevant chunks.")
            return relevant_chunks
        except Exception as e:
            logging.error(f"Error during FAISS search for query '{query}': {e}", exc_info=True)
            return []


    def answer_query(self, query):
        """
        Answers a query using the RAG approach:
        1. Retrieve relevant document chunks.
        2. Construct a prompt for the LLM.
        3. Call the OpenAI API to get the answer.
        """
        logging.info(f"Answering query: '{query}'")

        # 1. Retrieve relevant context
        relevant_chunks = self.retrieve_relevant_chunks(query, k=5) # Get top 5 chunks

        if not relevant_chunks:
            logging.warning("No relevant chunks found for the query.")
            # Decide how to respond: could be a fixed message or still ask the LLM
            # Let's try asking the LLM anyway, but with a specific instruction
            context = "No relevant information found in the provided documents."
        else:
            # Combine chunks into a single context string
            context = "\n\n".join([chunk['text'] for chunk in relevant_chunks])
            sources = list(set([chunk['source'] for chunk in relevant_chunks])) # Get unique source filenames
            logging.info(f"Context built from sources: {sources}")


        logging.info(f"Context for query: {context[:1000]}...") # Log first 1000 chars of context for brevity

        # 2. Construct the prompt
        prompt = f"""
        You are an assistant answering questions based ONLY on the provided context and some common knowledge.
        Try very hard to answer only with context and inference upon context.
        If the answer is not found by combination of context and inference and you had to instead rely on commond knowledge outside of it, say "I could not find the answer in the provided documents, but I can answer from common knowledge:" and proceed with answer.

        Context:
        ---
        {context}
        ---

        Question: {query}

        Answer:
        """

        logging.info("Sending request to OpenAI API...")
        # 3. Call OpenAI API
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo", # Or use "gpt-4" if preferred/available
                messages=[
                    {"role": "system", "content": "You are a helpful assistant answering questions based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2, # Lower temperature for more factual answers
                max_tokens=250 # Adjust as needed
            )
            answer = response.choices[0].message.content.strip()
            logging.info("Received response from OpenAI API.")
            return answer

        except Exception as e:
            logging.error(f"Error calling OpenAI API: {e}", exc_info=True)
            return "Sorry, I encountered an error while trying to generate an answer."

