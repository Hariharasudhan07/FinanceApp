# routes/expenses.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
from app.services.parser import parse_sms_spacy
from typing import Optional, Dict

router = APIRouter()

class SMSInput(BaseModel):
    sms_text: str
from app.services.parser import parse_sms_spacy

router = APIRouter()

@router.get("/ping")
def health_check():
    return {"status": "Server is running"}





from app.services.parser import parse_sms_spacy, SMSParseError


class SMSRequest(BaseModel):
    message: str
    timestamp: datetime = datetime.now()

@router.post("/parse_expense")
async def parse_expense(sms: SMSRequest):
    try:
        parsed_data = parse_sms_spacy(sms.message, sms.timestamp)
        return {"success": True, "data": parsed_data}
    except SMSParseError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")