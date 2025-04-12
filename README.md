# KIU_AI_PoweredApps_NotebookML_Clone

## Description

This application allows users to upload text documents (.txt) or PDFs (.pdf) and ask questions about their content. It uses a Retrieval-Augmented Generation (RAG) approach, leveraging vector embeddings (via `sentence-transformers` and `FAISS`) and a large language model (via the OpenAI API) to provide answers based *only* on the information present in the uploaded documents, and tell them if not possible and only then proceed to answer with general knowledge.

The application consists of:
1.  A Python Flask backend (`app.py`, `rag_processor.py`) that handles document processing, embedding, storage, and querying the OpenAI API.
2.  A Python Tkinter GUI (`gui.py`) that provides a user-friendly interface for uploading files and interacting with the backend in a chat format.

## Prerequisites

* Python 3.7+
* An OpenAI API Key

## Setup Instructions

1.  **Clone the Repository (if applicable):**
    ```bash
    git clone https://github.com/nikakogho/KIU_AI_PoweredApps_NotebookML_Clone
    cd KIU_AI_PoweredApps_NotebookML_Clone
    ```

2.  **Create and Activate Virtual Environment:**
    * Create the environment:
        ```bash
        python -m venv venv
        ```
    * Activate the environment:
        * **Windows (Command Prompt/PowerShell):**
            ```bash
            .\venv\Scripts\activate
            ```
        * **Linux/macOS (Bash/Zsh):**
            ```bash
            source venv/bin/activate
            ```
        *(You should see `(venv)` at the beginning of your terminal prompt.)*

3.  **Install Dependencies:**
    * Ensure `pip` is up-to-date:
        ```bash
        python -m pip install --upgrade pip
        ```
    * Install required packages from `requirements.txt`:
        ```bash
        pip install -r requirements.txt
        ```

4.  **Configure OpenAI API Key:**
    * Create a file named `.env` in the root directory of the project.
    * Add the following line to the `.env` file, replacing `your_openai_api_key_here` with your actual key:
        ```
        OPENAI_API_KEY=your_openai_api_key_here
        ```

## Running the Application

You need to run the backend server and the GUI application separately, typically in two different terminals. **Make sure the virtual environment is activated in both terminals.**

1.  **Terminal 1: Start the Backend Server:**
    * Navigate to the project directory.
    * Activate the virtual environment (if not already active).
    * Run the Flask app:
        ```bash
        python app.py
        ```
    * Wait until you see output indicating the server is running (e.g., `* Running on http://...`). Leave this terminal running.

2.  **Terminal 2: Start the GUI Application:**
    * Open a **new** terminal.
    * Navigate to the project directory.
    * Activate the virtual environment.
    * Run the Tkinter GUI app:
        ```bash
        python gui.py
        ```
    * The GUI window should appear.

## How to Use

1.  **Ensure Backend is Running:** Make sure the backend server (from Terminal 1) is running before starting and using the GUI.
2.  **Upload Document:** Click the "Upload File (.txt, .pdf)" button in the GUI. Select a valid document file.
3.  **Wait for Processing:** The status bar will indicate "Uploading..." and then "Successfully processed..." once the backend has handled the file. The "Send" button will become active.
4.  **Ask Questions:** Type your question about the document content into the input field at the bottom.
5.  **Send Query:** Press Enter or click the "Send" button.
6.  **View Answer:** Your question will appear in the chat display, followed by the backend's response ("Bot: ..."). The response is generated based *only* on the content of the uploaded document(s).
7.  **Continue Chatting:** Ask follow-up questions as needed.

## app.py

Backend with 3 endpoints:

/heartbeat GET - check that server is alive

/upload POST - upload txt or pdf

/query POST - ask a question

## rag_processor.py

Uses vector store to order and answer prompts from a query

main functions are `add_document` and `answer_query`
Adds basic citation (which part of document mentions answer to query)

## gui.py

Friendly UI that calls this server
![showoff](showoff/showoff.png)
