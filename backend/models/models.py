from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, Enum, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    user_id       = Column(Integer, primary_key=True, autoincrement=True)
    email         = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(String(10), nullable=False)   # HOD | Proctor
    name          = Column(String(100), nullable=False)
    created_at    = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    createdAt     = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updatedAt     = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow)

    hod_availability = relationship("HODAvailability", back_populates="hod", uselist=False)
    hod_info         = relationship("HODInfo",         back_populates="hod", uselist=False)
    students         = relationship("StudentCore",     foreign_keys="StudentCore.assigned_proctor_id", back_populates="proctor")
    todo_tasks       = relationship("ToDoTask",        back_populates="user")


class HODAvailability(Base):
    __tablename__ = "hod_availability"
    hod_id                = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    is_available          = Column(Boolean, nullable=False, default=False)
    status_message        = Column(String(255))
    estimated_return_time = Column(DateTime)
    last_updated          = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now(), onupdate=func.now())
    createdAt             = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updatedAt             = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow)

    hod = relationship("User", back_populates="hod_availability")


class HODInfo(Base):
    __tablename__ = "hod_info"
    hod_id         = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    department     = Column(String(50), nullable=False)
    designation    = Column(String(50), default="Head of Department")
    office_room    = Column(String(30))
    contact_number = Column(String(15))

    hod = relationship("User", back_populates="hod_info")


class StudentCore(Base):
    __tablename__ = "students_core"
    student_id          = Column(Integer, primary_key=True, autoincrement=True)
    roll_number         = Column(String(20), unique=True, nullable=False)
    full_name           = Column(String(150), nullable=False)
    year_group          = Column(String(10))
    department          = Column(String(50))
    assigned_proctor_id = Column(Integer, ForeignKey("users.user_id"))
    admission_type      = Column(String(50))
    section             = Column(String(5))
    joining_year        = Column(String(10))
    completion_year     = Column(String(10))
    createdAt           = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updatedAt           = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow)

    proctor            = relationship("User",                   foreign_keys=[assigned_proctor_id], back_populates="students")
    personal_info      = relationship("StudentPersonalInfo",    back_populates="student", uselist=False)
    academic_scores    = relationship("StudentAcademicScore",   back_populates="student")
    semester_summaries = relationship("StudentSemesterSummary", back_populates="student")
    midterm_scores     = relationship("StudentMidtermScore",    back_populates="student")
    lab_exams          = relationship("StudentLabExam",         back_populates="student")
    attendances        = relationship("StudentAttendance",      back_populates="student")
    extracurriculars   = relationship("StudentExtracurricular", back_populates="student")


class StudentPersonalInfo(Base):
    __tablename__ = "students_personal_info"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    student_id     = Column(Integer, ForeignKey("students_core.student_id"), nullable=False)
    phone_number   = Column(String(50))
    college_email  = Column(String(100))
    personal_email = Column(String(100))
    father_name    = Column(String(100))
    father_phone   = Column(String(50))
    mother_name    = Column(String(100))
    mother_phone   = Column(String(50))
    address        = Column(Text)
    gender         = Column(String(10))
    date_of_birth  = Column(Date)

    student = relationship("StudentCore", back_populates="personal_info")


class StudentAcademicScore(Base):
    __tablename__ = "students_academic_scores"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    student_id     = Column(Integer, ForeignKey("students_core.student_id"), nullable=False)
    academic_year  = Column(String(10))
    semester       = Column(Integer)
    subject_code   = Column(String(20))
    subject_name   = Column(String(100))
    credits        = Column(Numeric(3, 1))
    internal_marks = Column(Float)
    grade_points   = Column(Numeric(4, 2))

    student = relationship("StudentCore", back_populates="academic_scores")


class StudentSemesterSummary(Base):
    __tablename__ = "student_semester_summaries"
    id                   = Column(Integer, primary_key=True, autoincrement=True)
    student_id           = Column(Integer, ForeignKey("students_core.student_id"), nullable=False)
    semester             = Column(Integer, nullable=False)
    total_credits_earned = Column(Numeric(5, 1))
    sgpa                 = Column(Numeric(4, 2))
    cgpa                 = Column(Numeric(4, 2))

    student = relationship("StudentCore", back_populates="semester_summaries")


class StudentMidtermScore(Base):
    __tablename__ = "students_midterm_scores"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    student_id     = Column(Integer, ForeignKey("students_core.student_id"), nullable=False)
    semester       = Column(Integer)
    subject_name   = Column(String(100))
    midterm_number = Column(Integer)
    marks          = Column(Float)

    student = relationship("StudentCore", back_populates="midterm_scores")


class StudentLabExam(Base):
    __tablename__ = "students_lab_exams"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    student_id     = Column(Integer, ForeignKey("students_core.student_id"), nullable=False)
    semester       = Column(Integer)
    lab_name       = Column(String(100))
    internal_marks = Column(Float)
    external_marks = Column(Float)

    student = relationship("StudentCore", back_populates="lab_exams")


class StudentAttendance(Base):
    __tablename__ = "students_attendance"
    id                    = Column(Integer, primary_key=True, autoincrement=True)
    student_id            = Column(Integer, ForeignKey("students_core.student_id"), nullable=False)
    semester              = Column(Integer)
    month                 = Column(String(20))
    attendance_percentage = Column(Float)
    createdAt             = Column(DateTime)
    updatedAt             = Column(DateTime)

    student = relationship("StudentCore", back_populates="attendances")


class StudentExtracurricular(Base):
    __tablename__ = "students_extracurriculars"
    id                = Column(Integer, primary_key=True, autoincrement=True)
    student_id        = Column(Integer, ForeignKey("students_core.student_id"), nullable=False)
    activity_name     = Column(String(100))
    description       = Column(Text)
    achievement_level = Column(String(50))
    date              = Column(DateTime)

    student = relationship("StudentCore", back_populates="extracurriculars")


class VisitLog(Base):
    __tablename__ = "visit_logs_history"
    visit_id           = Column(Integer, primary_key=True, autoincrement=True)
    check_in_time      = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    visitor_name       = Column(String(100), nullable=False)
    visitor_role       = Column(String(20), nullable=False)
    related_student_id = Column(Integer, ForeignKey("students_core.student_id"), nullable=True)
    purpose            = Column(Text, nullable=False)
    status             = Column(String(30), nullable=False, default="Queued")
    end_time           = Column(DateTime)
    hod_notes          = Column(Text)
    reason_not_met     = Column(Text)
    scheduled_time     = Column(DateTime)
    action_taken       = Column(Enum("Pending", "Scheduled", "Cancelled", "Completed"), nullable=False, default="Pending")
    alert_sent         = Column(Boolean, nullable=False, default=False)
    createdAt          = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updatedAt          = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow)

    student = relationship("StudentCore", foreign_keys=[related_student_id])


class ToDoTask(Base):
    __tablename__ = "todo_tasks"
    task_id      = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    title        = Column(String(255), nullable=False)
    priority     = Column(String(10), nullable=False, default="medium")
    is_completed = Column(Boolean, nullable=False, default=False)
    due_date     = Column(Date)
    createdAt    = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now())
    updatedAt    = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=func.now(), onupdate=datetime.utcnow)

    user = relationship("User", back_populates="todo_tasks")
