# Personal Finance AI System

A sophisticated, end-to-end web application designed to automate personal finance management by intelligently parsing bank statement PDFs, storing the data in a multi-user database, and providing AI-powered expense categorization.

---

## Key Features

* **Multi-Bank PDF Parsing**: A robust ingestion pipeline that handles complex, password-protected PDF statements from multiple Indian banks (Union Bank, SBI, Bank of Baroda).
* **Multi-Format Support**: Intelligently detects and parses different statement formats from the same bank (e.g., standard e-statements vs. mobile app "Relationship Summaries").
* **Persistent Multi-User Database**: A secure SQLite backend built with SQLAlchemy ORM that keeps each user's financial data completely separate and allows for the storage of historical data over time.
* **AI-Powered Smart Categorization**: A machine learning model using Sentence-BERT embeddings and Cosine Similarity to learn from a user's habits and automatically suggest categories for new transactions.
* **Interactive Dashboard**: A clean user interface built with Streamlit that allows users to view their entire financial history, categorize expenses, and analyze their spending with interactive Plotly charts.
* **Robust Data Extraction**: Utilizes a two-step identification process (high-speed text analysis with an OCR fallback) to handle both text-based and image-based PDF content.

---

## Tech Stack & Architecture

This project was built with a focus on professional, scalable, and job-relevant technologies.

* **Backend**: Python
* **Frontend**: Streamlit
* **Database**: SQLite with SQLAlchemy ORM
* **Data Processing**: Pandas, NumPy
* **PDF Parsing**: pdfplumber, pytesseract (OCR), pikepdf
* **AI/ML**: sentence-transformers, scikit-learn

The core of the data pipeline is built on a "Manager-Experts" design pattern. A central "Manager" (`bank_parser.py`) identifies the bank, while dedicated "Expert" classes (`parsers.py`) handle the unique parsing logic for each specific bank and format. This architecture makes the system highly scalable and easy to maintain.

---

## Setup & Installation

To run this project locally, please follow these steps:

**1. Prerequisites:**
* Python 3.10+
* Tesseract OCR Engine installed and configured on your system.

**2. Clone the repository:**
```bash
git clone [https://github.com/Gaurang2737/personal-finance-AI-system.git](https://github.com/Gaurang2737/personal-finance-AI-system.git)
cd personal-finance-AI-system
```
### 3. Create and activate a virtual environment:
* **On Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```
* **On macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

---
### 4. Install the required packages:
```bash
pip install -r requirements.txt
```

### 5. Run the Streamlit application:
```bash
streamlit run app.py
```

## Current Status & Next Steps
The project has successfully completed its foundational data and intelligence layers. The core functionality of parsing, storing, and categorizing transactions is fully implemented. The next major feature in development is the AI Advisor, a chatbot that will allow users to ask natural language questions about their finances.
