A modern, open-source desktop application for Windows to manage personal debts, loans, and finances with powerful tracking and analysis tools, including AI-powered insights.

**System Requirement:** This application is built for **Windows 10 and Windows 11**

## Key Features

- **Comprehensive Ledger:** Full CRUD (Create, Read, Update, Delete) support for all debts and loans.

- **Transaction Tracking:** Log individual payments and repayments against any ledger entry.

- **Visual Dashboard:** An immaculate dashboard with charts and key metrics, including:
  - Total Debt vs. Loan Balances (Pie Chart)
  - Net Worth Over Time (Line Chart)
  - Detailed Financial Summary

- **Tagging System:** Organize entries with a flexible, built-in tagging system, including support for custom tags.

- **Financial Journal:** Keep timestamped notes and thoughts about your financial journey.

- **Advanced Tools:**
  - **Debt Snowball Strategy:** Get an AI-powered recommendation on which debt to prioritize.
  - **What-If Calculator:** See how extra monthly payments can accelerate your debt-free date.
  - **Net Worth Logger:** Track your net worth over time with simple snapshots.

- **AI Co-Pilot (Optional):**
  - **Financial Health Check:** Get a detailed report and actionable suggestions from an AI assistant.
  - **AI Chat:** Have a conversational Q&A session about your finances.
  - **AI Command Bar:** Use natural language to perform actions like "add a $500 debt for rent".

- **Data Portability:**
  - **Export to CSV:** Export all your ledger and transaction data for use in other tools like Excel or Power BI.
  - **Automatic Saving:** Your data is saved automatically on close, with a manual save option available.

- **Professional Installer:** Packaged in a user-friendly `setup.exe` for easy installation on Windows.

---

## For Users: Installation

Getting started is easy. No need to install Python or any dependencies.

1.  Go to the [**Releases Page**](https://github.com/Woak0/Finance-Board/releases/latest).
2.  Under the "Assets" section of the latest release, download the `FinanceBoard-1.0.1-setup.exe` file.
3.  Run the downloaded installer and follow the on-screen instructions.

That's it! The application will be installed on your computer, complete with Start Menu and desktop shortcuts.

---

## For Developers: Building from Source

If you'd like to run the application from the source code or contribute to the project, follow these steps.

### 1. Setup the Environment

```bash
# Clone the repository
git clone https://github.com/Woak0/Finance-Board.git
cd Finance-Board

# Create and activate a virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate

# Install the required packages
pip install -r requirements.txt

# To run the Application use the following:
python main.py

# Building the executable
1. Make sure you have an icon.ico file in the assets/ directory
2. Run the build script:
.\build.bat

3. This will create the dist/FinanceBoard folder.
4. To create the final setup.exe, use the inno setup tool and follow the steps in the wizard.
```

