import flet as ft
import uuid
import json
import base64
import requests
import os
from datetime import datetime
from flet import colors, icons

# ========== CONFIGURATION ==========
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE", "YOUR_SHORTCODE")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY", "YOUR_PASSKEY")
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY", "YOUR_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET", "YOUR_CONSUMER_SECRET")

# ========== DATA STORAGE ==========
class Database:
    def __init__(self):
        self.users = []
        self.jobs = []
        self.transactions = []
        self.reviews = []
        self.load_data()
    
    def save_data(self):
        with open('data.json', 'w') as f:
            json.dump({
                'users': self.users,
                'jobs': self.jobs,
                'transactions': self.transactions,
                'reviews': self.reviews
            }, f)
    
    def load_data(self):
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
                self.users = data.get('users', [])
                self.jobs = data.get('jobs', [])
                self.transactions = data.get('transactions', [])
                self.reviews = data.get('reviews', [])
        except (FileNotFoundError, json.JSONDecodeError):
            self.save_data()

db = Database()

# ========== MAIN APP ==========
def main(page: ft.Page):
    page.title = "TaskerApp"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = colors.GREY_50
    
    current_user = None

    def create_app_bar(title):
        return ft.AppBar(
            title=ft.Text(title, font_family="Poppins", color=colors.WHITE),
            bgcolor=colors.BLUE_800,
            center_title=True,
            elevation=4
        )
    
    def show_login():
        phone = ft.TextField(label="Safaricom Number", prefix_text="+254", width=300)
        otp = ft.TextField(label="OTP Code", visible=False, password=True)
        
        def send_otp(e):
            if not phone.value.startswith('7') or len(phone.value) != 9:
                page.snack_bar = ft.SnackBar(ft.Text("Invalid Safaricom number!"), bgcolor=colors.RED_400)
                page.snack_bar.open = True
                page.update()
                return
            otp.value = "1234"  # Mock OTP
            otp.visible = True
            verify_btn.visible = True
            page.update()
        
        def verify_otp(e):
            nonlocal current_user
            if otp.value == "1234":
                current_user = {"id": str(uuid.uuid4()), "phone": f"+254{phone.value}"}
                db.users.append(current_user)
                db.save_data()
                page.go("/main")
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Incorrect OTP!"), bgcolor=colors.RED_400)
                page.snack_bar.open = True
                page.update()
        
        verify_btn = ft.FilledButton("Verify", visible=False, on_click=verify_otp)
        return ft.View("/login", [
            create_app_bar("Login"),
            ft.Column([
                phone,
                otp,
                ft.FilledButton("Send OTP", on_click=send_otp),
                verify_btn
            ], alignment=ft.MainAxisAlignment.CENTER)
        ])
    
    def main_dashboard():
        jobs_column = ft.Column(spacing=15, scroll=ft.ScrollMode.ALWAYS)
        for job in db.jobs:
            jobs_column.controls.append(ft.Card(ft.Text(job['title'])))
        return ft.View("/main", [create_app_bar("Available Jobs"), jobs_column])
    
    def route_change(e):
        page.views.clear()
        if page.route == "/login":
            page.views.append(show_login())
        elif page.route == "/main":
            page.views.append(main_dashboard())
        page.update()
    
    page.on_route_change = route_change
    page.go("/login")

port = int(os.getenv("PORT", "5000"))
ft.app(target=main, view=ft.WEB_BROWSER, port=port)

