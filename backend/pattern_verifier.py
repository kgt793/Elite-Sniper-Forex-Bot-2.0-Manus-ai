import os
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.applications import VGG16
from tensorflow.keras.applications.vgg16 import preprocess_input
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from PIL import Image
import io

class PatternVerifier:
    """
    A class to verify chart patterns using TradingView screenshots
    """
    
    def __init__(self, model_path=None):
        """
        Initialize the pattern verifier
        
        Args:
            model_path (str): Path to pre-trained model (optional)
        """
        self.model = None
        self.pattern_classes = [
            'head_and_shoulders', 'inverse_head_and_shoulders', 
            'double_top', 'double_bottom', 
            'triple_top', 'triple_bottom',
            'ascending_triangle', 'descending_triangle', 'symmetrical_triangle',
            'flag', 'pennant', 'wedge',
            'cup_and_handle', 'rounding_bottom', 'rounding_top'
        ]
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self._build_model()
    
    def _build_model(self):
        """
        Build the pattern recognition model based on VGG16
        """
        # Load VGG16 as base model without top layers
        base_model = VGG16(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
        
        # Add custom top layers
        x = base_model.output
        x = GlobalAveragePooling2D()(x)
        x = Dense(512, activation='relu')(x)
        x = Dropout(0.5)(x)
        x = Dense(256, activation='relu')(x)
        x = Dropout(0.3)(x)
        predictions = Dense(len(self.pattern_classes), activation='softmax')(x)
        
        # Create the model
        self.model = Model(inputs=base_model.input, outputs=predictions)
        
        # Freeze base model layers
        for layer in base_model.layers:
            layer.trainable = False
        
        # Compile the model
        self.model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
    
    def load_model(self, model_path):
        """
        Load a pre-trained model
        
        Args:
            model_path (str): Path to the model file
        """
        self.model = tf.keras.models.load_model(model_path)
    
    def save_model(self, model_path):
        """
        Save the current model
        
        Args:
            model_path (str): Path to save the model
        """
        if self.model:
            self.model.save(model_path)
    
    def preprocess_image(self, image_path):
        """
        Preprocess an image for the model
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            numpy.ndarray: Preprocessed image
        """
        # Load and resize image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (224, 224))
        
        # Preprocess for VGG16
        img = np.expand_dims(img, axis=0)
        img = preprocess_input(img)
        
        return img
    
    def preprocess_image_from_bytes(self, image_bytes):
        """
        Preprocess an image from bytes for the model
        
        Args:
            image_bytes (bytes): Image data as bytes
            
        Returns:
            numpy.ndarray: Preprocessed image
        """
        # Convert bytes to image
        img = Image.open(io.BytesIO(image_bytes))
        img = img.convert('RGB')
        img = img.resize((224, 224))
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Preprocess for VGG16
        img_array = np.expand_dims(img_array, axis=0)
        img_array = preprocess_input(img_array)
        
        return img_array
    
    def verify_pattern(self, image_path=None, image_bytes=None, confidence_threshold=0.6):
        """
        Verify a chart pattern from an image
        
        Args:
            image_path (str): Path to the image file (optional)
            image_bytes (bytes): Image data as bytes (optional)
            confidence_threshold (float): Minimum confidence threshold
            
        Returns:
            dict: Verification results
        """
        if not self.model:
            raise ValueError("Model not initialized")
        
        if image_path:
            img = self.preprocess_image(image_path)
        elif image_bytes:
            img = self.preprocess_image_from_bytes(image_bytes)
        else:
            raise ValueError("Either image_path or image_bytes must be provided")
        
        # Make prediction
        predictions = self.model.predict(img)[0]
        
        # Get top 3 patterns
        top_indices = predictions.argsort()[-3:][::-1]
        top_patterns = [
            {
                'pattern': self.pattern_classes[idx],
                'confidence': float(predictions[idx])
            }
            for idx in top_indices
        ]
        
        # Check if the top pattern meets the confidence threshold
        verified = top_patterns[0]['confidence'] >= confidence_threshold
        
        return {
            'verified': verified,
            'top_pattern': top_patterns[0]['pattern'],
            'confidence': top_patterns[0]['confidence'],
            'alternative_patterns': top_patterns[1:],
            'all_patterns': [
                {
                    'pattern': self.pattern_classes[i],
                    'confidence': float(predictions[i])
                }
                for i in range(len(self.pattern_classes))
            ]
        }
    
    def extract_chart_region(self, image_path):
        """
        Extract the chart region from a TradingView screenshot
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            numpy.ndarray: Extracted chart region
        """
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to find chart area (usually the main white/light area)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find the largest contour (likely the chart area)
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Extract the chart region
            chart_region = img[y:y+h, x:x+w]
            
            return chart_region
        
        # If no contours found, return the original image
        return img
    
    def detect_candlesticks(self, image_path):
        """
        Detect candlesticks in a chart image
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            list: Detected candlesticks
        """
        # Extract chart region
        chart = self.extract_chart_region(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(chart, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to find candlesticks
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours to find candlesticks
        candlesticks = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Candlesticks typically have a certain aspect ratio
            aspect_ratio = h / w if w > 0 else 0
            
            if aspect_ratio > 2 and h > 10:  # Likely a candlestick
                candlesticks.append({
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h
                })
        
        return candlesticks
    
    def detect_trend_lines(self, image_path):
        """
        Detect trend lines in a chart image
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            list: Detected trend lines
        """
        # Extract chart region
        chart = self.extract_chart_region(image_path)
        
        # Convert to grayscale
        gray = cv2.cvtColor(chart, cv2.COLOR_BGR2GRAY)
        
        # Apply Canny edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Apply Hough Line Transform
        lines = cv2.HoughLinesP(
            edges, 
            rho=1, 
            theta=np.pi/180, 
            threshold=100, 
            minLineLength=100, 
            maxLineGap=10
        )
        
        trend_lines = []
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Calculate line angle
                angle = np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi
                
                # Filter out vertical and horizontal lines (likely grid lines)
                if 5 < abs(angle) < 85:
                    trend_lines.append({
                        'x1': int(x1),
                        'y1': int(y1),
                        'x2': int(x2),
                        'y2': int(y2),
                        'angle': float(angle)
                    })
        
        return trend_lines
    
    def analyze_tradingview_screenshot(self, image_path):
        """
        Analyze a TradingView screenshot for patterns and trend lines
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Analysis results
        """
        # Verify pattern
        pattern_result = self.verify_pattern(image_path)
        
        # Detect trend lines
        trend_lines = self.detect_trend_lines(image_path)
        
        # Detect candlesticks
        candlesticks = self.detect_candlesticks(image_path)
        
        # Extract chart region
        chart = self.extract_chart_region(image_path)
        
        # Save the extracted chart
        chart_path = f"{os.path.splitext(image_path)[0]}_chart.jpg"
        cv2.imwrite(chart_path, chart)
        
        return {
            'pattern_verification': pattern_result,
            'trend_lines': trend_lines,
            'candlesticks': candlesticks,
            'chart_path': chart_path
        }
    
    def train_on_examples(self, data_dir, epochs=10, batch_size=32):
        """
        Train the model on example images
        
        Args:
            data_dir (str): Directory containing training data
            epochs (int): Number of training epochs
            batch_size (int): Batch size for training
            
        Returns:
            dict: Training history
        """
        if not self.model:
            self._build_model()
        
        # Create data generators
        from tensorflow.keras.preprocessing.image import ImageDataGenerator
        
        train_datagen = ImageDataGenerator(
            rotation_range=20,
            width_shift_range=0.2,
            height_shift_range=0.2,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True,
            validation_split=0.2
        )
        
        train_generator = train_datagen.flow_from_directory(
            data_dir,
            target_size=(224, 224),
            batch_size=batch_size,
            class_mode='categorical',
            subset='training'
        )
        
        validation_generator = train_datagen.flow_from_directory(
            data_dir,
            target_size=(224, 224),
            batch_size=batch_size,
            class_mode='categorical',
            subset='validation'
        )
        
        # Update pattern classes from directory
        self.pattern_classes = list(train_generator.class_indices.keys())
        
        # Train the model
        history = self.model.fit(
            train_generator,
            steps_per_epoch=train_generator.samples // batch_size,
            epochs=epochs,
            validation_data=validation_generator,
            validation_steps=validation_generator.samples // batch_size
        )
        
        return history.history
