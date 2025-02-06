import tkinter as tk
from tkinter import messagebox, ttk
import time
import spacy
import sqlite3
import requests
import webbrowser
from duckduckgo_search import DDGS
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
cursor.execute('''
CREATE TABLE IF NOT EXISTS admin (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE
)
''')
conn.commit()

# Add admin user if not exists
cursor.execute("SELECT * FROM admin WHERE username = 'admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO admin (username) VALUES ('admin')")
    conn.commit()

# Predefined illnesses
ILLNESS_DATABASE = {
    "cold": {
        "symptoms": ["cough", "sneezing", "runny nose", "sore throat"],
        "search_query": "best medicine for cold site:healthline.com OR site:webmd.com OR site:mayoclinic.org"
    },
    "flu": {
        "symptoms": ["fever", "chills", "body ache", "fatigue"],
        "search_query": "best medicine for flu site:healthline.com OR site:webmd.com OR site:mayoclinic.org"
    },
    "migraine": {
        "symptoms": ["headache", "nausea", "light sensitivity"],
        "search_query": "best medicine for migraine site:healthline.com OR site:webmd.com OR site:mayoclinic.org"
    }
}


# Extract symptoms from user input
def extract_symptoms(user_text):
    doc = nlp(user_text.lower())
    return [token.text for token in doc if token.text in sum([d["symptoms"] for d in ILLNESS_DATABASE.values()], [])]


# Diagnose illness
def diagnose(symptoms):
    matched_illness = None
    best_match_count = 0
    search_query = None

    for illness, data in ILLNESS_DATABASE.items():
        common_symptoms = set(symptoms).intersection(data["symptoms"])
        if len(common_symptoms) > best_match_count:
            best_match_count = len(common_symptoms)
            matched_illness = illness
            search_query = data["search_query"]

    return matched_illness, search_query


# Use DuckDuckGo to fetch medicine names
def search_medicines(query):
    try:
        medicines = []
        links = []
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            for res in results:
                medicines.append(res["title"])
                links.append(res["href"])

        return medicines, links if medicines else (["No specific medicines found"], [])

    except Exception as e:
        print(f"Error fetching medicines: {e}")
        return ["Error fetching medicines"], []


# Open medicine source in browser
def open_link(url):
    webbrowser.open(url)


# Display text letter by letter
def typing_effect(text, label):
    label.config(text="")
    for i in range(len(text)):
        label.config(text=text[:i + 1])
        time.sleep(0.05)
        root.update()


# Handle user input & show diagnosis
def get_diagnosis():
    global medicine_buttons_frame, medicine_list_label
    user_input = entry.get().strip()
    symptoms = extract_symptoms(user_input)

    # Clear old results
    for widget in medicine_buttons_frame.winfo_children():
        widget.destroy()
    medicine_list_label.config(text="")

    if not symptoms:
        result_text = "❌ No recognizable symptoms found. Please describe your condition more clearly."
    else:
        illness, search_query = diagnose(symptoms)
        if illness and search_query:
            medicines, links = search_medicines(search_query)

            result_text = f"\n🩺 Diagnosis: {illness.capitalize()}\n\n💊 Recommended Medicines:\n"

            # Display medicine names as text
            medicine_names_text = "\n".join(f"➡ {med}" for med in medicines)
            medicine_list_label.config(text=medicine_names_text)

            # Create buttons for each medicine with a link
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


# Get user symptoms
def get_user_symptoms(username):
    cursor.execute("SELECT symptoms FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    return result[0] if result else ""


# Admin: View all users' history
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


# Create new user
def create_account():
    new_user = new_user_entry.get().strip()
    if new_user:
        cursor.execute("INSERT INTO users (username, symptoms) VALUES (?, '')", (new_user,))
        conn.commit()
        messagebox.showinfo("Success", "Account created successfully!")
    else:
        messagebox.showerror("Error", "Enter a valid username!")


# Login
def login():
    global username, root
    username = user_var.get()

    if username == "admin":
        view_all_users()
        return

    main_app()


# Main UI
def main_app():
    global root, entry, result_label, medicine_buttons_frame, medicine_list_label

    root = tk.Tk()
    root.title("🩺 Symptom Checker")
    root.geometry("550x550")
    root.configure(bg="#f0f8ff")

    title_label = tk.Label(root, text="Describe your symptoms:", font=("Arial", 14, "bold"), bg="#f0f8ff")
    title_label.pack(pady=10)

    entry = tk.Entry(root, width=50, font=("Arial", 12))
    entry.pack(pady=5)

    submit_button = tk.Button(root, text="🔍 Diagnose", command=get_diagnosis, font=("Arial", 12), bg="#4caf50",
                              fg="white")
    submit_button.pack(pady=10)

    result_label = tk.Label(root, text="", font=("Arial", 12), justify="left", wraplength=500, bg="#f0f8ff")
    result_label.pack(pady=10)

    medicine_list_label = tk.Label(root, text="", font=("Arial", 12), justify="left", wraplength=500, bg="#f0f8ff",
                                   fg="darkred")
    medicine_list_label.pack(pady=5)

    medicine_buttons_frame = tk.Frame(root, bg="#f0f8ff")
    medicine_buttons_frame.pack(pady=10)

    root.mainloop()


# Login UI
login_window = tk.Tk()
login_window.title("Login")
login_window.geometry("400x250")

user_var = tk.StringVar()
cursor.execute("SELECT username FROM users")
users = [row[0] for row in cursor.fetchall()]

tk.Label(login_window, text="Select your username:", font=("Arial", 12)).pack(pady=5)
ttk.Combobox(login_window, textvariable=user_var, values=users).pack()

tk.Button(login_window, text="Login", command=login).pack(pady=5)
tk.Button(login_window, text="Create Account", command=create_account).pack(pady=5)

new_user_entry = tk.Entry(login_window)
new_user_entry.pack(pady=5)

login_window.mainloop()
