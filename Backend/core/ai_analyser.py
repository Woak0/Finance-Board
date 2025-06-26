from transformers import pipeline
from Backend.core.ledger_manager import LedgerEntry
from Backend.core.transaction_manager import Transaction
from datetime import timezone, datetime
import json
import requests
from dotenv import load_dotenv
import os

# --- Constants ---
API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Using a highly capable free model
MODEL_NAME = "deepseek/deepseek-coder-instruct" 

class FinancialAnalyser:
    def __init__(self, api_key: str | None):
        """Initialises the analyser with the provided API key."""
        self.api_key = api_key
        print("AI Analyser initialised.")

    def _call_ai(self, system_prompt: str, user_prompt: str, is_json_mode: bool = False) -> str:
        """Private helper to call the external AI API with a separated prompt."""
        if not self.api_key:
            return "AI feature disabled. An API key from OpenRouter.ai is required."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Financial Co-Pilot",
        }
        
        data = {
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        # Conditionally add the JSON response format constraint
        if is_json_mode:
            data["response_format"] = {"type": "json_object"}

        try:
            print("Contacting AI assistant...")
            response = requests.post(API_URL, headers=headers, json=data, timeout=90)
            response.raise_for_status()
            response_json = response.json()
            content = response_json['choices'][0]['message']['content']
            return content.strip()
        except requests.exceptions.RequestException as e:
            return f"Error connecting to AI service: {e}"
        except (KeyError, IndexError):
            return "Error: Received an unexpected response format from the AI service."

    def generate_insights(self, all_entries: list[LedgerEntry], all_transactions: list[Transaction]) -> str:
        """Generates a financial health check report."""
        debt_entries = [e for e in all_entries if e.entry_type == 'debt']
        has_debts = bool(debt_entries)
        has_transactions = bool(all_transactions)

        system_prompt = ""
        user_prompt = ""

        if has_debts and has_transactions:
            system_prompt = """
            You are a professional, encouraging, and detail-oriented financial analyst based in Australia. Your primary directive is to analyse the user's financial data and provide a concise, structured 'Financial Health Check'.

            **Core Directives:**
            1.  **NEVER Invent Data:** You must base your entire analysis STRICTLY on the data provided in the user's context. Do not invent numbers, trends, or transactions.
            2.  **Strict Structure:** Your response MUST follow this exact three-part structure, using these exact Markdown headers:
                ### Financial Summary
                ### Key Observation
                ### Actionable Suggestion
            3.  **Tone:** Maintain a positive and empowering tone. Frame suggestions as opportunities for growth.
            4.  **Conciseness:** Keep the entire response under 200 words.
            5. **NEVER Recommend Specific Products:** Do not mention any specific brand names, financial products, or third-party applications (e.g., Mint, YNAB, specific banks, etc.). Your advice must be generic.
            """
            entries_text_block = "Current Active Debts:\n" + "\n".join([f"- {e.label}: ${e.amount:,.2f}" for e in debt_entries if e.status == 'active'])
            transactions_text_block = "\nRecent Transactions:\n" + "\n".join([f"- {t.date_paid.strftime('%Y-%m-%d')}, {t.label}: ${t.amount:,.2f}" for t in sorted(all_transactions, key=lambda t: t.date_paid, reverse=True)[:15]])
            user_prompt = f"Here is my financial data:\n{entries_text_block}\n{transactions_text_block}\nPlease provide your analysis."

        elif has_debts and not has_transactions:
            entries_text_block = "Current Debts:\n" + "\n".join([f"- {e.label}: ${e.amount:,.2f}" for e in debt_entries])
            system_prompt = """
            You are a motivational financial coach from Australia. The user has taken the courageous first step of listing their debts but feels overwhelmed and hasn't started making payments. Your task is to provide a clear, simple, and encouraging action plan.

            **Core Directives:**
            1.  **Acknowledge and Praise:** Start by congratulating the user on tracking their finances, framing it as the most important step.
            2.  **Introduce the "Debt Snowball":** Simply and clearly explain the concept of focusing all extra effort on the smallest debt first to create a quick win and build psychological momentum.
            3.  **Provide a Clear Call to Action:** End by encouraging them to make one small payment towards their smallest debt today, emphasizing that starting is more important than the amount.
            4. **NEVER Recommend Specific Products:** Do not mention any specific brand names, financial products, or third-party applications (e.g., Mint, YNAB, specific banks, etc.). Your advice must be generic.
            """
            user_prompt = f"I have these debts but haven't started paying:\n{entries_text_block}\nWhat's a good way to start?"

        else:
            system_prompt = """
            You are a friendly and knowledgeable financial guide from Australia. A new user is starting their financial journey from scratch. Your goal is to provide three simple, powerful, and universally applicable tips to set them up for success.

            **Core Directives:**
            1.  **Welcoming Tone:** Start with a warm welcome.
            2.  **Three-Point Structure:** Present your advice in a clear, numbered list.
            3.  **NEVER Recommend Specific Products:** Do not mention any specific brand names, financial products, or third-party applications (e.g., Mint, YNAB, specific banks, etc.). Your advice must be generic.
            4.  **The Tips:** The three tips must cover:
                1.  A simple budgeting rule (like the 50/30/20 rule).
                2.  The concept and importance of a small emergency fund.
                3.  The power of consistent tracking (mentioning this app).
            """

            user_prompt = "I'm new here and want to get better with my finances. What are the first things I should know?"
            
        return self._call_ai(system_prompt, user_prompt)

    def answer_user_question(self, question: str, all_entries: list[LedgerEntry], all_transactions: list[Transaction]) -> str:
        """Answers a specific user question with their financial data as context."""
        entries_text_block = "Current Debts & Loans:\n" + "\n".join([f"- {e.label}: ${e.amount:,.2f}" for e in all_entries])
        transactions_text_block = "Recent Transactions:\n" + "\n".join([f"- {t.label}: ${t.amount:,.2f}" for t in all_transactions[:15]])
        system_prompt = """ 
        You are an expert financial Q&A assistant from Australia. You have one primary directive.
        **THE GOLDEN RULE:** You MUST answer the user's question based ONLY on the "Current Financial Context" provided.
        - If the context contains the information, use it to form your answer.
        - If the context is empty or does not contain the information needed, you MUST respond with ONLY the phrase: "Based on the data you've provided, I don't have enough information to answer that question."
        - DO NOT, under any circumstances, invent, create, or assume any numbers, figures, or scenarios. You are a data-driven assistant, not a creative storyteller.
        - If the question is clearly off-topic (e.g., medical advice, personal identity, politics, harmful content), respond with ONLY the phrase: "I can only answer questions related to personal finance.

        **NEVER Recommend Specific Products:** Do not mention any specific brand names, financial products, or third-party applications (e.g., Mint, YNAB, specific banks, etc.). Your advice must be generic.
        """

        user_prompt = f"Here is my financial situation:\n{entries_text_block}\n{transactions_text_block}\n\nMy question is: \"{question}\""
        return self._call_ai(system_prompt, user_prompt)

    def parse_command_to_json(self, command_str: str) -> dict:
        """Converts a user's natural language command into a structured JSON object."""
        today_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        system_prompt = f"""You are a hyper-precise data extraction model. Your ONLY function is to convert the user's command into a single, valid JSON object that strictly adheres to the provided schema.
        **Core Directives:**
        1.  **JSON ONLY:** Your entire response must be a single JSON object. Do not include any text before or after it, no explanations, no markdown ` ```json ` wrappers.
        2. **ONE ACTION ONLY:** You must only identify and process the FIRST logical command in the user's input. Ignore any subsequent requests in the same line. For example, if the user says "Add a debt and then show me the summary", you must ONLY process "Add a debt".
        3.  **Adhere to Schema:** The `action` key must be one of the allowed values. The `payload` must contain the relevant extracted fields.
        4.  **Infer Types:** Correctly infer data types (e.g., convert "$1,200.50" to the number `1200.5`).
        5.  **Handle Ambiguity:** If a command is ambiguous or not a financial action, you MUST use `action: "unknown"`. Do not try to guess.
        
        **JSON Schema Definition:**
        ```typescript
        {{
          "action": "add_entry" | "add_transaction" | "list" | "delete_entry" | "show_summary" | "unknown",
          "payload": {{
            // for add_entry
            "entry_type"?: "debt" | "loan",
            "label"?: string,
            "amount"?: number,
            "tags"?: string[],
            "comments"?: string,
            
            // for add_transaction
            "transaction_type"?: "payment" | "repayment",
            "target_entry_label"?: string,
            
            // for list
            "filter_by_type"?: "debt" | "loan" | "all",
            
            // for delete
            // uses target_entry_label
            
            // for show_summary
            "focus"?: "debt_balance" | "all",
            
            // for unknown
            "reason"?: string
          }}
        }}"""
                
        user_prompt = f"Convert this command to JSON: \"{command_str}\""

        ai_response_str = self._call_ai(system_prompt, user_prompt, is_json_mode=True)
        try:
            return json.loads(ai_response_str)
        except json.JSONDecodeError:
            print(f"DEBUG: AI returned non-JSON response: {ai_response_str}")
            return {"action": "unknown", "payload": {"reason": "AI failed to generate a valid command."}}



