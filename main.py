import flet as ft
import uuid
import json
import base64
import requests
from datetime import datetime
from flet import colors, icons

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
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=ft.colors.BLUE_800,
            secondary=ft.colors.AMBER_600,
            surface=ft.colors.GREY_100,
        ),
        text_theme=ft.TextTheme(
            body_medium=ft.TextStyle(
                color=ft.colors.GREY_800,
                font_family="Poppins"
            )
        ),
    )
    page.fonts = {
        "Poppins": "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap"
    }
    page.bgcolor = ft.colors.GREY_50
    page.padding = 0
    
    current_user = None
    selected_job = None

    # ========== UI COMPONENTS ==========
    def create_app_bar(title):
        return ft.AppBar(
            title=ft.Text(title, style=ft.TextStyle(font_family="Poppins")),
            bgcolor=ft.colors.BLUE_800,
            color=ft.colors.WHITE,
            center_title=True,
            elevation=4
        )

    def create_loading_indicator():
        return ft.Container(
            content=ft.ProgressRing(),
            alignment=ft.alignment.center,
            bgcolor=ft.colors.BLACK54,
            expand=True
        )

    # ========== AUTHENTICATION ==========
    def show_login():
        phone = ft.TextField(
            label="Safaricom Number",
            prefix_text="+254",
            border_radius=12,
            border_color=ft.colors.BLUE_200,
            focused_border_color=ft.colors.BLUE_800,
            width=300
        )
        
        otp = ft.TextField(
            label="OTP Code",
            visible=False,
            border_radius=12,
            password=True
        )
        
        send_otp_btn = ft.FilledButton(
            "Send OTP",
            icon=icons.SEND,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.BLUE_800,
                padding=20,
                shape=ft.RoundedRectangleBorder(radius=12)
            ),
            on_click=lambda e: send_otp(phone.value)
        )
        
        verify_btn = ft.FilledButton(
            "Verify",
            icon=icons.CHECK,
            visible=False,
            style=ft.ButtonStyle(
                bgcolor=ft.colors.AMBER_600,
                padding=20,
                shape=ft.RoundedRectangleBorder(radius=12)
            ),
            on_click=lambda e: verify_otp(phone.value, otp.value)
        )

        def send_otp(number):
            if len(number) != 9 or not number.startswith('7'):
                page.snack_bar = ft.SnackBar(
                    ft.Text("Invalid Safaricom number!"),
                    bgcolor=ft.colors.RED_400
                )
                page.snack_bar.open = True
                page.update()
                return
            
            otp.value = "1234"  # Mock OTP
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
            [
                ft.Stack([
                    ft.Container(gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=[ft.colors.BLUE_800, ft.colors.BLUE_600]
                    ), expand=True),
                    
                    ft.Column([
                        ft.Icon(icons.WORK_OUTLINE, size=80, color=ft.colors.WHITE),
                        ft.Text("Welcome to\nTaskerApp", 
                              size=32, 
                              text_align=ft.TextAlign.CENTER,
                              color=ft.colors.WHITE,
                              weight=ft.FontWeight.BOLD),
                        ft.Container(height=40),
                        ft.Card(
                            content=ft.Column([
                                phone,
                                otp,
                                send_otp_btn,
                                verify_btn
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                            elevation=8,
                            width=400,
                            padding=20
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER)
                ])
            ]
        )

    # ========== MAIN DASHBOARD ==========
    def main_dashboard():
        jobs_column = ft.Column(spacing=15, scroll=ft.ScrollMode.ALWAYS)
        loading = create_loading_indicator()
        
        def load_jobs():
            jobs_column.controls.clear()
            for job in db.jobs:
                jobs_column.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.ListTile(
                                    title=ft.Text(job['title'], weight=ft.FontWeight.BOLD),
                                    subtitle=ft.Text(job['description'], max_lines=2),
                                    trailing=ft.Column([
                                        ft.Text(f"KES {job['budget']}", 
                                               weight=ft.FontWeight.BOLD,
                                               color=ft.colors.GREEN_800),
                                        ft.Text(job.get('location', 'Nairobi')),
                                        ft.Text("Posted 2h ago", size=12)
                                    ])
                                ),
                                ft.Divider(height=1),
                                ft.Row([
                                    ft.FilledButton("View Details"),
                                    ft.Icon(icons.STAR, color=ft.colors.AMBER_600),
                                    ft.Text("4.8", size=14)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                            ]),
                            padding=15
                        ),
                        elevation=3,
                        shadow_color=ft.colors.GREY_300
                    )
                )
            loading.visible = False
            page.update()

        page.views.append(
            ft.View(
                "/main",
                [
                    create_app_bar("Available Jobs"),
                    ft.Container(
                        content=ft.Stack([loading, jobs_column]),
                        padding=20,
                        expand=True
                    ),
                    ft.FloatingActionButton(
                        icon=icons.ADD,
                        bgcolor=ft.colors.AMBER_600,
                        on_click=lambda e: page.go("/post-job")
                    )
                ]
            )
        )
        load_jobs()

    # ========== JOB POSTING ==========
    def post_job_view():
        title = ft.TextField(label="Job Title")
        description = ft.TextField(label="Description", multiline=True)
        budget = ft.TextField(label="Budget (KES)", prefix_text="KES ")
        location = ft.TextField(label="Location")
        
        def submit_job(e):
            db.jobs.append({
                "id": str(uuid.uuid4()),
                "title": title.value,
                "description": description.value,
                "budget": budget.value,
                "location": location.value,
                "client": current_user['phone'],
                "timestamp": datetime.now().isoformat()
            })
            db.save_data()
            page.go("/main")
        
        return ft.View(
            "/post-job",
            [
                create_app_bar("Post New Job"),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Create New Job", size=24),
                        title,
                        description,
                        budget,
                        location,
                        ft.FilledButton(
                            "Post Job",
                            icon=icons.UPLOAD_FILE,
                            style=ft.ButtonStyle(padding=20),
                            on_click=submit_job
                        )
                    ], spacing=20),
                    padding=30,
                    expand=True
                )
            ]
        )

    # ========== ROUTING ==========
    def route_change(e):
        page.views.clear()
        if page.route == "/login":
            page.views.append(show_login())
        elif page.route == "/main":
            main_dashboard()
        elif page.route == "/post-job":
            page.views.append(post_job_view())
        page.update()

    page.on_route_change = route_change
    page.go("/login")

ft.app(target=main, view=ft.WEB_BROWSER, port=8500)
