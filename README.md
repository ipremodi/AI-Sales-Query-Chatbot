# Supermarket Analytics Chatbot

A chatbot that lets you query sales data using natural language. Built with Streamlit, MySQL, and Google's Gemini AI.

## What it does

Ask questions in plain English and get instant answers from your database. No SQL knowledge needed.

**Try asking:**
- "Show me all items from April 2025"
- "Top 10 products by sales"
- "What items contain DETTOL?"

## Setup

**Requirements:**
- Python 3.8+
- MySQL 8.0+
- Google Gemini API key ([get one free](https://makersuite.google.com/app/apikey))

**Install:**

```bash
# Clone and install dependencies
git clone https://github.com/yourusername/supermarket-chatbot.git
cd supermarket-chatbot
pip install -r requirements.txt

# Import database
mysql -u root -p < database.sql

# Configure app.py with your credentials
GEMINI_API_KEY = "your-key-here"
DB_PASSWORD = "your-password"

# Run
streamlit run app.py
```

## Project Structure

```
├── app.py              # Main application
├── database.sql        # Database with sample data
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## Database

The `martdatabase` table contains sales data for 70+ products across 7 categories:
- Personal Care (PC)
- Hair Care (HC)
- Groceries (GR)
- Beverages (BV)
- Snacks (SN)
- Dairy (DR)
- Household (HH)

Sample data covers December 2024 through April 2025.

## How it works??

1. User enters a natural language query
2. Gemini AI converts it to SQL
3. Query runs on MySQL database
4. Results display in a table (with charts when applicable)

## Tech Stack

- **Streamlit** - Web interface
- **Google Gemini AI** - Natural language processing
- **MySQL** - Database
- **Pandas** - Data handling

## Common Issues

**Database connection fails:**
- Check MySQL is running
- Verify credentials in app.py

**Table doesn't exist:**
- Make sure you ran `database.sql`
- Check with: `USE mahaveermart; SHOW TABLES;`

**API errors:**
- Verify your Gemini API key is valid
- Check you have quota remaining

## Future Ideas

- Export results to Excel
- Add user authentication
- Support for multiple databases
- Voice input
- Query history
