"""
UI components for the ESX/QB-Core Converter application.
Desktop GUI using CustomTkinter.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Callable


class FolderSelector(ctk.CTkFrame):
    """A component for selecting a folder from the file system."""

    def __init__(self, master):
        """Initialize the folder selector component."""
        super().__init__(master)
        self.pack(pady=5, padx=5, fill="x")

        self.label = ctk.CTkLabel(self, text="Select Folder:", font=("Arial", 12, "bold"))
        self.label.pack(side="left", padx=5)

        self.path_input = ctk.CTkEntry(self, placeholder_text="Path to folder...", width=300)
        self.path_input.pack(side="left", padx=5, fill="x", expand=True)

        self.browse_button = ctk.CTkButton(
            self,
            text="Browse",
            command=self._browse_folder,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            width=70,
            height=28
        )
        self.browse_button.pack(side="right", padx=5)

    def _browse_folder(self):
        """Open a dialog to select a folder."""
        folder = filedialog.askdirectory(title="Select a folder")
        if folder:
            self.path_input.delete(0, "end")
            self.path_input.insert(0, folder)

    @property
    def value(self) -> str:
        """Get the selected folder path."""
        return self.path_input.get() or ''

    @value.setter
    def value(self, path: str):
        """Set the folder path."""
        self.path_input.delete(0, "end")
        self.path_input.insert(0, path)


class ConversionOptions(ctk.CTkFrame):
    """A component for selecting conversion options."""

    def __init__(self, master):
        """Initialize the conversion options component."""
        super().__init__(master)
        self.pack(pady=5, padx=5, fill="x")

        self.label = ctk.CTkLabel(self, text="Conversion Options", font=("Arial", 14, "bold"))
        self.label.pack(pady=5)

        # Direction selector
        self.direction_label = ctk.CTkLabel(self, text="Direction:")
        self.direction_label.pack(pady=2)

        self.direction_var = ctk.StringVar(value="ESX to QB-Core")
        self.direction_combo = ctk.CTkComboBox(
            self,
            values=["ESX to QB-Core", "QB-Core to ESX"],
            variable=self.direction_var,
            width=180,
            height=26
        )
        self.direction_combo.pack(pady=2)

        # SQL patterns switch
        self.sql_var = ctk.BooleanVar(value=False)
        self.sql_checkbox = ctk.CTkCheckBox(
            self,
            text="Include SQL Patterns",
            variable=self.sql_var,
            font=("Arial", 11)
        )
        self.sql_checkbox.pack(pady=5)

    @property
    def conversion_direction(self) -> str:
        """Get the selected conversion direction."""
        return self.direction_var.get()

    @property
    def include_sql_patterns(self) -> bool:
        """Get whether to include SQL patterns."""
        return self.sql_var.get()


class OutputConsole(ctk.CTkFrame):
    """A component for displaying output messages."""

    def __init__(self, master):
        """Initialize the output console component."""
        super().__init__(master)
        self.pack(pady=5, padx=5, fill="both", expand=True)

        self.label = ctk.CTkLabel(self, text="Conversion Output", font=("Arial", 12, "bold"))
        self.label.pack(pady=2)

        # Create a text widget with scrollbar
        self.text_frame = ctk.CTkFrame(self)
        self.text_frame.pack(fill="both", expand=True, padx=5, pady=2)

        self.textbox = ctk.CTkTextbox(
            self.text_frame,
            font=("Consolas", 11),
            wrap="word",
            state="disabled"
        )
        self.textbox.pack(side="left", fill="both", expand=True)

        self.scrollbar = ctk.CTkScrollbar(self.text_frame, command=self.textbox.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.textbox.configure(yscrollcommand=self.scrollbar.set)

        # Clear button
        self.clear_button = ctk.CTkButton(
            self,
            text="Clear Output",
            command=self.clear,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            width=100,
            height=28
        )
        self.clear_button.pack(pady=5)

    def add_message(self, message: str, message_type: str = 'info'):
        """Add a message to the output console."""
        # Define colors for different message types
        colors = {
            'info': '#2196F3',      # Blue
            'success': '#4CAF50',   # Green
            'error': '#F44336',     # Red
            'warning': '#FF9800'    # Orange
        }

        color = colors.get(message_type, colors['info'])

        self.textbox.configure(state="normal")
        self.textbox.insert("end", message + "\n")
        self.textbox.tag_add(message_type, "end-2l", "end-1l")
        self.textbox.tag_config(message_type, foreground=color)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")

    def clear(self):
        """Clear all messages from the output console."""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")

    @property
    def value(self) -> str:
        """Get the current output text."""
        return self.textbox.get("1.0", "end-1c")


class ActionButtons(ctk.CTkFrame):
    """A component for action buttons."""

    def __init__(self, master, convert_callback: Callable[[], None], quit_callback: Callable[[], None]):
        """Initialize the action buttons component."""
        super().__init__(master)
        self.pack(pady=5, padx=5, fill="x")

        self.convert_button = ctk.CTkButton(
            self,
            text="Convert",
            command=convert_callback,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            width=100,
            height=32
        )
        self.convert_button.pack(side="left", padx=10, expand=True)

        self.quit_button = ctk.CTkButton(
            self,
            text="Exit",
            command=quit_callback,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            width=70,
            height=32
        )
        self.quit_button.pack(side="right", padx=10, expand=True)
