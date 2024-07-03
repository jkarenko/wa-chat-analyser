import argparse
from PIL import Image
import pytesseract
import pandas as pd

def perform_ocr(image_path):
    """Perform OCR on the given image."""
    try:
        # Perform OCR with specific parameters
        ocr_result = pytesseract.image_to_data(
            Image.open(image_path),
            lang='fin',
            config='--psm 6',
            output_type=pytesseract.Output.DATA_FRAME
        )
        return ocr_result
    except Exception as e:
        print(f"Error performing OCR: {e}")
        return None

def process_ocr_result(ocr_result):
    """Process the OCR result to identify message blocks and senders."""
    processed_messages = []
    current_sender = None
    current_message = ""
    prev_top = None
    line_height_threshold = 20  # Adjust this value based on your image resolution

    # Sort the dataframe by top position and then by left position
    ocr_result = ocr_result.sort_values(['top', 'left'])

    for _, row in ocr_result.iterrows():
        if pd.notna(row['text']):
            text = row['text'].strip()
            
            # Check if this is potentially a new message
            if prev_top is None or (row['top'] - prev_top) > line_height_threshold:
                # If we have a current message, add it to processed_messages
                if current_message:
                    processed_messages.append(f"{current_sender}: {current_message.strip()}")
                    current_message = ""
                
                # Check if this line could be a sender name
                if row['left'] < 100 and len(text) < 30:  # Adjust these values as needed
                    current_sender = text
                    continue
            
            # Add this text to the current message
            current_message += " " + text
            prev_top = row['top']

    # Add the last message if there is one
    if current_message:
        processed_messages.append(f"{current_sender}: {current_message.strip()}")

    return processed_messages

def save_conversation(processed_messages, output_file):
    """Save the processed messages to a text file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for message in processed_messages:
                f.write(f"{message}\n")
        print(f"Conversation saved to {output_file}")
    except Exception as e:
        print(f"Error saving conversation: {e}")

def main():
    parser = argparse.ArgumentParser(description="Convert WhatsApp screenshot to text")
    parser.add_argument("image_path", help="Path to the WhatsApp screenshot image")
    parser.add_argument("-o", "--output", help="Output file path", default="conversation.txt")
    args = parser.parse_args()

    ocr_result = perform_ocr(args.image_path)
    if ocr_result is not None:
        processed_messages = process_ocr_result(ocr_result)
        save_conversation(processed_messages, args.output)

if __name__ == "__main__":
    main()
