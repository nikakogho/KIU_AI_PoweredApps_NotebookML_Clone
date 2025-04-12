import tkinter as tk
from tkinter import ttk # For themed widgets
from tkinter import filedialog # For open file dialog
from tkinter import scrolledtext # For scrollable text area

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
        self.upload_button = ttk.Button(self.top_frame, text="Upload File (.txt, .pdf)", command=self.upload_file_placeholder)
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
        self.chat_display.tag_configure("error", foreground="#DC143C") # Crimson Red
        self.chat_display.tag_configure("status", foreground="#696969", font=("Helvetica", 9, "italic")) # Dim Gray

        # Bottom Frame Widgets
        self.query_entry = ttk.Entry(self.bottom_frame, width=60, font=("Helvetica", 10))
        self.query_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.query_entry.bind("<Return>", self.send_query_placeholder) # Bind Enter key

        self.send_button = ttk.Button(self.bottom_frame, text="Send", command=self.send_query_placeholder)
        self.send_button.grid(row=0, column=1)

        # Status Frame Widgets
        self.status_label = ttk.Label(self.status_frame, text="Status: Ready", anchor="w") # Anchor West (left)
        self.status_label.grid(row=0, column=0, sticky="ew")

        # --- Placeholder Methods ---
        # These will be replaced with actual functionality later
        self.add_message("Welcome! Please upload a .txt or .pdf document to begin.", "status")


    def upload_file_placeholder(self):
        """Placeholder for file upload logic."""
        print("Upload button clicked (placeholder)")
        self.update_status("Placeholder: File upload initiated.")
        # Simulate file selection for now
        # filename = filedialog.askopenfilename(
        #     title="Select a Document",
        #     filetypes=(("Text files", "*.txt"), ("PDF files", "*.pdf"), ("All files", "*.*"))
        # )
        # if filename:
        #     self.file_label.config(text=f"Selected: {os.path.basename(filename)}")
        #     self.update_status(f"Placeholder: Selected {os.path.basename(filename)}")
        # else:
        #      self.update_status("Placeholder: File selection cancelled.")
        self.file_label.config(text="Selected: placeholder.pdf")
        self.update_status("Placeholder: Selected placeholder.pdf")


    def send_query_placeholder(self, event=None): # Add event=None for key binding
        """Placeholder for sending query logic."""
        query = self.query_entry.get().strip()
        if not query:
            return # Don't send empty messages

        print(f"Sending query (placeholder): {query}")
        self.add_message(f"You: {query}", "user") # Display user query
        self.query_entry.delete(0, tk.END) # Clear input field
        self.update_status("Placeholder: Query sent...")

        # Simulate bot response
        self.root.after(1000, lambda: self.add_message(f"Bot: Placeholder response to '{query}'", "bot"))
        self.root.after(1000, lambda: self.update_status("Status: Ready"))


    def add_message(self, message, tag):
        """Adds a message to the chat display with specified tag for styling."""
        self.chat_display.config(state='normal') # Enable editing
        self.chat_display.insert(tk.END, message + "\n\n", tag) # Add message and extra newline
        self.chat_display.config(state='disabled') # Disable editing
        self.chat_display.see(tk.END) # Scroll to the bottom


    def update_status(self, message):
        """Updates the status bar label."""
        self.status_label.config(text=message)
        self.root.update_idletasks() # Force GUI update


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = RagAppGUI(root)
    root.mainloop()

