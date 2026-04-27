import spacy
from spacy.matcher import PhraseMatcher

nlp = spacy.load("en_core_web_sm")
matcher = PhraseMatcher(nlp.vocab, attr="LOWER") # Ignore capitalization

# Define the pattern we want to find
patterns = [nlp.make_doc("Login Page")]
matcher.add("GHERKIN_PAGE", patterns)

# Test text
text = "Given a user is on the Login Page"
doc = nlp(text)

# Find matches
matches = matcher(doc)

print("--- Matches Found ---")
for match_id, start, end in matches:
    span = doc[start:end] # The matched span
    print(f"Found: {span.text}")