"""
Phone Change Router

Secure 3-step phone number change flow:
1. Request phone change - Send OTP to current phone
2. Verify current phone - Verify OTP from current phone
3. Send OTP to new phone - Send OTP to new phone number
4. Verify new phone - Verify OTP and complete phone change

Security features:
- Verify current phone ownership first
- Check new phone not already registered
- Rate limiting (max 3 attempts per hour)
- Cooldown period (1 hour between successful changes)
- Session-based verification with expiration
- Maintain audit trail of phone changes
- Update all user data atomically
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database import get_db
from ..models import User, PhoneChangeRequest, CaseHistory
from ..auth import get_current_user
from ..services.otp_service import OTPService
from ..services.sms_service import SMSService

router = APIRouter(prefix="/v1/users/phone-change", tags=["phone-change"])

# Rate limiting config
MAX_ATTEMPTS_PER_HOUR = 3
COOLDOWN_HOURS = 1
SESSION_EXPIRY_MINUTES = 15


class PhoneChangeRequestModel(BaseModel):
    """Request to initiate phone change"""
    pass


class VerifyCurrentPhoneModel(BaseModel):
    """Verify current phone OTP"""
    session_id: str = Field(..., description="Phone change session ID")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")


class SendNewPhoneOTPModel(BaseModel):
    """Send OTP to new phone number"""
    session_id: str = Field(..., description="Phone change session ID")
    new_phone: str = Field(..., description="New phone number with country code")

    @validator('new_phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if not v.startswith('+91'):
            raise ValueError('Phone must start with +91')
        if len(v) != 13:  # +91 + 10 digits
            raise ValueError('Phone must be 10 digits after country code')
        if not v[3:].isdigit():
            raise ValueError('Phone must contain only digits after country code')
        if v[3] not in '6789':
            raise ValueError('Phone must start with 6, 7, 8, or 9')
        return v


class VerifyNewPhoneModel(BaseModel):
    """Verify new phone OTP and complete change"""
    session_id: str = Field(..., description="Phone change session ID")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP")


class PhoneChangeResponse(BaseModel):
    """Phone change response"""
    success: bool
    message: str
    session_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    new_phone: Optional[str] = None


def check_rate_limit(db: Session, user_id: int) -> None:
    """Check if user has exceeded rate limits"""
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)

    # Count attempts in last hour
    recent_attempts = db.query(PhoneChangeRequest).filter(
        and_(
            PhoneChangeRequest.user_id == user_id,
            PhoneChangeRequest.created_at >= hour_ago,
        )
    ).count()

    if recent_attempts >= MAX_ATTEMPTS_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many attempts. Please try again after 1 hour."
        )

    # Check cooldown period for successful changes
    last_successful = db.query(PhoneChangeRequest).filter(
        and_(
            PhoneChangeRequest.user_id == user_id,
            PhoneChangeRequest.status == "completed",
            PhoneChangeRequest.completed_at >= hour_ago,
        )
    ).first()

    if last_successful:
        remaining = COOLDOWN_HOURS * 60 - int((now - last_successful.completed_at).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {remaining} minutes before changing phone again."
        )


def get_active_session(db: Session, session_id: str, user_id: int) -> PhoneChangeRequest:
    """Get and validate active phone change session"""
    session = db.query(PhoneChangeRequest).filter(
        and_(
            PhoneChangeRequest.session_id == session_id,
            PhoneChangeRequest.user_id == user_id,
        )
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired session"
        )

    if session.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already completed"
        )

    if session.expires_at < datetime.utcnow():
        session.status = "expired"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session expired. Please start again."
        )

    return session


@router.post("/request", response_model=PhoneChangeResponse)
async def request_phone_change(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Step 1: Request phone change - Send OTP to current phone

    Security checks:
    - Rate limiting (max 3 attempts per hour)
    - Cooldown period (1 hour between successful changes)
    - Create session with expiration
    """
    # Check rate limits
    check_rate_limit(db, current_user.id)

    # Generate OTP for current phone
    otp_code = OTPService.generate_otp()

    # Create phone change session
    import uuid
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=SESSION_EXPIRY_MINUTES)

    phone_change = PhoneChangeRequest(
        session_id=session_id,
        user_id=current_user.id,
        current_phone=current_user.phone,
        current_phone_otp=otp_code,
        status="pending_current_verification",
        expires_at=expires_at,
        created_at=datetime.utcnow(),
    )
    db.add(phone_change)
    db.commit()

    # Send OTP to current phone
    try:
        SMSService.send_otp(
            phone=current_user.phone,
            otp=otp_code,
            message_template=f"Your Boloo phone change verification OTP is: {otp_code}. Valid for 15 minutes."
        )
    except Exception as e:
        # Log error but don't expose to user
        print(f"SMS send error: {str(e)}")
        # In development, you might want to return the OTP
        # raise HTTPException(status_code=500, detail=f"Failed to send OTP: {str(e)}")

    return PhoneChangeResponse(
        success=True,
        message="OTP sent to your current phone number",
        session_id=session_id,
        expires_at=expires_at,
    )


@router.post("/verify-current", response_model=PhoneChangeResponse)
async def verify_current_phone(
    request: VerifyCurrentPhoneModel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Step 2: Verify current phone OTP

    Validates OTP sent to current phone number
    Updates session to allow new phone entry
    """
    # Get active session
    session = get_active_session(db, request.session_id, current_user.id)

    # Verify OTP
    if session.current_phone_otp != request.otp:
        session.current_phone_attempts = (session.current_phone_attempts or 0) + 1

        if session.current_phone_attempts >= 3:
            session.status = "failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum attempts exceeded. Please start again."
            )

        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP. {3 - session.current_phone_attempts} attempts remaining."
        )

    # Update session status
    session.status = "current_verified"
    session.current_verified_at = datetime.utcnow()
    db.commit()

    return PhoneChangeResponse(
        success=True,
        message="Current phone verified successfully",
        session_id=session.session_id,
    )


@router.post("/send-new-otp", response_model=PhoneChangeResponse)
async def send_new_phone_otp(
    request: SendNewPhoneOTPModel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Step 3: Send OTP to new phone number

    Security checks:
    - Verify current phone was verified
    - Check new phone not already registered
    - Check new phone different from current
    - Generate and send OTP to new phone
    """
    # Get active session
    session = get_active_session(db, request.session_id, current_user.id)

    # Verify current phone was verified
    if session.status != "current_verified":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please verify current phone first"
        )

    # Check new phone is different
    if request.new_phone == current_user.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New phone must be different from current phone"
        )

    # Check new phone not already registered
    existing_user = db.query(User).filter(User.phone == request.new_phone).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This phone number is already registered"
        )

    # Generate OTP for new phone
    otp_code = OTPService.generate_otp()

    # Update session
    session.new_phone = request.new_phone
    session.new_phone_otp = otp_code
    session.status = "pending_new_verification"
    db.commit()

    # Send OTP to new phone
    try:
        SMSService.send_otp(
            phone=request.new_phone,
            otp=otp_code,
            message_template=f"Your Boloo new phone verification OTP is: {otp_code}. Valid for 15 minutes."
        )
    except Exception as e:
        print(f"SMS send error: {str(e)}")

    return PhoneChangeResponse(
        success=True,
        message="OTP sent to new phone number",
        session_id=session.session_id,
    )


@router.post("/verify-new", response_model=PhoneChangeResponse)
async def verify_new_phone(
    request: VerifyNewPhoneModel,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Step 4: Verify new phone OTP and complete phone change

    Security:
    - Verify OTP from new phone
    - Update user phone atomically
    - Send confirmation to both numbers
    - Create audit trail
    - Update all related records
    """
    # Get active session
    session = get_active_session(db, request.session_id, current_user.id)

    # Verify session status
    if session.status != "pending_new_verification":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session state"
        )

    # Verify OTP
    if session.new_phone_otp != request.otp:
        session.new_phone_attempts = (session.new_phone_attempts or 0) + 1

        if session.new_phone_attempts >= 3:
            session.status = "failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum attempts exceeded. Please start again."
            )

        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP. {3 - session.new_phone_attempts} attempts remaining."
        )

    # Store old phone for notifications
    old_phone = current_user.phone
    new_phone = session.new_phone

    # Update user phone atomically
    try:
        # Update user
        current_user.phone = new_phone
        current_user.updated_at = datetime.utcnow()

        # Update session
        session.status = "completed"
        session.completed_at = datetime.utcnow()

        # Create audit trail in case history
        case_update = CaseHistory(
            case_id=None,  # System-level change
            user_id=current_user.id,
            action="phone_changed",
            details=f"Phone changed from {old_phone} to {new_phone}",
            metadata={
                "old_phone": old_phone,
                "new_phone": new_phone,
                "session_id": session.session_id,
                "changed_at": datetime.utcnow().isoformat(),
            },
            created_at=datetime.utcnow(),
        )
        db.add(case_update)

        # Commit all changes atomically
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update phone number. Please try again."
        )

    # Send confirmation SMS to both numbers
    try:
        # Notify old phone
        SMSService.send_notification(
            phone=old_phone,
            message=f"Your Boloo phone number has been changed to {new_phone}. If you didn't make this change, contact support immediately."
        )

        # Notify new phone
        SMSService.send_notification(
            phone=new_phone,
            message=f"Your Boloo phone number has been successfully changed. Welcome!"
        )
    except Exception as e:
        print(f"Notification send error: {str(e)}")

    return PhoneChangeResponse(
        success=True,
        message="Phone number changed successfully",
        new_phone=new_phone,
    )


@router.get("/history")
async def get_phone_change_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get phone change history for current user

    Returns list of phone change attempts with status
    """
    history = db.query(PhoneChangeRequest).filter(
        PhoneChangeRequest.user_id == current_user.id
    ).order_by(PhoneChangeRequest.created_at.desc()).limit(10).all()

    return {
        "history": [
            {
                "session_id": item.session_id,
                "status": item.status,
                "current_phone": item.current_phone,
                "new_phone": item.new_phone if item.status == "completed" else None,
                "created_at": item.created_at,
                "completed_at": item.completed_at,
            }
            for item in history
        ]
    }
