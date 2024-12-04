from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import models
import database
from fastapi.responses import RedirectResponse
from prometheus_client import Counter, generate_latest
from fastapi.responses import PlainTextResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Prometheus Metrics
USER_REGISTRATIONS = Counter("user_registrations", "Number of user registrations")
PASSWORD_CHANGES = Counter("password_changes", "Number of password changes")
USER_LOGINS = Counter("user_logins", "Number of user logins", ["username"])

# Database dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or user.password != password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
    USER_LOGINS.labels(username=username).inc()  # Increment login count for the user
    
    return RedirectResponse(url=f"/welcome/{username}", status_code=303)

@app.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username").strip()  # Remove whitespace
    email = form.get("email")
    password = form.get("password")
    confirm_password = form.get("confirm_password")
    
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords don't match")
    
    existing_user = db.query(models.User).filter(
        (models.User.username == username) | 
        (models.User.email == email)
    ).first()
    
    if existing_user:
        if existing_user.username == username:
            raise HTTPException(status_code=400, detail="Username already taken")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = models.User(username=username, email=email, password=password)
    db.add(user)
    db.commit()
    
    USER_REGISTRATIONS.inc()  # Increment registration count
    
    return RedirectResponse(url="/login", status_code=303)

@app.get("/welcome/{username}")
async def welcome(request: Request, username: str):
    return templates.TemplateResponse("welcome.html", {"request": request, "username": username})

@app.get("/forgot-password")
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot-password.html", {"request": request})

@app.post("/forgot-password")
async def forgot_password(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    email = form.get("email")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Email not found")
    
    return RedirectResponse(url=f"/reset-password?email={email}", status_code=303)

@app.get("/reset-password")
async def reset_password_page(request: Request, email: str):
    return templates.TemplateResponse("reset-password.html", {"request": request, "email": email})

@app.post("/reset-password")
async def reset_password(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    email = form.get("email")
    new_password = form.get("new_password")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email")
    
    user.password = new_password
    db.commit()
    
    PASSWORD_CHANGES.inc()  # Increment password change count
    
    return RedirectResponse(url="/login", status_code=303)

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    return generate_latest()

@app.get("/data/users")
async def get_all_users(db: Session = Depends(get_db)):
    """Fetch all registered users with their details."""
    users = db.query(models.User).all()  # Fetch all users from the database
    user_list = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "password": user.password  # Optional: Include if necessary
        }
        for user in users
    ]
    return {"users": user_list}

