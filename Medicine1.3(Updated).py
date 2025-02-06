import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import requests
import webbrowser
import matplotlib.pyplot as plt
from threading import Thread


import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Drop the old table (ONLY IF SAFE)
cursor.execute("DROP TABLE IF EXISTS users")

# Recreate the table with a password column
cursor.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    symptoms TEXT
)
''')

conn.commit()
conn.close()
print("Database reset and updated successfully!")

import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Add the password column if it does not exist
try:
    cursor.execute("ALTER TABLE users ADD COLUMN password TEXT DEFAULT ''")
    conn.commit()
    print("Password column added successfully!")
except sqlite3.OperationalError:
    print("Column already exists or another issue occurred.")

conn.close()


# --------------------------- DATABASE SETUP --------------------------- #
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create user table with passwords
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    symptoms TEXT
)
''')

# Add default admin and doctor users
default_users = [
    ("admin", "admin123", "admin"),
    ("doctor", "doctor123", "doctor")
]

for user, pwd, role in default_users:
    cursor.execute("SELECT * FROM users WHERE username = ?", (user,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role, symptoms) VALUES (?, ?, ?, '')", (user, pwd, role))

conn.commit()

# --------------------------- PREDEFINED ILLNESSES --------------------------- #
ILLNESS_DATABASE = {
    "cold": ["cough", "sneezing", "runny nose", "sore throat"],
    "flu": ["fever", "chills", "body ache", "fatigue"],
    "migraine": ["headache", "nausea", "light sensitivity"]
}

# --------------------------- MEDICINE LOOKUP FUNCTION --------------------------- #
def get_medicines_for_disease(disease):
    """Fetch medicines using RxNorm API"""
    base_url = "https://rxnav.nlm.nih.gov/REST/drugs.json?name="
    response = requests.get(base_url + disease)

    if response.status_code == 200:
        data = response.json()
        medicines = []

        if "drugGroup" in data and "conceptGroup" in data["drugGroup"]:
            for group in data["drugGroup"]["conceptGroup"]:
                if "conceptProperties" in group:
                    for item in group["conceptProperties"]:
                        medicines.append(item["name"])

        return medicines[:3] if medicines else ["No medicines found"]
    return ["Error fetching medicines"]

# --------------------------- DIAGNOSIS FUNCTION --------------------------- #
def diagnose(symptoms):
    best_match = None
    max_match_count = 0

    for illness, illness_symptoms in ILLNESS_DATABASE.items():
        common_symptoms = set(symptoms).intersection(illness_symptoms)
        if len(common_symptoms) > max_match_count:
            max_match_count = len(common_symptoms)
            best_match = illness

    return best_match

# --------------------------- UI FUNCTIONS --------------------------- #
def get_diagnosis():
    symptoms = entry.get().strip().lower().split(", ")
    illness = diagnose(symptoms)

    if illness:
        medicines = get_medicines_for_disease(illness)
        result_label.config(text=f"🩺 Diagnosis: {illness.capitalize()}\n\n💊 Recommended Medicines:\n" + "\n".join(medicines))
    else:
        result_label.config(text="❌ No matching illness found.")

def create_account():
    new_user = new_user_entry.get().strip()
    new_pass = new_pass_entry.get().strip()

    if new_user and new_pass:
        cursor.execute("SELECT * FROM users WHERE username = ?", (new_user,))
        if cursor.fetchone():
            messagebox.showerror("Error", "Username already exists!")
        else:
            cursor.execute("INSERT INTO users (username, password, role, symptoms) VALUES (?, ?, 'user', '')",
                           (new_user, new_pass))
            conn.commit()
            messagebox.showinfo("Success", "Account created successfully!")
    else:
        messagebox.showerror("Error", "Enter valid details!")

def login():
    global username, root
    username = user_var.get()
    password = pass_var.get()

    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user_data = cursor.fetchone()

    if user_data:
        role = user_data[3]
        if role == "admin":
            view_all_users()
        else:
            main_app()
    else:
        messagebox.showerror("Error", "Invalid username or password!")

def view_all_users():
    cursor.execute("SELECT username, symptoms FROM users")
    all_users = cursor.fetchall()

    admin_window = tk.Toplevel()
    admin_window.title("Admin Panel")
    admin_window.geometry("400x300")

    text = tk.Text(admin_window, wrap=tk.WORD, font=("Arial", 12))
    text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    for user, symptoms in all_users:
        text.insert(tk.END, f"👤 {user}: {symptoms}\n\n")

def show_symptom_graph():
    labels = list(ILLNESS_DATABASE.keys())
    values = [len(symptoms) for symptoms in ILLNESS_DATABASE.values()]

    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color=["blue", "green", "red"])
    plt.xlabel("Illnesses")
    plt.ylabel("Number of Symptoms")
    plt.title("Illness vs. Number of Symptoms")
    plt.show()

# --------------------------- MAIN UI --------------------------- #
def main_app():
    global root, entry, result_label

    root = tk.Tk()
    root.title("🩺 Symptom Checker")
    root.geometry("550x500")
    root.configure(bg="#f0f8ff")

    title_label = tk.Label(root, text="Describe your symptoms:", font=("Arial", 14, "bold"), bg="#f0f8ff")
    title_label.pack(pady=10)

    entry = tk.Entry(root, width=50, font=("Arial", 12))
    entry.pack(pady=5)

    submit_button = tk.Button(root, text="🔍 Diagnose", command=get_diagnosis, font=("Arial", 12), bg="#4caf50",
                              fg="white")
    submit_button.pack(pady=10)

    result_label = tk.Label(root, text="", font=("Arial", 12), justify="left", wraplength=500, bg="#f0f8ff")
    result_label.pack(pady=20)

    graph_button = tk.Button(root, text="📊 Show Symptom Graph", command=show_symptom_graph, font=("Arial", 12),
                             bg="#ff9800", fg="white")
    graph_button.pack(pady=10)

    root.mainloop()

# --------------------------- LOGIN UI --------------------------- #
login_window = tk.Tk()
login_window.title("Login")
login_window.geometry("400x300")

user_var = tk.StringVar()
pass_var = tk.StringVar()

cursor.execute("SELECT username FROM users")
users = [row[0] for row in cursor.fetchall()]

tk.Label(login_window, text="Username:", font=("Arial", 12)).pack(pady=5)
ttk.Combobox(login_window, textvariable=user_var, values=users).pack()

tk.Label(login_window, text="Password:", font=("Arial", 12)).pack(pady=5)
new_pass_entry = tk.Entry(login_window, textvariable=pass_var, show="*")
new_pass_entry.pack()

tk.Button(login_window, text="Login", command=login).pack(pady=5)
tk.Button(login_window, text="Create Account", command=create_account).pack(pady=5)

new_user_entry = tk.Entry(login_window)
new_user_entry.pack(pady=5)

login_window.mainloop()
