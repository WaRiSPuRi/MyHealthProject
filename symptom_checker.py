import json
import tkinter as tk
from tkinter import messagebox, ttk
import requests
from bs4 import BeautifulSoup
import webbrowser
import matplotlib.pyplot as plt

# === USER DATA STORAGE (JSON FILE) === #
USER_DATA_FILE = "users.json"

# Pre-set Admin and Doctor users
DEFAULT_USERS = {
    "admin": {"password": "admin123", "role": "admin", "symptoms": []},
    "doctor": {"password": "doctor123", "role": "doctor", "symptoms": []},
}


# === FUNCTION TO LOAD USERS === #
def load_users():
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return DEFAULT_USERS


# === FUNCTION TO SAVE USERS === #
def save_users(users):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(users, f, indent=4)


# === FUNCTION TO SCRAPE MEDICINES === #
def get_medicines_for_disease(disease):
    search_url = f"https://www.webmd.com/search/search_results/default.aspx?query={disease} medicine"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, "html.parser")

    medicines = []

    # Find medicine names by searching for specific classes in WebMD
    for div in soup.find_all("div", class_="search-results-doc-title"):
        title = div.text.strip()
        link = div.find("a")["href"] if div.find("a") else "#"

        if "drug" in title.lower() or "medication" in title.lower():
            medicines.append((title, "https://www.webmd.com" + link))

    return medicines[:3]  # Return top 3 medicines


# === LOGIN FUNCTION === #
def login():
    username = entry_username.get()
    password = entry_password.get()
    users = load_users()

    if username in users and users[username]["password"] == password:
        messagebox.showinfo("Login Successful", f"Welcome, {username}!")
        root.destroy()
        main_app(username, users[username]["role"])
    else:
        messagebox.showerror("Login Failed", "Invalid username or password!")


# === REGISTER FUNCTION === #
def register():
    username = entry_username.get()
    password = entry_password.get()
    users = load_users()

    if username in users:
        messagebox.showerror("Error", "Username already exists!")
    else:
        users[username] = {"password": password, "role": "user", "symptoms": []}
        save_users(users)
        messagebox.showinfo("Success", "Account created successfully!")


# === MAIN APP UI === #
def main_app(username, role):
    app = tk.Tk()
    app.title("Symptom Checker")
    app.geometry("600x500")

    tk.Label(app, text="Describe your symptoms:", font=("Arial", 14)).pack(pady=10)
    symptom_entry = tk.Entry(app, width=50)
    symptom_entry.pack(pady=5)

    def diagnose():
        symptoms = symptom_entry.get()
        disease = "flu" if "fever" in symptoms else "migraine"  # Example simple diagnosis
        medicines = get_medicines_for_disease(disease)

        result_label.config(text=f"Diagnosis: {disease.capitalize()}")
        medicines_frame.pack()

        # Clear previous buttons
        for widget in medicines_frame.winfo_children():
            widget.destroy()

        # Show medicines
        for med, link in medicines:
            tk.Button(medicines_frame, text=med, fg="blue", cursor="hand2",
                      command=lambda url=link: webbrowser.open(url)).pack(pady=2)

    tk.Button(app, text="Diagnose", bg="green", fg="white", command=diagnose).pack(pady=10)

    result_label = tk.Label(app, text="", font=("Arial", 12))
    result_label.pack()

    medicines_frame = tk.Frame(app)
    medicines_frame.pack()

    # Admin Feature: View User Data
    if role == "admin":
        def show_user_data():
            users = load_users()
            user_info = "\n".join([f"{u}: {d['symptoms']}" for u, d in users.items()])
            messagebox.showinfo("User Data", user_info)

        tk.Button(app, text="View User Data", bg="red", fg="white", command=show_user_data).pack(pady=10)

    # Show graph button
    def show_graph():
        users = load_users()
        disease_counts = {}
        for user in users.values():
            for symptom in user["symptoms"]:
                disease_counts[symptom] = disease_counts.get(symptom, 0) + 1

        if not disease_counts:
            messagebox.showwarning("No Data", "No symptom data available.")
            return

        diseases = list(disease_counts.keys())
        counts = list(disease_counts.values())

        plt.figure(figsize=(6, 4))
        plt.bar(diseases, counts, color="skyblue")
        plt.xlabel("Diseases")
        plt.ylabel("Occurrences")
        plt.title("Common Diagnosed Illnesses")
        plt.xticks(rotation=45)
        plt.show()

    tk.Button(app, text="Show Symptom Graph", command=show_graph).pack(pady=10)

    app.mainloop()


# === LOGIN UI === #
root = tk.Tk()
root.title("Login Page")
root.geometry("400x300")

tk.Label(root, text="Username:", font=("Arial", 12)).pack()
entry_username = tk.Entry(root, width=30)
entry_username.pack()

tk.Label(root, text="Password:", font=("Arial", 12)).pack()
entry_password = tk.Entry(root, width=30, show="*")
entry_password.pack()

tk.Button(root, text="Login", command=login, bg="blue", fg="white").pack(pady=10)
tk.Button(root, text="Create Account", command=register, bg="green", fg="white").pack(pady=5)

root.mainloop()
