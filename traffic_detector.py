import streamlit as st
from ultralytics import YOLO
import os
import glob
from PIL import Image
import numpy as np
import time

# === Simple Clean UI ===
st.title("🚗 Traffic Object Detector")
st.write("Upload an image to detect traffic objects using YOLOv8")

# === Sidebar Information ===
with st.sidebar:
    st.header("Model Info")
    st.info("Trained on custom traffic dataset")
    st.success("7 Classes: Car, Number Plate, Blur Plate, Two Wheeler, Auto, Bus, Truck")
    
    st.header("Settings")
    confidence_threshold = st.slider("Confidence Threshold", 0.1, 1.0, 0.25, 0.05)

# === Model Loading Function ===
@st.cache_resource
def load_model():
    """Load the trained YOLOv8 model"""
    runs_dir = "runs/detect"
    trained_model_path = None
    
    # Look for trained model
    if os.path.exists(runs_dir):
        train_dirs = glob.glob(os.path.join(runs_dir, "train*"))
        if train_dirs:
            latest_train_dir = max(train_dirs, key=os.path.getmtime)
            trained_model_path = os.path.join(latest_train_dir, "weights", "best.pt")
            st.sidebar.success(f"✅ Found trained model: {os.path.basename(trained_model_path)}")
    
    # Load model
    if trained_model_path and os.path.exists(trained_model_path):
        try:
            model = YOLO(trained_model_path)
            st.sidebar.success("🎯 Trained model loaded successfully!")
            return model, "trained"
        except Exception as e:
            st.sidebar.error(f"Error loading trained model: {e}")
            st.sidebar.info("Falling back to pre-trained model...")
    
    # Fallback to pre-trained model
    st.sidebar.warning("⚠️ Using pre-trained yolov8n.pt")
    model = YOLO('yolov8n.pt')
    return model, "pretrained"

# === Load the model ===
with st.spinner("Loading detection model..."):
    model, model_type = load_model()

# === Main Content Area ===
st.header("Upload Image for Detection")

# File uploader
uploaded_file = st.file_uploader(
    "Choose an image file", 
    type=["jpg", "jpeg", "png"]
)

# === Detection Process ===
if uploaded_file is not None:
    # Display uploaded image
    st.subheader("Uploaded Image")
    
    image = Image.open(uploaded_file)
    st.image(image, caption="Original Image", use_column_width=True)
    
    # Detection button
    if st.button("Detect Objects"):
        with st.spinner("Analyzing image..."):
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Simulate progress
            for i in range(100):
                time.sleep(0.01)  # Small delay for visual effect
                progress_bar.progress(i + 1)
                if i < 30:
                    status_text.text("Loading image...")
                elif i < 70:
                    status_text.text("Running detection...")
                else:
                    status_text.text("Processing results...")
            
            # Convert PIL Image to numpy array
            img_array = np.array(image)
            
            # Perform inference
            try:
                results = model.predict(
                    source=img_array, 
                    save=False, 
                    conf=confidence_threshold
                )
                
                status_text.empty()
                progress_bar.empty()
                
                if results and len(results) > 0:
                    # Get annotated image
                    annotated_image = results[0].plot(labels=True, conf=True)
                    
                    # Display results
                    st.subheader("Detection Results")
                    
                    # Show annotated image
                    st.image(
                        annotated_image, 
                        caption="Detected Objects", 
                        use_column_width=True
                    )
                    
                    # Show detection info
                    result = results[0]
                    if hasattr(result, 'boxes') and result.boxes is not None:
                        boxes = result.boxes
                        class_names = model.names
                        
                        st.write("### Detection Summary")
                        
                        # Count objects by class
                        class_counts = {}
                        for box in boxes:
                            cls = int(box.cls[0])
                            class_name = class_names[cls]
                            class_counts[class_name] = class_counts.get(class_name, 0) + 1
                        
                        # Display counts
                        for class_name, count in class_counts.items():
                            st.write(f"- **{class_name.title()}:** {count}")
                        
                        # Show total count
                        total_objects = sum(class_counts.values())
                        st.write(f"**Total Objects Detected:** {total_objects}")
                        
                        # Show confidence info
                        confidences = [float(box.conf[0]) for box in boxes]
                        if confidences:
                            avg_conf = sum(confidences) / len(confidences)
                            st.info(f"Average Confidence: {avg_conf:.2%}")
                    
                    # Success message
                    st.success("✅ Detection completed successfully!")
                    
                else:
                    st.warning("⚠️ No objects detected in the image.")
                    st.info("Try adjusting the confidence threshold or using a different image.")
                    
            except Exception as e:
                st.error(f"❌ Error during detection: {str(e)}")
                st.info("Please try uploading a different image.")
