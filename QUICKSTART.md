# 🚀 FinanceApp Quick Start Guide

Get FinanceApp up and running in under 5 minutes!

## ⚡ Quick Installation

### Option 1: One-Command Install (Linux/macOS)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv first
git clone <your-repo-url>
cd FinanceApp
./install.sh  # Run the automated installer
```

### Option 2: Manual Install
```bash
git clone <your-repo-url>
cd FinanceApp
uv sync  # or: pip install -r requirements.txt
uv run python -m spacy download en_core_web_lg
```

## 🏃‍♂️ Quick Start

1. **Start the server:**
   ```bash
   uv run uvicorn app.main:app --reload --port 8000
   ```

2. **Open your browser:**
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/ping

3. **Test with a sample SMS:**
   ```bash
   curl -X POST "http://localhost:8000/api/parse_expense" \
        -H "Content-Type: application/json" \
        -d '{"message": "Rs.500 debited for UPI transfer to John Doe"}'
   ```

## 📱 Sample SMS to Test

Try these different SMS formats:

- **UPI**: "Rs.1000 debited for UPI transfer to Merchant Name"
- **ATM**: "Rs.5000 withdrawn from ATM at Location"
- **Credit Card**: "Rs.2500 charged on your HDFC Credit Card"
- **Loan**: "EMI of Rs.5000 debited for your Personal Loan"

## 🔧 Troubleshooting

- **Port already in use**: Change port with `--port 8001`
- **spaCy model not found**: Run `python -m spacy download en_core_web_lg`
- **Import errors**: Ensure you're in the virtual environment

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the interactive API docs at `/docs`
- Check out the [parser.py](app/services/parser.py) for customization options

---

**Need help?** Check the full README or open an issue in the repository.
