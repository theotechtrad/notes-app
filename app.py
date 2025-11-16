from flask import Flask, request, jsonify, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import jwt
import datetime
from functools import wraps
import random
import os


app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'my-super-secret-key-12345'
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DB")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create uploads folder
if not os.path.exists('uploads'):
    os.makedirs('uploads')

db = SQLAlchemy(app)

# In-memory OTP storage
otp_storage = {}

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    notes = db.relationship('Note', backref='user', lazy=True, cascade='all, delete-orphan')

# Note Model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    color = db.Column(db.String(20), default='#ffffff')
    image_data = db.Column(db.Text)  # Store base64 encoded image
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.create_all()

# Token required decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except:
            return jsonify({'message': 'Invalid token!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASS")
EMAIL_FROM = os.getenv("EMAIL_FROM")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME")


def send_otp_email(email, otp):
    subject = "Your OTP Code"

    html = f"""
    <h2>Your OTP Code</h2>
    <p>Your OTP is:</p>
    <h1 style="letter-spacing:5px;">{otp}</h1>
    <p>This OTP is valid for 5 minutes.</p>
    """

    msg = MIMEText(html, "html")
    msg["Subject"] = subject
    msg["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>"
    msg["To"] = email

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(EMAIL_FROM, email, msg.as_string())
        server.quit()
        print("OTP email sent!")
    except Exception as e:
        print("Email error:", e)


# Homepage
@app.route('/')
def home():
    return render_template_string('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notes App - Google Keep Style</title>
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Roboto, Arial, sans-serif;
            background: #fff;
        }
        
        /* Auth Styles */
        .auth-page {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .auth-container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 450px;
        }
        
        .auth-container h2 {
            color: #667eea;
            margin-bottom: 30px;
            text-align: center;
        }
        
        .tabs {
            display: flex;
            margin-bottom: 30px;
            border-bottom: 2px solid #eee;
        }
        
        .tab {
            flex: 1;
            padding: 12px;
            text-align: center;
            cursor: pointer;
            color: #999;
            font-weight: 600;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .form { display: none; }
        .form.active { display: block; }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
        }
        
        .input-group input {
            width: 100%;
            padding: 14px;
            border: 2px solid #eee;
            border-radius: 10px;
            font-size: 15px;
            background: #f8f9fa;
        }
        
        .input-group input:focus {
            outline: none;
            border-color: #667eea;
            background: white;
        }
        
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .message {
            margin-top: 15px;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            display: none;
        }
        
        .message.success { background: #d4edda; color: #155724; }
        .message.error { background: #f8d7da; color: #721c24; }
        
        .otp-section { display: none; }
        .otp-section.active { display: block; }
        
        /* Dashboard Styles */
        .dashboard {
            display: none;
            min-height: 100vh;
            background: #f5f5f5;
            transition: background 0.3s;
        }
        
        .dashboard.active { display: block; }
        
        .header {
            background: #fff;
            padding: 15px 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 {
            color: #667eea;
            font-size: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .header-right {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .user-email {
            color: #666;
            font-size: 14px;
        }
        
        .logout-btn {
            padding: 8px 16px;
            background: #dc3545;
            width: auto;
            font-size: 14px;
        }
        
        .main-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
        }
        
        .note-input-section {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .note-input-section input,
        .note-input-section textarea {
            width: 100%;
            border: none;
            padding: 10px;
            font-size: 15px;
            font-family: inherit;
            resize: none;
        }
        
        .note-input-section input {
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .note-input-section input:focus,
        .note-input-section textarea:focus {
            outline: none;
        }
        
        .note-actions {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }
        
        .color-picker {
            display: flex;
            gap: 10px;
        }
        
        .color-btn {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            border: 2px solid #ddd;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .color-btn:hover {
            transform: scale(1.1);
        }
        
        .image-upload-btn {
            display: flex;
            align-items: center;
            gap: 5px;
            padding: 8px 15px;
            background: #f0f0f0;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            width: auto;
        }
        
        .image-upload-btn:hover {
            background: #e0e0e0;
        }
        
        .add-note-btn {
            padding: 8px 20px;
            width: auto;
        }
        
        .search-box {
            background: white;
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .search-box input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 15px;
        }
        
        .notes-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 20px;
        }
        
        .note-card {
    background: white;
    border-radius: 10px;
    padding: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    transition: all 0.2s;
    cursor: pointer;
    position: relative;
    height: 280px; /* Fixed height */
    display: flex;
    flex-direction: column;
    overflow: hidden; /* Hide overflow content */
}

.note-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.note-card.pinned {
    border: 2px solid #667eea;
}

.note-card.black-note h4,
.note-card.black-note p {
    color: white !important;
}

.note-card h4 {
    margin-bottom: 8px;
    color: #333;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap; /* Single line title */
}

.note-card p {
    color: #666;
    line-height: 1.5;
    word-wrap: break-word;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 6; /* Show max 6 lines */
    -webkit-box-orient: vertical;
    flex: 1; /* Take available space */
}

.note-actions-bar {
    display: none;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid rgba(0,0,0,0.1);
}

.note-card:hover .note-actions-bar {
    display: flex;
}
        
        .note-icon-btn {
            background: none;
            border: none;
            cursor: pointer;
            padding: 5px;
            border-radius: 50%;
            width: auto;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .note-icon-btn:hover {
            background: rgba(0,0,0,0.1);
        }
        
        .pin-icon {
            position: absolute;
            top: 10px;
            right: 10px;
            color: #999;
            cursor: pointer;
        }
        
        .pin-icon.pinned {
            color: #667eea;
        }
        
        .note-image {
            width: 100%;
            border-radius: 5px;
            margin-bottom: 10px;
            max-height: 200px;
            object-fit: cover;
        }
        
        .note-card h4 {
            margin-bottom: 8px;
            color: #333;
        }
        
        .note-card p {
            color: #666;
            line-height: 1.5;
            word-wrap: break-word;
        }
        
        .note-card-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
        }
        
        .note-date {
            font-size: 11px;
            color: #999;
        }
        
        .delete-icon {
            color: #dc3545;
            cursor: pointer;
            font-size: 20px;
        }
        
        .no-notes {
            text-align: center;
            color: #999;
            padding: 60px 20px;
            font-size: 16px;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .image-preview {
            max-width: 100%;
            max-height: 150px;
            border-radius: 5px;
            margin: 10px 0;
        }
        
         /* Responsive Design for Mobile & Tablet */                 
                                  
        @media screen and (max-width: 768px) {
            .auth-container {
                padding: 30px 20px;
                max-width: 100%;
                margin: 10px;
            }
            
            .header {
                padding: 10px 15px;
                flex-wrap: wrap;
            }
            
            .header h1 {
                font-size: 18px;
            }
            
            .header-right {
                gap: 10px;
            }
            
            .user-email {
                display: none;
            }
            
            .logout-btn {
                padding: 6px 12px;
                font-size: 12px;
            }
            
            .main-content {
                padding: 15px 10px;
            }
            
            .note-input-section {
                padding: 15px;
            }
            
            .note-actions {
                flex-direction: column;
                gap: 10px;
                align-items: stretch;
            }
            
            .color-picker {
                overflow-x: auto;
                padding-bottom: 5px;
                justify-content: flex-start;
            }
            
            .image-upload-btn, .add-note-btn {
                width: 100%;
                justify-content: center;
            }
            
            .notes-grid {
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                gap: 15px;
            }
            
            .note-card {
                height: 250px;
            }
        }

        @media screen and (max-width: 480px) {
            .notes-grid {
                grid-template-columns: 1fr;
            }
            
            .note-card {
                height: 220px;
            }
            
            .color-picker {
                flex-wrap: wrap;
            }
            
            .tabs {
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
    <!-- Auth Page -->
    <div id="authPage" class="auth-page">
        <div class="auth-container">
            <div id="authSection">
                <h2>🔐 Notes App</h2>
                <div class="tabs">
                    <div class="tab active" onclick="showTab('login')">Login</div>
                    <div class="tab" onclick="showTab('register')">Register</div>
                </div>
                
                <div id="loginForm" class="form active">
                    <div class="input-group">
                        <label>Email</label>
                        <input type="email" id="loginEmail" placeholder="your@email.com">
                    </div>
                    <div class="input-group">
                        <label>Password</label>
                        <input type="password" id="loginPassword" placeholder="••••••••">
                    </div>
                    <button onclick="login()">Login</button>
                    <div id="loginMessage" class="message"></div>
                </div>
                
                <div id="registerForm" class="form">
                    <div class="input-group">
                        <label>Email</label>
                        <input type="email" id="registerEmail" placeholder="your@email.com">
                    </div>
                    <div class="input-group">
                        <label>Password</label>
                        <input type="password" id="registerPassword" placeholder="••••••••">
                    </div>
                    <button onclick="register()">Register</button>
                    <div id="registerMessage" class="message"></div>
                </div>
            </div>
            
            <div id="otpSection" class="otp-section">
                <h2>📧 Verify Email</h2>
                <p style="margin-bottom: 20px; color: #666;">Enter the OTP sent to your email</p>
                <div class="input-group">
                    <input type="text" id="otpInput" placeholder="Enter 6-digit OTP" maxlength="6">
                </div>
                <button onclick="verifyOTP()">Verify</button>
                <div id="otpMessage" class="message"></div>
            </div>
        </div>
    </div>

    <!-- Dashboard -->
    <div id="dashboard" class="dashboard">
        <div class="header">
            <h1><span class="material-icons">note</span> My Notes</h1>
            <div class="header-right">
                <span class="user-email" id="userEmail"></span>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>
        </div>
        
        <div class="main-content">
            <!-- Note Input -->
            <div class="note-input-section">
                <input type="text" id="noteTitle" placeholder="Title">
                <textarea id="noteContent" placeholder="Take a note..." rows="3"></textarea>
                <img id="imagePreview" class="image-preview" style="display:none;">
                <div class="note-actions">
                    <div class="color-picker">
                        <div class="color-btn" style="background:#ffffff; border: 2px solid #000;" onclick="selectColor('#ffffff')"></div>
                        <div class="color-btn" style="background:#000000;" onclick="selectColor('#000000')"></div>
                        <div class="color-btn" style="background:#f28b82;" onclick="selectColor('#f28b82')"></div>
                        <div class="color-btn" style="background:#fbbc04;" onclick="selectColor('#fbbc04')"></div>
                        <div class="color-btn" style="background:#fff475;" onclick="selectColor('#fff475')"></div>
                        <div class="color-btn" style="background:#ccff90;" onclick="selectColor('#ccff90')"></div>
                        <div class="color-btn" style="background:#a7ffeb;" onclick="selectColor('#a7ffeb')"></div>
                        <div class="color-btn" style="background:#cbf0f8;" onclick="selectColor('#cbf0f8')"></div>
                        <div class="color-btn" style="background:#aecbfa;" onclick="selectColor('#aecbfa')"></div>
                        <div class="color-btn" style="background:#d7aefb;" onclick="selectColor('#d7aefb')"></div>
                        <div class="color-btn" style="background:#fdcfe8;" onclick="selectColor('#fdcfe8')"></div>
                    </div>
                    <label class="image-upload-btn">
                        <span class="material-icons">image</span> Add Image
                        <input type="file" id="imageInput" accept="image/*" onchange="previewImage()">
                    </label>
                    <button class="add-note-btn" onclick="createNote()">Add Note</button>
                </div>
                <div id="noteMessage" class="message"></div>
            </div>
            
            <!-- Search -->
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="🔍 Search notes..." oninput="searchNotes()">
            </div>
            
            <!-- Notes Grid -->
            <div class="notes-grid" id="notesGrid">
                <p class="no-notes">Loading notes...</p>
            </div>
        </div>
    </div>

    <script>
        let currentToken = null;
        let pendingEmail = null;
        let selectedColor = '#ffffff';
        let selectedImage = null;
        let editingNoteId = null;
        
        function showTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.form').forEach(f => f.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tab + 'Form').classList.add('active');
        }
        
        function showMessage(elementId, message, type) {
            const el = document.getElementById(elementId);
            el.textContent = message;
            el.className = 'message ' + type;
            el.style.display = 'block';
        }
        
        async function register() {
            const email = document.getElementById('registerEmail').value.trim();
            const password = document.getElementById('registerPassword').value;
            
            if (!email || !password) {
                showMessage('registerMessage', 'Please fill all fields!', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await response.json();
                
                if (response.ok) {
                    showMessage('registerMessage', '✅ OTP sent to your email!', 'success');
                    pendingEmail = email;
                    setTimeout(() => {
                        document.getElementById('authSection').style.display = 'none';
                        document.getElementById('otpSection').classList.add('active');
                    }, 1500);
                } else {
                    showMessage('registerMessage', '❌ ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('registerMessage', '❌ Network error!', 'error');
            }
        }
        
        async function verifyOTP() {
            const otp = document.getElementById('otpInput').value.trim();
            
            if (otp.length !== 6) {
                showMessage('otpMessage', 'Please enter 6-digit OTP!', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/verify-otp', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: pendingEmail, otp })
                });
                const data = await response.json();
                
                if (response.ok) {
                    showMessage('otpMessage', '✅ Verified! Please login.', 'success');
                    setTimeout(() => {
                        document.getElementById('otpSection').classList.remove('active');
                        document.getElementById('authSection').style.display = 'block';
                        showTab('login');
                    }, 1500);
                } else {
                    showMessage('otpMessage', '❌ ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('otpMessage', '❌ Network error!', 'error');
            }
        }
        
        async function login() {
            const email = document.getElementById('loginEmail').value.trim();
            const password = document.getElementById('loginPassword').value;
            
            if (!email || !password) {
                showMessage('loginMessage', 'Please fill all fields!', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password })
                });
                const data = await response.json();
                
                if (response.ok) {
                    currentToken = data.token;
                    document.getElementById('authPage').style.display = 'none';
                    document.getElementById('dashboard').classList.add('active');
                    document.getElementById('userEmail').textContent = data.user.email;
                    loadNotes();
                } else {
                    showMessage('loginMessage', '❌ ' + data.message, 'error');
                }
            } catch (error) {
                showMessage('loginMessage', '❌ Network error!', 'error');
            }
        }
        
        function selectColor(color) {
            selectedColor = color;
            // Change dashboard background
            const dashboard = document.getElementById('dashboard');
            if (color === '#000000') {
                dashboard.style.background = '#1a1a1a';
            } else if (color === '#ffffff') {
                dashboard.style.background = '#f5f5f5';
            } else {
                dashboard.style.background = color + '40'; // Add transparency
            }
        }
        
        function previewImage() {
            const file = document.getElementById('imageInput').files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    selectedImage = e.target.result;
                    document.getElementById('imagePreview').src = e.target.result;
                    document.getElementById('imagePreview').style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        }
        
        async function createNote() {
            const title = document.getElementById('noteTitle').value.trim();
            const content = document.getElementById('noteContent').value.trim();
            
            if (!title && !content && !selectedImage) {
                showMessage('noteMessage', 'Please add title, content, or image!', 'error');
                return;
            }
            
            try {
                const url = editingNoteId ? `/api/notes/${editingNoteId}` : '/api/notes';
                const method = editingNoteId ? 'PUT' : 'POST';
                
                const response = await fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + currentToken
                    },
                    body: JSON.stringify({
                        title: title,
                        content: content,
                        color: selectedColor,
                        image_data: selectedImage
                    })
                });
                
                if (response.ok) {
                    document.getElementById('noteTitle').value = '';
                    document.getElementById('noteContent').value = '';
                    document.getElementById('imageInput').value = '';
                    document.getElementById('imagePreview').style.display = 'none';
                    selectedImage = null;
                    selectedColor = '#ffffff';
                    editingNoteId = null;
                    document.querySelector('.add-note-btn').textContent = 'Add Note';
                    document.getElementById('dashboard').style.background = '#f5f5f5';
                    loadNotes();
                }
            } catch (error) {
                showMessage('noteMessage', '❌ Error saving note!', 'error');
            }
        }
        
        async function loadNotes() {
            try {
                const response = await fetch('/api/notes', {
                    headers: { 'Authorization': 'Bearer ' + currentToken }
                });
                const data = await response.json();
                
                displayNotes(data.notes);
            } catch (error) {
                document.getElementById('notesGrid').innerHTML = '<p class="no-notes">Error loading notes</p>';
            }
        }
        
        function displayNotes(notes) {
            const grid = document.getElementById('notesGrid');
            
            if (notes.length === 0) {
                grid.innerHTML = '<p class="no-notes">No notes yet. Create your first note! 📝</p>';
                return;
            }
            
            const pinned = notes.filter(n => n.is_pinned);
            const unpinned = notes.filter(n => !n.is_pinned);
            const sorted = [...pinned, ...unpinned];
            
            grid.innerHTML = sorted.map(note => {
                const isBlack = note.color === '#000000';
                const textColor = isBlack ? 'color: white;' : '';
                return `
                <div class="note-card ${note.is_pinned ? 'pinned' : ''} ${isBlack ? 'black-note' : ''}" 
                     style="background-color: ${note.color}" 
                     onclick="editNote(${note.id})">
                    <span class="material-icons pin-icon ${note.is_pinned ? 'pinned' : ''}" 
                          onclick="event.stopPropagation(); togglePin(${note.id})"
                          style="${textColor}">
                        ${note.is_pinned ? 'push_pin' : 'push_pin'}
                    </span>
                    ${note.image_data ? `<img src="${note.image_data}" class="note-image">` : ''}
                    ${note.title ? `<h4 style="${textColor}">${note.title}</h4>` : ''}
                    ${note.content ? `<p style="${textColor}">${note.content}</p>` : ''}
                    <div class="note-actions-bar">
                        <button class="note-icon-btn" onclick="event.stopPropagation(); shareNote(${note.id}, '${note.title}', '${note.content}')" title="Share">
                            <span class="material-icons" style="${textColor}">share</span>
                        </button>
                        <button class="note-icon-btn" onclick="event.stopPropagation(); deleteNote(${note.id})" title="Delete">
                            <span class="material-icons" style="color: #dc3545;">delete</span>
                        </button>
                    </div>
                    <div class="note-card-footer">
                        <span class="note-date" style="${textColor}">${new Date(note.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
            `;
            }).join('');
        }
        
        function editNote(noteId) {
            fetch(`/api/notes/${noteId}`, {
                headers: { 'Authorization': 'Bearer ' + currentToken }
            })
            .then(res => res.json())
            .then(data => {
                const note = data.note;
                document.getElementById('noteTitle').value = note.title || '';
                document.getElementById('noteContent').value = note.content || '';
                selectedColor = note.color;
                selectedImage = note.image_data;
                
                if (note.image_data) {
                    document.getElementById('imagePreview').src = note.image_data;
                    document.getElementById('imagePreview').style.display = 'block';
                }
                
                editingNoteId = noteId;
                document.querySelector('.add-note-btn').textContent = 'Update Note';
                
                // Scroll to top
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        }
        
        function shareNote(noteId, title, content) {
            const text = `${title}\n\n${content}`;
            const url = window.location.href;
            
            if (navigator.share) {
                // Mobile share
                navigator.share({
                    title: title || 'My Note',
                    text: text,
                    url: url
                }).catch(err => console.log('Share failed'));
            } else {
                // Desktop - copy to clipboard and show social options
                const shareText = encodeURIComponent(text);
                const shareUrl = encodeURIComponent(url);
                
                const options = `
                    <div style="padding: 20px;">
                        <h3>Share Note</h3>
                        <div style="display: flex; gap: 10px; margin-top: 15px;">
                            <a href="https://twitter.com/intent/tweet?text=${shareText}" target="_blank" 
                               style="padding: 10px 15px; background: #1DA1F2; color: white; text-decoration: none; border-radius: 5px;">
                                Twitter
                            </a>
                            <a href="https://www.facebook.com/sharer/sharer.php?u=${shareUrl}" target="_blank"
                               style="padding: 10px 15px; background: #4267B2; color: white; text-decoration: none; border-radius: 5px;">
                                Facebook
                            </a>
                            <a href="https://wa.me/?text=${shareText}" target="_blank"
                               style="padding: 10px 15px; background: #25D366; color: white; text-decoration: none; border-radius: 5px;">
                                WhatsApp
                            </a>
                            <button onclick="copyToClipboard('${text.replace(/'/g, "\\'")}'); this.parentElement.parentElement.parentElement.remove();"
                                    style="padding: 10px 15px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                                Copy Text
                            </button>
                        </div>
                    </div>
                `;
                
                const popup = document.createElement('div');
                popup.style.cssText = 'position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); z-index: 1000;';
                popup.innerHTML = options;
                document.body.appendChild(popup);
                
                setTimeout(() => popup.remove(), 30000);
            }
        }
        
        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                alert('✅ Note copied to clipboard!');
            });
        }
        
        async function togglePin(noteId) {
            try {
                await fetch(`/api/notes/${noteId}/pin`, {
                    method: 'PUT',
                    headers: { 'Authorization': 'Bearer ' + currentToken }
                });
                loadNotes();
            } catch (error) {
                alert('Error pinning note!');
            }
        }
        
        async function deleteNote(noteId) {
            if (!confirm('Delete this note?')) return;
            
            try {
                await fetch(`/api/notes/${noteId}`, {
                    method: 'DELETE',
                    headers: { 'Authorization': 'Bearer ' + currentToken }
                });
                loadNotes();
            } catch (error) {
                alert('Error deleting note!');
            }
        }
        
        function searchNotes() {
            const query = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.note-card');
            
            cards.forEach(card => {
                const text = card.textContent.toLowerCase();
                card.style.display = text.includes(query) ? 'block' : 'none';
            });
        }
        
        function logout() {
            currentToken = null;
            document.getElementById('dashboard').classList.remove('active');
            document.getElementById('authPage').style.display = 'flex';
            document.getElementById('loginEmail').value = '';
            document.getElementById('loginPassword').value = '';
        }
    </script>
</body>
</html>''')

# API: Register
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Missing fields!'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already exists!'}), 409

    otp = str(random.randint(100000, 999999))
    otp_storage[email] = {
        'otp': otp,
        'password': password,
        'timestamp': datetime.datetime.now()
    }

    send_otp_email(email, otp)
    return jsonify({'message': 'OTP sent to your email!'}), 200

# API: Verify OTP
@app.route('/api/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if email not in otp_storage:
        return jsonify({'message': 'No OTP found. Please register again.'}), 400

    stored = otp_storage[email]
    
    if (datetime.datetime.now() - stored['timestamp']).seconds > 300:
        del otp_storage[email]
        return jsonify({'message': 'OTP expired!'}), 400

    if stored['otp'] != otp:
        return jsonify({'message': 'Invalid OTP!'}), 400

    hashed_password = generate_password_hash(stored['password'])
    new_user = User(email=email, password_hash=hashed_password, is_verified=True)
    db.session.add(new_user)
    db.session.commit()

    del otp_storage[email]
    return jsonify({'message': 'Account verified successfully!'}), 200

# API: Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'message': 'Invalid credentials!'}), 401

    if not user.is_verified:
        return jsonify({'message': 'Please verify your email first!'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'])

    return jsonify({
        'message': 'Login successful!',
        'token': token,
        'user': {'email': user.email, 'id': user.id}
    }), 200

# API: Get all notes
@app.route('/api/notes', methods=['GET'])
@token_required
def get_notes(current_user):
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.is_pinned.desc(), Note.created_at.desc()).all()
    return jsonify({
        'notes': [{
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'color': note.color,
            'image_data': note.image_data,
            'is_pinned': note.is_pinned,
            'created_at': note.created_at.isoformat()
        } for note in notes]
    }), 200

# API: Create note
@app.route('/api/notes', methods=['POST'])
@token_required
def create_note(current_user):
    data = request.get_json()
    
    new_note = Note(
        title=data.get('title', ''),
        content=data.get('content', ''),
        color=data.get('color', '#ffffff'),
        image_data=data.get('image_data'),
        user_id=current_user.id
    )
    db.session.add(new_note)
    db.session.commit()
    
    return jsonify({'message': 'Note created!', 'note_id': new_note.id}), 201

# API: Get single note
@app.route('/api/notes/<int:note_id>', methods=['GET'])
@token_required
def get_single_note(current_user, note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    
    if not note:
        return jsonify({'message': 'Note not found!'}), 404
    
    return jsonify({
        'note': {
            'id': note.id,
            'title': note.title,
            'content': note.content,
            'color': note.color,
            'image_data': note.image_data,
            'is_pinned': note.is_pinned,
            'created_at': note.created_at.isoformat()
        }
    }), 200

# API: Update note
@app.route('/api/notes/<int:note_id>', methods=['PUT'])
@token_required
def update_note(current_user, note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    
    if not note:
        return jsonify({'message': 'Note not found!'}), 404
    
    data = request.get_json()
    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)
    note.color = data.get('color', note.color)
    note.image_data = data.get('image_data', note.image_data)
    
    db.session.commit()
    
    return jsonify({'message': 'Note updated!'}), 200

# API: Delete note
@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@token_required
def delete_note(current_user, note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    
    if not note:
        return jsonify({'message': 'Note not found!'}), 404
    
    db.session.delete(note)
    db.session.commit()
    
    return jsonify({'message': 'Note deleted!'}), 200

# API: Toggle pin
@app.route('/api/notes/<int:note_id>/pin', methods=['PUT'])
@token_required
def toggle_pin(current_user, note_id):
    note = Note.query.filter_by(id=note_id, user_id=current_user.id).first()
    
    if not note:
        return jsonify({'message': 'Note not found!'}), 404
    
    note.is_pinned = not note.is_pinned
    db.session.commit()
    
    return jsonify({'message': 'Pin toggled!', 'is_pinned': note.is_pinned}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)