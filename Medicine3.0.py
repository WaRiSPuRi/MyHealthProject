import tkinter as tk
import time
import spacy
import requests
from threading import Thread
from duckduckgo_search import DDGS  # For searching medicines online

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Predefined symptoms and illnesses
ILLNESS_DATABASE = {
    "cold": {
        "symptoms": ["cough", "sneezing", "runny nose", "sore throat"],
        "keywords": ["cold", "flu", "congestion"]
    },
    "flu": {
        "symptoms": ["fever", "chills", "body ache", "fatigue"],
        "keywords": ["flu", "influenza", "body ache"]
    },
    "migraine": {
        "symptoms": ["headache", "nausea", "light sensitivity"],
        "keywords": ["migraine", "headache", "pain reliever"]
    },
    "allergy": {
        "symptoms": ["itchy eyes", "runny nose", "sneezing"],
        "keywords": ["allergy", "antihistamine", "pollen"]
    },
    "covid-19": {
        "symptoms": ["fever", "cough", "loss of taste", "loss of smell"],
        "keywords": ["covid", "coronavirus", "vaccine"]
    },
    "stomach flu": {
        "symptoms": ["vomiting", "diarrhea", "stomach pain", "nausea"],
        "keywords": ["stomach flu", "gastroenteritis", "probiotics"]
    },
    "food poisoning": {
        "symptoms": ["vomiting", "stomach cramps", "diarrhea"],
        "keywords": ["food poisoning", "charcoal tablets", "hydration"]
    },
    "anxiety": {
        "symptoms": ["rapid heartbeat", "sweating", "fear", "restlessness"],
        "keywords": ["anxiety", "stress relief", "calm"]
    }
}

# Function to extract symptoms from user input
def extract_symptoms(user_text):
    doc = nlp(user_text.lower())  # Process text with NLP
    extracted_symptoms = [token.text for token in doc if token.text in sum([d["symptoms"] for d in ILLNESS_DATABASE.values()], [])]
    return extracted_symptoms

# Function to diagnose illness
def diagnose(symptoms):
    matched_illness = None
    best_match_count = 0
    best_keywords = []

    for illness, data in ILLNESS_DATABASE.items():
        common_symptoms = set(symptoms).intersection(data["symptoms"])
        if len(common_symptoms) > best_match_count:
            best_match_count = len(common_symptoms)
            matched_illness = illness
            best_keywords = data["keywords"]

    return matched_illness, best_keywords

# Function to fetch top medicine recommendations from DuckDuckGo
def fetch_medicines(search_query):
    with DDGS() as ddgs:
        results = list(ddgs.text(search_query, max_results=3))
        return [res["title"] for res in results[:3]]  # Return top 3 medicine names

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
        illness, keywords = diagnose(symptoms)
        if illness:
            medicines = fetch_medicines(f"Best medicine for {illness}")
            result_text = f"\n🩺 Diagnosis: {illness.capitalize()}\n\n💊 Recommended Medicines:\n"
            result_text += "\n".join(f"➡ {med}" for med in medicines)
        else:
            result_text = "❌ No matching illness found. Please consult a doctor."

    # Run typing effect on a separate thread (to prevent GUI freezing)
    Thread(target=typing_effect, args=(result_text, result_label)).start()

# Function to handle dropdown selection
def select_symptom(symptom):
    current_text = entry.get()
    if current_text:
        entry.delete(0, tk.END)
        entry.insert(0, f"{current_text}, {symptom}")
    else:
        entry.insert(0, symptom)

# GUI Setup
root = tk.Tk()
root.title("🩺 Symptom Checker")
root.geometry("550x500")
root.configure(bg="#f0f8ff")

# Header Label
title_label = tk.Label(root, text="Describe your symptoms:", font=("Arial", 14, "bold"), bg="#f0f8ff")
title_label.pack(pady=10)

# User Input Field
entry = tk.Entry(root, width=50, font=("Arial", 12))
entry.pack(pady=5)

# Suggest Symptoms Dropdown
dropdown_label = tk.Label(root, text="Or select from common symptoms:", font=("Arial", 12), bg="#f0f8ff")
dropdown_label.pack(pady=5)

dropdown_frame = tk.Frame(root, bg="#f0f8ff")
dropdown_frame.pack()

common_symptoms = ["cough", "fever", "headache", "nausea", "sore throat", "sneezing"]
for symptom in common_symptoms:
    btn = tk.Button(dropdown_frame, text=symptom, font=("Arial", 10), bg="#add8e6", command=lambda s=symptom: select_symptom(s))
    btn.pack(side=tk.LEFT, padx=5)

# Submit Button
submit_button = tk.Button(root, text="🔍 Diagnose", command=get_diagnosis, font=("Arial", 12), bg="#4caf50", fg="white")
submit_button.pack(pady=10)

# Result Label (where the answer will be shown letter by letter)
result_label = tk.Label(root, text="", font=("Arial", 12), justify="left", wraplength=500, bg="#f0f8ff")
result_label.pack(pady=20)

# Run GUI
root.mainloop()
