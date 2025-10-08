# GuruSchool Backend API

A comprehensive FastAPI-based backend for a language learning platform with role-based access control, course management, and subscription handling.

## 📋 Features

- ✅ **Role-Based Authentication** (Student, Teacher, Super Admin)
- ✅ **Course Management** (Courses, Modules, Lessons)
- ✅ **Enrollment System** with subscription management
- ✅ **Pricing & Discounts** with country-based pricing
- ✅ **Teacher Application System**
- ✅ **Admin Dashboard** capabilities
- ✅ **User Profile Management**
- ✅ **JWT Authentication** with Supabase
- ✅ **Auto-generated API Documentation** (Swagger/ReDoc)

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Supabase account

### Installation

1. **Clone & Navigate**

   ```bash
   cd guruschool_final_backend
   ```

2. **Activate Virtual Environment**

   ```bash
   # Windows PowerShell
   .\myenv\Scripts\Activate.ps1

   # Windows CMD
   myenv\Scripts\activate.bat
   ```

3. **Configure Environment**

   Create/update `.env` file:

   ```env
   PROJECT_NAME=GuruSchool API
   debug=True
   secret_key=your-secret-key-here
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   SECRET_KEY=your-secret-key
   ENCRYPTION_ALGORITHM=HS256
   MONGODB_URI=your-mongodb-uri
   API_VERSION=v1
   PORT=8000
   SUPABASE_URL=your-supabase-url
   SUPABASE_KEY=your-supabase-key
   JWT_SECRET=your-jwt-secret
   ```

4. **Run the Application**

   ```bash
   python main.py
   ```

5. **Access Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## 📁 Project Structure

```
guruschool_final_backend/
├── main.py                          # FastAPI application entry point
├── .env                             # Environment configuration
├── README.md                        # This file
├── API_DOCUMENTATION.md             # Detailed API docs with examples
├── API_QUICK_REFERENCE.md           # Quick reference table
├── CODE_STRUCTURE.md                # Code organization guide
├── REFACTORING_SUMMARY.md           # Refactoring details
│
├── src/
│   ├── models/                      # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth_schemas.py          # Authentication models
│   │   ├── course_schemas.py        # Course/Module/Lesson models
│   │   ├── user_schemas.py          # User profile models
│   │   └── enrollment_schemas.py    # Enrollment/Pricing models
│   │
│   ├── routers/                     # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py                  # Authentication endpoints
│   │   ├── courses.py               # Course management
│   │   ├── admin.py                 # Admin operations
│   │   ├── enrollments.py           # Enrollment management
│   │   ├── profiles.py              # User profiles
│   │   └── teachers.py              # Teacher features
│   │
│   └── utils/                       # Utilities
│       ├── auth_helpers.py          # Authentication helpers
│       └── config.py                # Configuration
│
└── myenv/                           # Virtual environment
```

## 🎯 API Overview

### Base URL

```
http://localhost:8000/api/v1
```

### Endpoint Categories

| Category           | Endpoints | Description                  |
| ------------------ | --------- | ---------------------------- |
| **Authentication** | 7         | User registration & login    |
| **Courses**        | 8         | Course/module/lesson CRUD    |
| **Admin**          | 8         | Admin operations             |
| **Enrollments**    | 4         | Course enrollment management |
| **Profiles**       | 2         | User profile management      |
| **Teachers**       | 2         | Teacher-specific features    |
| **Total**          | **31**    |                              |

## 🔑 User Roles

### Student

- Register and enroll in courses
- View course content
- Manage profile
- Track enrollments

### Teacher

- Create courses, modules, and lessons
- View enrollment statistics
- Manage own courses

### Super Admin

- Approve teacher applications
- Set course pricing
- Create discount codes
- Manage all users
- Full system access

## 📖 Documentation

### Comprehensive Guides

1. **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)**

   - Complete request/response examples
   - All 31 endpoints documented
   - Error handling examples
   - cURL examples

2. **[API_QUICK_REFERENCE.md](./API_QUICK_REFERENCE.md)**

   - Quick lookup table
   - Access requirements
   - Common workflows
   - Testing checklist

3. **[CODE_STRUCTURE.md](./CODE_STRUCTURE.md)**

   - Detailed code organization
   - Module responsibilities
   - Import patterns
   - Development guide

4. **[REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md)**
   - Before/after comparison
   - Benefits of new structure
   - Migration guide

## 🔐 Authentication

Most endpoints require JWT authentication:

```http
Authorization: Bearer <your-jwt-token>
```

### Getting Started

1. **Register:**

   ```bash
   POST /api/v1/auth/register/student
   ```

2. **Login:**

   ```bash
   POST /api/v1/auth/login
   ```

3. **Use Token:**
   Include the `access_token` in Authorization header

## 🧪 Testing

### Using Swagger UI

1. Start server: `python main.py`
2. Navigate to: http://localhost:8000/docs
3. Click "Authorize" button
4. Enter: `Bearer <your-token>`
5. Test endpoints interactively

### Using cURL

```bash
# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Get Profile (with token)
curl -X GET "http://localhost:8000/api/v1/profile/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Using Postman

1. Import OpenAPI spec from http://localhost:8000/openapi.json
2. Set authorization type to "Bearer Token"
3. Use the access_token from login response

## 🛠️ Development

### Adding New Endpoints

1. **Create/Update Schema** in `src/models/`
2. **Create Endpoint** in appropriate `src/routers/` file
3. **Import Router** in `main.py` (if new router)
4. **Test** using Swagger UI

### Code Style

- Follow existing patterns
- Use type hints
- Add docstrings
- Keep single responsibility

### File Organization

- **Models:** Data validation schemas (Pydantic)
- **Routers:** API endpoints grouped by domain
- **Utils:** Shared utilities and helpers

## 🔧 Configuration

### Environment Variables

| Variable       | Description          | Required |
| -------------- | -------------------- | -------- |
| `PROJECT_NAME` | Application name     | Yes      |
| `API_VERSION`  | API version          | Yes      |
| `PORT`         | Server port          | Yes      |
| `SUPABASE_URL` | Supabase project URL | Yes      |
| `SUPABASE_KEY` | Supabase API key     | Yes      |
| `JWT_SECRET`   | JWT signing secret   | Yes      |
| `debug`        | Debug mode           | No       |

## 📊 Database Schema

### Supabase Tables

- **profiles** - User profiles with roles
- **courses** - Course information
- **modules** - Course modules
- **lessons** - Module lessons
- **enrollments** - Student enrollments
- **course_pricing** - Country-based pricing
- **discounts** - Discount codes
- **teacher_applications** - Teacher applications
- **invites** - Teacher invites

## 🐛 Common Issues

### Import Errors

```bash
# Make sure virtual environment is activated
.\myenv\Scripts\Activate.ps1
```

### Port Already in Use

```bash
# Change PORT in .env file
PORT=8001
```

### Supabase Connection

```bash
# Verify SUPABASE_URL and SUPABASE_KEY in .env
# Check Supabase project is active
```

## 📦 Dependencies

Main dependencies:

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `supabase` - Database & auth
- `python-jose` - JWT handling
- `pydantic` - Data validation
- `python-dateutil` - Date handling

## 🚢 Deployment

### Production Checklist

- [ ] Update CORS settings in `main.py`
- [ ] Set `debug=False` in .env
- [ ] Use strong JWT_SECRET
- [ ] Configure proper Supabase RLS policies
- [ ] Set up monitoring
- [ ] Enable HTTPS
- [ ] Configure rate limiting

### Running in Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📝 API Versioning

Current version: **v1**

Base path: `/api/v1`

## 🤝 Contributing

1. Follow existing code structure
2. Update documentation for new features
3. Add tests for new endpoints
4. Maintain type hints and docstrings

## 📄 License

[Add your license here]

## 👥 Team

[Add team members]

## 📞 Support

- **Documentation:** See markdown files in root directory
- **API Docs:** http://localhost:8000/docs
- **Issues:** [Add issue tracker link]

## 🎉 Acknowledgments

Built with FastAPI, Supabase, and ❤️

---

**Last Updated:** October 9, 2025  
**Version:** 1.0.0  
**Status:** Active Development
