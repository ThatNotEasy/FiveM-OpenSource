"""
Main application for the ESX/QB-Core Converter.
Desktop GUI using CustomCTkinter.
"""
import sys
import os
import threading
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk

from modules.banners import clear_and_print
from modules.patterns import load_conversion_patterns
from modules.converter import process_folder
from modules.components import (
    FolderSelector,
    ConversionOptions,
    OutputConsole,
    ActionButtons,
)


class ConverterApp(ctk.CTk):
    """Main application class for the ESX/QB-Core Converter."""

    def __init__(self):
        """Initialize the converter application."""
        super().__init__()

        # Configure the window
        self.title("ESX/QB-Core Converter")
        self.geometry("800x700")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Set widget scaling to make everything smaller (0.9 = 90%)
        ctk.set_widget_scaling(0.95)

        # Load conversion patterns
        self.patterns = load_conversion_patterns()

        # Set up the UI layout
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI layout."""
        # Main container with scroll
        self.main_frame = ctk.CTkScrollableFrame(self, label_text="ESX/QB-Core Converter")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="ESX/QB-Core Converter",
            font=("Arial", 24, "bold")
        )
        self.title_label.pack(pady=10)

        self.subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Convert FiveM scripts between ESX and QB-Core frameworks",
            font=("Arial", 12),
            text_color="gray"
        )
        self.subtitle_label.pack(pady=5)

        # Add the folder selector
        self.folder_selector = FolderSelector(self.main_frame)

        # Add conversion options
        self.conversion_options = ConversionOptions(self.main_frame)

        # Add action buttons
        self.action_buttons = ActionButtons(
            self.main_frame,
            convert_callback=self._convert,
            quit_callback=self._quit
        )

        # Add output console
        self.output_console = OutputConsole(self.main_frame)

    def _convert(self):
        """Start the conversion process based on user input."""
        folder = self.folder_selector.value
        if not folder:
            self.show_warning("Please select a folder")
            return

        if not os.path.isdir(folder):
            self.show_warning("Selected path is not a valid directory")
            return

        direction = self.conversion_options.conversion_direction
        include_sql = self.conversion_options.include_sql_patterns

        # Clear and update output console
        self.output_console.clear()
        self.output_console.add_message(f"Starting conversion: {direction}", 'info')
        self.output_console.add_message(f"Processing folder: {folder}", 'info')
        self.output_console.add_message(
            f"Include SQL Patterns: {'Yes' if include_sql else 'No'}", 'info'
        )

        # Select patterns based on direction
        if direction == 'ESX to QB-Core':
            selected_patterns = self.patterns['ESX_to_QB_Core']
        else:
            selected_patterns = self.patterns['QB_Core_to_ESX']

        sql_patterns = self.patterns.get('SQL_patterns', [])

        # Define callback for progress updates
        def update_progress(message: str):
            if 'Converted:' in message:
                self.output_console.add_message(message, 'success')
            elif 'No changes needed:' in message:
                self.output_console.add_message(message, 'info')
            elif 'Error' in message:
                self.output_console.add_message(message, 'error')
            else:
                self.output_console.add_message(message, 'info')

        # Run conversion in a separate thread to keep UI responsive
        def run_conversion():
            try:
                # Process the folder
                stats = process_folder(
                    folder,
                    selected_patterns,
                    direction,
                    include_sql,
                    sql_patterns,
                    update_progress,
                    output_prefix="qb-"
                )

                # Display summary
                self.output_console.add_message('\n--- Conversion Summary ---', 'info')
                self.output_console.add_message(
                    f'Total files processed: {stats["total_files"]}', 'info'
                )
                self.output_console.add_message(
                    f'Files converted: {stats["converted_files"]}', 'success'
                )
                self.output_console.add_message(
                    f'Files skipped (no changes needed): {stats["skipped_files"]}', 'info'
                )

                if stats['error_files'] > 0:
                    self.output_console.add_message(
                        f'Files with errors: {stats["error_files"]}', 'error'
                    )

                self.output_console.add_message(
                    '\nConversion completed successfully!', 'success'
                )
                self.output_console.add_message(
                    f'Output folder: qb-{os.path.basename(folder)}', 'info'
                )

                # Show success notification
                self.show_success("Conversion completed successfully!")
            except Exception as e:
                error_msg = f'\nAn error occurred: {str(e)}'
                self.output_console.add_message(error_msg, 'error')
                self.show_error(f'An error occurred: {str(e)}')

        # Start conversion thread
        conversion_thread = threading.Thread(target=run_conversion, daemon=True)
        conversion_thread.start()

    def _quit(self):
        """Exit the application."""
        self.destroy()

    def show_warning(self, message: str):
        """Show a warning message."""
        self.output_console.add_message(f"Warning: {message}", 'warning')

    def show_error(self, message: str):
        """Show an error message."""
        self.output_console.add_message(f"Error: {message}", 'error')

    def show_success(self, message: str):
        """Show a success message."""
        self.output_console.add_message(message, 'success')


if __name__ in {"__main__", "__mp_main__"}:
    clear_and_print()
    app = ConverterApp()
    app.mainloop()
