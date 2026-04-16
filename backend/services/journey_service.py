"""
Journey service — business logic for funding status, story chapters, visibility scoring.
These functions are shared between journey routes and payment/contribution routes.
"""
from datetime import datetime, timezone, timedelta
import uuid

from config import db, logger, FRONTEND_URL
from email_service import (
    get_email_base_template, send_email_resend,
    send_journey_funded_emails
)


# ==================== STORY CHAPTERS ====================

DEFAULT_STORY_CHAPTERS = {
    "1": {"title": "O sonho nasce", "lines": ["Um sonho de atravessar terras distantes,", "de descobrir culturas e paisagens novas.", "", "Esta jornada começa aqui."]},
    "2": {"title": "O sonho ganha forma", "lines": ["Cada contribuição aproxima esta viagem da realidade.", "", "A comunidade já começou a construir este sonho."]},
    "3": {"title": "O sonho está a caminho", "lines": ["A jornada começa a ganhar forma.", "", "A rota começa a desenhar-se entre cidades", "e paisagens milenares."]},
    "4": {"title": "O sonho quase acontece", "lines": ["A viagem está cada vez mais próxima.", "", "Em breve esta história deixará de ser apenas um sonho."]},
    "5": {"title": "O sonho torna-se realidade", "lines": ["A comunidade tornou este sonho possível.", "", "Agora começa a verdadeira aventura."]}
}


def get_chapter_number(percentage: float) -> int:
    """Get story chapter number based on funding percentage"""
    if percentage >= 100:
        return 5
    if percentage >= 75:
        return 4
    if percentage >= 50:
        return 3
    if percentage >= 25:
        return 2
    return 1


def _build_chapter_email_body(poetic_name, chapter_num, chapter_title, chapter_text, percentage, remaining_text, journey_url):
    """Build the HTML body for chapter change emails"""
    pct_int = int(min(percentage, 100))
    filled_blocks = max(1, pct_int // 5)
    empty_blocks = 20 - filled_blocks
    progress_bar_text = "█" * filled_blocks + "░" * empty_blocks

    return f"""
        <div style="text-align: center; padding: 20px 0;">
            <p style="color: #6B6661; font-size: 16px; line-height: 1.6;">
                O sonho da viagem "<strong>{poetic_name}</strong>"<br>
                acabou de entrar numa nova fase.
            </p>
            <div style="background: #FFF8F3; border-radius: 16px; padding: 24px; margin: 24px 0; border-left: 4px solid #FFBE98;">
                <p style="color: #6B6661; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">
                    Capítulo {chapter_num}
                </p>
                <p style="color: #FFBE98; font-size: 22px; font-style: italic; margin-bottom: 12px;">
                    {chapter_title}
                </p>
                <p style="color: #6B6661; font-size: 14px; line-height: 1.8;">
                    {chapter_text}
                </p>
            </div>
            <div style="background: #F5F5F4; border-radius: 16px; padding: 20px; margin: 20px 0;">
                <p style="color: #6B6661; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;">
                    Progresso atual da viagem
                </p>
                <div style="background: #E7E5E4; border-radius: 8px; height: 12px; overflow: hidden; margin-bottom: 8px;">
                    <div style="background: linear-gradient(90deg, #FFBE98, #F2C94C); height: 100%; width: {pct_int}%; border-radius: 8px;"></div>
                </div>
                <p style="font-family: monospace; color: #6B6661; font-size: 12px; letter-spacing: 1px; margin-bottom: 4px;">
                    {progress_bar_text}
                </p>
                <p style="color: #2D2A26; font-size: 18px; font-weight: bold;">
                    {percentage}% financiado
                </p>
                {remaining_text}
            </div>
            <p style="color: #6B6661; font-size: 14px; margin-bottom: 20px;">
                Se quiseres ajudar a dar o próximo passo:
            </p>
            <a href="{journey_url}" style="display: inline-block; background: #FFBE98; color: #2D2A26; padding: 14px 28px; border-radius: 12px; font-weight: bold; text-decoration: none; font-size: 16px;">
                Contribuir para este sonho
            </a>
        </div>
    """


async def send_chapter_change_emails(journey: dict, chapter_num: int):
    """Send email to all users when a journey enters a new chapter"""
    chapters = journey.get("story_chapters") or DEFAULT_STORY_CHAPTERS
    chapter = chapters.get(str(chapter_num), DEFAULT_STORY_CHAPTERS.get(str(chapter_num)))

    if not chapter:
        return

    journey_name = journey.get("name", "")
    poetic_name = journey.get("poetic_name", "")
    journey_id = journey.get("journey_id", "")
    chapter_title = chapter.get("title", "")
    chapter_lines = chapter.get("lines", [])
    chapter_text = "<br>".join(line if line else "<br>" for line in chapter_lines)

    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    percentage = round((current_amount / goal_amount) * 100, 1) if goal_amount > 0 else 0

    next_milestones = {1: 25, 2: 50, 3: 75, 4: 100}
    next_milestone = next_milestones.get(chapter_num)
    remaining_text = ""
    if next_milestone and percentage < next_milestone:
        remaining = round(next_milestone - percentage, 1)
        remaining_text = f'<p style="color: #FFBE98; font-size: 14px; font-style: italic; margin-top: 12px;">Faltam {remaining}% para o próximo capítulo do sonho.</p>'

    journey_url = f"{FRONTEND_URL}/journey/{journey_id}"
    subject = f'O sonho da {journey_name} entrou numa nova fase'

    html_content = get_email_base_template(_build_chapter_email_body(
        poetic_name, chapter_num, chapter_title, chapter_text,
        percentage, remaining_text, journey_url
    ), title=f"4Luis — Capítulo {chapter_num}")

    # Get all users with email
    users = await db.users.find({"email": {"$exists": True, "$ne": ""}}, {"_id": 0, "email": 1}).to_list(500)

    sent_count = 0
    for user_doc in users:
        email = user_doc.get("email", "")
        if email and "@" in email and not email.endswith("@test.com"):
            try:
                await send_email_resend(email, subject, html_content)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send chapter email to {email}: {e}")

    logger.info(f"Chapter {chapter_num} emails sent to {sent_count} users for journey {journey.get('journey_id')}")


# ==================== FUNDING STATUS ====================

async def check_and_update_journey_funding_status(journey_id: str):
    """Check if journey reached funding goal and update status based on journey type.
    - Main journey (is_main_trip): sets funding_status to 'pending_validation', notifies admin
    - Ambassador journeys: sets funding_status to 'completed' automatically (no manual validation)
    Both types continue to accept contributions after reaching 100%.
    """
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        return None

    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    current_funding_status = journey.get("funding_status", "active")

    # Skip if already completed or pending_validation
    if current_funding_status in ("completed", "pending_validation"):
        return current_funding_status

    # Check if funded (100%+)
    if current_amount >= goal_amount:
        now_iso = datetime.now(timezone.utc).isoformat()
        is_main = journey.get("is_main_trip", False)
        is_ambassador = journey.get("is_ambassador_journey", False)

        if is_main and not is_ambassador:
            # ── MAIN JOURNEY: pending admin validation ──
            new_status = "pending_validation"
            await db.journeys.update_one(
                {"journey_id": journey_id},
                {"$set": {
                    "funding_status": new_status,
                    "funded_at": now_iso,
                    "updated_at": now_iso
                }}
            )
            # Notify admin
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "type": "main_journey_funded",
                "title": "Viagem Principal atingiu 100%!",
                "message": f"A viagem principal '{journey.get('name')}' atingiu o objetivo. Aguarda a tua validação para ativar a celebração.",
                "journey_id": journey_id,
                "for_admin": True,
                "read": False,
                "created_at": now_iso
            })
            logger.info(f"Main journey {journey_id} reached 100% — set to pending_validation")
        else:
            # ── AMBASSADOR JOURNEY: auto-complete ──
            new_status = "completed"
            await db.journeys.update_one(
                {"journey_id": journey_id},
                {"$set": {
                    "funding_status": new_status,
                    "status": "financiada",
                    "funded_at": now_iso,
                    "is_active": False,
                    "updated_at": now_iso
                }}
            )
            # Notify admin
            await db.notifications.insert_one({
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "type": "journey_funded",
                "title": "Viagem Financiada!",
                "message": f"A viagem '{journey.get('name')}' atingiu o objetivo de financiamento.",
                "journey_id": journey_id,
                "for_admin": True,
                "read": False,
                "created_at": now_iso
            })
            # Notify ambassador
            if journey.get("ambassador_user_id"):
                ambassador_user_id = journey["ambassador_user_id"]
                await db.notifications.insert_one({
                    "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                    "type": "your_journey_funded",
                    "title": "A tua viagem foi financiada!",
                    "message": f"Parabéns! A tua viagem '{journey.get('name')}' atingiu o objetivo de financiamento.",
                    "journey_id": journey_id,
                    "user_id": ambassador_user_id,
                    "read": False,
                    "created_at": now_iso
                })
                ambassador = await db.users.find_one({"user_id": ambassador_user_id}, {"_id": 0})
                await send_journey_funded_emails(journey, ambassador, current_amount)
            else:
                await send_journey_funded_emails(journey, None, current_amount)

            # ── Create payout record for ambassador ──
            if journey.get("ambassador_user_id"):
                existing_payout = await db.payouts.find_one({"journey_id": journey_id}, {"_id": 0})
                if not existing_payout:
                    payout_id = f"payout_{uuid.uuid4().hex[:12]}"
                    await db.payouts.insert_one({
                        "payout_id": payout_id,
                        "journey_id": journey_id,
                        "journey_name": journey.get("name", ""),
                        "ambassador_user_id": journey["ambassador_user_id"],
                        "ambassador_name": journey.get("ambassador_name", ""),
                        "amount": float(current_amount),
                        "goal_amount": float(goal_amount),
                        "status": "pending",
                        "payment_method": None,
                        "payment_reference": None,
                        "admin_notes": None,
                        "created_at": now_iso,
                        "updated_at": now_iso,
                        "completed_at": None
                    })
                    logger.info(f"Payout {payout_id} created for ambassador journey {journey_id}")

            logger.info(f"Ambassador journey {journey_id} auto-completed")

        return new_status

    return current_funding_status


async def check_and_update_story_chapter(journey_id: str):
    """Check if the journey has entered a new story chapter and send emails if needed"""
    journey = await db.journeys.find_one({"journey_id": journey_id}, {"_id": 0})
    if not journey:
        return

    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    percentage = (current_amount / goal_amount) * 100 if goal_amount > 0 else 0

    new_chapter = get_chapter_number(percentage)
    old_chapter = journey.get("current_chapter", 1)

    if new_chapter > old_chapter:
        # Check which milestone was crossed (25, 50, 75, 100)
        milestones = {2: "25", 3: "50", 4: "75", 5: "100"}
        milestone_key = milestones.get(new_chapter)

        # Check if email was already sent for this milestone
        chapters_sent = journey.get("chapters_emails_sent") or {}
        already_sent = chapters_sent.get(milestone_key, False) if milestone_key else False

        # Update the chapter and mark milestone as sent
        update_fields = {
            "current_chapter": new_chapter,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        if milestone_key:
            update_fields[f"chapters_emails_sent.{milestone_key}"] = True
            update_fields["last_milestone_reached"] = int(milestone_key)
            update_fields["last_milestone_at"] = datetime.now(timezone.utc).isoformat()

        await db.journeys.update_one(
            {"journey_id": journey_id},
            {"$set": update_fields}
        )

        logger.info(f"Journey {journey_id} moved from chapter {old_chapter} to {new_chapter}")

        # Send emails only if enabled AND not already sent for this milestone
        if journey.get("story_emails_enabled", True) and not already_sent:
            await send_chapter_change_emails(journey, new_chapter)
        elif already_sent:
            logger.info(f"Email for chapter {new_chapter} (milestone {milestone_key}%) already sent, skipping")


# ==================== VISIBILITY SCORING ====================

async def calculate_journey_visibility_score(journey: dict) -> float:
    """
    Calculate visibility score for a journey based on multiple criteria.
    Score components (all normalized to 0-100):
    - Funding progress (30%): Higher progress = higher visibility
    - Recent activity (25%): More recent contributions = higher visibility
    - Number of contributions (20%): More contributions = higher visibility
    - Ambassador social impact (15%): More referrals = higher visibility
    - Recency bonus (10%): Newer journeys get a slight boost
    """
    journey_id = journey.get("journey_id")

    # 1. Funding Progress (30%)
    goal = journey.get("goal_amount", 1)
    current = journey.get("current_amount", 0)
    funding_percentage = min((current / goal) * 100, 100) if goal > 0 else 0
    funding_score = funding_percentage * 0.30

    # 2. Recent Activity (25%) - Contributions in last 7 days
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    recent_contributions = await db.contributions.count_documents({
        "journey_id": journey_id,
        "status": {"$in": ["confirmed", "completed"]},
        "created_at": {"$gte": seven_days_ago}
    })
    activity_score = min(recent_contributions * 10, 100) * 0.25

    # 3. Total Contributions (20%)
    total_contributions = await db.contributions.count_documents({
        "journey_id": journey_id,
        "status": {"$in": ["confirmed", "completed"]}
    })
    contribution_score = min(total_contributions * 5, 100) * 0.20

    # 4. Ambassador Social Impact (15%)
    social_score = 0
    if journey.get("ambassador_user_id"):
        ambassador = await db.users.find_one(
            {"user_id": journey["ambassador_user_id"]},
            {"_id": 0, "valid_referrals_count": 1}
        )
        if ambassador:
            referrals = ambassador.get("valid_referrals_count", 0)
            social_score = min(referrals * 10, 100) * 0.15

    # 5. Recency Bonus (10%) - Decays over 30 days
    created_at = journey.get("created_at")
    if created_at:
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        days_old = (datetime.now(timezone.utc) - created_at).days
        recency_factor = max(0, (30 - days_old) / 30)
        recency_score = recency_factor * 100 * 0.10
    else:
        recency_score = 0

    # Calculate total score
    base_score = funding_score + activity_score + contribution_score + social_score + recency_score

    # Apply admin boost (-100 to +100)
    admin_boost = journey.get("visibility_boost", 0)
    final_score = max(0, min(200, base_score + admin_boost))

    # Featured journeys get +100 bonus
    if journey.get("is_featured"):
        final_score += 100

    return round(final_score, 2)
