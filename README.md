# FiveM ESX/QB-Core Converter
The ESX/QB-Core Converter is a modern web-based application that helps you convert FiveM resource scripts between the ESX and QB-Core frameworks. It provides an intuitive user interface built with the `customtkinter` library.

## Features

- Converts FiveM resource scripts from ESX to QB-Core and vice versa.
- Supports a wide range of conversion patterns for client-side and server-side code.
- Processes all `.lua` files in the selected folder and its subfolders.
- Provides a modern, responsive web interface for selecting the folder and conversion direction.
- Displays the conversion progress and results in real-time with color-coded output.
- Modular architecture for easy maintenance and extension.

## Requirements

- Install the requirements
```pip install -r requirements.txt```

## Installation

- Clone the repository:
   ```bash
   git clone https://github.com/ThatNotEasy/FiveM-OpenSource
   cd FiveM-OpenSource
   ```

## Usage

1. Run the application:
   ```bash
   python main.py
   ```

- The web interface will open in your default browser.
- Select the folder containing the FiveM resource scripts you want to convert.
- Choose the conversion direction (ESX to QB-Core or QB-Core to ESX).
- Optionally, enable SQL pattern conversion.
- Click the "Convert" button to start the conversion process.
- View the conversion progress and results in the output console.
