# app/services/parser_spacy.py
import spacy
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Tuple, Union

# Load spaCy model with error handling
try:
    nlp = spacy.load("en_core_web_lg")
except OSError:
    nlp = spacy.load("en_core_web_md")

# Comprehensive financial entity patterns
FINANCIAL_PATTERNS = {
    "amount": re.compile(
        r"(?:rs|inr|usd|aed|eur|sgd|gbp|\$|₹|€|£|¥|﷼)?\s*"
        r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)\b",
        re.IGNORECASE
    ),
    "account": re.compile(r"\b[a-z]?x{2,4}\d{2,4}\b|\b(?:acc|a/c|acct)\.? ?[a-z]?\d{4,}\b", re.IGNORECASE),
    "reference": re.compile(r"\b(?:ref|txn|trans|upi|trf|id|crn|urn)[:\-]?\s*[a-z0-9]{5,20}\b", re.IGNORECASE),
    "phone": re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "balance": re.compile(r"(?:bal(?:ance)?|avail(?:able)?)(?:[:\-]|\s+of|\s+is)?\s*(rs|inr|usd|aed|eur)?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)", re.IGNORECASE),
    "date_compact": re.compile(r"(\d{1,2})([a-z]{3})(\d{2,4})", re.IGNORECASE),
    "date_standard": re.compile(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})", re.IGNORECASE),
    "date_verbose": re.compile(r"(\d{1,2})\s+([a-z]{3,9})\s+(\d{4})", re.IGNORECASE),
    "transaction_indicators": re.compile(
        r"\b(debited|credited|paid|sent|received|transfer|recharge|withdrawn|billed|utilized|charged|repayment|emi|purchase)\b",
        re.IGNORECASE
    )
}

# Comprehensive category system with informational category
TRANSACTION_CATEGORIES = {
    "loan": {
        "keywords": [
            "loan", "emi", "equated monthly installment", "repayment", "disbursement", 
            "borrow", "lend", "credit limit", "credit line", "credit score", "creditline",
            "pre-approved", "sanctioned", "borrow limit", "loan a/c", "loan account"
        ],
        "providers": {
            "slice": ["slice", "pluxee"],
            "airtel": ["airtel black", "airtel payments bank"],
            "hdfc": ["hdfc credit", "hdfc bank credit"],
            "icici": ["icici credit", "icici bank credit"],
            "kotak": ["kotak credit", "kotak 811"],
            "cred": ["cred", "cRED"],
            "lazyPay": ["lazypay", "lazy pay"],
            "sbi": ["sbi credit", "state bank credit"]
        },
        "context_phrases": [
            r"repay\s+(?:rs|inr)?\s*\d+\.?\d*",
            r"credit\s+score",
            r"slice\s+app",
            r"airtel\s+black\s+id",
            r"emi\s+for",
            r"due\s+date"
        ]
    },
    "credit": {
        "keywords": [
            "credited", "received", "load", "added", "topped up", "deposit", 
            "income", "salary", "recredited", "refund", "reversal", "cashback",
            "interest", "bonus", "credit", "reimbursed", "transfer received",
            "funds added", "amount credited", "deposit successful"
        ],
        "exceptions": [
            "reversal of credit", "credit card payment", "credit score", 
            "credit limit", "credit line", "creditline"
        ]
    },
    "debit": {
        "keywords": [
            "debited", "spent", "withdrawn", "paid", "sent", "deducted", 
            "purchase", "billed", "used", "withdrew", "transfer", "payment", 
            "utilized", "charged", "reversal", "outstanding", "minimum due",
            "past due", "overdue", "amount debited", "transaction successful"
        ],
        "exceptions": [
            "reversal of debit", "credit card payment", "emi payment"
        ]
    },
    "investment": {
        "keywords": [
            "mf", "mutual fund", "sip", "stock", "equity", "investment",
            "portfolio", "groww", "coin", "zerodha", "upstox", "mf red",
            "mutualfund", "investment account"
        ],
        "context_phrases": [
            r"mf\s+investment",
            r"sip\s+on",
            r"stock\s+purchased"
        ]
    },
    "insurance": {
        "keywords": [
            "insurance", "premium", "policy", "claim", "renewal", "term plan",
            "health insurance", "life insurance", "car insurance", "bike insurance"
        ],
        "providers": [
            "lic", "bharti axa", "hdfc ergo", "icici lombard", "tata aig"
        ]
    },
    "emi": {
        "keywords": [
            "emi", "equated monthly installment", "installment", "emi payment",
            "emi due", "emi processed", "emi debited"
        ],
        "context_phrases": [
            r"emi\s+for\s+\w+",
            r"emi\s+processed\s+for"
        ]
    },
    "recharge": {
        "keywords": [
            "recharge", "topup", "top-up", "validity", "mobile recharge",
            "dth recharge", "data pack", "voice plan", "renewal"
        ],
        "providers": [
            "airtel", "jio", "vi", "vodafone", "idea", "bsnl", "reliance"
        ]
    },
    "atm": {
        "keywords": [
            "atm", "cash withdrawal", "cash withdraw", "withdrawn at atm",
            "atm transaction", "atm withdrawal"
        ]
    },
    "cheque": {
        "keywords": [
            "cheque", "check", "cheque deposit", "cheque cleared", 
            "cheque bounce", "cheque issued"
        ]
    },
    "informational": {
        "keywords": [
            "balance", "fund balance", "security balance", "portfolio", "update",
            "notification", "alert", "reminder", "promotional", "offer", "deal",
            "price", "rate", "buy", "sell", "investment opportunity", "market update"
        ],
        "exclusions": [
            "debited", "credited", "paid", "sent", "received", "transfer", "recharge",
            "withdrawn", "billed", "utilized", "charged", "repayment", "emi"
        ]
    }
}

# Merchant blacklists
MERCHANT_BLACKLIST = {
    "bank", "account", "a/c", "savings", "current", "balance", "available",
    "wallet", "upi", "refno", "reference", "id", "user", "app", "details",
    "call", "if not", "not you", "please", "contact", "customer care",
    "mobile", "recharge", "validity", "prepaid", "postpaid", "plan",
    "transaction", "amount", "rs", "inr", "usd", "aed", "eur", "date",
    "time", "location", "terminal", "pos", "card", "credit", "debit",
    "payment", "transfer", "to", "from", "at", "on", "for", "your",
    "account", "acc", "a/c", "xxx", "xx", "xxxx", "****", "card",
    "cardnumber", "crd", "crdno", "cardno", "card number", "cvv",
    "expiry", "exp", "valid", "thru", "thru date", "mm/yy", "mm/yy",
    "thank", "thanks", "regards", "team", "banking", "online", "app",
    "sms", "message", "alert", "notification", "service", "charges",
    "fund", "securities", "balance", "bal", "reported", "excludes"
}

# Global currency mapping
CURRENCY_CODES = {
    "rs": "INR", "inr": "INR", "₹": "INR",
    "usd": "USD", "$": "USD", "dollars": "USD",
    "aed": "AED", "dirhams": "AED",
    "eur": "EUR", "€": "EUR", "euros": "EUR",
    "gbp": "GBP", "£": "GBP", "pounds": "GBP",
    "sgd": "SGD", "singapore dollars": "SGD",
    "jpy": "JPY", "¥": "JPY", "yen": "JPY"
}

class SMSParseError(Exception):
    """Custom exception for SMS parsing failures"""
    pass

def is_transactional_message(text: str) -> bool:
    """
    Determine if the message represents an actual financial transaction
    
    Returns True for transactional messages, False for informational/promotional messages
    """
    text_lower = text.lower()
    
    # 1. Check for explicit transaction indicators
    if FINANCIAL_PATTERNS["transaction_indicators"].search(text_lower):
        return True
    
    # 2. Check for common transaction verbs in context
    transaction_verbs = {"pay", "send", "transfer", "spend", "use", "purchase", "withdraw", "recharge"}
    doc = nlp(text_lower)
    
    for token in doc:
        if token.lemma_ in transaction_verbs and token.pos_ == "VERB":
            return True
    
    # 3. Check for amount patterns with transaction context
    amount_indicators = ["by", "of", "for", "rs", "inr", "amount", "charged"]
    for indicator in amount_indicators:
        if indicator in text_lower:
            # Check if there's an amount after the indicator
            pos = text_lower.find(indicator) + len(indicator)
            if pos < len(text_lower):
                context = text_lower[pos:pos+30]
                if re.search(r"\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?", context):
                    return True
    
    # 4. Check for reference numbers which often indicate transactions
    if FINANCIAL_PATTERNS["reference"].search(text_lower):
        return True
    
    # 5. If we've reached here, it's likely informational
    return False

def detect_category(text: str) -> Tuple[str, str, float]:
    """
    Determine transaction category with comprehensive financial awareness
    
    Returns:
        (primary_category, subcategory, confidence_score)
    """
    text_lower = re.sub(r"[^\w\s]", " ", text.lower())
    text_lower = re.sub(r"\s+", " ", text_lower).strip()
    
    # 1. Check if this is even a transactional message
    if not is_transactional_message(text):
        return "informational", "general", 0.95
    
    # 2. Check for specialized categories first (loan, investment, insurance, etc.)
    for category, config in TRANSACTION_CATEGORIES.items():
        if category in ["credit", "debit", "informational"]:
            continue  # Skip basic categories for now
            
        # Check keywords
        if "keywords" in config:
            for kw in config["keywords"]:
                if kw in text_lower:
                    # Verify context if needed
                    if "context_phrases" in config:
                        if any(re.search(pattern, text_lower) for pattern in config["context_phrases"]):
                            # Check for specific providers where applicable
                            if category == "loan" and "providers" in config:
                                for provider, aliases in config["providers"].items():
                                    for alias in aliases:
                                        if alias in text_lower:
                                            return category, provider, 0.95
                            return category, "", 0.90
                    
                    # No context verification needed
                    return category, "", 0.85
    
    # 3. Check for loan category with provider identification
    if "loan" in TRANSACTION_CATEGORIES:
        loan_config = TRANSACTION_CATEGORIES["loan"]
        for kw in loan_config["keywords"]:
            if kw in text_lower:
                if any(re.search(pattern, text_lower) for pattern in loan_config["context_phrases"]):
                    # Identify specific loan provider
                    for provider, aliases in loan_config["providers"].items():
                        for alias in aliases:
                            if alias in text_lower:
                                return "loan", provider, 0.95
                    return "loan", "generic", 0.90
    
    # 4. Check for credit indicators
    credit_config = TRANSACTION_CATEGORIES["credit"]
    for kw in credit_config["keywords"]:
        if kw in text_lower:
            # Check exceptions
            if not any(exc in text_lower for exc in credit_config["exceptions"]):
                # Special handling for EMI-related credits
                if "emi" in text_lower and "credit" in text_lower:
                    return "emi", "credit", 0.85
                return "credit", "", 0.80
    
    # 5. Check for debit indicators
    debit_config = TRANSACTION_CATEGORIES["debit"]
    for kw in debit_config["keywords"]:
        if kw in text_lower:
            # Check exceptions
            if not any(exc in text_lower for exc in debit_config["exceptions"]):
                # Special handling for EMI payments
                if "emi" in text_lower:
                    return "emi", "debit", 0.85
                # Identify transaction method
                if "upi" in text_lower:
                    return "debit", "upi", 0.80
                if "atm" in text_lower:
                    return "debit", "atm", 0.80
                if "pos" in text_lower or "swipe" in text_lower:
                    return "debit", "pos", 0.80
                return "debit", "general", 0.75
    
    # 6. Fallback to debit as most common transaction type
    return "debit", "general", 0.70

def extract_amount(text: str) -> Optional[Dict[str, object]]:
    """
    Extract amount with proper context awareness to avoid account number confusion
    
    Key improvements:
    1. Prioritizes amounts appearing after transaction keywords ("by", "of", "for")
    2. Specifically avoids matching account numbers (like X6072)
    3. Uses multiple validation checks to ensure we get the correct amount
    """
    text_lower = text.lower()
    
    # 1. Priority: Amount after transaction indicators with context
    transaction_indicators = ["by", "of", "for", "rs", "inr", "amount", "charged", "debited", "credited"]
    
    amounts = []
    
    for indicator in transaction_indicators:
        if indicator in text_lower:
            # Find the position of the indicator
            pos = text_lower.find(indicator) + len(indicator)
            # Look for amount pattern in the next 30 characters
            context = text[pos:pos+30]
            
            # Improved amount pattern that requires proper amount formatting
            amount_pattern = r"(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+\.\d{1,2}|\d+)"
            if match := re.search(amount_pattern, context):
                amount_str = match.group(1).replace(",", "")
                try:
                    amount = float(amount_str)
                    # Validate amount is reasonable for a transaction
                    if 1 <= amount <= 10_000_000:
                        # CRITICAL FIX: Check if this is likely an account number (preceded by X or #)
                        actual_pos = pos + match.start()
                        if actual_pos > 0:
                            prev_char = text[actual_pos - 1]
                            if prev_char in ["X", "x", "#"]:
                                continue  # Skip account numbers
                        
                        # Additional check: Ensure amount is properly separated
                        if actual_pos + len(match.group(0)) < len(text):
                            next_char = text[actual_pos + len(match.group(0))]
                            if not next_char.isspace() and next_char not in [".", ",", ")", "]", "}"]:
                                continue
                        
                        amounts.append((amount, actual_pos))
                except (ValueError, TypeError):
                    continue
    
    # Sort by position (earlier in text is more likely to be the transaction amount)
    if amounts:
        amounts.sort(key=lambda x: x[1])
        amount, _ = amounts[0]
        
        # Find currency
        currency = "INR"
        for currency_name, code in CURRENCY_CODES.items():
            if currency_name in text_lower:
                currency = code
                break
        
        return {
            "value": amount,
            "currency": currency,
            "formatted": f"{currency} {amount:,.2f}"
        }
    
    # 2. Look for MONEY entities with transaction context
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "MONEY":
            # Verify it's near transaction keywords
            start_idx = max(0, ent.start_char - 50)
            context = text_lower[start_idx:ent.start_char]
            if any(kw in context for kw in transaction_indicators):
                clean_amt = re.sub(r"[^\d.]", "", ent.text)
                if clean_amt.replace(".", "", 1).isdigit():
                    try:
                        amount = float(clean_amt)
                        if 1 <= amount <= 10_000_000:
                            # Find currency
                            currency = "INR"
                            for currency_name, code in CURRENCY_CODES.items():
                                if currency_name in text_lower:
                                    currency = code
                                    break
                            
                            return {
                                "value": amount,
                                "currency": currency,
                                "formatted": f"{currency} {amount:,.2f}"
                            }
                    except (ValueError, TypeError):
                        continue
    
    # 3. Fallback: Scan for amounts with more context awareness
    amount_pattern = r"(?:rs\.?\s*|inr\s*)(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)\b"
    if match := re.search(amount_pattern, text_lower):
        try:
            amount = float(match.group(1).replace(",", ""))
            if 1 <= amount <= 10_000_000:
                currency = "INR"
                for currency_name, code in CURRENCY_CODES.items():
                    if currency_name in text_lower:
                        currency = code
                        break
                
                return {
                    "value": amount,
                    "currency": currency,
                    "formatted": f"{currency} {amount:,.2f}"
                }
        except (ValueError, TypeError):
            pass
    
    # 4. Last resort: Find any numeric value that looks like an amount
    # CRITICAL FIX: Added account number protection
    for token in nlp(text):
        if token.like_num and token.ent_type_ != "DATE":
            try:
                amount = float(token.text.replace(",", ""))
                # Skip account numbers (X1234 pattern)
                if token.i > 0 and re.match(r"^[a-zA-Z]$", token.doc[token.i-1].text):
                    continue
                if 1 <= amount <= 10_000_000:
                    return {
                        "value": amount,
                        "currency": "INR",
                        "formatted": f"INR {amount:,.2f}"
                    }
            except (ValueError, TypeError):
                continue
    
    return None

def extract_merchant(text: str, category: str, subcategory: str) -> Optional[str]:
    """Extract merchant with comprehensive financial context handling"""
    text_lower = text.lower()
    
    # 1. For informational messages, return None or relevant entity
    if category == "informational":
        # Extract the company/app name if it's a promotional message
        if "app" in text_lower or "buy" in text_lower or "sell" in text_lower:
            # Look for app name patterns
            if match := re.search(r"on your ([a-zA-Z]+) App", text, re.IGNORECASE):
                return f"{match.group(1)} App"
            if match := re.search(r"only on ([a-zA-Z]+)", text, re.IGNORECASE):
                return f"{match.group(1)} App"
        # For balance updates, return the institution name
        if "balance" in text_lower or "fund" in text_lower:
            # Extract the institution name
            if match := re.search(r"^([A-Z\s]+) on", text):
                return match.group(1).strip()
        return None
    
    # 2. Special handling for specific categories
    if category == "loan" and subcategory != "generic":
        return f"{subcategory.title()} Loan"
    
    if category == "recharge":
        for provider in TRANSACTION_CATEGORIES["recharge"]["providers"]:
            if provider in text_lower:
                return f"{provider.title()} Recharge"
        return "Mobile Recharge"
    
    if category == "insurance":
        for provider in TRANSACTION_CATEGORIES["insurance"]["providers"]:
            if provider in text_lower:
                return f"{provider.title()} Insurance"
        return "Insurance Premium"
    
    if category == "investment":
        investment_providers = ["groww", "coin", "zerodha", "upstox", "mf utility"]
        for provider in investment_providers:
            if provider in text_lower:
                return f"{provider.title()} Investment"
        return "Investment"
    
    # 3. UPI transaction merchant extraction
    if category == "debit" and subcategory == "upi":
        # Look for patterns like "trf to MERCHANT" or "sent to MERCHANT"
        upi_patterns = [
            r"trf\s+to\s+([a-zA-Z0-9\s]{3,30})", 
            r"sent\s+to\s+([a-zA-Z0-9\s]{3,30})",
            r"paid\s+to\s+([a-zA-Z0-9\s]{3,30})",
            r"transfer\s+to\s+([a-zA-Z0-9\s]{3,30})"
        ]
        
        for pattern in upi_patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                merchant = match.group(1).strip()
                # Clean up merchant name
                merchant = re.sub(r"\s+Ref.*$", "", merchant)
                merchant = re.sub(r"\s+(?:UPI|ref|id|crn).*", "", merchant)
                return merchant.title()
    
    # 4. General merchant extraction
    merchant_indicators = ["to", "at", "from", "trf", "transfer", "recharge", "paid"]
    for indicator in merchant_indicators:
        if indicator in text_lower:
            pos = text_lower.find(indicator) + len(indicator)
            if pos < len(text):
                # Extract next 2-5 words as potential merchant
                candidate = text[pos:pos+50]
                # Remove reference numbers, amounts, and blacklisted terms
                candidate = re.sub(r"\b(?:ref|id|user|upi|rs|inr|amount|charged)\b.*", "", candidate, flags=re.IGNORECASE)
                candidate = re.sub(r"[^\w\s]", " ", candidate)
                words = [
                    w.capitalize() for w in candidate.split()[:5] 
                    if w.lower() not in MERCHANT_BLACKLIST and len(w) > 1
                ]
                if words:
                    return " ".join(words).strip()
    
    # 5. Fallback: Look for proper nouns after transaction verbs
    transaction_verbs = {"pay", "send", "transfer", "spend", "use", "purchase", "withdraw", "recharge"}
    doc = nlp(text)
    
    for token in doc:
        if token.lemma_ in transaction_verbs and token.pos_ == "VERB":
            for chunk in doc.noun_chunks:
                if chunk.root.head == token and chunk.root.dep_ in ("dobj", "pobj"):
                    words = [
                        w.text.capitalize() for w in chunk 
                        if w.text.lower() not in MERCHANT_BLACKLIST
                    ]
                    if words:
                        return " ".join(words)
    
    # 6. Default merchants for known transaction types
    if "atm" in text_lower:
        return "ATM Withdrawal"
    if "pos" in text_lower or "swipe" in text_lower:
        return "Card Purchase"
    if "cheque" in text_lower:
        return "Cheque Transaction"
    
    return "Merchant"

def extract_date(text: str, sms_timestamp: Optional[datetime] = None) -> Optional[str]:
    """Extract date with comprehensive global format support"""
    text_lower = text.lower()
    
    # 1. Handle relative dates first
    relative_dates = {
        "today": 0,
        "yesterday": -1,
        "tomorrow": 1,
        "now": 0,
        "just now": 0,
        "a moment ago": 0
    }
    
    for rel_date, offset in relative_dates.items():
        if rel_date in text_lower:
            base = sms_timestamp or datetime.now()
            return (base + timedelta(days=offset)).strftime("%Y-%m-%d")
    
    # 2. Compact date patterns (15May25, 02Aug25)
    if match := FINANCIAL_PATTERNS["date_compact"].search(text):
        day, month_abbr, year = match.groups()
        # Handle 2-digit vs 4-digit years
        if len(year) == 2:
            year = f"20{year}" if int(year) < 50 else f"19{year}"
        try:
            return datetime.strptime(f"{day} {month_abbr} {year}", "%d %b %Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    
    # 3. Standard date formats (dd/mm/yy, dd-mm-yyyy, etc.)
    if match := FINANCIAL_PATTERNS["date_standard"].search(text):
        parts = match.groups()
        # Try different interpretations based on locale
        for fmt in ["%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y", "%d.%m.%Y", "%m.%d.%Y"]:
            try:
                # Handle 2-digit years
                if len(parts[2]) == 2:
                    parts = (parts[0], parts[1], f"20{parts[2]}" if int(parts[2]) < 50 else f"19{parts[2]}")
                return datetime.strptime(f"{parts[0]} {parts[1]} {parts[2]}", fmt.replace("/", " ").replace("-", " ")).strftime("%Y-%m-%d")
            except ValueError:
                continue
    
    # 4. Verbose date formats (15 May 2025)
    if match := FINANCIAL_PATTERNS["date_verbose"].search(text):
        day, month, year = match.groups()
        try:
            return datetime.strptime(f"{day} {month} {year}", "%d %B %Y").strftime("%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(f"{day} {month} {year}", "%d %b %Y").strftime("%Y-%m-%d")
            except ValueError:
                pass
    
    # 5. Date indicators + next tokens
    date_indicators = ["on", "date", "for", "by", "at"]
    for indicator in date_indicators:
        if (pos := text_lower.find(indicator)) != -1:
            date_candidate = text[pos + len(indicator):pos + len(indicator) + 30]
            # Try to find date patterns in the candidate text
            if match := re.search(r"(\d{1,2})\s+([a-z]{3,9})\s+(\d{4})", date_candidate, re.IGNORECASE):
                try:
                    return datetime.strptime(f"{match.group(1)} {match.group(2)} {match.group(3)}", "%d %b %Y").strftime("%Y-%m-%d")
                except ValueError:
                    pass
    
    # 6. Fallback to SMS timestamp or today
    return (sms_timestamp or datetime.now()).strftime("%Y-%m-%d")

def extract_balance(text: str) -> Optional[Dict[str, object]]:
    """Extract balance information if present"""
    balances = []
    
    # 1. Find balance patterns
    for match in FINANCIAL_PATTERNS["balance"].finditer(text):
        currency = match.group(1) if match.group(1) else "INR"
        amount_str = match.group(2).replace(",", "")
        
        try:
            amount = float(amount_str)
            balances.append((amount, currency, match.start()))
        except (ValueError, TypeError):
            continue
    
    # 2. Return the most relevant balance (usually the one closest to "available")
    if balances:
        balances.sort(key=lambda x: x[2])  # Sort by position
        amount, currency, _ = balances[0]
        currency_code = CURRENCY_CODES.get(currency.lower(), currency.upper())
        
        return {
            "value": amount,
            "currency": currency_code,
            "formatted": f"{currency_code} {amount:,.2f}"
        }
    
    return None

def extract_reference(text: str) -> Optional[str]:
    """Extract transaction reference number if present"""
    if match := FINANCIAL_PATTERNS["reference"].search(text):
        ref = match.group(0)
        # Clean up reference format
        ref = re.sub(r"[:\-]\s*", " ", ref)
        ref = re.sub(r"\s+", " ", ref)
        return ref.strip().upper()
    return None

def parse_sms_spacy(sms_text: str, sms_timestamp: Optional[datetime] = None) -> Dict:
    """
    Parse ANY financial SMS into structured transaction data
    
    Args:
        sms_text: Raw SMS content from ANY bank/fintech globally
        sms_timestamp: Optional SMS timestamp for date resolution
        
    Returns:
        Structured transaction dictionary with comprehensive financial data
    """
    if not sms_text or not sms_text.strip():
        raise SMSParseError("Empty SMS content")
    
    try:
        # 1. Detect transaction category
        category, subcategory, confidence = detect_category(sms_text)
        
        # 2. Extract financial data
        amount = None
        merchant = None
        reference = None
        
        # Only extract transactional data for actual transactions
        if category != "informational":
            amount = extract_amount(sms_text)
            merchant = extract_merchant(sms_text, category, subcategory)
            reference = extract_reference(sms_text)
        
        transaction_date = extract_date(sms_text, sms_timestamp)
        balance = extract_balance(sms_text)
        
        # 3. Prepare comprehensive response
        result = {
            "raw_text": sms_text,
            "category": category,
            "subcategory": subcategory,
            "amount": amount["value"] if amount else None,
            "currency": amount["currency"] if amount else None,
            "formatted_amount": amount["formatted"] if amount else None,
            "merchant": merchant,
            "date": transaction_date,
            "balance": balance,
            "reference": reference,
            "description": sms_text,
            "parser": "spacy_universal_v4",
            "timestamp": datetime.now().isoformat(),
            "confidence": confidence
        }
        
        # 4. Add category-specific metadata
        if category == "loan":
            result["loan_provider"] = subcategory if subcategory != "generic" else merchant
        elif category == "investment":
            result["investment_platform"] = subcategory or merchant
        elif category == "insurance":
            result["insurance_provider"] = subcategory or merchant
        elif category == "informational":
            # Add additional fields for informational messages
            if "price" in sms_text.lower() or "rate" in sms_text.lower():
                result["info_type"] = "market_update"
            elif "balance" in sms_text.lower() or "fund" in sms_text.lower():
                result["info_type"] = "balance_update"
            elif "offer" in sms_text.lower() or "deal" in sms_text.lower() or "buy" in sms_text.lower():
                result["info_type"] = "promotion"
        
        return result
    
    except Exception as e:
        raise SMSParseError(f"Universal SMS parsing failed: {str(e)}") from e