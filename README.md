# WhatsApp Screenshot to Text Converter

This Python CLI program converts screenshots of WhatsApp conversations into annotated plaintext conversation files. It uses Optical Character Recognition (OCR) to extract text from images and processes the result to identify message blocks and their senders.

## Features

- Process JPG screenshots of WhatsApp conversations
- Perform OCR using Tesseract with specific parameters
- Extrapolate message blocks and identify senders
- Generate an annotated plaintext conversation file

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management. To set up the project:

1. Clone this repository
2. Install Poetry if you haven't already
3. Run `poetry install` in the project directory
4. Ensure Tesseract OCR is installed on your system and accessible from the command line

## Usage

Run the program from the command line, providing the path to your WhatsApp screenshot:

```
python whatsapp_analyzer.py path/to/your/screenshots
```

The program will process the images insude the directory and create a text file containing the extracted and annotated conversations.

## Dependencies

- pytesseract
- Pillow (PIL)
