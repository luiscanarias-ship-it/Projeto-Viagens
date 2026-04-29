"""
Auth routes — registration, login, password reset, Google OAuth, session management.
"""
from fastapi import APIRouter, HTTPException, Request, Response
from datetime import datetime, timezone, timedelta
import uuid
import asyncio
import httpx

from config import db, logger, ADMIN_PASSWORD, FRONTEND_URL
from models import UserCreate, UserLogin, generate_anonymous_alias
from auth import get_current_user, require_auth, create_jwt_token, hash_password, verify_password
from email_service import get_email_base_template, send_email_resend
from services.notification_service import create_notification

router = APIRouter()


@router.post("/auth/register")
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email já registado")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    is_admin = user_data.password == ADMIN_PASSWORD
    
    sponsor_id = None
    if user_data.sponsor_code:
        sponsor_link = await db.sponsor_links.find_one(
            {"link_id": user_data.sponsor_code}, {"_id": 0, "user_id": 1}
        )
        if sponsor_link:
            sponsor_user_id = sponsor_link["user_id"]
            sponsor_user = await db.users.find_one({"user_id": sponsor_user_id}, {"_id": 0, "email": 1})
            if sponsor_user and sponsor_user.get("email") != user_data.email:
                sponsor_id = sponsor_user_id
                await db.sponsor_links.update_one(
                    {"link_id": user_data.sponsor_code},
                    {"$inc": {"referral_count": 1}}
                )
    
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "surname": user_data.surname,
        "password_hash": hash_password(user_data.password),
        "is_admin": is_admin,
        "avatar": None,
        "use_real_name": True,
        "sponsor_id": sponsor_id,
        "level": "sonhador",
        "contributed_to_main_trip": False,
        "valid_referrals_count": 0,
        "total_contributed": 0,
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "embaixador_unlocked_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    if sponsor_id:
        asyncio.create_task(create_notification(
            sponsor_id, "referral_registered",
            f"O teu amigo {user_data.name} acabou de se registar! Falta contribuir para a Viagem Principal.",
            {"referred_name": user_data.name, "referred_user_id": user_id}
        ))
    
    token = create_jwt_token(user_id, is_admin)
    return {
        "token": token,
        "user": {
            "user_id": user_id,
            "email": user_data.email,
            "name": user_data.name,
            "is_admin": is_admin
        }
    }


@router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    token = create_jwt_token(user["user_id"], user.get("is_admin", False))
    return {
        "token": token,
        "user": {
            "user_id": user["user_id"],
            "email": user["email"],
            "name": user["name"],
            "is_admin": user.get("is_admin", False)
        }
    }


@router.post("/auth/forgot-password")
async def forgot_password(request: Request):
    data = await request.json()
    email = data.get("email", "").strip().lower()
    if not email:
        return {"message": "Se este email existir, vais receber instruções."}
    
    user = await db.users.find_one({"email": email}, {"_id": 0, "user_id": 1, "name": 1})
    if user:
        token = str(uuid.uuid4())
        await db.password_resets.delete_many({"user_id": user["user_id"]})
        await db.password_resets.insert_one({
            "token": token,
            "user_id": user["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat(),
            "used": False
        })
        reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
        name = user.get("name", "Sonhador")
        html_content = get_email_base_template(f"""
            <h2 style="color: #2D2A26; font-size: 20px; margin: 0 0 16px 0;">Recuperar palavra-passe</h2>
            <p style="color: #6B6661; font-size: 14px; line-height: 1.6;">
                Olá {name},<br><br>
                Recebemos um pedido para repor a tua palavra-passe. Clica no botão abaixo para criar uma nova.
            </p>
            <div style="text-align: center; margin: 24px 0;">
                <a href="{reset_link}" style="display: inline-block; background-color: #FFBE98; color: #2D2A26; padding: 14px 32px; border-radius: 12px; text-decoration: none; font-weight: bold; font-size: 14px;">
                    Repor palavra-passe
                </a>
            </div>
            <p style="color: #9B9590; font-size: 12px; line-height: 1.5;">
                Este link expira em 30 minutos.<br>
                Se não fizeste este pedido, ignora este email.
            </p>
        """, "Recuperar palavra-passe — 4Luis")
        try:
            await send_email_resend(email, "Recuperar palavra-passe — 4Luis", html_content)
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
    
    return {"message": "Se este email existir, vais receber instruções."}


@router.post("/auth/reset-password")
async def reset_password(request: Request):
    data = await request.json()
    token = data.get("token", "")
    new_password = data.get("password", "")
    
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token e nova palavra-passe são obrigatórios.")
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="A palavra-passe deve ter pelo menos 8 caracteres.")
    
    reset_doc = await db.password_resets.find_one({"token": token, "used": False}, {"_id": 0})
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Link inválido ou já utilizado.")
    
    expires_at = datetime.fromisoformat(reset_doc["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="O link expirou. Solicita uma nova recuperação.")
    
    await db.users.update_one(
        {"user_id": reset_doc["user_id"]},
        {"$set": {"password_hash": hash_password(new_password)}}
    )
    await db.password_resets.update_one({"token": token}, {"$set": {"used": True}})
    
    return {"message": "Palavra-passe atualizada com sucesso."}


@router.post("/auth/google/session")
async def process_google_session(request: Request, response: Response):
    data = await request.json()
    session_id = data.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id é obrigatório")
    
    async with httpx.AsyncClient() as client_http:
        resp = await client_http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=401, detail="Sessão Google inválida")
        google_data = resp.json()
    
    email = google_data.get("email")
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        is_admin = existing_user.get("is_admin", False)
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"name": google_data.get("name"), "picture": google_data.get("picture")}}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        is_admin = False
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": google_data.get("name"),
            "picture": google_data.get("picture"),
            "is_admin": is_admin,
            "avatar": None,
            "use_real_name": True,
            "anonymous_alias": generate_anonymous_alias(),
            "sponsor_id": None,
            "level": "sonhador",
            "contributed_to_main_trip": False,
            "valid_referrals_count": 0,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "embaixador_unlocked_at": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
    
    session_token = google_data.get("session_token")
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    response.set_cookie(
        key="session_token", value=session_token,
        httponly=True, secure=True, samesite="none", path="/", max_age=7*24*60*60
    )
    
    jwt_token = create_jwt_token(user_id, is_admin)
    return {
        "token": jwt_token,
        "user": {
            "user_id": user_id,
            "email": email,
            "name": google_data.get("name"),
            "picture": google_data.get("picture"),
            "is_admin": is_admin
        }
    }


@router.get("/auth/me")
async def get_me(request: Request):
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Não autenticado")
    return user.model_dump()


@router.post("/auth/logout")
async def logout(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    response.delete_cookie("session_token", path="/", secure=True, samesite="none")
    return {"message": "Logout realizado com sucesso"}



@router.put("/auth/change-password")
async def change_password(request: Request):
    """Change password for authenticated user"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    user = await require_auth(request)
    data = await request.json()
    current_password = data.get("current_password")
    new_password = data.get("new_password")

    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Password atual e nova são obrigatórias")

    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="A nova password deve ter pelo menos 6 caracteres")

    user_doc = await db.users.find_one({"user_id": user.user_id})
    if not user_doc or not user_doc.get("password_hash"):
        raise HTTPException(status_code=400, detail="Utilizador sem password definida")

    if not pwd_context.verify(current_password, user_doc["password_hash"]):
        raise HTTPException(status_code=403, detail="Password atual incorreta")

    new_hash = pwd_context.hash(new_password)
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"password_hash": new_hash}}
    )

    return {"message": "Password alterada com sucesso"}
