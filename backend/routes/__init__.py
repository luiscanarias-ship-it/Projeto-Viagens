"""
Shared dependencies and utilities used across all route modules.
Import this module to get access to db, auth helpers, and common utilities.
"""
from fastapi import APIRouter, HTTPException, Request, Response, UploadFile, File, Header, Query
from typing import Optional
from datetime import datetime, timezone, timedelta
import uuid, asyncio, logging

from config import (
    db, client, logger, JWT_SECRET, JWT_ALGORITHM, ADMIN_PASSWORD, ADMIN_EMAIL,
    STRIPE_API_KEY, STRIPE_SONHADOR_PRICE_ID, STRIPE_WEBHOOK_SECRET, FRONTEND_URL,
    FIXED_CONTRIBUTION_AMOUNTS, PAYMENT_METHODS, CRYPTO_TYPES, JOURNEY_STATUSES,
    TICKET_TYPES, TICKET_STATUSES, TICKET_PRIORITIES,
    PAYPAL_CLIENT_ID, PAYPAL_SECRET, PAYPAL_API_URL, PAYPAL_MODE,
    TIP_OPTIONS, DEFAULT_TIP_AMOUNT,
    CERTIFICATION_LEVELS, TRUSTED_AMBASSADOR_MIN_SUPPORTERS, TRUSTED_AMBASSADOR_MIN_RAISED
)
from models import (
    UserCreate, UserLogin, JourneyCreate, JourneyUpdate,
    ContributionCreate, Contribution
)
from auth import get_current_user, require_admin, create_jwt_token
