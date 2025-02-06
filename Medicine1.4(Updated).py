import tkinter as tk
from tkinter import messagebox, ttk
import time
import spacy
import sqlite3
import webbrowser
from duckduckgo_search import DDGS
from threading import Thread

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Initialize SQLite Database
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# Create tables
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


# Add default admin & doctor
def add_default_users():
    default_users = [
        ("admin", "admin123", "admin", ""),
        ("doctor", "doctor123", "doctor", "")
    ]
    for user, pwd, role, symp in default_users:
        cursor.execute("SELECT * FROM users WHERE username = ?", (user,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, role, symptoms) VALUES (?, ?, ?, ?)",
                           (user, pwd, role, symp))
            conn.commit()


add_default_users()

# Predefined illnesses
ILLNESS_DATABASE = {
    "cold": {
        "symptoms": ["cough", "sneezing", "runny nose", "sore throat"],
        "search_query": "best medicine for cold site:healthline.com OR site:webmd.com"
    },
    "flu": {
        "symptoms": ["fever", "chills", "body ache", "fatigue"],
        "search_query": "best medicine for flu site:healthline.com OR site:webmd.com"
    },
    "migraine": {
        "symptoms": ["headache", "nausea", "light sensitivity"],
        "search_query": "best medicine for migraine site:healthline.com OR site:webmd.com"
    }
}


# Extract symptoms
def extract_symptoms(user_text):
    doc = nlp(user_text.lower())
    return [token.text for token in doc if token.text in sum([d["symptoms"] for d in ILLNESS_DATABASE.values()], [])]


# Diagnose illness
def diagnose(symptoms):
    matched_illness = None
    best_match_count = 0
    search_query = None

    print(f"User symptoms: {symptoms}")  # Debugging

    for illness, data in ILLNESS_DATABASE.items():
        common_symptoms = set(symptoms).intersection(data["symptoms"])
        print(f"Checking illness: {illness}, Matched symptoms: {common_symptoms}")  # Debugging

        if len(common_symptoms) > best_match_count:
            best_match_count = len(common_symptoms)
            matched_illness = illness
            search_query = data["search_query"]

    print(f"Diagnosis: {matched_illness}, Search Query: {search_query}")  # Debugging
    return matched_illness, search_query


# Fetch medicines from DuckDuckGo
def search_medicines(query):
    try:
        print(f"Searching for medicines using query: {query}")  # Debugging
        medicines = []
        links = []
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            print(f"Results from DuckDuckGo: {results}")  # Debugging
            for res in results:
                medicines.append(res["title"])
                links.append(res["href"])

        if not medicines:
            print("No medicines found!")
            return ["No specific medicines found"], []

        return medicines, links

    except Exception as e:
        print(f"Error fetching medicines: {e}")
        return ["Error fetching medicines"], []


# Open link in browser
def open_link(url):
    webbrowser.open(url)


# Typing effect
def typing_effect(text, label):
    label.config(text="")
    for i in range(len(text)):
        label.config(text=text[:i + 1])
        time.sleep(0.05)
        root.update()


# Handle user input
def get_diagnosis():
    global medicine_buttons_frame
    user_input = entry.get().strip()
    symptoms = extract_symptoms(user_input)

    for widget in medicine_buttons_frame.winfo_children():
        widget.destroy()

    if not symptoms:
        result_text = "❌ No recognizable symptoms found. Please describe your condition more clearly."
    else:
        illness, search_query = diagnose(symptoms)
        if illness and search_query:
            medicines, links = search_medicines(search_query)
            result_text = f"\n🩺 Diagnosis: {illness.capitalize()}\n\n💊 Recommended Medicines:\n"

            for i in range(len(medicines)):
                if i < len(links):
                    btn = tk.Button(medicine_buttons_frame, text=medicines[i], font=("Arial", 10), fg="blue",
                                    cursor="hand2", command=lambda url=links[i]: open_link(url))
                    btn.pack(pady=2)
        else:
            result_text = "❌ No matching illness found. Please consult a doctor."

    save_user_symptoms(username, user_input)
    Thread(target=typing_effect, args=(result_text, result_label)).start()


# Store user symptoms
def save_user_symptoms(username, symptoms):
    cursor.execute("UPDATE users SET symptoms = ? WHERE username = ?", (symptoms, username))
    conn.commit()


# Admin: View all users
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


# Login system
def login():
    global username, root
    username = user_var.get()
    password = password_entry.get()

    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    if user:
        if username == "admin":
            view_all_users()
        else:
            main_app()
    else:
        messagebox.showerror("Login Failed", "Incorrect username or password")


# Main UI
def main_app():
    global root, entry, result_label, medicine_buttons_frame

    root = tk.Tk()
    root.title("🩺 Symptom Checker")
    root.geometry("550x500")

    tk.Label(root, text="Describe your symptoms:", font=("Arial", 14, "bold")).pack(pady=10)
    entry = tk.Entry(root, width=50, font=("Arial", 12))
    entry.pack(pady=5)

    tk.Button(root, text="🔍 Diagnose", command=get_diagnosis, font=("Arial", 12), bg="#4caf50", fg="white").pack(
        pady=10)

    result_label = tk.Label(root, text="", font=("Arial", 12), justify="left", wraplength=500)
    result_label.pack(pady=20)

    medicine_buttons_frame = tk.Frame(root)
    medicine_buttons_frame.pack(pady=10)

    root.mainloop()


# Login UI
login_window = tk.Tk()
login_window.title("Login")
login_window.geometry("400x250")

user_var = tk.StringVar()
password_entry = tk.Entry(login_window, show="*")
tk.Label(login_window, text="Username:").pack()
ttk.Combobox(login_window, textvariable=user_var, values=["admin", "doctor"]).pack()
tk.Label(login_window, text="Password:").pack()
password_entry.pack()
tk.Button(login_window, text="Login", command=login).pack()

login_window.mainloop()
