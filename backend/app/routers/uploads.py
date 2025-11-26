"""
Media Upload Router - Photo and Document uploads
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import logging
import uuid
import os
from datetime import datetime
import magic  # python-magic for file type detection

from app.database import get_db
from app.models import CaseAttachment, User
from app.utils.auth import get_current_user_or_dev
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# File upload settings
UPLOAD_DIR = settings.UPLOAD_DIR or "/tmp/boloo-uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
ALLOWED_DOCUMENT_TYPES = ["application/pdf"]
ALLOWED_TYPES = ALLOWED_IMAGE_TYPES + ALLOWED_DOCUMENT_TYPES

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)


def validate_file(file: UploadFile) -> tuple[bool, str]:
    """
    Validate uploaded file type and size
    Returns: (is_valid, error_message)
    """
    # Read file content for magic number validation
    file_content = file.file.read(2048)
    file.file.seek(0)  # Reset file pointer

    # Detect actual MIME type from content
    mime = magic.Magic(mime=True)
    detected_type = mime.from_buffer(file_content)

    # Validate type
    if detected_type not in ALLOWED_TYPES:
        return False, f"File type not allowed: {detected_type}. Allowed: images and PDFs only"

    # Validate size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset

    if file_size > MAX_FILE_SIZE:
        return False, f"File too large: {file_size / 1024 / 1024:.2f}MB (max 10MB)"

    return True, ""


@router.post("/upload")
async def upload_media(
    files: List[UploadFile] = File(...),
    case_id: str = None,
    current_user: User = Depends(get_current_user_or_dev),
    db: Session = Depends(get_db)
):
    """
    Upload photos or documents

    - **files**: List of files to upload (max 5)
    - **case_id**: Optional case ID to attach files to
    - Returns list of uploaded file URLs
    """
    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 files allowed per upload"
        )

    uploaded_files = []

    try:
        for file in files:
            # Validate file
            is_valid, error_msg = validate_file(file)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )

            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)

            # Save file
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            # Determine file type
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(file_path)
            file_type = "image" if mime_type.startswith("image/") else "document"

            # Create attachment record
            attachment = CaseAttachment(
                case_id=case_id if case_id else None,
                user_id=current_user.id,
                file_url=f"/uploads/{unique_filename}",
                file_type=file_type,
                file_name=file.filename,
                file_size=os.path.getsize(file_path),
                mime_type=mime_type,
            )
            db.add(attachment)

            uploaded_files.append({
                "file_name": file.filename,
                "file_url": attachment.file_url,
                "file_type": file_type,
                "file_size": attachment.file_size,
            })

        db.commit()

        logger.info(f"User {current_user.id} uploaded {len(files)} files")

        return {
            "success": True,
            "message": f"Successfully uploaded {len(files)} file(s)",
            "files": uploaded_files,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Upload error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/attachments/{case_id}")
async def get_case_attachments(
    case_id: str,
    current_user: User = Depends(get_current_user_or_dev),
    db: Session = Depends(get_db)
):
    """
    Get all attachments for a case
    """
    attachments = db.query(CaseAttachment).filter(
        CaseAttachment.case_id == case_id
    ).all()

    return {
        "success": True,
        "count": len(attachments),
        "attachments": [
            {
                "id": str(att.id),
                "file_url": att.file_url,
                "file_type": att.file_type,
                "file_name": att.file_name,
                "file_size": att.file_size,
                "created_at": att.created_at.isoformat(),
            }
            for att in attachments
        ],
    }


@router.delete("/attachments/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    current_user: User = Depends(get_current_user_or_dev),
    db: Session = Depends(get_db)
):
    """
    Delete an attachment (user must own it or be admin)
    """
    attachment = db.query(CaseAttachment).filter(
        CaseAttachment.id == attachment_id
    ).first()

    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )

    # Check ownership
    if attachment.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this attachment"
        )

    # Delete file from disk
    try:
        file_path = os.path.join(UPLOAD_DIR, os.path.basename(attachment.file_url))
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.error(f"Error deleting file: {e}")

    # Delete database record
    db.delete(attachment)
    db.commit()

    return {
        "success": True,
        "message": "Attachment deleted successfully"
    }
