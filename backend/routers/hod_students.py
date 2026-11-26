from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models.models import (
    StudentCore, StudentAttendance, StudentAcademicScore,
    StudentSemesterSummary, StudentPersonalInfo, StudentExtracurricular,
    HODInfo, User
)
from auth import get_current_user

router = APIRouter(prefix="/api/hod/students", tags=["HOD Students"])

# ── GET /api/hod/students ─────────────────────────────────────────────────────
@router.get("/")
@router.get("", include_in_schema=False)
def get_hod_students(
    year: Optional[str] = Query(None),
    section: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    hod_id = current_user["user_id"]
    hod_info = db.query(HODInfo).filter(HODInfo.hod_id == hod_id).first()
    if not hod_info:
        raise HTTPException(status_code=404, detail="No HODInfo found for given ID")

    query = db.query(StudentCore).filter(StudentCore.department == hod_info.department)
    if year:    query = query.filter(StudentCore.year_group == year)
    if section: query = query.filter(StudentCore.section == section)
    students = query.all()

    result = []
    for s in students:
        # Attendance — latest record
        att = db.query(StudentAttendance).filter(
            StudentAttendance.student_id == s.student_id
        ).order_by(StudentAttendance.id.desc()).first()

        # CGPA — from summary table or fallback average
        summary = db.query(StudentSemesterSummary).filter(
            StudentSemesterSummary.student_id == s.student_id
        ).order_by(StudentSemesterSummary.semester.desc()).first()

        if summary:
            cgpa = str(summary.cgpa)
        else:
            scores = db.query(StudentAcademicScore).filter(
                StudentAcademicScore.student_id == s.student_id
            ).all()
            if scores:
                total = sum(float(sc.grade_points or 0) for sc in scores)
                cgpa = f"{total / len(scores):.2f}"
            else:
                cgpa = "N/A"

        proctor_name = "N/A"
        if s.assigned_proctor_id:
            proctor = db.query(User).filter(User.user_id == s.assigned_proctor_id).first()
            if proctor:
                proctor_name = proctor.name

        result.append({
            "id": s.student_id,
            "rollNumber": s.roll_number,
            "name": s.full_name,
            "year": s.year_group,
            "section": s.section or "N/A",
            "attendance": att.attendance_percentage if att else "N/A",
            "gpa": cgpa,
            "proctor": proctor_name,
        })

    return result

# ── GET /api/hod/students/names ───────────────────────────────────────────────
@router.get("/names")
def get_student_names(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    hod_info = db.query(HODInfo).filter(HODInfo.hod_id == current_user["user_id"]).first()
    query = db.query(StudentCore.full_name)
    if hod_info:
        query = query.filter(StudentCore.department == hod_info.department)
    return [row.full_name for row in query.all()]

# ── GET /api/hod/students/{id} ────────────────────────────────────────────────
@router.get("/{student_id}")
def get_hod_student_details(student_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    s = db.query(StudentCore).filter(StudentCore.student_id == student_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Student not found")

    scores = s.academic_scores
    total_points = sum(float(sc.grade_points or 0) for sc in scores)
    gpa_fallback = f"{total_points / len(scores):.2f}" if scores else "N/A"

    attendances = sorted(s.attendances, key=lambda a: a.id, reverse=True)
    latest_att = attendances[0] if attendances else None
    p = s.personal_info

    return {
        "roll_number": s.roll_number,
        "full_name": s.full_name,
        "department": s.department,
        "year_group": s.year_group,
        "section": s.section or "N/A",
        "dob": str(p.date_of_birth) if p and p.date_of_birth else "N/A",
        "gender": p.gender if p else "N/A",
        "phone": p.phone_number if p else "N/A",
        "email": p.college_email if p else "N/A",
        "personal_email": p.personal_email if p else "N/A",
        "father_name": p.father_name if p else "N/A",
        "mother_name": p.mother_name if p else "N/A",
        "father_phone": p.father_phone if p else "N/A",
        "mother_phone": p.mother_phone if p else "N/A",
        "gpa": gpa_fallback,
        "attendance_percentage": latest_att.attendance_percentage if latest_att else "N/A",
        "proctor": s.proctor.name if s.proctor else "N/A",
        "student_semester_summaries": [
            {"semester": sm.semester, "sgpa": str(sm.sgpa), "cgpa": str(sm.cgpa)}
            for sm in s.semester_summaries
        ],
        "academic_scores": [
            {"semester": sc.semester, "subject_name": sc.subject_name,
             "grade_points": str(sc.grade_points), "subject_code": sc.subject_code}
            for sc in scores
        ],
        "extracurriculars": [
            {"activity_name": e.activity_name, "description": e.description,
             "achievement_level": e.achievement_level, "date": str(e.date)}
            for e in s.extracurriculars
        ],
    }
