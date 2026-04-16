"""
Admin routes — stats, user management, email admin, settings, gallery, audit logs.
"""
from fastapi import APIRouter, HTTPException, Request
from typing import Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import uuid

from config import (
    db, logger, FRONTEND_URL, ADMIN_EMAIL
)
from auth import get_current_user, require_auth, require_admin
from email_service import (
    get_email_base_template, send_email_resend,
    send_weekly_summary_emails, send_dream_funded_announcement,
    send_new_journey_email,
    _build_email_cta_button, _build_standard_email
)
from services.audit_service import log_admin_action, get_audit_logs

router = APIRouter()


# ==================== ADMIN STATS ====================

@router.get("/admin/stats")
async def get_admin_stats(request: Request):
    await require_admin(request)

    total_contributions = await db.contributions.count_documents({"status": "completed"})
    total_amount = 0
    contributions = await db.contributions.find({"status": "completed"}, {"_id": 0}).to_list(10000)
    for c in contributions:
        total_amount += c.get("amount", 0)

    total_users = await db.users.count_documents({})
    total_journeys = await db.journeys.count_documents({})

    return {
        "total_contributions": total_contributions,
        "total_amount_raised": total_amount,
        "total_users": total_users,
        "total_journeys": total_journeys
    }


# ==================== SITE SETTINGS ====================

@router.get("/settings")
async def get_site_settings():
    """Get public site settings"""
    settings = await db.site_settings.find_one({"setting_id": "main"}, {"_id": 0})
    if not settings:
        return {
            "contact_email": "contacto@4luis.com",
            "contact_message": "Tem alguma questão? Entre em contacto connosco."
        }
    return {
        "contact_email": settings.get("contact_email", "contacto@4luis.com"),
        "contact_message": settings.get("contact_message", "Tem alguma questão? Entre em contacto connosco.")
    }


@router.put("/admin/settings")
async def update_site_settings(request: Request):
    """Update site settings (admin only)"""
    admin = await require_admin(request)
    data = await request.json()

    await db.site_settings.update_one(
        {"setting_id": "main"},
        {"$set": {
            "setting_id": "main",
            "contact_email": data.get("contact_email"),
            "contact_message": data.get("contact_message"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )

    await log_admin_action(admin.user_id, "settings_updated", "settings", "main", {
        "fields": list(data.keys())
    })

    return {"message": "Configurações atualizadas com sucesso"}


@router.get("/admin/settings")
async def get_admin_settings(request: Request):
    """Get all site settings (admin only)"""
    await require_admin(request)
    settings = await db.site_settings.find_one({"setting_id": "main"}, {"_id": 0})
    if not settings:
        return {
            "contact_email": "contacto@4luis.com",
            "contact_message": "Tem alguma questão? Entre em contacto connosco."
        }
    return settings


# ==================== DREAMERS STATS ====================

@router.get("/dreamers-stats")
async def get_dreamers_stats():
    """Get anonymous stats for the Dreamers community"""
    total_users = await db.users.count_documents({})
    total_contributions = await db.contributions.count_documents({"status": {"$in": ["confirmed", "completed"]}})
    unique_contributors = len(await db.contributions.distinct("contributor_email", {"status": {"$in": ["confirmed", "completed"]}}))

    ambassadors = await db.users.count_documents({"level": "embaixador"})
    total_referred = await db.users.count_documents({"sponsor_id": {"$ne": None}})

    active_journeys = await db.journeys.count_documents({"status": "ativa", "is_active": True})
    funded_journeys = await db.journeys.count_documents({"status": {"$in": ["financiada", "realizada"]}})

    pipeline = [
        {"$match": {"status": {"$in": ["confirmed", "completed"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    result = await db.contributions.aggregate(pipeline).to_list(1)
    total_raised = result[0]["total"] if result else 0

    display_contributors = unique_contributors + 57
    display_total = total_users + 57

    top_dreamer = None
    top_pipeline = [
        {"$match": {"status": {"$in": ["confirmed", "completed"]}, "user_id": {"$ne": None}}},
        {"$group": {"_id": "$user_id", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}},
        {"$limit": 1}
    ]
    top_result = await db.contributions.aggregate(top_pipeline).to_list(1)
    if top_result:
        top_user = await db.users.find_one({"user_id": top_result[0]["_id"]}, {"_id": 0})
        if top_user:
            use_real = top_user.get("use_real_name", True)
            top_dreamer = {
                "display_name": top_user.get("name", "Sonhador") if use_real else (top_user.get("anonymous_alias") or "Sonhador"),
                "avatar": top_user.get("avatar") or top_user.get("anonymous_avatar"),
                "total_contributed": top_result[0]["total"],
                "contributions_count": top_result[0]["count"]
            }

    return {
        "community_size": display_total,
        "unique_contributors": display_contributors,
        "total_contributions": total_contributions,
        "total_raised": total_raised,
        "ambassadors_count": ambassadors,
        "total_referred": total_referred,
        "active_journeys": active_journeys,
        "funded_journeys": funded_journeys,
        "top_dreamer": top_dreamer
    }


# ==================== ADMIN USER MANAGEMENT ====================

@router.put("/admin/users/{user_id}/subscription")
async def toggle_user_subscription(user_id: str, request: Request):
    """Toggle subscription_active for a user"""
    admin = await require_admin(request)

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    new_status = not user.get("subscription_active", False)
    update_data = {"subscription_active": new_status}

    if new_status and user.get("valid_referrals_count", 0) >= 3:
        update_data["level"] = "premium"
        update_data["premium_unlocked_at"] = datetime.now(timezone.utc).isoformat()
    elif not new_status and user.get("level") == "premium":
        update_data["level"] = "sonhador" if user.get("valid_referrals_count", 0) >= 1 else "curioso"

    await db.users.update_one({"user_id": user_id}, {"$set": update_data})

    await log_admin_action(admin.user_id, "subscription_toggled", "user", user_id, {
        "new_status": new_status, "level": update_data.get("level", user.get("level"))
    })

    return {
        "message": f"Subscrição {'ativada' if new_status else 'desativada'}",
        "subscription_active": new_status,
        "level": update_data.get("level", user.get("level", "curioso"))
    }


@router.get("/admin/users/dashboard")
async def get_users_dashboard(request: Request):
    """Get comprehensive users dashboard with metrics and insights"""
    await require_admin(request)

    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    all_contributions = await db.contributions.find({"status": "completed"}, {"_id": 0}).to_list(10000)

    user_contributions = {}
    for contrib in all_contributions:
        uid = contrib.get("user_id")
        if uid:
            if uid not in user_contributions:
                user_contributions[uid] = {"total": 0, "count": 0}
            user_contributions[uid]["total"] += contrib.get("amount", 0)
            user_contributions[uid]["count"] += 1

    sponsor_impact = {}
    for user in users:
        if user.get("sponsor_id"):
            sid = user["sponsor_id"]
            if sid not in sponsor_impact:
                sponsor_impact[sid] = {"value": 0, "referrals": []}
            uc = user_contributions.get(user["user_id"], {"total": 0})
            sponsor_impact[sid]["value"] += uc["total"]
            sponsor_impact[sid]["referrals"].append({
                "user_id": user["user_id"], "name": user.get("name"), "contributed": uc["total"]
            })

    enriched_users = []
    for user in users:
        uid = user["user_id"]
        sponsor_name = None
        if user.get("sponsor_id"):
            sp = await db.users.find_one({"user_id": user["sponsor_id"]}, {"_id": 0, "name": 1, "email": 1})
            sponsor_name = sp.get("name") if sp else "Desconhecido"
        referrals_made = await db.users.count_documents({"sponsor_id": uid})
        contribs = user_contributions.get(uid, {"total": 0, "count": 0})
        impact = sponsor_impact.get(uid, {"value": 0, "referrals": []})

        enriched_users.append({
            "user_id": uid, "name": user.get("name"), "email": user.get("email"),
            "alias": user.get("alias"), "avatar": user.get("avatar"),
            "level": user.get("level", "curioso"),
            "subscription_active": user.get("subscription_active", False),
            "valid_referrals_count": user.get("valid_referrals_count", 0),
            "referrals_made": referrals_made,
            "contributions_total": contribs["total"], "contributions_count": contribs["count"],
            "sponsor_id": user.get("sponsor_id"), "sponsor_name": sponsor_name,
            "sponsor_impact_value": impact["value"], "invited_users": impact["referrals"],
            "registered_at": user.get("registered_at") or user.get("created_at"),
            "premium_unlocked_at": user.get("premium_unlocked_at"),
            "is_admin": user.get("is_admin", False)
        })

    enriched_users.sort(key=lambda x: (x["valid_referrals_count"], x["sponsor_impact_value"]), reverse=True)

    now = datetime.now(timezone.utc)
    week_ago_iso = (now - timedelta(days=7)).isoformat()
    month_ago_iso = (now - timedelta(days=30)).isoformat()

    total_users = len(users)
    active_subscriptions = sum(1 for u in users if u.get("subscription_active"))
    premium_users = sum(1 for u in users if u.get("level") == "premium")
    sonhador_users = sum(1 for u in users if u.get("level") == "sonhador")
    curioso_users = sum(1 for u in users if u.get("level") == "curioso")
    active_user_ids = set(c.get("user_id") for c in all_contributions if c.get("created_at", "") >= month_ago_iso)
    active_users = len(active_user_ids)
    weekly_signups = sum(1 for u in users if (u.get("registered_at") or u.get("created_at", "")) >= week_ago_iso)
    total_contributions_value = sum(c.get("amount", 0) for c in all_contributions)
    total_contributions_count = len(all_contributions)
    average_contribution_value = total_contributions_value / total_contributions_count if total_contributions_count > 0 else 0
    valid_referrals_total = sum(u.get("valid_referrals_count", 0) for u in users)
    weekly_contributions = sum(1 for c in all_contributions if c.get("created_at", "") >= week_ago_iso)

    all_journeys = await db.journeys.find({}, {"_id": 0}).to_list(100)
    journeys_funded = sum(1 for j in all_journeys if j.get("status") == "funded")
    journeys_active = sum(1 for j in all_journeys if j.get("status") == "active")

    top_sponsors = sorted(
        [{"user_id": uid, "name": next((u["name"] for u in users if u["user_id"] == uid), "?"),
          "impact_value": d["value"], "referrals_count": len(d["referrals"])}
         for uid, d in sponsor_impact.items() if d["value"] > 0],
        key=lambda x: x["impact_value"], reverse=True
    )[:5]

    top_contributors = sorted(
        [{"user_id": u["user_id"], "name": u["name"],
          "total_contributed": u["contributions_total"], "contributions_count": u["contributions_count"]}
         for u in enriched_users if u["contributions_total"] > 0],
        key=lambda x: x["total_contributed"], reverse=True
    )[:5]

    momentum_score = weekly_signups + weekly_contributions + valid_referrals_total

    def _monthly_counts(dates):
        c = defaultdict(int)
        for d in dates:
            if d:
                try:
                    c[d[:7]] += 1
                except:
                    pass
        return [{"month": k, "count": v} for k, v in sorted(c.items())[-12:]]

    def _monthly_contribs(contribs):
        m = defaultdict(lambda: {"count": 0, "amount": 0})
        for c in contribs:
            d = c.get("created_at", "")
            if d:
                try:
                    m[d[:7]]["count"] += 1
                    m[d[:7]]["amount"] += c.get("amount", 0)
                except:
                    pass
        return [{"month": k, "count": v["count"], "amount": v["amount"]} for k, v in sorted(m.items())[-12:]]

    referrals_by_month = []
    for u in users:
        reg = u.get("registered_at") or u.get("created_at", "")
        if reg and u.get("sponsor_id"):
            mk = reg[:7]
            ex = next((r for r in referrals_by_month if r["month"] == mk), None)
            if ex:
                ex["count"] += 1
            else:
                referrals_by_month.append({"month": mk, "count": 1})
    referrals_by_month.sort(key=lambda x: x["month"])

    return {
        "metrics": {
            "total_users": total_users, "active_users": active_users,
            "active_subscriptions": active_subscriptions,
            "premium_users": premium_users, "sonhador_users": sonhador_users, "curioso_users": curioso_users,
            "total_contributions_value": total_contributions_value,
            "total_contributions_count": total_contributions_count,
            "average_contribution_value": round(average_contribution_value, 2),
            "total_sponsor_impact": sum(s["value"] for s in sponsor_impact.values()),
            "weekly_signups": weekly_signups, "weekly_contributions": weekly_contributions,
            "valid_referrals_total": valid_referrals_total,
            "journeys_funded": journeys_funded, "journeys_active": journeys_active,
            "momentum_score": momentum_score
        },
        "level_distribution": {"curioso": curioso_users, "sonhador": sonhador_users, "premium": premium_users},
        "charts": {
            "signups_by_month": _monthly_counts([u.get("registered_at") or u.get("created_at") for u in users]),
            "contributions_by_month": _monthly_contribs(all_contributions),
            "referrals_by_month": referrals_by_month[-12:]
        },
        "top_sponsors": top_sponsors,
        "top_contributors": top_contributors,
        "users": enriched_users
    }


@router.get("/admin/users/{user_id}/detail")
async def get_user_detail(user_id: str, request: Request):
    """Get detailed user profile with full history"""
    await require_admin(request)
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    contributions = await db.contributions.find({"user_id": user_id}, {"_id": 0}).to_list(1000)
    sponsor_links = await db.sponsor_links.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    invited_users = await db.users.find(
        {"sponsor_id": user_id},
        {"_id": 0, "user_id": 1, "name": 1, "email": 1, "created_at": 1, "level": 1}
    ).to_list(1000)

    sponsor_info = None
    if user.get("sponsor_id"):
        sponsor_info = await db.users.find_one(
            {"user_id": user["sponsor_id"]}, {"_id": 0, "user_id": 1, "name": 1, "email": 1}
        )

    impact_value = 0
    for inv in invited_users:
        ic = await db.contributions.find(
            {"user_id": inv["user_id"], "status": "completed"}, {"_id": 0, "amount": 1}
        ).to_list(1000)
        inv["contributions_total"] = sum(c.get("amount", 0) for c in ic)
        impact_value += inv["contributions_total"]

    return {
        "user": user, "contributions": contributions,
        "contributions_total": sum(c.get("amount", 0) for c in contributions if c.get("status") == "completed"),
        "sponsor_links": sponsor_links, "sponsor_info": sponsor_info,
        "invited_users": invited_users, "sponsor_impact_value": impact_value
    }


@router.put("/admin/users/{user_id}/level")
async def update_user_level(user_id: str, request: Request):
    """Manually update user level"""
    admin = await require_admin(request)
    data = await request.json()
    new_level = data.get("level")

    if new_level not in ["sonhador", "verificado", "embaixador"]:
        raise HTTPException(status_code=400, detail="Nível inválido. Use: sonhador, verificado, embaixador")

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizador não encontrado")

    old_level = user.get("level", "sonhador")
    update_data = {"level": new_level}
    if new_level == "embaixador" and not user.get("embaixador_unlocked_at"):
        update_data["embaixador_unlocked_at"] = datetime.now(timezone.utc).isoformat()

    await db.users.update_one({"user_id": user_id}, {"$set": update_data})

    await log_admin_action(admin.user_id, "user_level_changed", "user", user_id, {
        "old_level": old_level, "new_level": new_level
    })

    return {"message": f"Nível atualizado para {new_level}", "level": new_level}


@router.put("/admin/users/{user_id}/referrals")
async def update_user_referrals(user_id: str, request: Request):
    """Manually correct user's valid_referrals_count"""
    admin = await require_admin(request)
    data = await request.json()
    new_count = data.get("valid_referrals_count")

    if not isinstance(new_count, int) or new_count < 0:
        raise HTTPException(status_code=400, detail="Contagem inválida")

    await db.users.update_one({"user_id": user_id}, {"$set": {"valid_referrals_count": new_count}})

    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if user and user.get("subscription_active") and new_count >= 3 and user.get("level") != "premium":
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"level": "premium", "premium_unlocked_at": datetime.now(timezone.utc).isoformat()}}
        )

    await log_admin_action(admin.user_id, "user_referrals_changed", "user", user_id, {
        "new_count": new_count
    })

    return {"message": f"Referrals atualizados para {new_count}", "valid_referrals_count": new_count}


@router.get("/admin/users")
async def get_all_users(request: Request):
    """Get all users with their sponsor/premium status"""
    await require_admin(request)
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)

    for user in users:
        if user.get("sponsor_id"):
            sp = await db.users.find_one({"user_id": user["sponsor_id"]}, {"_id": 0, "name": 1, "email": 1})
            user["sponsor_name"] = sp.get("name") if sp else "Desconhecido"
        referrals = await db.users.count_documents({"sponsor_id": user["user_id"]})
        user["referrals_made"] = referrals

    return {"total_users": len(users), "users": users}


@router.post("/admin/migrate-users")
async def migrate_existing_users(request: Request):
    """Add new fields to existing users (one-time migration)"""
    await require_admin(request)

    result = await db.users.update_many(
        {"level": {"$exists": False}},
        {"$set": {
            "sponsor_id": None, "level": "curioso", "subscription_active": False,
            "valid_referrals_count": 0, "registered_at": None, "premium_unlocked_at": None
        }}
    )
    journey_result = await db.journeys.update_many(
        {"status": {"$exists": False}},
        {"$set": {"status": "active", "owner_user_id": None}}
    )

    return {
        "users_migrated": result.modified_count,
        "journeys_migrated": journey_result.modified_count,
        "message": "Migração concluída"
    }


# ==================== ADMIN EMAIL ROUTES ====================

@router.get("/admin/emails")
async def get_email_queue(request: Request, status: Optional[str] = None, limit: int = 50):
    """Get email queue"""
    await require_admin(request)
    query = {}
    if status:
        query["status"] = status
    emails = await db.email_queue.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    total = await db.email_queue.count_documents({})
    sent = await db.email_queue.count_documents({"status": "sent"})
    queued = await db.email_queue.count_documents({"status": "queued"})
    failed = await db.email_queue.count_documents({"status": "failed"})
    return {"emails": emails, "stats": {"total": total, "sent": sent, "queued": queued, "failed": failed}}


@router.post("/admin/test-email")
async def test_email_send(request: Request):
    """Test email sending"""
    await require_admin(request)
    data = await request.json()
    test_email = data.get("to_email", data.get("email", ADMIN_EMAIL))
    content = f"""
    <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px;">Teste de Email 4Luis</h1>
    <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; line-height: 1.6;">
        Este é um email de teste para verificar a integração do Resend.
    </p>
    <div style="background-color: #E6F4F1; border-radius: 12px; padding: 24px; text-align: center;">
        <p style="margin: 0; color: #2D2A26;">Timestamp: {datetime.now(timezone.utc).isoformat()}</p>
    </div>
    """
    html = get_email_base_template(content, "Teste Email - 4Luis")
    result = await send_email_resend(to_email=test_email, subject="Teste de Email - 4Luis", html_content=html)
    return {"message": f"Email de teste enviado para {test_email}", "result": result}


@router.get("/admin/sponsors-report")
async def get_sponsors_report(request: Request):
    """Get report of sponsors who have 3+ successful referrals"""
    await require_admin(request)
    sponsors = await db.sponsor_links.find({"successful_referrals": {"$gte": 3}}, {"_id": 0}).to_list(1000)

    report = []
    for sponsor in sponsors:
        user = await db.users.find_one({"user_id": sponsor["user_id"]}, {"_id": 0, "name": 1, "email": 1, "alias": 1})
        journey = await db.journeys.find_one({"journey_id": sponsor["journey_id"]}, {"_id": 0, "name": 1})
        points = await db.points.find({"user_id": sponsor["user_id"]}, {"_id": 0}).to_list(1000)
        total_points = sum(p.get("points_value", 1) for p in points)

        report.append({
            "user_id": sponsor["user_id"],
            "user_name": user.get("name") if user else "Desconhecido",
            "user_email": user.get("email") if user else "",
            "alias": user.get("alias") if user else None,
            "journey_name": journey.get("name") if journey else "Desconhecida",
            "successful_referrals": sponsor["successful_referrals"],
            "total_referrals": sponsor["referral_count"],
            "total_points": total_points,
            "registration_numbers": [p["point_id"] for p in points],
            "created_at": sponsor.get("created_at")
        })

    report.sort(key=lambda x: x["total_points"], reverse=True)
    return {"total_qualified_sponsors": len(report), "sponsors": report}


@router.post("/admin/emails/weekly-summary")
async def trigger_weekly_summary(request: Request):
    """Send weekly progress summary email to all users"""
    await require_admin(request)
    result = await send_weekly_summary_emails()
    return {"message": "Resumo semanal enviado", **result}


@router.get("/admin/emails/preview/weekly-summary")
async def preview_weekly_summary(request: Request):
    """Preview weekly summary email"""
    await require_admin(request)
    active_journeys = await db.journeys.find({"status": "ativa", "is_active": True}, {"_id": 0}).to_list(50)

    journeys_html = ""
    for j in active_journeys:
        pct = round((j.get("current_amount", 0) / j.get("goal_amount", 1)) * 100, 1) if j.get("goal_amount", 0) > 0 else 0
        pct_int = int(min(pct, 100))
        journey_url = f"{FRONTEND_URL}/journey/{j['journey_id']}"
        journeys_html += f"""
        <div style="background: #FFF8F3; border-radius: 12px; padding: 20px; margin-bottom: 16px;">
            <p style="color: #2D2A26; font-size: 18px; font-weight: bold; margin: 0 0 4px 0;">{j.get('name', '')}</p>
            <p style="color: #FFBE98; font-style: italic; font-size: 14px; margin: 0 0 12px 0;">{j.get('poetic_name', '')}</p>
            <div style="background: #E7E5E4; border-radius: 8px; height: 10px; overflow: hidden; margin-bottom: 8px;">
                <div style="background: linear-gradient(90deg, #FFBE98, #F2C94C); height: 100%; width: {pct_int}%; border-radius: 8px;"></div>
            </div>
            <p style="color: #2D2A26; font-size: 14px; font-weight: bold; margin: 0 0 12px 0;">{pct}% financiado</p>
            <a href="{journey_url}" style="color: #FFBE98; font-size: 14px; font-weight: bold; text-decoration: none;">Ver este sonho &rarr;</a>
        </div>
        """

    body = f"""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px;">Resumo Semanal dos Sonhos</h1>
        <p style="color: #6B6661; font-size: 16px; line-height: 1.8; margin-bottom: 24px;">
            Aqui esta o progresso dos sonhos que estamos a construir juntos esta semana.
        </p>
        {journeys_html}
        {_build_email_cta_button(FRONTEND_URL, "Explorar todos os sonhos")}
    </div>
    """
    html = get_email_base_template(body, "Resumo Semanal - 4Luis")
    users = await db.users.find({"email": {"$exists": True, "$ne": ""}}, {"_id": 0, "email": 1}).to_list(500)
    recipient_count = sum(1 for u in users if u.get("email") and "@" in u["email"] and not u["email"].endswith("@test.com"))
    return {"subject": "Resumo semanal dos sonhos - 4Luis", "html": html, "recipient_count": recipient_count}


@router.get("/admin/emails/preview/dream-funded/{journey_id}")
async def preview_dream_funded(journey_id: str, request: Request):
    """Preview dream funded email"""
    await require_admin(request)
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem nao encontrada")
    journey_name = journey.get("name", "")
    poetic_name = journey.get("poetic_name", "")
    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    percentage = round((current_amount / goal_amount) * 100, 1) if goal_amount > 0 else 100
    journey_url = f"{FRONTEND_URL}/journey/{journey_id}"
    contributors = await db.contributions.find({"journey_id": journey_id, "status": "completed"}, {"_id": 0}).to_list(500)
    body = _build_standard_email(
        title="Este sonho tornou-se realidade!",
        narrative=f"""A viagem &ldquo;<strong>{poetic_name or journey_name}</strong>&rdquo; acaba de ser totalmente financiada.<br><br>
        Gracas a <strong>{len(contributors)} sonhadores</strong> que acreditaram, este sonho vai acontecer.""",
        percentage=percentage, cta_url=journey_url, cta_text="Ver este sonho realizado"
    )
    html = get_email_base_template(body, f"Sonho Realizado: {journey_name} - 4Luis")
    users = await db.users.find({"email": {"$exists": True, "$ne": ""}}, {"_id": 0, "email": 1}).to_list(500)
    recipient_count = sum(1 for u in users if u.get("email") and "@" in u["email"] and not u["email"].endswith("@test.com"))
    return {"subject": f"O sonho da {journey_name} tornou-se realidade!", "html": html, "recipient_count": recipient_count}


@router.get("/admin/emails/preview/new-journey/{journey_id}")
async def preview_new_journey(journey_id: str, request: Request):
    """Preview new journey announcement email"""
    await require_admin(request)
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem nao encontrada")
    journey_name = journey.get("name", "")
    poetic_name = journey.get("poetic_name", "")
    description = journey.get("description", "")
    ambassador_name = journey.get("ambassador_name", "")
    journey_url = f"{FRONTEND_URL}/journey/{journey_id}"
    ambassador_line = f"<br>Sonho de <strong>{ambassador_name}</strong>" if ambassador_name else ""
    body = _build_standard_email(
        title=f"Novo sonho: {journey_name}",
        narrative=f"""Um novo sonho acabou de chegar a plataforma 4Luis.<br><br>
        &ldquo;<em>{poetic_name or description}</em>&rdquo;{ambassador_line}<br><br>
        Cada sonho comeca com um primeiro passo. Sera que este vai ser o teu?""",
        percentage=0, cta_url=journey_url, cta_text="Descobrir este sonho"
    )
    html = get_email_base_template(body, f"Novo Sonho: {journey_name} - 4Luis")
    users = await db.users.find({"email": {"$exists": True, "$ne": ""}}, {"_id": 0, "email": 1}).to_list(500)
    recipient_count = sum(1 for u in users if u.get("email") and "@" in u["email"] and not u["email"].endswith("@test.com"))
    return {"subject": f"Novo sonho na 4Luis: {journey_name}", "html": html, "recipient_count": recipient_count}


@router.post("/admin/emails/dream-funded/{journey_id}")
async def trigger_dream_funded_email(journey_id: str, request: Request):
    """Send dream funded announcement email"""
    admin = await require_admin(request)
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    await db.journeys.update_one(
        {"journey_id": journey_id},
        {"$set": {"status": "financiada", "funded_at": datetime.now(timezone.utc).isoformat(),
                  "funded_email_sent": True, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    await log_admin_action(admin.user_id, "dream_funded_email_sent", "journey", journey_id, {})
    result = await send_dream_funded_announcement(journey)
    return {"message": f"Email de sonho financiado enviado para {result['sent']} utilizadores", **result}


@router.post("/admin/emails/new-journey/{journey_id}")
async def trigger_new_journey_email(journey_id: str, request: Request):
    """Send new journey announcement email"""
    admin = await require_admin(request)
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        raise HTTPException(status_code=404, detail="Viagem não encontrada")
    result = await send_new_journey_email(journey)
    await db.journeys.update_one({"journey_id": journey_id}, {"$set": {"announcement_email_sent": True}})
    await log_admin_action(admin.user_id, "new_journey_email_sent", "journey", journey_id, {})
    return {"message": f"Email de novo sonho enviado para {result['sent']} utilizadores", **result}


# ==================== TRIP GALLERY ====================

@router.get("/gallery")
async def get_trip_gallery():
    photos = await db.trip_photos.find({"is_approved": True}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return photos


@router.post("/gallery/upload")
async def upload_trip_photo(request: Request):
    user = await require_auth(request)
    data = await request.json()
    raffle = await db.raffle_results.find_one({"winner_user_id": user.user_id}, {"_id": 0})
    if not raffle:
        raise HTTPException(status_code=403, detail="Apenas vencedores de sorteios podem adicionar fotos")
    photo_doc = {
        "photo_id": f"photo_{uuid.uuid4().hex[:12]}", "user_id": user.user_id,
        "journey_id": data.get("journey_id"), "image_url": data.get("image_url"),
        "caption": data.get("caption", ""), "location": data.get("location", ""),
        "is_approved": True, "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.trip_photos.insert_one(photo_doc)
    return {"message": "Foto adicionada com sucesso", "photo_id": photo_doc["photo_id"]}


@router.get("/admin/gallery")
async def get_all_gallery_photos(request: Request):
    await require_admin(request)
    return await db.trip_photos.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)


@router.put("/admin/gallery/{photo_id}/approve")
async def approve_gallery_photo(photo_id: str, request: Request):
    await require_admin(request)
    await db.trip_photos.update_one({"photo_id": photo_id}, {"$set": {"is_approved": True}})
    return {"message": "Foto aprovada"}


@router.delete("/admin/gallery/{photo_id}")
async def delete_gallery_photo(photo_id: str, request: Request):
    await require_admin(request)
    await db.trip_photos.delete_one({"photo_id": photo_id})
    return {"message": "Foto eliminada"}


# ==================== AUDIT LOG ENDPOINT ====================

@router.get("/admin/audit-logs")
async def get_admin_audit_logs(request: Request, target_type: Optional[str] = None, limit: int = 100):
    """Get audit logs of admin actions"""
    await require_admin(request)
    logs = await get_audit_logs(limit=limit, target_type=target_type)
    return {"count": len(logs), "logs": logs}
