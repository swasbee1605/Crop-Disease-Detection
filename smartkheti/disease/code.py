import cv2
import os
import numpy as np

# Define input and output directories
input_dir = 'E:\\tomato_data\\test'  # Parent directory with subfolders
output_dir = 'E:\\output_data'  # Output directory

# Create output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Flag to track if any images were processed
images_processed = False

# Function to process images in subdirectories
def process_images_in_subdir(subdir):
    global images_processed  # Ensure global flag is used
    # Loop through all files in the subdirectory
    for root, dirs, files in os.walk(subdir):  # Traverse subdirectories
        for filename in files:
            if filename.endswith('.jpg') or filename.endswith('.png'):  # Modify for your dataset
                # Construct full image path
                img_path = os.path.join(root, filename)
                print(f"Processing: {img_path}")

                # Read the image
                image = cv2.imread(img_path)

                # Check if image is loaded successfully
                if image is None:
                    print(f"Error loading image: {img_path}")
                    continue

                # Convert to grayscale
                gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                # Apply Gaussian Blur for smoothing
                smoothed_image = cv2.GaussianBlur(gray_image, (7, 7), 0)  # Adjust kernel size as needed
                
                # Apply Otsu's thresholding to binarize the smoothed image
                _, binary_image = cv2.threshold(smoothed_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                # Apply adaptive thresholding
                adaptive_binary = cv2.adaptiveThreshold(smoothed_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

                # Combine Otsu and Adaptive results
                combined_binary = cv2.bitwise_or(binary_image, adaptive_binary)

                # Define a kernel for morphological operations
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

                # Apply morphological operations
                cleaned_binary = cv2.morphologyEx(combined_binary, cv2.MORPH_CLOSE, kernel)
                cleaned_binary_3ch = cv2.cvtColor(cleaned_binary, cv2.COLOR_GRAY2BGR)
                combined_binary_and_original = cv2.bitwise_and(cleaned_binary_3ch, image)

                # Create corresponding subfolder structure in output directory
                rel_path = os.path.relpath(root, input_dir)  # Get relative path
                _output_dir = os.path.join(output_dir, rel_path)
                if not os.path.exists(_output_dir):
                    os.makedirs(_output_dir)

                # Save the image in the corresponding subfolder
                gray_img_path = os.path.join(_output_dir, filename)
                result = cv2.imwrite(gray_img_path, combined_binary_and_original)

                # Check if image was saved successfully
                if result:
                    print(f"Converted {filename} to grayscale and smoothed it. Saved at {gray_img_path}")
                    images_processed = True  # Mark that at least one image was processed
                else:
                    print(f"Failed to save the image: {gray_img_path}")

    return images_processed  # Return the status after processing

# Process all subfolders in the input directory
for subdir in os.listdir(input_dir):
    subdir_path = os.path.join(input_dir, subdir)
    if os.path.isdir(subdir_path):  # Ensure it's a directory
        process_images_in_subdir(subdir_path)

# Check if any images were processed
if not images_processed:
    print("No images were processed. Please check the input directory and image formats.")
else:
    print("Conversion and smoothing complete.")
