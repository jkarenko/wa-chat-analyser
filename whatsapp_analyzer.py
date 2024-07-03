import argparse
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pandas as pd
import re
import glob

def perform_ocr(image_path, lang):
    """Perform OCR on the given image."""
    print(f"\nPerforming OCR on {image_path}")
    try:
        preprocessed_image = preprocess_image(image_path)
        if preprocessed_image is None:
            print(f"Error preprocessing image {image_path}")
            return None
        
        ocr_result = pytesseract.image_to_data(
            preprocessed_image,
            config=f"--psm 6 --oem 3 -l {lang} --user-words user-words-finnish.txt",
            output_type=pytesseract.Output.DICT
        )
        df = pd.DataFrame(ocr_result)
        return df
    except Exception as e:
        print(f"Error performing OCR on {image_path}: {e}")
        return None

def process_ocr_result(ocr_result, participant_names):
    """Process the OCR result to identify message blocks and senders."""
    processed_messages = []
    current_message = ""
    current_participant = None
    left_threshold = 100

    def add_message():
        nonlocal current_message, current_participant
        if current_message:
            # Clean up the message
            current_message = re.sub(r'\s+', ' ', current_message).strip()
            current_message = re.sub(r'\s([,.!?])', r'\1', current_message)
            processed_messages.append((current_participant, current_message))
            current_message = ""
            current_participant = None

    for _, row in ocr_result.iterrows():
        conf = float(row['conf'])
        text = str(row['text']).strip()
        left = int(row['left'])
        
        if conf == -1:
            add_message()
            continue
        
        if left == 555:
            print(f"Skipping centered text: text: '{text}', confidence: {conf}, left: {left}")
            continue
        
        # if conf < 80 and conf >= 60:
        #     text = handle_low_confidence_word(text, conf)
            
        if conf < 60:
            if should_skip_text(text, conf, left):
                continue
            print(f"Warning: Low confidence text: '{text}', confidence: {conf}, left: {left}")

        if not current_participant:
            current_participant = determine_participant(left, left_threshold, participant_names)

        if text:
            current_message = append_to_message(current_message, text)
    
    # Add the last message
    add_message()

    return processed_messages


def preprocess_image(image_path):
    """Preprocess the image to improve OCR accuracy."""
    print(f"Preprocessing image: {image_path}")
    try:
        img = Image.open(image_path)
        img = img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = img.filter(ImageFilter.SHARPEN)
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(1.1)
        img = img.point(lambda x: 0 if x < 200 else 255, '1')
        return img
    except Exception as e:
        print(f"Error preprocessing image {image_path}: {e}")
        return None


def handle_low_confidence_word(text, conf):
    with open('user-words-finnish.txt', 'r', encoding='utf-8') as f:
        user_words = [word.strip() for word in f.readlines()]
    from difflib import SequenceMatcher
    def optical_similarity(a, b):
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    closest_match = max(user_words, key=lambda word: optical_similarity(word, text))
    similarity = optical_similarity(closest_match, text)
    if similarity >= 0.5:  # Adjust this threshold as needed
        print(f"Low confidence word '{text}' (conf: {conf}). Closest optical match: '{closest_match}' (similarity: {similarity:.2f})")
        return closest_match
    return text

def should_skip_text(text, conf, left):
    if re.match(r'^\W+$', text):
        print(f"Skipping low confidence garbage text: '{text}', confidence: {conf}, left: {left}")
        return True
    if conf < 30:
        print(f"Skipping low confidence text: '{text}', confidence: {conf}, left: {left}")
        return True
    if left > 1000:
        print(f"Skipping low confidence text near right edge: '{text}', confidence: {conf}, left: {left}")
        return True
    return False

def determine_participant(left, left_threshold, participant_names):
    participant_index = 0 if left < left_threshold else 1
    return participant_names[participant_index] if participant_names else f"Participant {'A' if participant_index == 0 else 'B'}"

def append_to_message(current_message, text):
    if current_message and not current_message.endswith(' '):
        current_message += ' '
    return current_message + text

def format_conversation(processed_messages):
    """Format the processed messages into the desired output format."""
    formatted_output = ""
    current_participant = None
    for participant, message in processed_messages:
        if participant != current_participant:
            if current_participant is not None:
                formatted_output += "\n"
            formatted_output += f"{participant}:\n"
            current_participant = participant
        formatted_output += f"{message}\n"
    return formatted_output

def save_conversation(formatted_conversation, output_file):
    """Save the formatted conversation to a text file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_conversation)
        print(f"Conversation saved to {output_file}")
    except Exception as e:
        print(f"Error saving conversation: {e}")

def main():
    parser = argparse.ArgumentParser(description="Convert WhatsApp screenshot(s) to text")
    parser.add_argument("image_path", help="Path to the WhatsApp screenshot image or file pattern")
    parser.add_argument("-o", "--output", help="Output file path", default="conversation.txt")
    parser.add_argument("--names", help="Comma-separated participant names", default="Participant A,Participant B")
    parser.add_argument("--lang", help="Language code for Tesseract OCR", default="fin")
    args = parser.parse_args()

    participant_names = [name.strip() for name in args.names.split(',')] if args.names else []
    if participant_names and len(participant_names) != 2:
        print("Error: Please provide exactly two participant names or none.")
        return

    image_paths = glob.glob(args.image_path)
    if not image_paths:
        print(f"No images found matching the pattern: {args.image_path}")
        return

    all_processed_messages = []
    for image_path in sorted(image_paths):
        ocr_result = perform_ocr(image_path, args.lang)
        if ocr_result is not None:
            processed_messages = process_ocr_result(ocr_result, participant_names)
            all_processed_messages.extend(processed_messages)

    if all_processed_messages:
        formatted_conversation = format_conversation(all_processed_messages)
        save_conversation(formatted_conversation, args.output)
    else:
        print("No messages were processed. Check your input images and OCR settings.")

if __name__ == "__main__":
    main()
