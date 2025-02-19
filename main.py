import flet as ft
import uuid
import json
import base64
import requests
from datetime import datetime

# ========== CONFIGURATION ==========
MPESA_SHORTCODE = "YOUR_SHORTCODE"
MPESA_PASSKEY = "YOUR_PASSKEY"
MPESA_CONSUMER_KEY = "YOUR_CONSUMER_KEY"
MPESA_CONSUMER_SECRET = "YOUR_CONSUMER_SECRET"

# ========== DATA STORAGE ==========
class Database:
    def __init__(self):
        self.users = []
        self.jobs = []
        self.transactions = []
        self.reviews = []
    
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
        except FileNotFoundError:
            pass

db = Database()
db.load_data()

# ========== MPESA INTEGRATION ==========
class MpesaManager:
    @staticmethod
    def get_access_token():
        auth = base64.b64encode(f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}".encode()).decode()
        response = requests.get(
            "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials",
            headers={'Authorization': f'Basic {auth}'}
        )
        return response.json().get('access_token')

    @staticmethod
    def stk_push(phone, amount, reference):
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}".encode()).decode()
        
        payload = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": "https://your-domain.com/callback",
            "AccountReference": reference,
            "TransactionDesc": "TaskerApp Transaction"
        }
        
        response = requests.post(
            "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={
                'Authorization': f'Bearer {MpesaManager.get_access_token()}',
                'Content-Type': 'application/json'
            }
        )
        return response.json()

# ========== MAIN APP ==========
def main(page: ft.Page):
    page.title = "TaskerApp"
    page.theme = ft.Theme(color_scheme_seed=ft.colors.BLUE)
    page.bgcolor = ft.colors.GREY_100
    
    current_user = None
    
    def login_view():
        phone = ft.TextField(label="Phone Number", prefix_text="+254", bgcolor=ft.colors.WHITE, border_radius=8)
        otp = ft.TextField(label="OTP", visible=False, bgcolor=ft.colors.WHITE, border_radius=8)
        send_otp_btn = ft.FilledButton("Send OTP", icon=ft.icons.SEND, on_click=lambda e: send_otp(phone.value))
        verify_btn = ft.FilledButton("Verify", icon=ft.icons.CHECK, on_click=lambda e: verify_otp(phone.value, otp.value), visible=False)

        def send_otp(number):
            if len(number) != 9 or not number.startswith('7'):
                page.snack_bar = ft.SnackBar(ft.Text("Invalid Safaricom number!", color=ft.colors.RED))
                page.snack_bar.open = True
                page.update()
                return
            otp.value = "1234"
            otp.visible = True
            verify_btn.visible = True
            page.update()

        def verify_otp(number, code):
            nonlocal current_user
            if code == "1234":
                current_user = {
                    'id': str(uuid.uuid4()),
                    'phone': f"+254{number}",
                    'is_tasker': False,
                    'balance': 0.0,
                    'rating': 0.0,
                    'reviews': []
                }
                db.users.append(current_user)
                db.save_data()
                page.go("/main")
            page.update()

        return ft.View(
            "/login",
            controls=[
                ft.Column([
                    ft.Icon(name=ft.icons.WORK, size=80, color=ft.colors.BLUE),
                    ft.Text("Welcome to TaskerApp", size=24, weight=ft.FontWeight.BOLD),
                    phone,
                    otp,
                    send_otp_btn,
                    verify_btn
                ], alignment=ft.MainAxisAlignment.CENTER)
            ]
        )
    
    def main_view():
        jobs_column = ft.Column()
        
        def load_jobs():
            jobs_column.controls.clear()
            for job in db.jobs:
                jobs_column.controls.append(
                    ft.Card(
                        content=ft.ListTile(
                            title=ft.Text(job['title'], weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(job['description']),
                            trailing=ft.Text(f"KES {job['budget']}", weight=ft.FontWeight.BOLD, color=ft.colors.GREEN),
                            on_click=lambda e, j=job: page.snack_bar(ft.SnackBar(ft.Text(f"Selected: {j['title']}")))
                        )
                    )
                )
            page.update()
        
        load_jobs()
        return ft.View(
            "/main",
            controls=[
                ft.AppBar(title=ft.Text("Available Jobs"), bgcolor=ft.colors.BLUE),
                ft.FloatingActionButton(
                    icon=ft.icons.ADD, bgcolor=ft.colors.BLUE, on_click=lambda e: page.snack_bar(ft.SnackBar(ft.Text("Post Job Coming Soon")))
                ),
                jobs_column
            ]
        )

    def route_change(e):
        if page.route == "/login":
            page.views.append(login_view())
        elif page.route == "/main":
            page.views.append(main_view())
        page.update()

    page.on_route_change = route_change
    page.go("/login")

ft.app(target=main)

