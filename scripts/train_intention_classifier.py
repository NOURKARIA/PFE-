from datasets import Dataset
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, Trainer, TrainingArguments
import torch
import os

raw_data = {
    "text": [
        "I click the login button", "Click on 'Submit'", "Tap the sign-in icon", "Press the cancel button",
        "I type 'Nour' in the name field", "Enter my email address", "Fill the search bar with 'Python'",
        "I navigate to 'https://google.com'", "Go to the login page", "Open the url 'https://github.com'",
        "I should see 'Success' message", "Verify that the logo is visible", "Then I see the 'Error' notification",
    ],
    "label": [0,0,0,0, 1,1,1, 2,2,2, 3,3,3]
}

label_map = {0: "CLICK", 1: "TYPE", 2: "NAVIGATE", 3: "VERIFY"}

tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
dataset = Dataset.from_dict(raw_data)

def tokenize_function(examples):
    return tokenizer(examples['text'], padding='max_length', truncation=True)

tokenized_dataset = dataset.map(tokenize_function, batched=True)

model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=4)

training_args = TrainingArguments(
    output_dir='./intent_results',
    num_train_epochs=1,
    per_device_train_batch_size=4,
    logging_dir='./logs',
    logging_steps=10,
    save_strategy='no',
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)

print('Starting short intent classifier training (1 epoch)...')
trainer.train()

os.makedirs('trained_models/nlp', exist_ok=True)
model.save_pretrained('trained_models/nlp/intention_classifier_model')
torch.save(model.state_dict(), 'trained_models/nlp/intention_classifier.pt')
print('Saved intention classifier to trained_models/nlp/')
