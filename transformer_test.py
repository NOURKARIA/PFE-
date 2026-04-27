from transformers import pipeline

# Load a classification pipeline (this might take a minute to download the first time)
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Your Gherkin sentence
sequence_to_classify = "When the user clicks the purchase button"

# Labels you want the AI to check for
candidate_labels = ['navigation', 'authentication', 'transaction', 'error']

result = classifier(sequence_to_classify, candidate_labels)

print(f"Text: {result['sequence']}")
print(f"Top Intent: {result['labels'][0]} (Score: {round(result['scores'][0], 3)})")