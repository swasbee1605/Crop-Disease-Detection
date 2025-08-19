import cv2
import os
import numpy as np
from skimage.feature import graycomatrix, graycoprops
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib

# Define input and output directories
input_dir = 'E:\\tomato_data\\train'  # Parent directory with subfolders for each class
output_dir = 'E:\\output_data'  # Output directory
model_path = 'E:\\tomato_disease_model.joblib'  # Path to save/load the model
test_dir = 'E:\\tomato_data\\test' 

# Create output directory if it doesn't exist
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# SHAPE EXTRACTION
def calculate_shape_features(contour):
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0
    return area, perimeter, circularity

# COLOR EXTRACTION
def calculate_color_features(image, mask):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    total_pixels = np.sum(mask > 0)
    
    if total_pixels == 0:
        return [0, 0, 0]  # Return zeros if no pixels in mask
    
    color_features = []
    for channel in range(3):
        channel_mean = np.mean(hsv_image[:,:,channel][mask > 0])
        color_features.append(channel_mean)
    
    return color_features

# TEXTURE EXTRACTION
def calculate_texture_features(gray_image, mask):
    masked_image = cv2.bitwise_and(gray_image, gray_image, mask=mask)
    glcm = graycomatrix(masked_image, [1], [0], 256, symmetric=True, normed=True)
    properties = ['contrast', 'dissimilarity', 'homogeneity', 'energy', 'correlation']
    features = [graycoprops(glcm, prop)[0, 0] for prop in properties]
    return features

def extract_features(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error loading image: {image_path}")
        return None

    # Convert to HSV color space for better color filtering
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Create a mask that includes a wider range of colors
    lower_green = np.array([25, 40, 40])
    upper_green = np.array([100, 255, 255])
    mask = cv2.inRange(hsv_image, lower_green, upper_green)

    # Apply morphological operations to clean up the mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        print(f"No contours found in {image_path}")
        return None

    # Get the largest contour
    largest_contour = max(contours, key=cv2.contourArea)

    # Extract features
    shape_features = calculate_shape_features(largest_contour)
    color_features = calculate_color_features(image, mask)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    texture_features = calculate_texture_features(gray_image, mask)

    # Combine all features
    features = list(shape_features) + color_features + texture_features

    return features

def process_dataset(input_dir):
    features = []
    labels = []
    
    for class_name in os.listdir(input_dir):
        class_dir = os.path.join(input_dir, class_name)
        if not os.path.isdir(class_dir):
            continue
        
        for root, dirs, files in os.walk(class_dir):  # Walk through all subdirectories
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(root, file)
                    image_features = extract_features(image_path)
                    if image_features:
                        features.append(image_features)
                        labels.append(class_name)
    
    return features, labels

def train_model(features, labels):
    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate the model
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred))

    # Save the model
    joblib.dump(clf, model_path)
    print(f"Model saved to {model_path}")

def predict_image(image_path, model):
    features = extract_features(image_path)
    
    if features:
        prediction = model.predict([features])[0]
        return prediction
    
    return "Unable to process image"

# Main execution
if __name__ == "__main__":
    
   # Check if model exists
   if os.path.exists(model_path):
       print("Loading existing model...")
       model = joblib.load(model_path)
   else:
       print("Training new model...")
       features, labels = process_dataset(input_dir)
       if features and labels:
           train_model(features, labels)
           model = joblib.load(model_path)
       else:
           print("Failed to extract features and labels. Check your dataset.")
           exit(1)

   # Process test images using os.walk to find images in subdirectories.
   if not os.path.exists(test_dir):
       print(f"Test directory not found: {test_dir}")
       print("Please specify the correct path to the test directory.")
       exit(1)

   print(f"Examining contents of test directory: {test_dir}")
   test_images = []

   for root, dirs, files in os.walk(test_dir): 
       for file in files:
           if file.lower().endswith(('.png', '.jpg', '.jpeg')):
               test_images.append(os.path.join(root,file))

   print(f"Image files found: {len(test_images)}")
   for image in test_images:
       print(f"  {image}")

   if not test_images:
       print(f"No valid image files found in the test directory: {test_dir}")
       exit(1)

   # Predict on test images and save results (optional).
   for image_path in test_images:
       prediction = predict_image(image_path, model)
       print(f"{os.path.basename(image_path)}: Predicted class - {prediction}")

       # Optionally save processed image with prediction text.
       image = cv2.imread(image_path)
       cv2.putText(image,
                   f"Prediction: {prediction}",
                   (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX,
                   1,
                   (0, 255, 0),
                   2)

       output_file_name = f"processed_{os.path.basename(image_path)}"
       output_path = os.path.join(output_dir , output_file_name) 
       cv2.imwrite(output_path,image)

   print("Processing complete.")
