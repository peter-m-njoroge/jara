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
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    
    current_user = None
    selected_job = None

    # ========== AUTHENTICATION ==========
    def show_auth_dialog():
        phone = ft.TextField(label="Safaricom Number", prefix_text="+254")
        otp = ft.TextField(label="OTP", visible=False)
        send_otp_btn = ft.ElevatedButton("Send OTP", on_click=lambda e: send_otp(phone.value))
        verify_btn = ft.ElevatedButton("Verify", on_click=lambda e: verify_otp(phone.value, otp.value), visible=False)
        
        def send_otp(number):
            if len(number) != 9 or not number.startswith('7'):
                page.snackbar = ft.SnackBar(ft.Text("Invalid Safaricom number!"))
                page.update()
                return
            
            # In production: Send real OTP via SMS
            otp.value = "1234"  # Mock OTP
            otp.visible = True
            verify_btn.visible = True
            page.update()
        
        def verify_otp(number, code):
            nonlocal current_user
            if code == "1234":  # Mock verification
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
                page.go("/role_selection")
            page.update()
        
        page.dialog = ft.AlertDialog(
            title=ft.Text("Phone Verification"),
            content=ft.Column([phone, otp], tight=True),
            actions=[send_otp_btn, verify_btn]
        )
        page.dialog.open = True
        page.update()

    # ========== PAYMENT HANDLING ==========
    def handle_payment(amount, purpose):
        response = MpesaManager.stk_push(
            phone=current_user['phone'],
            amount=amount,
            reference=purpose
        )
        
        if response.get('ResponseCode') == '0':
            db.transactions.append({
                'user_id': current_user['id'],
                'amount': amount,
                'purpose': purpose,
                'timestamp': datetime.now().isoformat()
            })
            db.save_data()
            return True
        return False

    # ========== RATING SYSTEM ==========
    def submit_review(tasker_id, rating, comment):
        db.reviews.append({
            'tasker_id': tasker_id,
            'client_id': current_user['id'],
            'rating': rating,
            'comment': comment,
            'timestamp': datetime.now().isoformat()
        })
        
        # Update tasker rating
        tasker = next(u for u in db.users if u['id'] == tasker_id)
        ratings = [r['rating'] for r in db.reviews if r['tasker_id'] == tasker_id]
        tasker['rating'] = sum(ratings) / len(ratings)
        db.save_data()

    # ========== PAGE VIEWS ==========
    def role_selection_view():
        def select_role(e):
            current_user['is_tasker'] = (e.control.text == "Tasker")
            if current_user['is_tasker'] and not handle_payment(100, "registration"):
                page.snackbar = ft.SnackBar(ft.Text("Registration payment failed!"))
                return
            page.go("/main")
        
        return ft.View(
            "/role_selection",
            [
                ft.Column([
                    ft.Text("Select Your Role"),
                    ft.ElevatedButton("Client", on_click=select_role),
                    ft.ElevatedButton("Tasker (KES 100 fee)", on_click=select_role)
                ], alignment=ft.MainAxisAlignment.CENTER)
            ]
        )
    def login_view():
        phone = ft.TextField(label="Safaricom Number", prefix_text="+254")
        otp = ft.TextField(label="OTP", visible=False)
        send_otp_btn = ft.ElevatedButton("Send OTP", on_click=lambda e: send_otp(phone.value))
        verify_btn = ft.ElevatedButton("Verify", on_click=lambda e: verify_otp(phone.value, otp.value), visible=False)

        def send_otp(number):
            if len(number) != 9 or not number.startswith('7'):
                page.snackbar = ft.SnackBar(ft.Text("Invalid Safaricom number!"))
                page.update()
                return
        otp.value = "1234"  # Mock OTP
        otp.visible = True
        verify_btn.visible = True
        page.update()

        def verify_otp(number, code):
            nonlocal current_user
            if code == "1234":  # Mock verification
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
                page.go("/role_selection")
            page.update()

        return ft.View(
             "/login",
            [
            ft.Column([
                ft.Text("Login"),
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
                    ft.ListTile(
                        title=ft.Text(job['title']),
                        subtitle=ft.Text(job['description']),
                        trailing=ft.Text(f"KES {job['budget']}"),
                        on_click=lambda e, j=job: show_job_details(j)
                    )
                )
            page.update()
        
        def show_job_details(job):
            nonlocal selected_job
            selected_job = job
            
            # Rating UI
            rating = ft.Slider(min=1, max=5, divisions=4, label="Rating")
            review = ft.TextField(label="Your review")
            
            page.dialog = ft.AlertDialog(
                title=ft.Text("Job Completion"),
                content=ft.Column([
                    ft.Text("Rate the tasker:"),
                    rating,
                    review
                ]),
                actions=[
                    ft.TextButton("Submit", on_click=lambda e: submit_review(
                        job['tasker_id'],
                        rating.value,
                        review.value
                    ))
                ]
            )
            page.dialog.open = True
            page.update()
        
        load_jobs()
        return ft.View(
            "/main",
            [
                ft.AppBar(title=ft.Text("Available Jobs")),
                ft.FloatingActionButton(
                    icon=ft.icons.ADD,
                    on_click=lambda e: page.go("/post_job")
                ),
                jobs_column
            ]
        )

    # ========== ROUTING ==========
    def route_change(e):
        if page.route == "/role_selection":
            page.views.append(role_selection_view())
        elif page.route == "/main":
            page.views.append(main_view())
        elif page.route == "/login":
            page.views.append(login_view())  # Create a login view
        page.update()

    page.on_route_change = route_change
    page.go("/login")

ft.app(target=main, view=ft.WEB_BROWSER)
