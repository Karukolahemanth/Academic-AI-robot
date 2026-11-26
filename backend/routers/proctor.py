from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, desc
from pydantic import BaseModel
from typing import Optional
from datetime import date
from database import get_db
from models.models import (
    User, StudentCore, StudentPersonalInfo, StudentAttendance,
    StudentAcademicScore, StudentExtracurricular, ToDoTask
)
from auth import get_current_user, hash_password

router = APIRouter(prefix="/api/proctor", tags=["Proctor"])

# ── GET /api/proctor/dashboard ────────────────────────────────────────────────
@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    proctor_id = current_user["user_id"]
    students = db.query(StudentCore).filter(StudentCore.assigned_proctor_id == proctor_id).all()

    total_students = len(students)
    attendance_values, total_cgpa, count_with_grades, low_perf = [], 0, 0, 0

    for s in students:
        # Latest attendance
        att = db.query(StudentAttendance).filter(
            StudentAttendance.student_id == s.student_id
        ).order_by(desc(StudentAttendance.id)).first()
        if att:
            attendance_values.append(float(att.attendance_percentage))

        # CGPA + low performance detection
        scores = db.query(StudentAcademicScore).filter(
            StudentAcademicScore.student_id == s.student_id
        ).all()
        if scores:
            total_pts = sum(float(sc.grade_points or 0) for sc in scores)
            cgpa = total_pts / len(scores)
            total_cgpa += cgpa
            count_with_grades += 1

            # SGPA of latest semester
            max_sem = max((sc.semester or 0) for sc in scores)
            latest = [sc for sc in scores if sc.semester == max_sem]
            if latest:
                sgpa = sum(float(sc.grade_points or 0) for sc in latest) / len(latest)
                if sgpa < 6.0:
                    low_perf += 1

    avg_attendance = f"{sum(attendance_values)/len(attendance_values):.1f}" if attendance_values else "0.0"
    avg_cgpa = f"{total_cgpa/count_with_grades:.2f}" if count_with_grades else "0.00"

    return {
        "totalStudents": total_students,
        "avgAttendance": avg_attendance,
        "avgCGPA": avg_cgpa,
        "lowPerformance": low_perf,
        "students": [
            {
                "student_id": s.student_id,
                "roll_number": s.roll_number,
                "full_name": s.full_name,
                "year_group": s.year_group,
                "department": s.department,
                "section": s.section,
            }
            for s in students
        ],
    }

# ── GET /api/proctor/students ─────────────────────────────────────────────────
@router.get("/students")
def get_students(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    students = db.query(StudentCore).options(
        joinedload(StudentCore.academic_scores),
        joinedload(StudentCore.attendances),
    ).filter(
        StudentCore.assigned_proctor_id == current_user["user_id"]
    ).order_by(asc(StudentCore.roll_number)).all()

    serialized_students = [
        {
            "student_id": s.student_id,
            "roll_number": s.roll_number,
            "full_name": s.full_name,
            "year_group": s.year_group,
            "department": s.department,
            "assigned_proctor_id": s.assigned_proctor_id,
            "admission_type": s.admission_type,
            "section": s.section,
            "joining_year": s.joining_year,
            "completion_year": s.completion_year,
            "student_academic_scores": [
                {
                    "id": sc.id,
                    "semester": sc.semester,
                    "subject_code": sc.subject_code,
                    "subject_name": sc.subject_name,
                    "grade_points": float(sc.grade_points) if sc.grade_points is not None else None,
                    "internal_marks": sc.internal_marks,
                }
                for sc in s.academic_scores
            ],
            "student_attendances": [
                {
                    "id": a.id,
                    "semester": a.semester,
                    "month": a.month,
                    "attendance_percentage": a.attendance_percentage,
                    "createdAt": a.createdAt,
                }
                for a in s.attendances
            ],
        }
        for s in students
    ]

    tasks = db.query(ToDoTask).filter(
        ToDoTask.user_id == current_user["user_id"]
    ).order_by(asc(ToDoTask.is_completed), desc(ToDoTask.task_id)).all()
    return {"students": serialized_students, "tasks": tasks}


class ProctorTaskCreate(BaseModel):
    title: str
    priority: Optional[str] = "medium"

class ProctorTaskToggle(BaseModel):
    is_completed: bool

# ── POST /api/proctor/tasks ───────────────────────────────────────────────────
@router.post("/tasks", status_code=201)
def create_proctor_task(payload: ProctorTaskCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    task = ToDoTask(
        user_id=current_user["user_id"],
        title=payload.title,
        priority=payload.priority or "medium",
        is_completed=False,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

# ── PATCH /api/proctor/tasks/{task_id} ────────────────────────────────────────
@router.patch("/tasks/{task_id}")
def toggle_proctor_task(task_id: int, payload: ProctorTaskToggle, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    task = db.query(ToDoTask).filter(ToDoTask.task_id == task_id, ToDoTask.user_id == current_user["user_id"]).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.is_completed = payload.is_completed
    db.commit()
    db.refresh(task)
    return task

# ── GET /api/proctor/students/{id} ────────────────────────────────────────────
@router.get("/students/{student_id}")
def get_student_details(student_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    s = db.query(StudentCore).filter(StudentCore.student_id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    scores = s.academic_scores
    total_pts = sum(float(sc.grade_points or sc.internal_marks or 0) for sc in scores)
    calc_gpa = (total_pts / len(scores)) if scores else 0
    if calc_gpa > 10:
        calc_gpa /= 10
    gpa = f"{calc_gpa:.2f}" if calc_gpa else "N/A"

    latest_att = sorted(s.attendances, key=lambda a: a.id, reverse=True)
    p = s.personal_info

    return {
        "student_id": s.student_id,
        "roll_number": s.roll_number,
        "full_name": s.full_name,
        "department": s.department,
        "year": s.year_group,
        "section": s.section or "N/A",
        "proctor": s.proctor.name if s.proctor else "Unassigned",
        "email": p.college_email if p else "-",
        "phone": p.phone_number if p else "-",
        "father_name": p.father_name if p else "-",
        "address": p.address if p else "-",
        "gpa": gpa,
        "attendance_percentage": latest_att[0].attendance_percentage if latest_att else "0",
        "academic_scores": [
            {"id": sc.id, "semester": sc.semester, "grade_points": str(sc.grade_points)}
            for sc in scores
        ],
        "extracurriculars": [
            {"id": e.id, "activity": e.activity_name, "level": e.achievement_level, "date": str(e.date)}
            for e in s.extracurriculars
        ],
    }

# ── GET /api/proctor/profile ──────────────────────────────────────────────────
@router.get("/profile")
def get_profile(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    proctor = db.query(User).filter(User.user_id == current_user["user_id"]).first()
    if not proctor:
        raise HTTPException(status_code=404, detail="Proctor not found")
    return {"user_id": proctor.user_id, "name": proctor.name, "email": proctor.email, "role": proctor.role}

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

# ── PUT /api/proctor/profile & /api/proctor/settings/update ───────────────────
@router.put("/profile")
@router.put("/settings/update", include_in_schema=False)
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    proctor = db.query(User).filter(User.user_id == current_user["user_id"]).first()
    if not proctor:
        raise HTTPException(status_code=404, detail="Proctor not found")
    if payload.name:  proctor.name = payload.name
    if payload.email: proctor.email = payload.email
    if payload.password and payload.password.strip():
        proctor.password_hash = hash_password(payload.password)
    db.commit()
    return {"message": "Updated"}

class StudentCreate(BaseModel):
    roll_number: str
    full_name: str
    year_group: Optional[str] = None
    department: Optional[str] = None
    admission_type: Optional[str] = None
    personal_info: Optional[dict] = None

# ── POST /api/proctor/students ────────────────────────────────────────────────
@router.post("/students", status_code=201)
def add_student(payload: StudentCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    student = StudentCore(
        roll_number=payload.roll_number, full_name=payload.full_name,
        year_group=payload.year_group, department=payload.department,
        admission_type=payload.admission_type,
        assigned_proctor_id=current_user["user_id"]
    )
    db.add(student)
    db.flush()
    if payload.personal_info:
        db.add(StudentPersonalInfo(student_id=student.student_id, **payload.personal_info))
    db.commit()
    return {"message": "Student added successfully", "student_id": student.student_id}

class StudentUpdate(BaseModel):
    full_name: Optional[str] = None
    year_group: Optional[str] = None
    department: Optional[str] = None
    admission_type: Optional[str] = None
    personal_info: Optional[dict] = None

# ── PUT /api/proctor/students/{id} ────────────────────────────────────────────
@router.put("/students/{student_id}")
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    s = db.query(StudentCore).filter(StudentCore.student_id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")
    if payload.full_name:    s.full_name = payload.full_name
    if payload.year_group:   s.year_group = payload.year_group
    if payload.department:   s.department = payload.department
    if payload.admission_type: s.admission_type = payload.admission_type
    if payload.personal_info:
        p = db.query(StudentPersonalInfo).filter(StudentPersonalInfo.student_id == student_id).first()
        if p:
            for k, v in payload.personal_info.items():
                setattr(p, k, v)
        else:
            db.add(StudentPersonalInfo(student_id=student_id, **payload.personal_info))
    db.commit()
    return {"message": "Student updated successfully"}
