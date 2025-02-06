import tkinter as tk
from tkinter import messagebox, ttk
import time
import spacy
import sqlite3
import requests
import webbrowser
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

# Predefined illnesses and their symptoms
ILLNESS_DATABASE = {
    "cold": {
        "symptoms": ["cough", "sneezing", "runny nose", "sore throat"],
        "search_url": "https://www.webmd.com/cold-and-flu/cold-guide"
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
        medicine_links = []

        for section in soup.find_all("a", href=True):
            text = section.get_text().strip()
            link = section["href"]

            if any(keyword in text.lower() for keyword in ["medicine", "drug", "treatment", "medication"]):
                medicine_results.append(text)
                if "http" not in link:
                    link = "https://www.webmd.com" + link
                medicine_links.append(link)

        return medicine_results[:3], medicine_links[:3] if medicine_results else (["No specific medicines found"], [])

    except Exception as e:
        print(f"Error fetching medicines: {e}")
        return ["Error fetching medicines"], []


# Function to display text letter by letter
def typing_effect(text, label):
    label.config(text="")
    for i in range(len(text)):
        label.config(text=text[:i + 1])
        time.sleep(0.05)
        root.update()


# Function to open a website
def open_link(url):
    webbrowser.open(url)


# Function to handle user input and display diagnosis
def get_diagnosis():
    global medicine_buttons_frame
    user_input = entry.get().strip()
    symptoms = extract_symptoms(user_input)

    for widget in medicine_buttons_frame.winfo_children():
        widget.destroy()

    if not symptoms:
        result_text = "❌ No recognizable symptoms found. Please describe your condition more clearly."
    else:
        illness, search_url = diagnose(symptoms)
        if illness and search_url:
            medicines, links = scrape_medicines(search_url)
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


# Function to store user symptoms
def save_user_symptoms(username, symptoms):
    cursor.execute("UPDATE users SET symptoms = ? WHERE username = ?", (symptoms, username))
    conn.commit()


# Function to get user symptoms
def get_user_symptoms(username):
    cursor.execute("SELECT symptoms FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    return result[0] if result else ""


# Function for admin to view all users' history
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


# Function to create a new user account
def create_account():
    new_user = new_user_entry.get().strip()
    if new_user:
        cursor.execute("INSERT INTO users (username, symptoms) VALUES (?, '')", (new_user,))
        conn.commit()
        messagebox.showinfo("Success", "Account created successfully!")
    else:
        messagebox.showerror("Error", "Enter a valid username!")


# Function to display login window
def login():
    global username, root
    username = user_var.get()

    if username == "admin":
        view_all_users()
        return

    main_app()


# Function to create the main symptom checker UI
def main_app():
    global root, entry, result_label, medicine_buttons_frame

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

    medicine_buttons_frame = tk.Frame(root, bg="#f0f8ff")
    medicine_buttons_frame.pack(pady=10)

    root.mainloop()


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
