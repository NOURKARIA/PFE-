import os
import torch
from transformers import DistilBertForTokenClassification, DistilBertForSequenceClassification

def print_file_info(path):
    if os.path.exists(path):
        print(f"{path}: {os.path.getsize(path)} bytes")
    else:
        print(f"{path}: MISSING")

print("== File sizes ==")
print_file_info('trained_models/nlp/entity_extractor.pt')
print_file_info('trained_models/nlp/intention_classifier.pt')

print('\n== Loading into model architectures (strict=False) ==')
try:
    sd = torch.load('trained_models/nlp/entity_extractor.pt', map_location='cpu')
    model = DistilBertForTokenClassification.from_pretrained('distilbert-base-uncased', num_labels=5)
    res = model.load_state_dict(sd, strict=False)
    print('\nEntity extractor load result:')
    print(res)
except Exception as e:
    print('Entity extractor load error:', e)

try:
    sd2 = torch.load('trained_models/nlp/intention_classifier.pt', map_location='cpu')
    model2 = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=4)
    res2 = model2.load_state_dict(sd2, strict=False)
    print('\nIntention classifier load result:')
    print(res2)
except Exception as e:
    print('Intention classifier load error:', e)

print('\nDone')
