import asyncio
import uuid
from datetime import datetime, timezone
from config import db, RESEND_API_KEY, SENDER_EMAIL, ADMIN_EMAIL, FRONTEND_URL, logger
import resend


def get_email_base_template(content: str, title: str = "4Luis") -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #FAFAF9;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #FAFAF9;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                    <tr>
                        <td align="center" style="padding: 32px 40px 24px 40px; border-bottom: 1px solid #E6F4F1;">
                            <span style="font-size: 28px; font-weight: bold; color: #FFBE98;">4Luis</span>
                            <p style="margin: 8px 0 0 0; color: #6B6661; font-size: 14px;">Onde os sonhos ganham asas</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 32px 40px;">
                            {content}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 0 40px 24px 40px;">
                            <div style="border-top: 1px solid #E6F4F1; padding-top: 24px; text-align: center;">
                                <p style="margin: 0 0 4px 0; color: #6B6661; font-size: 13px; font-style: italic;">Antes de partires...</p>
                                <p style="margin: 0 0 4px 0; color: #2D2A26; font-size: 15px; font-weight: 600;">Nunca deixes de sonhar,</p>
                                <p style="margin: 0 0 16px 0; color: #FFBE98; font-size: 15px; font-style: italic;">sonha connosco.</p>
                                <a href="{FRONTEND_URL}" style="display: inline-block; padding: 12px 28px; background-color: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 10px; font-weight: bold; font-size: 14px;">
                                    Contribuir para este sonho
                                </a>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 24px 40px; background-color: #FAFAF9; border-radius: 0 0 16px 16px;">
                            <p style="margin: 0; color: #6B6661; font-size: 12px; text-align: center;">
                                <span style="font-size: 16px; font-weight: bold; color: #2D2A26;">4Luis</span><br>
                                <span style="color: #FFBE98; font-style: italic; font-size: 14px;">Sonha connosco.</span><br><br>
                                Este é um email transacional automático da 4Luis.<br>
                                <a href="{FRONTEND_URL}" style="color: #FFBE98; text-decoration: none;">4Luis.com</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


async def send_email_resend(to_email: str, subject: str, html_content: str) -> dict:
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, email not sent")
        return {"status": "skipped", "reason": "API key not configured"}

    email_id = f"email_{uuid.uuid4().hex[:12]}"
    email_doc = {
        "email_id": email_id,
        "to_email": to_email,
        "subject": subject,
        "status": "sending",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sent_at": None,
        "error": None
    }
    await db.email_queue.insert_one(email_doc)

    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        await db.email_queue.update_one(
            {"email_id": email_id},
            {"$set": {"status": "sent", "sent_at": datetime.now(timezone.utc).isoformat(), "resend_id": result.get("id")}}
        )
        logger.info(f"Email sent successfully: {email_id} to {to_email}")
        return {"status": "sent", "email_id": email_id, "resend_id": result.get("id")}
    except Exception as e:
        error_msg = str(e)
        await db.email_queue.update_one(
            {"email_id": email_id},
            {"$set": {"status": "failed", "error": error_msg}}
        )
        logger.error(f"Failed to send email {email_id}: {error_msg}")
        return {"status": "failed", "email_id": email_id, "error": error_msg}


def _build_email_progress_bar(percentage: float) -> str:
    pct_int = int(min(percentage, 100))
    filled_blocks = max(1, pct_int // 5) if pct_int > 0 else 0
    empty_blocks = 20 - filled_blocks
    progress_bar_text = "\u2588" * filled_blocks + "\u2591" * empty_blocks
    return f"""
    <div style="background: #F5F5F4; border-radius: 16px; padding: 20px; margin: 20px 0;">
        <p style="color: #6B6661; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;">Progresso atual</p>
        <div style="background: #E7E5E4; border-radius: 8px; height: 12px; overflow: hidden; margin-bottom: 8px;">
            <div style="background: linear-gradient(90deg, #FFBE98, #F2C94C); height: 100%; width: {pct_int}%; border-radius: 8px;"></div>
        </div>
        <p style="font-family: monospace; color: #6B6661; font-size: 12px; letter-spacing: 1px; margin-bottom: 4px;">{progress_bar_text}</p>
        <p style="color: #2D2A26; font-size: 18px; font-weight: bold;">{percentage}% financiado</p>
    </div>
    """


def _build_email_cta_button(url: str, text: str) -> str:
    return f"""
    <div style="text-align: center; margin-top: 24px;">
        <a href="{url}" style="display: inline-block; background: #FFBE98; color: #2D2A26; padding: 14px 28px; border-radius: 12px; font-weight: bold; text-decoration: none; font-size: 16px;">{text}</a>
    </div>
    """


def _build_standard_email(title: str, narrative: str, percentage: float, cta_url: str, cta_text: str, extra_html: str = "") -> str:
    progress_bar = _build_email_progress_bar(percentage) if percentage is not None else ""
    cta = _build_email_cta_button(cta_url, cta_text)
    return f"""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px;">{title}</h1>
        <p style="color: #6B6661; font-size: 16px; line-height: 1.8; margin-bottom: 8px;">{narrative}</p>
        {extra_html}
        {progress_bar}
        {cta}
    </div>
    """


def get_contribution_email_html(contributor_name: str, amount: float, journey_name: str, is_crypto: bool = False, crypto_type: str = None) -> str:
    crypto_badge = ""
    if is_crypto and crypto_type:
        crypto_badge = f"""
        <div style="margin: 24px 0; padding: 16px; background: linear-gradient(135deg, #F7931A20, #627EEA20); border-radius: 12px; text-align: center;">
            <span style="font-size: 24px;">🏆</span>
            <p style="margin: 8px 0 0 0; color: #2D2A26; font-weight: bold;">Contribuição em {crypto_type.upper()}</p>
            <p style="margin: 4px 0 0 0; color: #6B6661; font-size: 14px;">Badge especial de cripto-sonhador!</p>
        </div>
        """
    content = f"""
    <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px;">Obrigado, {contributor_name}! 💜</h1>
    <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; line-height: 1.6;">A tua contribuição foi confirmada com sucesso.</p>
    <div style="background-color: #E6F4F1; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 24px;">
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">Contribuíste</p>
        <p style="margin: 0; color: #2D2A26; font-size: 36px; font-weight: bold;">{amount}€</p>
        <p style="margin: 8px 0 0 0; color: #6B6661; font-size: 14px;">para "{journey_name}"</p>
    </div>
    {crypto_badge}
    <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; line-height: 1.6;">
        Graças a ti, este sonho está mais perto de se tornar realidade.
    </p>
    <div style="background-color: #FFF8F0; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px; border: 1px solid #FFBE9840;">
        <p style="margin: 0 0 8px 0; color: #2D2A26; font-weight: bold; font-size: 16px;">O sonho continua a crescer</p>
        <p style="margin: 0 0 16px 0; color: #6B6661; font-size: 14px;">Já ajudaste — agora convida alguém a fazer parte</p>
        <a href="{FRONTEND_URL}" style="display: inline-block; padding: 12px 28px; background-color: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 14px;">Convidar amigos</a>
    </div>
    <div style="text-align: center;">
        <a href="{FRONTEND_URL}/dashboard" style="display: inline-block; padding: 14px 32px; background-color: #2D2A26; color: #FFFFFF; text-decoration: none; border-radius: 12px; font-weight: bold;">Ver o meu Dashboard</a>
    </div>
    """
    return get_email_base_template(content, "Contribuição Confirmada - 4Luis")


def get_referral_contribution_email_html(sponsor_name: str, invitee_name: str, amount: float, journey_name: str, valid_referrals: int, contributed_to_main: bool) -> str:
    contribution_check = "✅" if contributed_to_main else "⬜"
    referrals_check = "✅" if valid_referrals >= 3 else "⬜"
    if contributed_to_main and valid_referrals >= 3:
        progress_to_ambassador = """
        <div style="margin: 24px 0; padding: 16px; background: linear-gradient(135deg, #FFBE9820, #E6F4F120); border-radius: 12px; text-align: center; border: 2px solid #FFBE98;">
            <span style="font-size: 32px;">🎉</span>
            <p style="margin: 8px 0 0 0; color: #2D2A26; font-weight: bold; font-size: 18px;">Parabéns! És agora Embaixador!</p>
            <p style="margin: 4px 0 0 0; color: #6B6661; font-size: 14px;">Podes criar a tua própria viagem de sonho.</p>
        </div>
        """
    else:
        progress_to_ambassador = f"""
        <div style="margin: 24px 0; padding: 16px; background-color: #FAFAF9; border-radius: 12px;">
            <p style="margin: 0 0 12px 0; color: #2D2A26; font-weight: bold;">Progresso para Embaixador:</p>
            <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">{contribution_check} Contribuir para a viagem principal</p>
            <p style="margin: 0; color: #6B6661; font-size: 14px;">{referrals_check} 3 convites válidos ({valid_referrals}/3)</p>
        </div>
        """
    content = f"""
    <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px;">Boa notícia, {sponsor_name}! 🌟</h1>
    <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; line-height: 1.6;">Alguém que convidaste acabou de contribuir para um sonho!</p>
    <div style="background-color: #E6F4F1; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
            <tr><td style="padding-bottom: 12px;"><p style="margin: 0; color: #6B6661; font-size: 14px;">Convidado</p><p style="margin: 4px 0 0 0; color: #2D2A26; font-size: 18px; font-weight: bold;">{invitee_name}</p></td></tr>
            <tr><td style="padding-bottom: 12px;"><p style="margin: 0; color: #6B6661; font-size: 14px;">Contribuiu</p><p style="margin: 4px 0 0 0; color: #FFBE98; font-size: 24px; font-weight: bold;">{amount}€</p></td></tr>
            <tr><td><p style="margin: 0; color: #6B6661; font-size: 14px;">Para a viagem</p><p style="margin: 4px 0 0 0; color: #2D2A26; font-size: 16px;">{journey_name}</p></td></tr>
        </table>
    </div>
    {progress_to_ambassador}
    <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; line-height: 1.6;">O teu impacto na comunidade está a crescer. Continua a partilhar o teu link de convite!</p>
    <div style="text-align: center;">
        <a href="{FRONTEND_URL}/dashboard" style="display: inline-block; padding: 14px 32px; background-color: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold;">Ver o meu Dashboard</a>
    </div>
    """
    return get_email_base_template(content, "O teu convidado contribuiu! - 4Luis")


def get_admin_referral_notification_html(sponsor_name: str, sponsor_email: str, invitee_name: str, invitee_email: str, amount: float, journey_name: str) -> str:
    content = f"""
    <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px;">📊 Nova Contribuição via Referral</h1>
    <div style="background-color: #FAFAF9; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
            <tr><td colspan="2" style="padding-bottom: 16px; border-bottom: 1px solid #E6F4F1;"><p style="margin: 0; color: #6B6661; font-size: 12px; text-transform: uppercase;">Contribuidor</p><p style="margin: 4px 0 0 0; color: #2D2A26; font-size: 16px; font-weight: bold;">{invitee_name}</p><p style="margin: 2px 0 0 0; color: #6B6661; font-size: 14px;">{invitee_email}</p></td></tr>
            <tr><td colspan="2" style="padding: 16px 0; border-bottom: 1px solid #E6F4F1;"><p style="margin: 0; color: #6B6661; font-size: 12px; text-transform: uppercase;">Sponsor</p><p style="margin: 4px 0 0 0; color: #2D2A26; font-size: 16px; font-weight: bold;">{sponsor_name}</p><p style="margin: 2px 0 0 0; color: #6B6661; font-size: 14px;">{sponsor_email}</p></td></tr>
            <tr><td style="padding-top: 16px; width: 50%;"><p style="margin: 0; color: #6B6661; font-size: 12px; text-transform: uppercase;">Valor</p><p style="margin: 4px 0 0 0; color: #FFBE98; font-size: 24px; font-weight: bold;">{amount}€</p></td><td style="padding-top: 16px; width: 50%;"><p style="margin: 0; color: #6B6661; font-size: 12px; text-transform: uppercase;">Viagem</p><p style="margin: 4px 0 0 0; color: #2D2A26; font-size: 16px;">{journey_name}</p></td></tr>
        </table>
    </div>
    <div style="text-align: center;">
        <a href="{FRONTEND_URL}/admin" style="display: inline-block; padding: 14px 32px; background-color: #2D2A26; color: #ffffff; text-decoration: none; border-radius: 12px; font-weight: bold;">Abrir Painel Admin</a>
    </div>
    """
    return get_email_base_template(content, "Notificação Admin - Contribuição Referral")


def get_ambassador_unlocked_email_html(name: str) -> str:
    content = f"""
    <div style="text-align: center; margin-bottom: 24px;"><span style="font-size: 64px;">🎖️</span></div>
    <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 28px; text-align: center;">Parabéns, {name}!</h1>
    <p style="margin: 0 0 24px 0; color: #FFBE98; font-size: 20px; text-align: center; font-style: italic;">És agora Embaixador 4Luis</p>
    <div style="background-color: #E6F4F1; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
        <p style="margin: 0 0 16px 0; color: #2D2A26; font-weight: bold;">O que conquistaste:</p>
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">✅ Contribuíste para a viagem principal</p>
        <p style="margin: 0; color: #6B6661; font-size: 14px;">✅ Convidaste 3+ pessoas que também contribuíram</p>
    </div>
    <div style="background: linear-gradient(135deg, #FFBE9820, #E6F4F120); border-radius: 12px; padding: 24px; margin-bottom: 24px;">
        <p style="margin: 0 0 16px 0; color: #2D2A26; font-weight: bold;">Como Embaixador, agora podes:</p>
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">🌟 Candidatar-te a criar a tua própria viagem de sonho</p>
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">💜 Receber contribuições da comunidade</p>
        <p style="margin: 0; color: #6B6661; font-size: 14px;">✨ Inspirar outros a sonhar</p>
    </div>
    <div style="text-align: center;">
        <a href="{FRONTEND_URL}/dashboard" style="display: inline-block; padding: 16px 40px; background-color: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 16px;">Começar a Criar o Meu Sonho</a>
    </div>
    """
    return get_email_base_template(content, "Parabéns Embaixador! - 4Luis")


def get_journey_funded_email_html(ambassador_name: str, journey_name: str, amount_raised: float) -> str:
    content = f"""
    <div style="text-align: center; margin-bottom: 24px;"><span style="font-size: 64px;">🎉</span></div>
    <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 28px; text-align: center;">A tua viagem foi financiada!</h1>
    <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; text-align: center; line-height: 1.6;">Parabéns, {ambassador_name}! A comunidade 4Luis acreditou no teu sonho.</p>
    <div style="background: linear-gradient(135deg, #FFBE9820, #E6F4F120); border-radius: 12px; padding: 32px; text-align: center; margin-bottom: 24px;">
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">Viagem</p>
        <p style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px; font-weight: bold;">{journey_name}</p>
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">Valor angariado</p>
        <p style="margin: 0; color: #FFBE98; font-size: 36px; font-weight: bold;">{amount_raised}€</p>
    </div>
    <div style="background-color: #FAFAF9; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
        <p style="margin: 0 0 16px 0; color: #2D2A26; font-weight: bold;">Próximos passos:</p>
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">1. ✅ Confirmação do financiamento recebida</p>
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">2. 📧 Entraremos em contacto para os detalhes</p>
        <p style="margin: 0; color: #6B6661; font-size: 14px;">3. ✈️ Prepara-te para viver esta aventura!</p>
    </div>
    <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; line-height: 1.6; text-align: center; font-style: italic;">"Quando os sonhos têm asas, voam mais alto."</p>
    <div style="text-align: center;">
        <a href="{FRONTEND_URL}/dashboard" style="display: inline-block; padding: 14px 32px; background-color: #FFBE98; color: #2D2A26; text-decoration: none; border-radius: 12px; font-weight: bold;">Ver o meu Dashboard</a>
    </div>
    """
    return get_email_base_template(content, "Viagem Financiada! - 4Luis")


def get_admin_journey_funded_html(journey_name: str, journey_id: str, amount_raised: float, ambassador_name: str) -> str:
    content = f"""
    <h1 style="margin: 0 0 16px 0; color: #2D2A26; font-size: 24px;">🎯 Viagem Financiada!</h1>
    <div style="background-color: #E6F4F1; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
            <tr><td style="padding-bottom: 12px;"><p style="margin: 0; color: #6B6661; font-size: 12px; text-transform: uppercase;">Viagem</p><p style="margin: 4px 0 0 0; color: #2D2A26; font-size: 18px; font-weight: bold;">{journey_name}</p></td></tr>
            <tr><td style="padding-bottom: 12px;"><p style="margin: 0; color: #6B6661; font-size: 12px; text-transform: uppercase;">ID</p><p style="margin: 4px 0 0 0; color: #6B6661; font-size: 14px; font-family: monospace;">{journey_id}</p></td></tr>
            <tr><td style="padding-bottom: 12px;"><p style="margin: 0; color: #6B6661; font-size: 12px; text-transform: uppercase;">Embaixador</p><p style="margin: 4px 0 0 0; color: #2D2A26; font-size: 16px;">{ambassador_name}</p></td></tr>
            <tr><td><p style="margin: 0; color: #6B6661; font-size: 12px; text-transform: uppercase;">Valor Angariado</p><p style="margin: 4px 0 0 0; color: #FFBE98; font-size: 24px; font-weight: bold;">{amount_raised}€</p></td></tr>
        </table>
    </div>
    <div style="background-color: #FEF3C7; border-radius: 12px; padding: 16px; margin-bottom: 24px;">
        <p style="margin: 0; color: #92400E; font-size: 14px;">⚠️ <strong>Ação necessária:</strong> Rever e aprovar os próximos passos com o embaixador.</p>
    </div>
    <div style="text-align: center;">
        <a href="{FRONTEND_URL}/admin" style="display: inline-block; padding: 14px 32px; background-color: #2D2A26; color: #ffffff; text-decoration: none; border-radius: 12px; font-weight: bold;">Abrir Painel Admin</a>
    </div>
    """
    return get_email_base_template(content, "[Admin] Viagem Financiada - 4Luis")


async def send_contribution_email(contribution: dict, journey: dict):
    if not contribution.get("contributor_email"):
        return
    is_crypto = contribution.get("payment_method") == "crypto"
    crypto_type = contribution.get("crypto_type") if is_crypto else None
    html = get_contribution_email_html(
        contributor_name=contribution.get("contributor_name", "Sonhador"),
        amount=contribution.get("amount"),
        journey_name=journey.get("name", ""),
        is_crypto=is_crypto,
        crypto_type=crypto_type
    )
    await send_email_resend(
        to_email=contribution["contributor_email"],
        subject=f"Contribuição de {contribution.get('amount')}€ confirmada - 4Luis",
        html_content=html
    )


async def send_referral_contribution_emails(contribution: dict, journey: dict, contributor_user: dict, sponsor_user: dict):
    sponsor_email = sponsor_user.get("email")
    sponsor_name = sponsor_user.get("name", "Sonhador")
    invitee_name = contributor_user.get("name", contribution.get("contributor_name", "Sonhador"))
    invitee_email = contributor_user.get("email", contribution.get("contributor_email", ""))
    amount = contribution.get("amount")
    journey_name = journey.get("name", "")
    valid_referrals = sponsor_user.get("valid_referrals_count", 0)
    contributed_to_main = sponsor_user.get("contributed_to_main_trip", False)

    if sponsor_email:
        sponsor_html = get_referral_contribution_email_html(
            sponsor_name=sponsor_name, invitee_name=invitee_name, amount=amount,
            journey_name=journey_name, valid_referrals=valid_referrals, contributed_to_main=contributed_to_main
        )
        await send_email_resend(to_email=sponsor_email, subject=f"🌟 {invitee_name} contribuiu {amount}€ - O teu convite funcionou!", html_content=sponsor_html)

    admin_html = get_admin_referral_notification_html(
        sponsor_name=sponsor_name, sponsor_email=sponsor_email or "N/A",
        invitee_name=invitee_name, invitee_email=invitee_email, amount=amount, journey_name=journey_name
    )
    await send_email_resend(to_email=ADMIN_EMAIL, subject=f"[Admin] Contribuição Referral: {invitee_name} → {amount}€", html_content=admin_html)


async def send_ambassador_unlocked_email(user_id: str):
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user or not user.get("email"):
        return
    html = get_ambassador_unlocked_email_html(name=user.get("name", "Embaixador"))
    await send_email_resend(to_email=user["email"], subject="🎖️ Parabéns! És agora Embaixador 4Luis!", html_content=html)
    logger.info(f"Ambassador unlocked email sent to user {user_id}")


async def send_tip_thank_you_email(contribution: dict):
    """Send thank you email to contributors who left a platform tip"""
    email = contribution.get("contributor_email")
    tip_amount = contribution.get("tip_amount", 0)
    
    # Only send if tip > 0 and email exists
    if not email or tip_amount <= 0:
        return
    
    name = contribution.get("contributor_name", "Sonhador")
    
    body = f"""
    <div style="text-align: center; padding: 20px 0;">
        <div style="font-size: 48px; margin-bottom: 16px;">❤️</div>
        <h1 style="margin: 0 0 24px 0; color: #2D2A26; font-size: 24px;">Obrigado por fazeres parte deste sonho</h1>
        
        <p style="color: #6B6661; font-size: 16px; line-height: 1.8; margin-bottom: 16px;">
            Olá {name},
        </p>
        
        <p style="color: #6B6661; font-size: 16px; line-height: 1.8; margin-bottom: 16px;">
            Obrigado por ajudares a manter esta plataforma viva.
        </p>
        
        <p style="color: #6B6661; font-size: 16px; line-height: 1.8; margin-bottom: 16px;">
            Sem pessoas como tu, não seria possível tornar estas viagens realidade.
        </p>
        
        <div style="background: linear-gradient(135deg, #FFF5F5 0%, #FFF8E1 100%); border-radius: 12px; padding: 24px; margin: 24px 0; border: 1px solid #FFE4E1;">
            <p style="color: #C53030; font-size: 18px; font-weight: bold; margin: 0;">
                O teu apoio faz mesmo a diferença.
            </p>
        </div>
        
        <p style="color: #6B6661; font-size: 16px; line-height: 1.8; margin-bottom: 24px;">
            Até breve ✨
        </p>
        
        <p style="color: #FFBE98; font-style: italic; font-size: 14px;">
            — Equipa 4Luis
        </p>
    </div>
    """
    
    html = get_email_base_template(body, "Obrigado - 4Luis")
    
    try:
        await send_email_resend(
            to_email=email,
            subject="Obrigado por fazeres parte deste sonho ❤️",
            html_content=html
        )
        logger.info(f"Tip thank you email sent to {email} (tip: {tip_amount}€)")
    except Exception as e:
        logger.error(f"Failed to send tip thank you email to {email}: {e}")


async def send_journey_funded_emails(journey: dict, ambassador_user: dict, amount_raised: float):
    journey_name = journey.get("name", "")
    journey_id = journey.get("journey_id", "")
    ambassador_name = ambassador_user.get("name", "Embaixador") if ambassador_user else journey.get("ambassador_name", "N/A")
    if ambassador_user and ambassador_user.get("email"):
        ambassador_html = get_journey_funded_email_html(ambassador_name=ambassador_name, journey_name=journey_name, amount_raised=amount_raised)
        await send_email_resend(to_email=ambassador_user["email"], subject=f"🎉 A tua viagem '{journey_name}' foi financiada!", html_content=ambassador_html)
    admin_html = get_admin_journey_funded_html(journey_name=journey_name, journey_id=journey_id, amount_raised=amount_raised, ambassador_name=ambassador_name)
    await send_email_resend(to_email=ADMIN_EMAIL, subject=f"[Admin] Viagem Financiada: {journey_name}", html_content=admin_html)


async def send_weekly_summary_emails():
    active_journeys = await db.journeys.find({"status": "ativa", "is_active": True}, {"_id": 0}).to_list(50)
    if not active_journeys:
        return {"sent": 0, "message": "No active journeys"}
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
        <p style="color: #6B6661; font-size: 16px; line-height: 1.8; margin-bottom: 24px;">Aqui esta o progresso dos sonhos que estamos a construir juntos esta semana.</p>
        {journeys_html}
        {_build_email_cta_button(FRONTEND_URL, "Explorar todos os sonhos")}
    </div>
    """
    html = get_email_base_template(body, "Resumo Semanal - 4Luis")
    subject = "Resumo semanal dos sonhos - 4Luis"
    users = await db.users.find({"email": {"$exists": True, "$ne": ""}}, {"_id": 0, "email": 1}).to_list(500)
    sent_count = 0
    for u in users:
        email = u.get("email", "")
        if email and "@" in email and not email.endswith("@test.com"):
            try:
                await send_email_resend(email, subject, html)
                sent_count += 1
            except Exception as e:
                logger.error(f"Weekly summary email failed for {email}: {e}")
    logger.info(f"Weekly summary sent to {sent_count} users")
    return {"sent": sent_count, "journeys_count": len(active_journeys)}


async def send_dream_funded_announcement(journey: dict):
    journey_name = journey.get("name", "")
    poetic_name = journey.get("poetic_name", "")
    journey_id = journey.get("journey_id", "")
    current_amount = journey.get("current_amount", 0)
    goal_amount = journey.get("goal_amount", 1)
    percentage = round((current_amount / goal_amount) * 100, 1) if goal_amount > 0 else 100
    journey_url = f"{FRONTEND_URL}/journey/{journey_id}"
    contributors = await db.contributions.find({"journey_id": journey_id, "status": "completed"}, {"_id": 0, "contributor_name": 1}).to_list(500)
    contributor_count = len(contributors)
    body = _build_standard_email(
        title="Este sonho tornou-se realidade!",
        narrative=f"""A viagem &ldquo;<strong>{poetic_name or journey_name}</strong>&rdquo; acaba de ser totalmente financiada.<br><br>
        Gracas a <strong>{contributor_count} sonhadores</strong> que acreditaram, este sonho vai acontecer.<br>
        Obrigado a todos os que ajudaram a transformar este sonho em realidade.""",
        percentage=percentage, cta_url=journey_url, cta_text="Ver este sonho realizado"
    )
    html = get_email_base_template(body, f"Sonho Realizado: {journey_name} - 4Luis")
    subject = f"O sonho da {journey_name} tornou-se realidade!"
    users = await db.users.find({"email": {"$exists": True, "$ne": ""}}, {"_id": 0, "email": 1}).to_list(500)
    sent_count = 0
    for u in users:
        email = u.get("email", "")
        if email and "@" in email and not email.endswith("@test.com"):
            try:
                await send_email_resend(email, subject, html)
                sent_count += 1
            except Exception as e:
                logger.error(f"Dream funded email failed for {email}: {e}")
    logger.info(f"Dream funded announcement sent to {sent_count} users for {journey_id}")
    return {"sent": sent_count}


async def send_new_journey_email(journey: dict):
    journey_name = journey.get("name", "")
    poetic_name = journey.get("poetic_name", "")
    description = journey.get("description", "")
    journey_id = journey.get("journey_id", "")
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
    subject = f"Novo sonho na 4Luis: {journey_name}"
    users = await db.users.find({"email": {"$exists": True, "$ne": ""}}, {"_id": 0, "email": 1}).to_list(500)
    sent_count = 0
    for u in users:
        email = u.get("email", "")
        if email and "@" in email and not email.endswith("@test.com"):
            try:
                await send_email_resend(email, subject, html)
                sent_count += 1
            except Exception as e:
                logger.error(f"New journey email failed for {email}: {e}")
    logger.info(f"New journey email sent to {sent_count} users for {journey_id}")
    return {"sent": sent_count}



# ==================== CONTRIBUTION CONFIRMATION EMAILS ====================

def get_contribution_confirmed_email_html(
    contributor_name: str,
    amount: float,
    journey_name: str,
    contributors_count: int,
    percentage: float,
    journey_id: str,
    referral_code: str = None,
    remaining_referrals: int = None
) -> str:
    social_proof = f"""
    <div style="background: #FFF7ED; border-radius: 12px; padding: 16px; text-align: center; margin: 20px 0;">
        <p style="margin: 0; color: #2D2A26; font-size: 15px;">
            Já somos <strong>{contributors_count}</strong> pessoas a apoiar este sonho
        </p>
    </div>
    """

    progress_bar = _build_email_progress_bar(percentage) if percentage > 0 else ""

    ambassador_section = ""
    if referral_code and remaining_referrals is not None and remaining_referrals > 0:
        invite_url = f"{FRONTEND_URL}/?ref={referral_code}"
        ambassador_section = f"""
        <div style="background: linear-gradient(135deg, #FFBE9810, #FFBE9830); border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center; border: 1px solid #FFBE9840;">
            <p style="margin: 0 0 4px 0; color: #2D2A26; font-size: 15px; font-weight: 600;">Queres acelerar este sonho?</p>
            <p style="margin: 0 0 16px 0; color: #6B6661; font-size: 13px;">Faltam-te <strong>{remaining_referrals}</strong> amigos para te tornares Embaixador</p>
            {_build_email_cta_button(invite_url, "Convidar amigos")}
        </div>
        """
    elif referral_code:
        invite_url = f"{FRONTEND_URL}/?ref={referral_code}"
        ambassador_section = f"""
        <div style="background: linear-gradient(135deg, #FFBE9810, #FFBE9830); border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center; border: 1px solid #FFBE9840;">
            <p style="margin: 0 0 12px 0; color: #2D2A26; font-size: 15px; font-weight: 600;">Queres acelerar este sonho?</p>
            {_build_email_cta_button(invite_url, "Convidar amigos")}
        </div>
        """

    content = f"""
    <div style="text-align: center;">
        <h1 style="margin: 0 0 8px 0; color: #2D2A26; font-size: 24px;">A tua contribuição foi confirmada com sucesso</h1>
        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 16px; line-height: 1.6;">
            Obrigado, {contributor_name}!
        </p>
        <p style="margin: 0 0 24px 0; color: #FFBE98; font-size: 14px; font-style: italic;">
            Já estás a ajudar a tornar este sonho realidade
        </p>

        <div style="background-color: #FFF7ED; border-radius: 12px; padding: 24px; text-align: center; margin-bottom: 20px;">
            <p style="margin: 0 0 4px 0; color: #6B6661; font-size: 13px;">A tua contribuição</p>
            <p style="margin: 0; color: #2D2A26; font-size: 36px; font-weight: bold;">{amount}€</p>
            <p style="margin: 6px 0 0 0; color: #6B6661; font-size: 14px;">para "{journey_name}"</p>
            <p style="margin: 12px 0 0 0; color: #10B981; font-size: 13px; font-weight: 600;">Pagamento confirmado</p>
        </div>

        {social_proof}
        {progress_bar}
        {ambassador_section}
    </div>
    """
    return get_email_base_template(content, "A tua contribuição foi confirmada")


def get_contribution_pending_email_html(
    contributor_name: str,
    amount: float,
    journey_name: str,
    payment_reference: str,
    payment_method: str
) -> str:
    method_label = "MB WAY" if payment_method == "mbway" else payment_method.upper()
    content = f"""
    <div style="text-align: center;">
        <h1 style="margin: 0 0 8px 0; color: #2D2A26; font-size: 24px;">Recebemos a tua confirmação</h1>
        <p style="margin: 0 0 24px 0; color: #6B6661; font-size: 16px; line-height: 1.6;">
            Obrigado, {contributor_name}! Vamos validar o teu pagamento em poucos minutos.
        </p>

        <div style="background-color: #FFF7ED; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <p style="margin: 0 0 4px 0; color: #6B6661; font-size: 13px;">Detalhes</p>
            <p style="margin: 0 0 4px 0; color: #2D2A26; font-size: 24px; font-weight: bold;">{amount}€</p>
            <p style="margin: 0 0 4px 0; color: #6B6661; font-size: 13px;">Método: {method_label}</p>
            <p style="margin: 0; color: #6B6661; font-size: 13px;">Referência: <strong style="color: #2D2A26;">{payment_reference}</strong></p>
        </div>

        <p style="margin: 0 0 8px 0; color: #6B6661; font-size: 14px;">
            Receberás outro email assim que o pagamento for confirmado.
        </p>
        <p style="margin: 0; color: #10B981; font-size: 13px; font-weight: 600;">
            Confirmação em poucos minutos
        </p>
    </div>
    """
    return get_email_base_template(content, "Pagamento em validação")


async def send_contribution_confirmed_email(contribution: dict, journey: dict):
    """Send email when admin confirms a contribution"""
    email = contribution.get("contributor_email")
    if not email:
        return

    # Get progress data
    progress = await db.contributions.count_documents({
        "journey_id": journey.get("journey_id"),
        "status": "confirmed"
    })
    goal = journey.get("goal_amount", 1)
    current = journey.get("current_amount", 0)
    percentage = round((current / goal) * 100, 1) if goal > 0 else 0

    # Get referral info if user exists
    referral_code = None
    remaining_referrals = None
    if contribution.get("user_id"):
        user = await db.users.find_one({"user_id": contribution["user_id"]}, {"_id": 0})
        if user:
            referral_code = user.get("referral_code")
            valid_refs = user.get("valid_referrals_count", 0)
            remaining_referrals = max(0, 3 - valid_refs)

    html = get_contribution_confirmed_email_html(
        contributor_name=contribution.get("contributor_name", "Sonhador"),
        amount=contribution.get("amount"),
        journey_name=journey.get("name", ""),
        contributors_count=progress,
        percentage=percentage,
        journey_id=journey.get("journey_id", ""),
        referral_code=referral_code,
        remaining_referrals=remaining_referrals
    )
    await send_email_resend(
        to_email=email,
        subject="Já fazes parte deste sonho",
        html_content=html
    )


async def send_contribution_pending_email(contribution: dict, journey: dict):
    """Send email when user confirms they made the payment (pending validation)"""
    email = contribution.get("contributor_email")
    if not email:
        return

    html = get_contribution_pending_email_html(
        contributor_name=contribution.get("contributor_name", "Sonhador"),
        amount=contribution.get("amount"),
        journey_name=journey.get("name", ""),
        payment_reference=contribution.get("payment_reference", "N/A"),
        payment_method=contribution.get("payment_method", "")
    )
    await send_email_resend(
        to_email=email,
        subject=f"Pagamento de {contribution.get('amount')}€ em validação - 4Luis",
        html_content=html
    )
