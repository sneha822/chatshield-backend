
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.toxicity import toxicity_analyzer

def test_toxicity():
    print("Loading model...")
    if not toxicity_analyzer.load_model():
        print("Failed to load model")
        return

    # Test cases
    texts = [
        ("Eng Toxic", "You are an idiot"),
        ("Eng Toxic 2", "I hate you, you should die"),
        ("Eng Safe", "Hello friend, how are you?"),
        ("Hindi Toxic", "तुम बेवकूफ हो"),
        ("Hindi Toxic 2", "तेरी हिम्मत कैसे हुई"),
        ("Hindi Safe", "नमस्ते दोस्त"),
        ("Hinglish Toxic", "Tera dimag kharab hai"),
        ("Hinglish Toxic 2", "Tu pagal hai kya"),
        ("Hinglish Toxic 3", "Sale kutte"),
        ("Hinglish Safe", "Hello bhai, kaise ho?"),
        ("Hinglish Safe 2", "Aaj ka mausam accha hai")
    ]

    print("\nCorrectness Check:")
    for lang, text in texts:
        results = toxicity_analyzer.analyze(text)
        print(f"[{lang}] '{text}'")
        print(f"  -> Toxicity: {results.get('toxicity', 0):.4f}")
        print(f"  -> Is Toxic: {results.get('is_toxic')}")
        print("-" * 20)

if __name__ == "__main__":
    test_toxicity()
