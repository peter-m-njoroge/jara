import flet as ft
import json

class AdminDatabase:
    def __init__(self):
        with open('data.json', 'r') as f:
            self.data = json.load(f)
    
    @property
    def users(self):
        return self.data.get('users', [])
    
    @property
    def transactions(self):
        return self.data.get('transactions', [])
    
    @property
    def reviews(self):
        return self.data.get('reviews', [])

def main(page: ft.Page):
    page.title = "Admin Dashboard"
    db = AdminDatabase()
    
    # ========== DATA TABLES ==========
    users_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Phone")),
            ft.DataColumn(ft.Text("Role")),
            ft.DataColumn(ft.Text("Rating")),
        ],
        rows=[ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(u['phone'])),
                ft.DataCell(ft.Text("Tasker" if u['is_tasker'] else "Client")),
                ft.DataCell(ft.Text(str(u.get('rating', 0)))),
            ]
        ) for u in db.users]
    )
    
    transactions_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Amount")),
            ft.DataColumn(ft.Text("Purpose")),
            ft.DataColumn(ft.Text("Date")),
        ],
        rows=[ft.DataRow(
            cells=[
                ft.DataCell(ft.Text(str(t['amount']))),
                ft.DataCell(ft.Text(t['purpose'])),
                ft.DataCell(ft.Text(t['timestamp'][:10])),
            ]
        ) for t in db.transactions]
    )
    
    # ========== LAYOUT ==========
    page.add(
        ft.Tabs(
            tabs=[
                ft.Tab(
                    text="Users",
                    content=ft.Column([ft.Text("Registered Users"), users_table])
                ),
                ft.Tab(
                    text="Transactions",
                    content=ft.Column([ft.Text("Payment History"), transactions_table])
                )
            ]
        )
    )

ft.app(target=main, view=ft.WEB_BROWSER)
