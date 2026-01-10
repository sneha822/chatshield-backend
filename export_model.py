"""Script to locate and export the toxicity detection model for sharing."""

import os
import shutil
from pathlib import Path
from transformers import pipeline

def find_and_export_model():
    """Find the cached model and export it to a shareable directory."""
    
    model_name = "textdetox/bert-multilingual-toxicity-classifier"
    export_dir = Path("./model_export")
    
    print("🔍 Locating the toxicity detection model...")
    
    # Load the model (this will use the cached version if available)
    try:
        model = pipeline("text-classification", model=model_name)
        print("✅ Model loaded successfully!")
        
        # Save the model to a local directory
        print(f"\n📦 Exporting model to: {export_dir.absolute()}")
        export_dir.mkdir(exist_ok=True)
        
        # Save model and tokenizer
        model.save_pretrained(export_dir)
        
        print(f"\n✅ Model exported successfully!")
        print(f"\n📍 Model location: {export_dir.absolute()}")
        print(f"\n📊 Directory size:")
        
        # Calculate directory size
        total_size = sum(f.stat().st_size for f in export_dir.rglob('*') if f.is_file())
        print(f"   {total_size / (1024**2):.2f} MB")
        
        print("\n📤 To share with your friend:")
        print(f"   1. Compress the '{export_dir.name}' folder")
        print(f"   2. Send it to your friend")
        print(f"   3. They should extract it and use the instructions in SHARED_MODEL_README.txt")
        
        # Create a README for your friend
        create_readme(export_dir)
        
        print("\n✨ Done! Check the model_export folder.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def create_readme(export_dir):
    """Create a README file with instructions for using the shared model."""
    
    readme_content = """# ChatShield Toxicity Detection Model

This folder contains a pre-downloaded toxicity detection model for the ChatShield backend.

## Model Information
- **Model Name**: textdetox/bert-multilingual-toxicity-classifier
- **Purpose**: Multilingual toxicity detection (English, Hindi, Hinglish)
- **Type**: BERT-based text classification model

## How to Use This Model

### Option 1: Use the exported model directly

1. Place this `model_export` folder in your ChatShield backend directory
2. Update `app/services/toxicity.py` to load from this local path instead of downloading

Replace line 36 in `app/services/toxicity.py`:
```python
# OLD:
self._model = pipeline("text-classification", model="textdetox/bert-multilingual-toxicity-classifier")

# NEW:
self._model = pipeline("text-classification", model="./model_export")
```

### Option 2: Place in Hugging Face cache directory

1. Create the directory (if it doesn't exist):
   ```
   C:\\Users\\YOUR_USERNAME\\.cache\\huggingface\\hub
   ```

2. Copy the contents of this folder to a new folder named:
   ```
   models--textdetox--bert-multilingual-toxicity-classifier
   ```

3. The full path should be:
   ```
   C:\\Users\\YOUR_USERNAME\\.cache\\huggingface\\hub\\models--textdetox--bert-multilingual-toxicity-classifier
   ```

Now the model will work exactly as if you downloaded it yourself!

## Model Size
Check the folder size - it should be around 400-700 MB.

## Troubleshooting
If the model doesn't load:
- Ensure all files are extracted properly
- Check that the path in the code matches the actual folder location
- Verify that the transformers and torch packages are installed
"""
    
    readme_path = export_dir / "SHARED_MODEL_README.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"   📝 Created: {readme_path.name}")

if __name__ == "__main__":
    find_and_export_model()
