from datasets import Dataset
from transformers import DistilBertTokenizerFast, DistilBertForTokenClassification, Trainer, TrainingArguments
import torch
import os

# Minimal NER training data (from uploaded notebook)
raw_json_data = [
    {"step": "When I click the login button", "intent": "ACTION_CLICK", "target": "login button", "value": None},
    {"step": "And I enter 'john.doe' in the username field", "intent": "ACTION_TYPE", "target": "username field", "value": "john.doe"},
    {"step": "Given I navigate to the home page", "intent": "NAVIGATION", "target": "home page", "value": None},
    {"step": "Then I verify the dashboard is visible", "intent": "VERIFICATION", "target": "dashboard", "value": None},
    {"step": "When I type 'password123' into the password input", "intent": "ACTION_TYPE", "target": "password input", "value": "password123"},
]

label_list = ["O", "B-TARGET", "I-TARGET", "B-VALUE", "I-VALUE"]
label_to_id = {l: i for i, l in enumerate(label_list)}

def build_examples(raw):
    texts = []
    tags = []
    for it in raw:
        text = it["step"]
        words = text.split()
        word_tags = ["O"] * len(words)

        # mark VALUE
        if it.get("value"):
            val = str(it["value"])
            # naive find: locate token(s) equal to val or containing val
            for i,w in enumerate(words):
                if val in w:
                    word_tags[i] = "B-VALUE"
        # mark TARGET
        if it.get("target"):
            target = it["target"]
            targ_words = target.split()
            # find subsequence
            for i in range(len(words)-len(targ_words)+1):
                if [w.strip("'\".,") for w in words[i:i+len(targ_words)]] == [tw.strip("'\".,") for tw in targ_words]:
                    word_tags[i] = "B-TARGET"
                    for j in range(1, len(targ_words)):
                        word_tags[i+j] = "I-TARGET"
                    break

        texts.append(words)
        tags.append([label_to_id[t] for t in word_tags])

    return texts, tags

texts, tags = build_examples(raw_json_data)

tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')

def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(examples['text'], is_split_into_words=True, truncation=True, padding='max_length')
    labels = []
    for i, label in enumerate(examples['labels']):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                label_ids.append(label[word_idx])
            else:
                # inside the same word: use I- prefix if available else same label
                lab = label[word_idx]
                label_ids.append(lab)
            previous_word_idx = word_idx
        labels.append(label_ids)
    tokenized_inputs['labels'] = labels
    return tokenized_inputs

dataset = Dataset.from_dict({'text': texts, 'labels': tags})
tokenized = dataset.map(tokenize_and_align_labels, batched=True)

model = DistilBertForTokenClassification.from_pretrained('distilbert-base-uncased', num_labels=len(label_list))

training_args = TrainingArguments(
    output_dir='./ner_results',
    num_train_epochs=1,
    per_device_train_batch_size=2,
    logging_steps=10,
    save_strategy='no',
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
)

print("Starting short entity extractor training (1 epoch)...")
trainer.train()

os.makedirs('trained_models/nlp', exist_ok=True)
model.save_pretrained('trained_models/nlp/entity_extractor_model')
torch.save(model.state_dict(), 'trained_models/nlp/entity_extractor.pt')
print('Saved entity extractor to trained_models/nlp/')
