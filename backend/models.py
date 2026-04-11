import uuid
import random
from datetime import datetime, timezone
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from config import ALIAS_PREFIXES, ALIAS_SUFFIXES, AVATAR_STYLES, AVATAR_BACKGROUNDS


def generate_anonymous_alias() -> str:
    prefix = random.choice(ALIAS_PREFIXES)
    suffix = random.choice(ALIAS_SUFFIXES)
    return f"{prefix} {suffix}"


def generate_anonymous_avatar(seed: str = None) -> str:
    if not seed:
        seed = uuid.uuid4().hex[:8]
    style = random.choice(AVATAR_STYLES)
    bg_color = random.choice(AVATAR_BACKGROUNDS)
    return f"https://api.dicebear.com/7.x/{style}/svg?seed={seed}&backgroundColor={bg_color}"


class UserBase(BaseModel):
    email: EmailStr
    name: str
    surname: Optional[str] = None
    avatar: Optional[str] = None
    use_real_name: bool = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    surname: Optional[str] = None
    sponsor_code: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(UserBase):
    user_id: str
    is_admin: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    picture: Optional[str] = None
    preferred_language: Optional[str] = None
    anonymous_alias: Optional[str] = None
    total_contributed: float = 0


class Journey(BaseModel):
    journey_id: str = Field(default_factory=lambda: f"journey_{uuid.uuid4().hex[:12]}")
    name: str
    poetic_name: str
    description: str
    emotional_message: str
    impact_description: str
    image_url: str
    goal_amount: float
    current_amount: float = 0.0
    currency: str = "EUR"
    target_date: Optional[str] = None
    is_active: bool = True
    is_main_trip: bool = False
    status: str = "ativa"
    region: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    is_ambassador_journey: bool = False
    ambassador_user_id: Optional[str] = None
    ambassador_name: Optional[str] = None
    application_message: Optional[str] = None
    approved_at: Optional[str] = None
    funded_at: Optional[str] = None
    realized_at: Optional[str] = None
    closed_at: Optional[str] = None
    story: Optional[str] = None
    photos: Optional[List[str]] = None
    is_featured: bool = False
    featured_at: Optional[str] = None
    featured_order: int = 0
    visibility_score: float = 0.0
    visibility_boost: float = 0.0
    hide_from_listings: bool = False
    show_goal_amount: bool = False
    contribution_descriptions: Optional[dict] = None
    story_chapters: Optional[dict] = None
    current_chapter: int = 1
    story_emails_enabled: bool = True
    chapters_emails_sent: Optional[dict] = None
    owner_user_id: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class JourneyCreate(BaseModel):
    name: str
    poetic_name: str
    description: str
    emotional_message: str
    impact_description: str
    image_url: str
    goal_amount: float
    currency: str = "EUR"
    target_date: Optional[str] = None


class JourneyUpdate(BaseModel):
    name: Optional[str] = None
    poetic_name: Optional[str] = None
    description: Optional[str] = None
    emotional_message: Optional[str] = None
    impact_description: Optional[str] = None
    image_url: Optional[str] = None
    goal_amount: Optional[float] = None
    target_date: Optional[str] = None
    is_active: Optional[bool] = None
    status: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    story: Optional[str] = None
    photos: Optional[List[str]] = None
    show_goal_amount: Optional[bool] = None
    contribution_descriptions: Optional[dict] = None
    story_chapters: Optional[dict] = None
    current_chapter: Optional[int] = None
    story_emails_enabled: Optional[bool] = None


class AmbassadorJourneyApplication(BaseModel):
    name: str
    poetic_name: str
    description: str
    emotional_message: str
    impact_description: str
    image_url: Optional[str] = None
    goal_amount: float
    currency: str = "EUR"
    target_date: Optional[str] = None
    application_message: str


class Contribution(BaseModel):
    contribution_id: str = Field(default_factory=lambda: f"contrib_{uuid.uuid4().hex[:12]}")
    journey_id: str
    user_id: Optional[str] = None
    amount: int  # Total payment amount (support_amount + tip_amount) - kept for payment processing compatibility
    support_amount: Optional[int] = None  # Amount going to journey/ambassador (100%)
    tip_amount: Optional[int] = 0  # Optional platform tip (always goes to platform)
    currency: str = "EUR"
    payment_method: str
    crypto_type: Optional[str] = None
    tx_hash: Optional[str] = None
    status: str = "pending"
    is_main_trip: bool = True
    validated_by: Optional[str] = None
    validated_at: Optional[str] = None
    sponsor_link_id: Optional[str] = None
    session_id: Optional[str] = None
    payment_reference: Optional[str] = None
    contributor_name: Optional[str] = None
    contributor_email: Optional[str] = None
    public_message: Optional[str] = None
    show_name: bool = True
    notes: Optional[str] = None
    # Distribution tracking (set after payment confirmed)
    ambassador_revenue: Optional[int] = None  # For ambassador campaigns: support_amount
    platform_revenue: Optional[int] = None  # tip_amount + (support_amount if platform campaign)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def generate_payment_reference() -> str:
    code = random.randint(1000, 9999)
    return f"CN-{code}"


class ContributionCreate(BaseModel):
    journey_id: str
    amount: int  # Total payment amount (support_amount + tip_amount)
    support_amount: Optional[int] = None  # Amount for journey/ambassador
    tip_amount: Optional[int] = 0  # Optional platform tip
    payment_method: str
    crypto_type: Optional[str] = None
    tx_hash: Optional[str] = None
    sponsor_code: Optional[str] = None
    contributor_name: Optional[str] = None
    contributor_email: Optional[str] = None
    public_message: Optional[str] = None
    show_name: bool = True


class SponsorLink(BaseModel):
    link_id: str = Field(default_factory=lambda: f"sponsor_{uuid.uuid4().hex[:8]}")
    user_id: str
    journey_id: str
    referral_count: int = 0
    successful_referrals: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Point(BaseModel):
    point_id: str
    user_id: str
    journey_id: str
    contribution_id: str
    points_value: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TranslationRequest(BaseModel):
    texts: Dict[str, str]
    target_language: str


class Offer(BaseModel):
    offer_id: str = Field(default_factory=lambda: f"offer_{uuid.uuid4().hex[:12]}")
    user_id: str
    type: str  # "voucher" or "parceiro"
    description: str
    status: str = "pending"  # "pending" or "sent"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OfferCreate(BaseModel):
    user_id: str
    type: str
    description: str


class TravelPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:12]}")
    cache_key: str
    destination: str
    plan: dict
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
