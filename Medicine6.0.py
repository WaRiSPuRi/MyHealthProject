import tkinter as tk
from tkinter import messagebox
import time
import spacy
import sqlite3
import requests
from bs4 import BeautifulSoup
from threading import Thread

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Initialize SQLite Database
conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    symptoms TEXT
)
''')
conn.commit()

# Predefined illnesses and their symptoms
ILLNESS_DATABASE = {
    "cold": {
        "symptoms": ["cough", "sneezing", "runny nose", "sore throat"],
        "search_url": "https://www.webmd.com/cold-and-flu/ss/slideshow-common-cold-overview"
    },
    "flu": {
        "symptoms": ["fever", "chills", "body ache", "fatigue"],
        "search_url": "https://www.webmd.com/cold-and-flu/flu-treatment-options"
    },
    "migraine": {
        "symptoms": ["headache", "nausea", "light sensitivity"],
        "search_url": "https://www.webmd.com/migraines-headaches/migraine-medications"
    }
}


# Function to extract symptoms from user input
def extract_symptoms(user_text):
    doc = nlp(user_text.lower())
    extracted_symptoms = [token.text for token in doc if
                          token.text in sum([d["symptoms"] for d in ILLNESS_DATABASE.values()], [])]
    return extracted_symptoms


# Function to diagnose illness
def diagnose(symptoms):
    matched_illness = None
    best_match_count = 0
    search_url = None

    for illness, data in ILLNESS_DATABASE.items():
        common_symptoms = set(symptoms).intersection(data["symptoms"])
        if len(common_symptoms) > best_match_count:
            best_match_count = len(common_symptoms)
            matched_illness = illness
            search_url = data["search_url"]

    return matched_illness, search_url


# Function to scrape medicine names from WebMD
def scrape_medicines(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        medicine_results = []
        for item in soup.find_all(["h2", "h3"]):  # Look for section headings (common medicine names)
            text = item.get_text().strip()
            if "medicine" in text.lower() or "treatment" in text.lower() or "drug" in text.lower():
                medicine_results.append(text)

        return medicine_results[:3] if medicine_results else ["No specific medicines found"]

    except Exception as e:
        print(f"Error fetching medicines: {e}")
        return ["Error fetching medicines"]


# Function to display text letter by letter
def typing_effect(text, label):
    label.config(text="")
    for i in range(len(text)):
        label.config(text=text[:i + 1])
        time.sleep(0.05)
        root.update()


# Function to handle user input and display diagnosis
def get_diagnosis():
    user_input = entry.get().strip()
    symptoms = extract_symptoms(user_input)

    if not symptoms:
        result_text = "❌ No recognizable symptoms found. Please describe your condition more clearly."
    else:
        illness, search_url = diagnose(symptoms)
        if illness and search_url:
            medicines = scrape_medicines(search_url)
            result_text = f"\n🩺 Diagnosis: {illness.capitalize()}\n\n💊 Recommended Medicines:\n"
            result_text += "\n".join(f"➡ {med}" for med in medicines)
        else:
            result_text = "❌ No matching illness found. Please consult a doctor."

    save_user_symptoms(username, user_input)
    Thread(target=typing_effect, args=(result_text, result_label)).start()


# Function to store user symptoms in the database
def save_user_symptoms(username, symptoms):
    cursor.execute("UPDATE users SET symptoms = ? WHERE username = ?", (symptoms, username))
    conn.commit()


# Function to get user's past symptoms
def get_user_symptoms(username):
    cursor.execute("SELECT symptoms FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    return result[0] if result else ""


# Function to handle user login
def login():
    global username, root
    username = username_entry.get().strip()

    if not username:
        messagebox.showerror("Login Error", "Please enter a username.")
        return

    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (username, symptoms) VALUES (?, '')", (username,))
        conn.commit()

    past_symptoms = get_user_symptoms(username)
    messagebox.showinfo("Login Successful", f"Welcome, {username}!\nYour last symptoms: {past_symptoms}")

    login_window.destroy()
    main_app()


# Function to create the main symptom checker UI
def main_app():
    global root, entry, result_label

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

    # Submit Button
    submit_button = tk.Button(root, text="🔍 Diagnose", command=get_diagnosis, font=("Arial", 12), bg="#4caf50",
                              fg="white")
    submit_button.pack(pady=10)

    # Result Label
    result_label = tk.Label(root, text="", font=("Arial", 12), justify="left", wraplength=500, bg="#f0f8ff")
    result_label.pack(pady=20)

    root.mainloop()


# Create Login Window
login_window = tk.Tk()
login_window.title("Login")
login_window.geometry("300x200")

login_label = tk.Label(login_window, text="Enter your username:", font=("Arial", 12))
login_label.pack(pady=10)

username_entry = tk.Entry(login_window, font=("Arial", 12))
username_entry.pack(pady=5)

login_button = tk.Button(login_window, text="Login", command=login, font=("Arial", 12))
login_button.pack(pady=10)

login_window.mainloop()
