import tkinter as tk
from tkinter import messagebox
import sqlite3
import bcrypt
import webbrowser

# ---------------- DATABASE SETUP ----------------
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    symptoms TEXT
)
''')
conn.commit()


def add_default_users():
    users = [
        ("admin", "admin123", "admin"),
        ("doctor", "doctor123", "doctor"),
    ]

    for username, password, role in users:
        cursor.execute("SELECT username FROM users WHERE username=?", (username,))
        user_exists = cursor.fetchone()

        if not user_exists:
            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
            cursor.execute("INSERT INTO users (username, password, role, symptoms) VALUES (?, ?, ?, ?)",
                           (username, hashed_pw, role, ""))

    conn.commit()


add_default_users()
conn.close()


# ---------------- USER AUTHENTICATION ----------------
def register_user():
    username = entry_new_username.get()
    password = entry_new_password.get()

    if not username or not password:
        messagebox.showerror("Error", "Username and Password cannot be empty!")
        return

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM users WHERE username=?", (username,))
    if cursor.fetchone():
        messagebox.showerror("Error", "Username already exists!")
    else:
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password, role, symptoms) VALUES (?, ?, ?, ?)",
                       (username, hashed_pw, "user", ""))
        conn.commit()
        messagebox.showinfo("Success", "Account created successfully!")

    conn.close()


def login_user():
    global current_user, user_role
    username = entry_username.get()
    password = entry_password.get()

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("SELECT password, role FROM users WHERE username=?", (username,))
    user_data = cursor.fetchone()

    if user_data and bcrypt.checkpw(password.encode(), user_data[0]):
        current_user = username
        user_role = user_data[1]
        messagebox.showinfo("Login Successful", f"Welcome, {username}!")
        login_window.destroy()
        open_symptom_checker()
    else:
        messagebox.showerror("Error", "Invalid Username or Password")

    conn.close()


# ---------------- MAIN UI ----------------
def open_symptom_checker():
    root = tk.Tk()
    root.title("Symptom Checker")

    tk.Label(root, text="Describe your symptoms:").pack()
    symptom_entry = tk.Entry(root, width=50)
    symptom_entry.pack()

    def diagnose():
        symptoms = symptom_entry.get()
        if not symptoms:
            messagebox.showerror("Error", "Please enter symptoms!")
            return

        diagnosis, medicines = get_diagnosis(symptoms)

        result_label.config(text=f"Diagnosis: {diagnosis}")
        medicine_list.delete(0, tk.END)

        for med in medicines:
            medicine_list.insert(tk.END, med[0])  # Medicine name
            tk.Button(root, text=med[0], command=lambda url=med[1]: webbrowser.open(url)).pack()

    tk.Button(root, text="Diagnose", command=diagnose).pack()

    result_label = tk.Label(root, text="")
    result_label.pack()

    medicine_list = tk.Listbox(root, width=50)
    medicine_list.pack()

    root.mainloop()


# ---------------- DIAGNOSIS LOGIC ----------------
def get_diagnosis(symptoms):
    """ Basic symptom-matching logic (could be expanded with AI/NLP). """
    symptoms = symptoms.lower()

    illness_data = {
        "cold": {
            "symptoms": ["cough", "fever", "sore throat", "sneezing"],
            "medicines": [("Tylenol", "https://www.tylenol.com/"),
                          ("NyQuil", "https://www.vicks.com/en-us")]
        },
        "flu": {
            "symptoms": ["fever", "chills", "body ache"],
            "medicines": [("Tamiflu", "https://www.tamiflu.com/"),
                          ("Advil", "https://www.advil.com/")]
        },
        "migraine": {
            "symptoms": ["headache", "nausea", "sensitivity to light"],
            "medicines": [("Excedrin", "https://www.excedrin.com/"),
                          ("Ibuprofen", "https://www.advil.com/")]
        }
    }

    for illness, data in illness_data.items():
        if any(symptom in symptoms for symptom in data["symptoms"]):
            return illness.capitalize(), data["medicines"]

    return "Unknown", [("Check WebMD", "https://www.webmd.com/")]


# ---------------- LOGIN UI ----------------
login_window = tk.Tk()
login_window.title("Login")

tk.Label(login_window, text="Username:").pack()
entry_username = tk.Entry(login_window)
entry_username.pack()

tk.Label(login_window, text="Password:").pack()
entry_password = tk.Entry(login_window, show="*")
entry_password.pack()

tk.Button(login_window, text="Login", command=login_user).pack()
tk.Label(login_window, text="New user? Create an account:").pack()

entry_new_username = tk.Entry(login_window)
entry_new_username.pack()

entry_new_password = tk.Entry(login_window, show="*")
entry_new_password.pack()

tk.Button(login_window, text="Register", command=register_user).pack()

login_window.mainloop()