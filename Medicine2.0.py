import tkinter as tk
import time
import spacy
from threading import Thread

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Predefined symptoms and illnesses
ILLNESS_DATABASE = {
    "cold": {
        "symptoms": ["cough", "sneezing", "runny nose", "sore throat"],
        "medicines": ["Tylenol", "NyQuil", "Vicks Vaporub"]
    },
    "flu": {
        "symptoms": ["fever", "chills", "body ache", "fatigue"],
        "medicines": ["Tamiflu", "Ibuprofen", "Theraflu"]
    },
    "migraine": {
        "symptoms": ["headache", "nausea", "light sensitivity"],
        "medicines": ["Excedrin", "Ibuprofen", "Aspirin"]
    },
    "allergy": {
        "symptoms": ["itchy eyes", "runny nose", "sneezing"],
        "medicines": ["Claritin", "Zyrtec", "Benadryl"]
    }
}

# Function to extract symptoms from user input
def extract_symptoms(user_text):
    doc = nlp(user_text.lower())  # Process text with NLP
    extracted_symptoms = [token.text for token in doc if token.text in sum([d["symptoms"] for d in ILLNESS_DATABASE.values()], [])]
    return extracted_symptoms

# Function to find illness based on symptoms
def diagnose(symptoms):
    matched_illness = None
    best_match_count = 0
    best_medicine = []

    for illness, data in ILLNESS_DATABASE.items():
        common_symptoms = set(symptoms).intersection(data["symptoms"])
        if len(common_symptoms) > best_match_count:
            best_match_count = len(common_symptoms)
            matched_illness = illness
            best_medicine = data["medicines"]

    return matched_illness, best_medicine

# Function to display text letter by letter
def typing_effect(text, label):
    label.config(text="")  # Clear previous text
    for i in range(len(text)):
        label.config(text=text[:i+1])
        time.sleep(0.05)  # Delay for typing effect
        root.update()

# Function to handle user input and display diagnosis
def get_diagnosis():
    user_input = entry.get().strip()
    symptoms = extract_symptoms(user_input)

    if not symptoms:
        result_text = "❌ No recognizable symptoms found. Please describe your condition more clearly."
    else:
        illness, medicines = diagnose(symptoms)
        if illness:
            result_text = f"\nDiagnosis: {illness.capitalize()}\n\nRecommended Medicines:\n"
            result_text += "\n".join(f"➡ {med}" for med in medicines)
        else:
            result_text = "❌ No matching illness found. Please consult a doctor."

    # Run typing effect on a separate thread (to prevent GUI freezing)
    Thread(target=typing_effect, args=(result_text, result_label)).start()

# GUI Setup
root = tk.Tk()
root.title("Symptom Checker")
root.geometry("500x400")

# Header Label
title_label = tk.Label(root, text="Describe your symptoms:", font=("Arial", 12))
title_label.pack(pady=10)

# User Input Field
entry = tk.Entry(root, width=50, font=("Arial", 12))
entry.pack(pady=5)

# Submit Button
submit_button = tk.Button(root, text="Diagnose", command=get_diagnosis, font=("Arial", 12))
submit_button.pack(pady=10)

# Result Label (where the answer will be shown letter by letter)
result_label = tk.Label(root, text="", font=("Arial", 12), justify="left", wraplength=400)
result_label.pack(pady=20)

# Run GUI
root.mainloop()
