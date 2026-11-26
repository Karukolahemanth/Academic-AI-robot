from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import models

# Import all routers
from routers import auth, hod, hod_students, visit_logs, todo, proctor, bot

# Create all tables (equivalent to sequelize.sync)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AcademicFlow-AI API",
    description="FastAPI backend for the AI-Powered Academic Dashboard",
    version="2.0.0"
)

# CORS — allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logger middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    return response

# Register routers
app.include_router(auth.router)
app.include_router(hod.router)
app.include_router(hod_students.router)
app.include_router(visit_logs.router)
app.include_router(todo.router)
app.include_router(proctor.router)
app.include_router(bot.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Academic Dashboard API!"}
