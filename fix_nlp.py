import torch
from app.services.nlp.intent_classifier import IntentClassifier

path = "trained_models/nlp/intention_classifier.pt"

print(f"--- Checking file: {path} ---")
try:
    # 1. Check direct load
    data = torch.load(path, map_location=torch.device('cpu'))
    print("✅ Torch load: Success!")
    
    # 2. Check Classifier Initialization
    clf = IntentClassifier()
    print("✅ IntentClassifier Init: Success!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    