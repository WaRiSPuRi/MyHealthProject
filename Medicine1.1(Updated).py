import requests
import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import webbrowser
import time

# Database Setup
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    symptoms TEXT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE
)
''')
conn.commit()

# Predefined Illness Data
ILLNESS_DATABASE = {
    "cold": ["cough", "sneezing", "runny nose", "sore throat"],
    "flu": ["fever", "chills", "body ache", "fatigue"],
    "migraine": ["headache", "nausea", "light sensitivity"]
}

# RxNorm API URL
RXNORM_API_URL = "https://rxnav.nlm.nih.gov/REST/drugs.json?name="

# Fetch medicine names from RxNorm
def get_medicines(illness_name):
    try:
        response = requests.get(RXNORM_API_URL + illness_name)
        data = response.json()

        if "drugGroup" in data and "conceptGroup" in data["drugGroup"]:
            medicines = []
            links = []

            for group in data["drugGroup"]["conceptGroup"]:
                if "conceptProperties" in group:
                    for med in group["conceptProperties"]:
                        medicines.append(med["name"])
                        links.append(f"https://mor.nlm.nih.gov/RxNav/search?searchBy=0&searchTerm={med['name']}")

            return medicines[:5], links[:5]  # Limit to 5 medicines
        else:
            return ["No medicines found"], []
    except Exception as e:
        print(f"Error fetching medicines: {e}")
        return ["Error fetching medicines"], []

# Determine illness based on symptoms
def diagnose(symptoms):
    for illness, illness_symptoms in ILLNESS_DATABASE.items():
        if any(symptom in illness_symptoms for symptom in symptoms):
            return illness
    return None

# Handle user input & show results
def get_diagnosis():
    user_input = entry.get().strip().lower()
    symptoms = user_input.split(", ")  # Simple symptom extraction

    result_label.config(text="")  # Clear previous result
    for widget in medicine_buttons_frame.winfo_children():
        widget.destroy()  # Clear previous medicine buttons
    medicine_list_label.config(text="")

    if not symptoms:
        result_label.config(text="❌ No symptoms detected. Please describe clearly.")
        return

    illness = diagnose(symptoms)
    if illness:
        medicines, links = get_medicines(illness)

        result_text = f"\n🩺 Diagnosis: {illness.capitalize()}\n\n💊 Recommended Medicines:\n"
        medicine_list_label.config(text="\n".join(f"➡ {med}" for med in medicines))

        # Create buttons for each medicine with a link
        for i in range(len(medicines)):
            if i < len(links):
                btn = tk.Button(medicine_buttons_frame, text=medicines[i], font=("Arial", 10), fg="blue",
                                cursor="hand2", command=lambda url=links[i]: webbrowser.open(url))
                btn.pack(pady=2)
    else:
        result_label.config(text="❌ No matching illness found. Consult a doctor.")

    save_user_symptoms(username, user_input)

# Store user symptoms
def save_user_symptoms(username, symptoms):
    cursor.execute("UPDATE users SET symptoms = ? WHERE username = ?", (symptoms, username))
    conn.commit()

# UI Setup
root = tk.Tk()
root.title("🩺 Symptom Checker")
root.geometry("550x550")
root.configure(bg="#f0f8ff")

title_label = tk.Label(root, text="Describe your symptoms:", font=("Arial", 14, "bold"), bg="#f0f8ff")
title_label.pack(pady=10)

entry = tk.Entry(root, width=50, font=("Arial", 12))
entry.pack(pady=5)

submit_button = tk.Button(root, text="🔍 Diagnose", command=get_diagnosis, font=("Arial", 12), bg="#4caf50", fg="white")
submit_button.pack(pady=10)

result_label = tk.Label(root, text="", font=("Arial", 12), justify="left", wraplength=500, bg="#f0f8ff")
result_label.pack(pady=10)

medicine_list_label = tk.Label(root, text="", font=("Arial", 12), justify="left", wraplength=500, bg="#f0f8ff", fg="darkred")
medicine_list_label.pack(pady=5)

medicine_buttons_frame = tk.Frame(root, bg="#f0f8ff")
medicine_buttons_frame.pack(pady=10)

root.mainloop()
