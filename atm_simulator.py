import tkinter as tk
from tkinter import messagebox
import mysql.connector
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# --- 1. MYSQL CONNECTION HELPER ---
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "atm_db")
    )


# --- 2. MAIN ATM APPLICATION ---
class ATMSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("ATM Banking Simulator (MySQL)")
        self.root.geometry("400x450")
        self.root.resizable(False, False)

        self.current_acc = None
        self.show_login_screen()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # --- SCREEN 1: LOGIN ---
    def show_login_screen(self):
        self.clear_screen()
        self.current_acc = None

        tk.Label(self.root, text="Welcome to Offline ATM", font=("Arial", 16, "bold")).pack(pady=20)

        tk.Label(self.root, text="Account Number:", font=("Arial", 11)).pack(pady=5)
        self.acc_entry = tk.Entry(self.root, font=("Arial", 12), justify="center")
        self.acc_entry.pack(pady=5)

        tk.Label(self.root, text="PIN:", font=("Arial", 11)).pack(pady=5)
        self.pin_entry = tk.Entry(self.root, font=("Arial", 12), show="*", justify="center")
        self.pin_entry.pack(pady=5)

        tk.Button(self.root, text="Login", font=("Arial", 12), width=15, command=self.verify_login).pack(pady=(20, 5))
        tk.Button(self.root, text="Create Account", font=("Arial", 11), width=15, command=self.show_register_screen).pack(pady=5)
        tk.Label(
            self.root,
            text="Sample Accounts:\nAcc: 1001 | PIN: 1234\nAcc: 1002 | PIN: 4321",
            fg="gray",
            font=("Arial", 9)
        ).pack(pady=10)

    def verify_login(self):
        acc_no = self.acc_entry.get().strip()
        pin = self.pin_entry.get().strip()

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM accounts WHERE acc_no = %s AND pin = %s", (acc_no, pin))
            user = cur.fetchone()
            conn.close()

            if user:
                self.current_acc = acc_no
                self.show_dashboard()
            else:
                messagebox.showerror("Login Failed", "Invalid Account Number or PIN.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Could not connect to MySQL:\n{err}")

    # --- SCREEN 1B: CREATE ACCOUNT ---
    def show_register_screen(self):
        self.clear_screen()

        tk.Label(self.root, text="Create New Account", font=("Arial", 16, "bold")).pack(pady=15)

        tk.Label(self.root, text="New Account Number:", font=("Arial", 11)).pack(pady=3)
        self.reg_acc_entry = tk.Entry(self.root, font=("Arial", 12), justify="center")
        self.reg_acc_entry.pack(pady=3)

        tk.Label(self.root, text="Set PIN:", font=("Arial", 11)).pack(pady=3)
        self.reg_pin_entry = tk.Entry(self.root, font=("Arial", 12), show="*", justify="center")
        self.reg_pin_entry.pack(pady=3)

        tk.Label(self.root, text="Initial Deposit (₹):", font=("Arial", 11)).pack(pady=3)
        self.reg_bal_entry = tk.Entry(self.root, font=("Arial", 12), justify="center")
        self.reg_bal_entry.pack(pady=3)

        tk.Button(self.root, text="Register", font=("Arial", 12), width=15, command=self.create_account).pack(pady=(15, 5))
        tk.Button(self.root, text="Back to Login", font=("Arial", 10), width=15, command=self.show_login_screen).pack(pady=5)

    def create_account(self):
        acc_no = self.reg_acc_entry.get().strip()
        pin = self.reg_pin_entry.get().strip()
        bal_text = self.reg_bal_entry.get().strip()

        # Check empty fields
        if not acc_no or not pin or not bal_text:
            messagebox.showwarning("Missing Info", "Please fill in all fields.")
            return

        # Validate initial deposit amount
        try:
            initial_balance = float(bal_text)
            if initial_balance < 0:
                messagebox.showwarning("Invalid Amount", "Initial deposit cannot be negative.")
                return
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for initial deposit.")
            return

        # Insert new account into MySQL
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO accounts (acc_no, pin, balance) VALUES (%s, %s, %s)",
                (acc_no, pin, initial_balance)
            )
            conn.commit()
            conn.close()

            messagebox.showinfo("Success", f"Account {acc_no} created! You can now log in.")
            self.show_login_screen()

        except mysql.connector.IntegrityError:
            # Triggers automatically if acc_no already exists (PRIMARY KEY)
            messagebox.showerror("Duplicate Account", "This Account Number already exists.")
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"MySQL Error:\n{err}")

    # --- SCREEN 2: DASHBOARD ---
    def show_dashboard(self):
        self.clear_screen()

        tk.Label(self.root, text=f"Account: {self.current_acc}", font=("Arial", 14, "bold")).pack(pady=15)

        self.balance_label = tk.Label(self.root, text="", font=("Arial", 13), fg="green")
        self.balance_label.pack(pady=5)
        self.update_balance_display()

        tk.Label(self.root, text="Enter Amount:", font=("Arial", 11)).pack(pady=(20, 5))
        self.amount_entry = tk.Entry(self.root, font=("Arial", 12), justify="center")
        self.amount_entry.pack(pady=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="Deposit", width=12, font=("Arial", 11), command=self.deposit).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Withdraw", width=12, font=("Arial", 11), command=self.withdraw).grid(row=0, column=1, padx=10)

        tk.Button(self.root, text="Transaction History", width=26, font=("Arial", 11), command=self.show_history).pack(pady=10)
        tk.Button(self.root, text="Logout", width=26, font=("Arial", 11), command=self.show_login_screen).pack(pady=5)

    def get_balance(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT balance FROM accounts WHERE acc_no = %s", (self.current_acc,))
        balance = float(cur.fetchone()[0])
        conn.close()
        return balance

    def update_balance_display(self):
        bal = self.get_balance()
        self.balance_label.config(text=f"Current Balance: ₹{bal:.2f}")

    def log_transaction(self, op_type, amount):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO transactions (acc_no, op_type, amount, timestamp) VALUES (%s, %s, %s, %s)",
            (self.current_acc, op_type, amount, now)
        )
        conn.commit()
        conn.close()

    # --- BANKING OPERATIONS ---
    def get_valid_amount(self):
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                messagebox.showwarning("Invalid Input", "Please enter a positive amount.")
                return None
            return amount
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid numeric amount.")
            return None

    def deposit(self):
        amount = self.get_valid_amount()
        if amount is None:
            return

        new_balance = self.get_balance() + amount

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE accounts SET balance = %s WHERE acc_no = %s", (new_balance, self.current_acc))
        conn.commit()
        conn.close()

        self.log_transaction("Deposit", amount)
        self.update_balance_display()
        self.amount_entry.delete(0, tk.END)
        messagebox.showinfo("Success", f"₹{amount:.2f} deposited successfully.")

    def withdraw(self):
        amount = self.get_valid_amount()
        if amount is None:
            return

        current_balance = self.get_balance()

        if amount > current_balance:
            messagebox.showerror("Transaction Declined", "Insufficient funds!")
            return

        new_balance = current_balance - amount

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE accounts SET balance = %s WHERE acc_no = %s", (new_balance, self.current_acc))
        conn.commit()
        conn.close()

        self.log_transaction("Withdrawal", amount)
        self.update_balance_display()
        self.amount_entry.delete(0, tk.END)
        messagebox.showinfo("Success", f"₹{amount:.2f} withdrawn successfully.")

    # --- SCREEN 3: TRANSACTION HISTORY ---
    def show_history(self):
        history_win = tk.Toplevel(self.root)
        history_win.title("Transaction History")
        history_win.geometry("420x300")

        tk.Label(history_win, text=f"History for Account {self.current_acc}", font=("Arial", 12, "bold")).pack(pady=10)

        text_area = tk.Text(history_win, width=48, height=13, font=("Consolas", 10))
        text_area.pack(padx=10, pady=5)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT op_type, amount, timestamp FROM transactions WHERE acc_no = %s ORDER BY id DESC",
            (self.current_acc,)
        )
        rows = cur.fetchall()
        conn.close()

        if not rows:
            text_area.insert(tk.END, "No transactions found.")
        else:
            text_area.insert(tk.END, f"{'TYPE':<12} | {'AMOUNT':<10} | {'DATE & TIME'}\n")
            text_area.insert(tk.END, "-" * 46 + "\n")
            for op_type, amount, timestamp in rows:
                text_area.insert(tk.END, f"{op_type:<12} | ₹{float(amount):<9.2f} | {timestamp}\n")

        text_area.config(state="disabled")


# --- START APPLICATION ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ATMSimulator(root)
    root.mainloop()