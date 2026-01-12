
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
        # Explicit Toxic
        ("Toxic 1", "You are an idiot and a loser"),
        ("Toxic 2", "I will kill you"),
        ("Toxic 3", "I hope you die"),
        
        # Subtly Toxic / Insults
        ("Subtle 1", "You are not very smart, are you?"),
        ("Subtle 2", "Did your brain take a vacation?"),

        # Identity Attack
        ("Identity 1", "Women are inferior"),
        ("Identity 2", "Go back to your country"),

        # Safe but negative sounding
        ("Safe Negative 1", "This movie was terrible"),
        ("Safe Negative 2", "I hate waking up early"),
        ("Safe Negative 3", "The weather is awful today"),

        # Safe Contextual / Tricky
        ("Tricky 1", "You are killing it!"),  # Slang for doing well
        ("Tricky 2", "I am dying of laughter"), # Metaphor
        ("Tricky 3", "That trick was sick!"), # Slang for cool
        ("Tricky 4", "Don't be a stranger"),
        ("Tricky 5", "You are not dumb"),
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
