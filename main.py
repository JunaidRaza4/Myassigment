import os
import uuid
from dotenv import load_dotenv
from fastapi import Cookie, FastAPI, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from supabase import Client, create_client

# .env file se secret variables load karte hain
load_dotenv()

app = FastAPI()

# Supabase Credentials (Yahan apni asli URL aur Key dalein)
SUPABASE_URL = "https://sfntkguliztwusabiqub.supabase.co"
SUPABASE_KEY = "sb_publishable_LTbQz8j4BUVec4hONHqL4w_y9shwmU6"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Password .env file se uthega (agar .env na ho toh default 'admin123' rahega)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


# ==========================================
# HELPER: Database se School Name uthane ke liye
# ==========================================
def get_school_name():
  try:
    res = supabase.table("schools").select("school_name").limit(1).execute()
    if res.data:
      return res.data[0]["school_name"]
  except Exception:
    pass
  return "Model High School"  # Fallback naam agar database connection na ho


# ==========================================
# 1. LOGIN PAGE (GET /login)
# ==========================================
@app.get("/login", response_class=HTMLResponse)
def login_page():
  school_name = get_school_name()
  return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Admin Login - School Portal</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen flex items-center justify-center p-4">
        <div class="w-full max-w-md bg-white rounded-3xl shadow-2xl p-8 border border-gray-100">
            <div class="text-center mb-6">
                <h1 class="text-2xl font-bold text-blue-600">Admin Login</h1>
                <p class="text-gray-400 text-sm mt-1">{school_name}</p>
            </div>
            
            <form action="/login" method="POST" class="space-y-4">
                <div>
                    <label class="block text-gray-600 text-sm font-medium mb-1">Password</label>
                    <input type="password" name="password" placeholder="Enter admin password" required class="w-full p-3 border rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <button type="submit" class="w-full bg-blue-600 text-white font-bold p-3 rounded-xl hover:bg-blue-700 transition">Login</button>
            </form>
        </div>
    </body>
    </html>
    """


# ==========================================
# 2. LOGIN CHECK LOGIC (POST /login)
# ==========================================
@app.post("/login")
def login_post(response: Response, password: str = Form(...)):
  if password == ADMIN_PASSWORD:
    res = RedirectResponse(url="/admin", status_code=303)
    res.set_cookie(key="is_admin", value="true")
    return res
  else:
    return HTMLResponse(
        content="""
        <script>
            alert('Galat Password! Dobara koshish karein.');
            window.location.href = '/login';
        </script>
        """,
        status_code=400,
    )


# ==========================================
# 3. ADMIN LOGOUT (GET /logout)
# ==========================================
@app.get("/logout")
def logout():
  res = RedirectResponse(url="/login", status_code=303)
  res.delete_cookie(key="is_admin")
  return res


# ==========================================
# 4. SECURE ADMIN PANEL (GET /admin)
# ==========================================
@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(is_admin: str = Cookie(None)):
  if is_admin != "true":
    return RedirectResponse(url="/login", status_code=303)

  school_name = get_school_name()

  try:
    response = (
        supabase.table("student_parent_map")
        .select(
            "parent_id, students(id, full_name, class_name, roll_number,"
            " attendance_percentage, fee_status), parents(full_name,"
            " phone_number)"
        )
        .execute()
    )
    records = response.data
  except Exception:
    records = []

  students_rows = ""
  for item in records:
    st = item.get("students")
    pr = item.get("parents")
    if st and pr:
      portal_link = (
          f"http://127.0.0.1:8000/api/student-portal/{item['parent_id']}"
      )
      wa_message = f"Assalam-o-Alaikum {pr['full_name']}, aapke bachhe {st['full_name']} ka report card check karne ke liye is secure link par click karein: {portal_link}"
      wa_link = f"https://wa.me/{pr['phone_number']}?text={wa_message}"

      fee_badge = (
          '<span style="background: #d1fae5; color: #065f46; padding: 2px 8px;'
          ' border-radius: 4px; font-weight: bold;">Paid</span>'
          if st["fee_status"] == "Paid"
          else '<span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 4px; font-weight: bold;">Pending</span>'
      )

      students_rows += f"""
            <tr style="border-bottom: 1px solid #e5e7eb;">
                <td style="padding: 12px; font-weight: bold;">{st['full_name']}</td>
                <td style="padding: 12px;">{st['class_name']} (Roll: {st['roll_number']})</td>
                <td style="padding: 12px;">{pr['full_name']} ({pr['phone_number']})</td>
                <td style="padding: 12px;">{st['attendance_percentage']}%</td>
                <td style="padding: 12px;">{fee_badge}</td>
                <td style="padding: 12px;">
                    <a href="{wa_link}" target="_blank" style="background: #25d366; color: white; padding: 6px 12px; border-radius: 6px; text-decoration: none; font-size: 14px; font-weight: bold;">📲 Send WhatsApp</a>
                </td>
            </tr>
            """

  html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>School Admin Panel</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 min-h-screen p-6">
        <div class="max-w-6xl mx-auto space-y-6">
            
            <div class="bg-white p-6 rounded-2xl shadow-md flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-bold text-blue-600">School Admin Dashboard</h1>
                    <p class="text-gray-500 text-sm">{school_name} - Student & Parent Management</p>
                </div>
                <a href="/logout" class="bg-red-500 text-white font-bold px-4 py-2 rounded-xl hover:bg-red-600 transition text-sm">🔒 Logout</a>
            </div>

            <div class="bg-white p-6 rounded-2xl shadow-md">
                <h2 class="text-lg font-bold text-gray-800 mb-4">➕ Add New Student & Parent</h2>
                <form action="/admin/add-student" method="POST" class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <input type="text" name="student_name" placeholder="Student Full Name" required class="p-3 border rounded-xl">
                    <input type="text" name="class_name" placeholder="Class (e.g. Class 8)" required class="p-3 border rounded-xl">
                    <input type="text" name="roll_number" placeholder="Roll Number (e.g. 803)" required class="p-3 border rounded-xl">
                    <input type="number" name="attendance" placeholder="Attendance % (e.g. 90)" required class="p-3 border rounded-xl">
                    <select name="fee_status" class="p-3 border rounded-xl">
                        <option value="Paid">Fee Paid</option>
                        <option value="Pending">Fee Pending</option>
                    </select>
                    <input type="text" name="parent_name" placeholder="Parent Name" required class="p-3 border rounded-xl">
                    <input type="text" name="parent_phone" placeholder="Parent Phone (+923001234567)" required class="p-3 border rounded-xl md:col-span-2">
                    
                    <button type="submit" class="bg-blue-600 text-white font-bold p-3 rounded-xl hover:bg-blue-700 transition md:col-span-3">Save Student & Generate Portal</button>
                </form>
            </div>

            <div class="bg-white p-6 rounded-2xl shadow-md overflow-x-auto">
                <h2 class="text-lg font-bold text-gray-800 mb-4">📋 Registered Students & Parent Portals</h2>
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr style="background: #f9fafb; border-bottom: 2px solid #e5e7eb;">
                            <th style="padding: 12px;">Student Name</th>
                            <th style="padding: 12px;">Class & Roll</th>
                            <th style="padding: 12px;">Parent Details</th>
                            <th style="padding: 12px;">Attendance</th>
                            <th style="padding: 12px;">Fee Status</th>
                            <th style="padding: 12px;">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {students_rows if students_rows else '<tr><td colspan="6" style="text-align: center; padding: 20px; color: gray;">Koi student nahi mila. Upar form se add karein!</td></tr>'}
                    </tbody>
                </table>
            </div>

        </div>
    </body>
    </html>
    """
  return html_content


# ==========================================
# 5. ADD STUDENT LOGIC (POST /admin/add-student)
# ==========================================
@app.post("/admin/add-student")
def add_student(
    is_admin: str = Cookie(None),
    student_name: str = Form(...),
    class_name: str = Form(...),
    roll_number: str = Form(...),
    attendance: int = Form(...),
    fee_status: str = Form(...),
    parent_name: str = Form(...),
    parent_phone: str = Form(...),
):
  if is_admin != "true":
    return RedirectResponse(url="/login", status_code=303)

  try:
    school_id = "11111111-1111-1111-1111-111111111111"
    student_id = str(uuid.uuid4())
    parent_id = str(uuid.uuid4())

    supabase.table("parents").insert(
        {"id": parent_id, "full_name": parent_name, "phone_number": parent_phone}
    ).execute()

    supabase.table("students").insert({
        "id": student_id,
        "school_id": school_id,
        "full_name": student_name,
        "class_name": class_name,
        "roll_number": roll_number,
        "attendance_percentage": attendance,
        "fee_status": fee_status,
    }).execute()

    supabase.table("student_parent_map").insert(
        {"parent_id": parent_id, "student_id": student_id}
    ).execute()

    return RedirectResponse(url="/admin", status_code=303)
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 6. PARENT PORTAL PAGE (GET /api/student-portal/{parent_id})
# ==========================================
@app.get("/api/student-portal/{parent_id}", response_class=HTMLResponse)
def get_student_portal(parent_id: str):
  school_name = get_school_name()
  try:
    map_response = (
        supabase.table("student_parent_map")
        .select("student_id")
        .eq("parent_id", parent_id)
        .execute()
    )

    if not map_response.data:
      return "<h3>Access Denied: Invalid Link</h3>"

    student_id = map_response.data[0]["student_id"]

    student_response = (
        supabase.table("students")
        .select(
            "full_name, class_name, roll_number, attendance_percentage,"
            " fee_status"
        )
        .eq("id", student_id)
        .execute()
    )

    if not student_response.data:
      raise HTTPException(status_code=404, detail="Student not found")

    student = student_response.data[0]
    fee_bg = (
        "background-color: #d1fae5; color: #065f46;"
        if student["fee_status"] == "Paid"
        else "background-color: #fee2e2; color: #991b1b;"
    )

    return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Student Portal</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-blue-50 min-h-screen flex items-center justify-center p-4">
            <div class="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden border">
                <div class="bg-blue-600 p-6 text-white text-center">
                    <h1 class="text-2xl font-bold">{school_name}</h1>
                    <p class="text-blue-100 text-sm mt-1">Student Progress Portal</p>
                </div>
                <div class="p-6 space-y-4">
                    <div class="bg-gray-50 p-4 rounded-2xl flex justify-between">
                        <span class="text-gray-500 font-medium">Student Name</span>
                        <span class="text-gray-900 font-bold text-lg">{student['full_name']}</span>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-2xl flex justify-between">
                        <span class="text-gray-500 font-medium">Class & Roll</span>
                        <span class="text-gray-900 font-bold">{student['class_name']} (Roll: {student['roll_number']})</span>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-2xl flex justify-between">
                        <span class="text-gray-500 font-medium">Attendance</span>
                        <span class="text-green-600 font-bold text-lg">{student['attendance_percentage']}%</span>
                    </div>
                    <div class="bg-gray-50 p-4 rounded-2xl flex justify-between">
                        <span class="text-gray-500 font-medium">Fee Status</span>
                        <span style="{fee_bg}" class="px-3 py-1 rounded-full text-xs font-bold uppercase">{student['fee_status']}</span>
                    </div>
                </div>
                <div class="bg-gray-50 px-6 py-4 text-center text-xs text-gray-400">
                    Secure Student-Parent Portal
                </div>
            </div>
        </body>
        </html>
        """
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))