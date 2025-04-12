import tkinter as tk
from tkinter import ttk # For themed widgets
from tkinter import filedialog # For open file dialog
from tkinter import scrolledtext # For scrollable text area
import os # To get base filename
import requests # To make HTTP requests to backend
import threading # To run network calls in background
import json # To parse JSON responses

# --- Configuration ---
# Make sure this matches the address your Flask backend is running on
BACKEND_URL = "http://localhost:5000"


class RagAppGUI:
    """
    A Tkinter GUI for interacting with the RAG backend.
    Allows uploading files and asking questions in a chat interface.
    """
    def __init__(self, root):
        """
        Initializes the GUI components.

        Args:
            root: The main Tkinter window (tk.Tk instance).
        """
        self.root = root
        self.root.title("RAG Document Q&A")
        self.root.geometry("700x600") # Set initial window size

        self.backend_upload_url = f"{BACKEND_URL}/upload"
        self.backend_query_url = f"{BACKEND_URL}/query"
        self.current_file = None # Store the path of the uploaded file

        # --- Style Configuration (Optional) ---
        style = ttk.Style()
        # print(style.theme_names()) # See available themes
        # style.theme_use('clam') # Example: Try different themes ('vista', 'xpnative', 'clam', 'alt', 'default', 'classic')

        # --- Main Frames ---
        # Configure grid layout for the main window
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0) # Top frame doesn't expand vertically
        self.root.rowconfigure(1, weight=1) # Middle frame (chat) expands vertically
        self.root.rowconfigure(2, weight=0) # Bottom frame doesn't expand vertically
        self.root.rowconfigure(3, weight=0) # Status frame doesn't expand vertically

        # Top Frame: File Upload
        self.top_frame = ttk.Frame(self.root, padding="10")
        self.top_frame.grid(row=0, column=0, sticky="ew") # Sticky East-West
        self.top_frame.columnconfigure(1, weight=1) # Make label expand

        # Middle Frame: Chat Display
        self.middle_frame = ttk.Frame(self.root, padding="10")
        self.middle_frame.grid(row=1, column=0, sticky="nsew") # Sticky North-South-East-West
        self.middle_frame.columnconfigure(0, weight=1)
        self.middle_frame.rowconfigure(0, weight=1)

        # Bottom Frame: User Input
        self.bottom_frame = ttk.Frame(self.root, padding="10")
        self.bottom_frame.grid(row=2, column=0, sticky="ew")
        self.bottom_frame.columnconfigure(0, weight=1) # Make entry expand

        # Status Frame: Status Bar
        self.status_frame = ttk.Frame(self.root, padding="5")
        self.status_frame.grid(row=3, column=0, sticky="ew")
        self.status_frame.columnconfigure(0, weight=1)

        # --- Widgets ---

        # Top Frame Widgets
        # *** Connect button command to the actual function ***
        self.upload_button = ttk.Button(self.top_frame, text="Upload File (.txt, .pdf)", command=self.select_and_upload_file)
        self.upload_button.grid(row=0, column=0, padx=(0, 10))

        self.file_label = ttk.Label(self.top_frame, text="No file selected.")
        self.file_label.grid(row=0, column=1, sticky="ew")

        # Middle Frame Widgets
        self.chat_display = scrolledtext.ScrolledText(
            self.middle_frame,
            wrap=tk.WORD, # Wrap text at word boundaries
            state='disabled', # Start as read-only
            height=15, # Initial height
            bg="#f0f0f0", # Lighter background for read-only area
            relief=tk.FLAT # Flat border
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew")
        # Add tags for styling chat messages
        self.chat_display.tag_configure("user", foreground="#00008B", font=("Helvetica", 10, "bold")) # Dark Blue
        self.chat_display.tag_configure("bot", foreground="#006400") # Dark Green
        self.chat_display.tag_configure("error", foreground="#DC143C", font=("Helvetica", 9, "bold")) # Crimson Red
        self.chat_display.tag_configure("status", foreground="#696969", font=("Helvetica", 9, "italic")) # Dim Gray

        # Bottom Frame Widgets
        self.query_entry = ttk.Entry(self.bottom_frame, width=60, font=("Helvetica", 10))
        self.query_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.query_entry.bind("<Return>", self.send_query_placeholder) # Bind Enter key (placeholder for now)

        self.send_button = ttk.Button(self.bottom_frame, text="Send", command=self.send_query_placeholder) # Placeholder for now
        self.send_button.grid(row=0, column=1)
        self.send_button.config(state=tk.DISABLED) # Start disabled until file is uploaded

        # Status Frame Widgets
        self.status_label = ttk.Label(self.status_frame, text="Status: Ready", anchor="w") # Anchor West (left)
        self.status_label.grid(row=0, column=0, sticky="ew")

        # --- Initial Message ---
        self.add_message("Welcome! Please upload a .txt or .pdf document to begin.", "status")

    # --- File Upload Methods ---

    def select_and_upload_file(self):
        """Opens file dialog, updates label, and starts upload thread."""
        self.update_status("Selecting file...")
        filepath = filedialog.askopenfilename(
            title="Select a Document",
            filetypes=(("Text files", "*.txt"), ("PDF files", "*.pdf"), ("All files", "*.*"))
        )
        if not filepath:
            self.update_status("File selection cancelled.")
            return

        self.current_file = filepath
        filename = os.path.basename(filepath)
        self.file_label.config(text=f"Selected: {filename}")
        self.add_message(f"Attempting to upload '{filename}'...", "status")
        self.update_status(f"Uploading {filename}...")
        self.send_button.config(state=tk.DISABLED) # Disable send while uploading
        self.upload_button.config(state=tk.DISABLED) # Disable upload while uploading

        # Run the upload in a separate thread to avoid freezing the GUI
        upload_thread = threading.Thread(target=self._upload_file_thread, args=(filepath, filename), daemon=True)
        upload_thread.start()

    def _upload_file_thread(self, filepath, filename):
        """
        Handles the actual file upload in a background thread.

        Args:
            filepath (str): The full path to the file to upload.
            filename (str): The base name of the file.
        """
        try:
            with open(filepath, 'rb') as f:
                files = {'file': (filename, f)}
                response = requests.post(self.backend_upload_url, files=files, timeout=120) # Add timeout
                response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

                # Process successful response
                try:
                    response_json = response.json()
                    message = response_json.get("message", "Upload successful, but no message received.")
                    # Schedule GUI update back on the main thread
                    self.root.after(0, self._update_gui_after_upload, True, message, filename)
                except json.JSONDecodeError:
                     # Handle cases where response is not JSON
                     self.root.after(0, self._update_gui_after_upload, True, f"Upload successful (Status {response.status_code}), but response was not valid JSON.", filename)

        except requests.exceptions.ConnectionError:
            error_message = f"Upload Error: Could not connect to the backend at {self.backend_upload_url}. Is it running?"
            self.root.after(0, self._update_gui_after_upload, False, error_message, filename)
        except requests.exceptions.Timeout:
             error_message = f"Upload Error: The request timed out while uploading {filename}."
             self.root.after(0, self._update_gui_after_upload, False, error_message, filename)
        except requests.exceptions.HTTPError as e:
             # Handle specific HTTP errors reported by the backend
             error_message = f"Upload Error: Backend returned status {e.response.status_code}."
             try:
                 # Try to get error detail from backend JSON response
                 error_detail = e.response.json().get("error", "No details provided.")
                 error_message += f" Detail: {error_detail}"
             except json.JSONDecodeError:
                 error_message += " Could not parse error details from response."
             self.root.after(0, self._update_gui_after_upload, False, error_message, filename)
        except requests.exceptions.RequestException as e:
            # Catch other potential requests errors
            error_message = f"Upload Error: An unexpected network error occurred: {e}"
            self.root.after(0, self._update_gui_after_upload, False, error_message, filename)
        except Exception as e:
            # Catch other potential errors (e.g., file reading issues)
            error_message = f"Upload Error: An unexpected error occurred: {e}"
            self.root.after(0, self._update_gui_after_upload, False, error_message, filename)

    def _update_gui_after_upload(self, success, message, filename):
        """
        Updates the GUI status and chat display after upload attempt.
        This method is scheduled to run on the main GUI thread.
        """
        if success:
            self.update_status(f"Successfully processed '{filename}'. Ready to chat.")
            self.add_message(f"'{filename}' processed successfully.", "status")
            self.send_button.config(state=tk.NORMAL) # Enable send button
        else:
            self.update_status(f"Failed to process '{filename}'. See details below.")
            self.add_message(message, "error") # Display the error message in chat
            self.file_label.config(text="No file selected.") # Reset file label on error
            self.current_file = None # Reset current file on error

        self.upload_button.config(state=tk.NORMAL) # Re-enable upload button


    # --- Query Methods (Placeholders for now) ---

    def send_query_placeholder(self, event=None): # Add event=None for key binding
        """Placeholder for sending query logic."""
        if self.send_button['state'] == tk.DISABLED:
             self.update_status("Please wait for the current operation or upload a file first.")
             return

        query = self.query_entry.get().strip()
        if not query:
            return # Don't send empty messages

        print(f"Sending query (placeholder): {query}")
        self.add_message(f"You: {query}", "user") # Display user query
        self.query_entry.delete(0, tk.END) # Clear input field
        self.update_status("Placeholder: Query sent...")
        self.send_button.config(state=tk.DISABLED) # Disable send while processing
        self.query_entry.config(state=tk.DISABLED) # Disable entry while processing

        # Simulate bot response
        self.root.after(1000, lambda: self.add_message(f"Bot: Placeholder response to '{query}'", "bot"))
        self.root.after(1000, lambda: self.update_status("Status: Ready"))
        self.root.after(1000, lambda: self.send_button.config(state=tk.NORMAL)) # Re-enable
        self.root.after(1000, lambda: self.query_entry.config(state=tk.NORMAL)) # Re-enable


    # --- Utility Methods ---

    def add_message(self, message, tag):
        """Adds a message to the chat display with specified tag for styling."""
        self.chat_display.config(state='normal') # Enable editing
        # Add message and ensure separation with newlines
        if not self.chat_display.get('1.0', tk.END).endswith('\n\n'):
             # Add extra newline if needed before inserting
             if not self.chat_display.get('1.0', tk.END).endswith('\n'):
                 self.chat_display.insert(tk.END, '\n')
             self.chat_display.insert(tk.END, '\n')

        self.chat_display.insert(tk.END, message, tag)
        self.chat_display.config(state='disabled') # Disable editing
        self.chat_display.see(tk.END) # Scroll to the bottom


    def update_status(self, message):
        """Updates the status bar label."""
        self.status_label.config(text=f"Status: {message}")
        self.root.update_idletasks() # Force GUI update


# --- Main Execution ---
if __name__ == "__main__":
    # --- Backend Check (Optional but helpful) ---
    backend_ok = False
    try:
        # Simple check if backend root is reachable before starting GUI
        ping_response = requests.get(BACKEND_URL, timeout=2)
        if ping_response.status_code == 200 or ping_response.status_code == 404: # Allow 404 on root
             print(f"Backend detected at {BACKEND_URL}")
             backend_ok = True
        else:
             print(f"Warning: Backend responded with status {ping_response.status_code} at {BACKEND_URL}")
             # Decide if you want to proceed even if backend isn't fully responsive
             # backend_ok = True # Uncomment to proceed anyway
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to backend at {BACKEND_URL}. Please ensure it's running.")
    except requests.exceptions.Timeout:
        print(f"Error: Connection to backend timed out ({BACKEND_URL}).")
    except Exception as e:
        print(f"An unexpected error occurred during backend check: {e}")

    # Only start GUI if backend seems okay (or if you decide to ignore the check)
    # if backend_ok: # Uncomment this line to enforce backend check
    root = tk.Tk()
    app = RagAppGUI(root)
    root.mainloop()
    # else: # Uncomment this block to enforce backend check
    #     print("Exiting GUI application because backend check failed.")


