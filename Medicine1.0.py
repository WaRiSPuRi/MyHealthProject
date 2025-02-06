import tkinter as tk
import time
from threading import Thread

# Predefined symptoms and illnesses
ILLNESS_DATABASE = {
    "cold": {
        "symptoms": ["cough", "sneezing", "runny nose", "sore throat", "Body Ache"],
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
        label.config(text=text[:i + 1])
        time.sleep(0.05)  # Delay for typing effect
        root.update()


# Function to handle user input and display diagnosis
def get_diagnosis():
    user_input = entry.get().lower().strip()
    symptoms = [s.strip() for s in user_input.split(",")]

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
root.geometry("800x700")

# Header Label
title_label = tk.Label(root, text="Enter your symptoms (comma-separated):", font=("Arial", 20))
title_label.pack(pady=10)

# User Input Field
entry = tk.Entry(root, width=50, font=("Arial", 20))
entry.pack(pady=5)

# Submit Button
submit_button = tk.Button(root, text="Diagnose", command=get_diagnosis, font=("Arial", 20))
submit_button.pack(pady=10)

# Result Label (where the answer will be shown letter by letter)
result_label = tk.Label(root, text="", font=("Arial", 20), justify="left", wraplength=400)
result_label.pack(pady=20)

# Run GUI
root.mainloop()
