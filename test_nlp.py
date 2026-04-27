import spacy
from spacy.matcher import Matcher
from spacy.util import filter_spans

nlp = spacy.load("en_core_web_sm")
matcher = Matcher(nlp.vocab)

# 1. N3arrou el Pattern
pattern = [{"POS": "PROPN", "OP": "+"}, {"LOWER": "page"}]
matcher.add("UI_PAGE", [pattern])

text = "Given a user named Nour is on the Login Page at 10:00 AM"
doc = nlp(text)

# 2. Naamlou el Matches
matches = matcher(doc)

# 3. Hounii el Solution: N'ajoustou el Matches kimaEntities jdod
new_ents = []
for match_id, start, end in matches:
    span = doc[start:end]
    # Nrodduha Entity mta3 UI_PAGE
    new_ents.append(spacy.tokens.Span(doc, start, end, label="UI_PAGE"))

# 4. Hounii el Force Override: 
# Nfaskhou el entities elli l9ahom el model aal "Login Page" 
# w n7ottou bdelhom el new_ents
doc.ents = filter_spans(list(doc.ents) + new_ents)

# 5. El 7all el Najeaa (Tathbit finali): nna77iw ay WORK_OF_ART li "Login" fiha
final_ents = []
for ent in doc.ents:
    if ent.label_ == "WORK_OF_ART" and "Login" in ent.text:
        continue # Nfaskhouha
    final_ents.append(ent)
doc.ents = final_ents

print("--- Final Entities ---")
for ent in doc.ents:
    print(f"Entity: {ent.text} | Label: {ent.label_}")