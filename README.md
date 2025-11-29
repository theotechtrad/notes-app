# Notes App (Google Keep Style) 📝

A secure, full-stack note-taking application with Google Keep-inspired design. Features robust authentication, OTP email verification, and comprehensive note management capabilities.

## Live Demo

🔗 [Notes App](https://kaakkhusundii.pythonanywhere.com/)

## Features

**Core Functionality:**
- Create, read, update, and delete notes
- Add titles and content to notes
- Color-code notes (11 colors including dark theme)
- Pin important notes to stay on top
- Attach images to notes (Base64 storage)
- Search through all notes instantly
- Share notes via social media or clipboard

**Security & Authentication:**
- User registration and login system
- JWT (JSON Web Tokens) for secure sessions
- Password hashing with Werkzeug
- OTP email verification for new accounts
- Token-based API authentication

**User Experience:**
- Google Keep-style interface
- Responsive design (mobile + desktop)
- Real-time note editing
- Smooth animations
- Intuitive drag-and-drop interface


## Tech Stack

**Backend:**
- Flask 3.1.2
- SQLAlchemy with SQLite
- JWT for authentication
- Flask-CORS
- Werkzeug security

**Frontend:**
- Vanilla JavaScript
- HTML5 & CSS3
- Material Icons
- Responsive CSS Grid

**Email:**
- SMTP for OTP delivery
- Python-dotenv for config

**Deployment:**
- Gunicorn server
- PythonAnywhere hosting

## Quick Start

**1. Clone the repo**
```bash
git clone https://github.com/theotechtrad/notes-app.git
cd notes-app
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure environment**

Create `.env` file:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_FROM_NAME=Notes App
```

**4. Run the app**
```bash
python app.py
```

Visit `http://localhost:5000`

## How It Works

### Registration Flow
1. User enters email and password
2. System generates 6-digit OTP
3. OTP sent to user's email
4. User verifies within 5 minutes
5. Account created and verified

### Authentication
- JWT tokens valid for 24 hours
- Passwords hashed using Werkzeug
- Token required for all note operations

### Note Management
- Full CRUD operations on notes
- Color customization (11 options)
- Image attachments via Base64 encoding
- Pin/unpin functionality
- Real-time search filtering

## Project Structure

```
notes-app/
├── app.py                  # Main Flask application
├── requirements.txt        # Dependencies
├── .env                    # Environment variables
├── instance/
│   └── users.db           # SQLite database
└── uploads/               # Image storage
```

## Database Schema

**Users Table:**
- id (Primary Key)
- email (Unique)
- password_hash
- is_verified
- created_at

**Notes Table:**
- id (Primary Key)
- user_id (Foreign Key)
- title
- content
- color
- image_data (Base64)
- is_pinned
- created_at

## API Endpoints

**Auth:**
```
POST /api/register       - Register new user
POST /api/verify-otp     - Verify email OTP
POST /api/login          - Login user
```

**Notes (requires JWT):**
```
GET    /api/notes        - Get all notes
POST   /api/notes        - Create note
GET    /api/notes/:id    - Get single note
PUT    /api/notes/:id    - Update note
DELETE /api/notes/:id    - Delete note
PUT    /api/notes/:id/pin - Toggle pin
```

## Key Features Explained

### Color Coding
11 color options including:
- White (default)
- Black (dark mode)
- Red, Yellow, Green, Cyan, Blue, Purple, Pink
- Background adapts when color selected

### Note Pinning
- Pinned notes appear first
- Visual indicator (pin icon)
- Toggle on/off anytime

### Image Attachments
- Upload images to notes
- Stored as Base64 in database
- Preview before saving
- Display in note cards

### Email Verification
- OTP sent via SMTP
- 6-digit code
- 5-minute expiry
- Secure account activation

## Security

- Werkzeug password hashing
- JWT token authentication
- OTP email verification
- CORS protection
- SQLAlchemy prevents SQL injection
- Token expiry handling

## Deployment

Deployed on PythonAnywhere. Steps:

1. Upload code to PythonAnywhere
2. Create virtual environment
3. Install requirements
4. Configure WSGI file
5. Set environment variables
6. Initialize database

## Environment Variables

Required in `.env`:
```
SMTP_HOST        # SMTP server
SMTP_PORT        # Usually 587
SMTP_USER        # Email username
SMTP_PASS        # Email password
EMAIL_FROM       # Sender email
EMAIL_FROM_NAME  # Display name
```

## Usage Tips

- Use black color for dark theme
- Pin frequently used notes
- Search works on title and content
- Images stored in database (be mindful of size)
- Edit notes by clicking on them

## Limitations

- Images stored as Base64 (not ideal for large files)
- SQLite for development (use PostgreSQL for production)
- No image compression
- Single-user concurrent editing

## Future Plans

- [ ] Note categories and tags
- [ ] Archive functionality
- [ ] Rich text editor
- [ ] Cloud image storage
- [ ] Export notes (PDF/Markdown)
- [ ] Collaborative editing
- [ ] Mobile app
- [ ] Dark mode toggle

## Contributing

Fork the repo and submit PRs. For major changes, open an issue first.

## License

MIT License - feel free to use for your projects.

## Contact

Himanshu Yadav  
[GitHub](https://github.com/theotechtrad) | [LinkedIn](https://www.linkedin.com/in/hvhimanshu-yadav)

---

Made with Flask & JavaScript | Hosted on PythonAnywhere
