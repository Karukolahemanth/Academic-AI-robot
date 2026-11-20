# 🎓 AcademicFlow-AI

> An AI-powered Academic Management System for Heads of Departments (HODs) and Proctors — built to streamline student monitoring, visitor management, and academic analytics.

---

## 📌 Table of Contents

- [About the Project](#about-the-project)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start with Docker](#quick-start-with-docker)
- [Default Login Credentials](#default-login-credentials)
- [API Endpoints](#api-endpoints)
- [Hardware Kiosk Integration](#hardware-kiosk-integration)
- [Project Structure](#project-structure)

---

## 📖 About the Project

**AcademicFlow-AI** is a full-stack academic dashboard built for the CSM Department at ANITS. It provides:

- **HODs** with a real-time overview of visitor appointments, student performance, and department-wide analytics.
- **Proctors** with individual student academic tracking — marks, attendance, SGPA/CGPA, and more.
- A **Hardware Kiosk API** that integrates with a Raspberry Pi device at the HOD office entrance to manage visitor queues digitally.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AcademicFlow-AI                        │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   Frontend   │    │   Backend    │    │   Database   │  │
│  │  React/Vite  │───▶│ Node/Express │───▶│    MySQL     │  │
│  │  Port: 3000  │    │  Port: 5000  │    │  Port: 3307  │  │
│  │  Nginx (prod)│    │  JWT Auth    │    │  Sequelize   │  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘  │
│                             │                               │
│                    ┌────────▼────────┐                      │
│                    │  Kiosk Bot API  │                      │
│                    │ /api/bot/status │ ← No auth needed     │
│                    │ /api/bot/log-   │                      │
│                    │   visit         │                      │
│                    └────────▲────────┘                      │
└─────────────────────────────│───────────────────────────────┘
                              │ HTTP POST
                   ┌──────────┴──────────┐
                   │  Raspberry Pi Kiosk │
                   │  (Physical device   │
                   │   at HOD entrance)  │
                   └─────────────────────┘
```

---

## ✨ Features

### 👨‍💼 HOD Dashboard
- **Availability Toggle** — Set real-time availability status visible to the kiosk
- **Visitor Queue** — Live feed of visitors waiting at the office
- **Appointment Management** — Schedule, complete, or cancel visitor appointments
- **Visit History** — Full log of past visits with status tracking
- **Student Overview** — Browse all department students with filters
- **To-Do List** — Task management for the HOD

### 👨‍🏫 Proctor Dashboard
- **Student List** — View all assigned students with academic profiles
- **Academic Scores** — Semester-wise subject marks, grade points, credits
- **SGPA / CGPA** — Automatically computed from grade data
- **Midterm Marks** — Internal assessment scores
- **Lab Exam Results** — Lab internal and external marks
- **Attendance Tracking** — Monthly attendance percentage per student
- **Extracurriculars** — Student achievements and activities
- **Personal Info** — Contact, parents, DOB, address
- **AI Insights** — Smart alerts for at-risk students

### 🤖 Hardware Kiosk (Raspberry Pi)
- Visitors register at the physical kiosk
- System checks HOD availability in real time
- Visit logged to the HOD's queue automatically

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, React Router |
| **Backend** | Node.js, Express.js, Sequelize ORM |
| **Database** | MySQL 8.0 |
| **Auth** | JWT (JSON Web Tokens) + bcryptjs |
| **Containerization** | Docker, Docker Compose |
| **Web Server** | Nginx (production frontend serving) |
| **Hardware** | Raspberry Pi (kiosk device) |

---

## ✅ Prerequisites

Make sure the following are installed on your machine:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v20+)
- [Git](https://git-scm.com/)

> No Node.js or MySQL installation required — Docker handles everything!

---

## 🚀 Quick Start with Docker

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Karukolahemanth/Academic-AI-robot.git
cd Academic-AI-robot
```

### Step 2 — Start All Services

```bash
docker compose up --build -d
```

This command will:
- 📦 Pull `mysql:8.0`, `node:22-alpine`, and `nginx:stable-alpine` images
- 🔨 Build the backend and frontend Docker images
- 🚀 Start all 3 containers (`academic_mysql`, `academic_backend`, `academic_frontend`)
- 🗄️ Automatically create all database tables via Sequelize sync

> ⏱️ **First run takes 3–5 minutes** (image downloads + npm installs). Subsequent runs start in seconds.

### Step 3 — Restore the Database (with student data)

If you have the SQL backup file (`academic_db_backup.sql`):

```powershell
# Windows PowerShell — Convert and restore
$src = "C:\path\to\academic_db_backup.sql"
$dst = "C:\path\to\academic_db_backup_utf8.sql"
$content = [System.IO.File]::ReadAllText($src, [System.Text.Encoding]::Unicode)
[System.IO.File]::WriteAllText($dst, $content, [System.Text.Encoding]::UTF8)

docker cp $dst academic_mysql:/tmp/backup_utf8.sql
docker exec academic_mysql bash -c "mysql -uharshini -pharshini academic_db < /tmp/backup_utf8.sql"
```

```bash
# Linux / Mac
docker cp academic_db_backup.sql academic_mysql:/tmp/backup.sql
docker exec academic_mysql bash -c "mysql -uharshini -pharshini academic_db < /tmp/backup.sql"
```

Then restart the backend to re-sync:

```bash
docker restart academic_backend
```

### Step 4 — Access the Application

| Service | URL |
|---|---|
| 🌐 **Web App** | http://localhost:3000 |
| ⚙️ **Backend API** | http://localhost:5000 |
| 🗄️ **MySQL** | `localhost:3307` |

---

## 🔐 Default Login Credentials

> Login credentials are managed by the system administrator. Use the email and password assigned to your account (HOD or Proctor) to log in.

---

## 🛑 Useful Docker Commands

```bash
# View logs from all services
docker compose logs -f

# View logs for a specific service
docker logs academic_backend -f
docker logs academic_frontend -f
docker logs academic_mysql -f

# Stop all containers (preserves data)
docker compose down

# Stop and delete all data (fresh start)
docker compose down -v

# Rebuild after code changes
docker compose up --build -d

# Check running containers
docker ps
```

---

## 📡 API Endpoints

### Authentication (Public)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/signup` | Register a new HOD or Proctor |
| `POST` | `/api/auth/login` | Login and receive JWT token |

### Kiosk Bot API (No Auth — for Raspberry Pi)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/bot/status` | Get HOD availability status |
| `POST` | `/api/bot/log-visit` | Log a new visitor from the kiosk |

**Kiosk POST body:**
```json
{
  "role": "Parent",
  "name": "Visitor Name",
  "contact": "9876543210",
  "student_id": "22CSM001",
  "purpose": "Inquiry about fee structure"
}
```

### HOD APIs (Requires JWT Token)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/hod/students` | List all department students |
| `GET/PUT` | `/api/hod/availability` | Manage HOD availability |
| `GET/POST/PUT` | `/api/visit_logs` | Manage visitor appointments |
| `GET/POST/PUT/DELETE` | `/api/todo` | HOD task management |

### Proctor APIs (Requires JWT Token)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/proctor/dashboard` | Proctor summary + student list |
| `GET` | `/api/proctor/student/:id` | Full student academic profile |

---

## 📟 Hardware Kiosk Integration

The system integrates with a **Raspberry Pi kiosk** placed at the HOD office entrance. The Pi runs a local touchscreen UI that:

1. Greets the visitor and collects: Name, Role, Contact, Student Roll No., Purpose
2. Calls `GET /api/bot/status` to show if the HOD is available
3. Calls `POST /api/bot/log-visit` to register the visit
4. Displays a queue number or estimated wait time

The HOD's dashboard automatically shows new visitors in the queue in real time.

---

## 📁 Project Structure

```
Academic-AI-robot/
├── backend/
│   ├── config/
│   │   └── db.config.js          # Database connection config
│   ├── controllers/
│   │   ├── auth.controller.js    # Login / Signup logic
│   │   ├── bot.controller.js     # Kiosk API logic
│   │   ├── hodStudents.controller.js
│   │   ├── hodAvailability.controller.js
│   │   ├── hodSettings.controller.js
│   │   ├── proctor.controller.js
│   │   └── proctorDashboard.controller.js
│   ├── middleware/
│   │   └── authJwt.js            # JWT verification middleware
│   ├── models/
│   │   └── index.js              # All Sequelize models & relationships
│   ├── routes/                   # Express route definitions
│   ├── scripts/                  # Data import scripts (CSV → DB)
│   ├── Dockerfile
│   ├── package.json
│   └── server.js                 # Express app entry point
│
├── frontend/
│   ├── src/
│   │   ├── components/           # All React components
│   │   │   ├── AuthForm.jsx      # Login page
│   │   │   ├── DashboardLayout.jsx
│   │   │   ├── HODAppointments.jsx
│   │   │   ├── HODStudents.jsx
│   │   │   ├── ProctorDashboard.jsx
│   │   │   ├── ProctorStudents.jsx
│   │   │   └── ...
│   │   ├── App.jsx               # Routing & Auth context
│   │   └── main.jsx
│   ├── nginx.conf                # Nginx config for React SPA routing
│   ├── Dockerfile
│   └── package.json
│
├── scripts for marks/            # Python scripts for mark extraction
│   ├── extract_sem2.py
│   └── extract_sem4.py
│
├── docker-compose.yml            # Orchestrates all 3 services
└── README.md
```

---

## 👥 Team

| Name | Role | GitHub |
|---|---|---|
| Karukola Hemanth | Full Stack Developer | [@Karukolahemanth](https://github.com/Karukolahemanth) |
| Khasif | Full Stack Developer | [@khasif](https://github.com/khasif) |
| Uttaravilli Geetika | Full Stack Developer | [@GeetikaUttaravilli](https://github.com/GeetikaUttaravilli) |
| Moyya Hasini | Full Stack Developer | — |

---

## 📄 License

This project is built for academic purposes at **ANITS (Anil Neerukonda Institute of Technology and Sciences)**, CSM Department.
