from datetime import timezone, datetime
import json
import requests

from Backend.core.ledger_manager import LedgerEntry
from Backend.core.transaction_manager import Transaction
from Backend.core.summary_calculator import calculate_balance_for_entry

class FinancialAnalyser:
    def __init__(self, api_key: str | None):
        """Initialises the analyser with the provided API key."""
        self.api_key = api_key
        self.models = {
            "parser": "mistralai/mistral-7b-instruct:free", 
            "analyst": "mistralai/mistral-7b-instruct:free", 
        }
        print("AI Analyser initialised.")

    def _call_ai(self, system_prompt: str, user_prompt: str, model_key: str = "analyst", is_json_mode: bool = False) -> str:
        """Private helper to call the external AI API with a separated prompt and specified model."""
        if not self.api_key:
            return "AI feature disabled. An API key from OpenRouter.ai is required."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:3000", 
            "X-Title": "Financial Co-Pilot",
        }
        
        data = {
            "model": self.models.get(model_key, self.models["analyst"]),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        if is_json_mode:
            data["response_format"] = {"type": "json_object"}

        try:
            print(f"Contacting AI assistant (using model: {data['model']})...")
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=90)
            response.raise_for_status()
            response_json = response.json()
            content = response_json['choices'][0]['message']['content']
            return content.strip()
        except requests.exceptions.RequestException as e:
            return f"Error connecting to AI service: {e}"
        except (KeyError, IndexError):
            return "Error: Received an unexpected response format from the AI service."

    def _create_financial_context_string(self, all_entries: list[LedgerEntry], all_transactions: list[Transaction]) -> str:
        """Creates a detailed, readable string of the user's financial data for the AI."""
        
        context_parts = []
        
        debt_entries = [e for e in all_entries if e.entry_type == 'debt']
        loan_entries = [e for e in all_entries if e.entry_type == 'loan']

        total_debt_balance = sum(calculate_balance_for_entry(d, all_transactions) for d in debt_entries)
        total_loan_balance = sum(calculate_balance_for_entry(l, all_transactions) for l in loan_entries)
        
        context_parts.append(f"### Overall Financial Snapshot\n- Total Debt Owed: ${total_debt_balance:,.2f}\n- Total Owed to You (Loans): ${total_loan_balance:,.2f}\n")

        if all_entries:
            context_parts.append("### Detailed Ledger Entries")
            for entry in sorted(all_entries, key=lambda e: (e.entry_type, e.label)):
                balance = calculate_balance_for_entry(entry, all_transactions)
                if balance > 0.01:
                    context_parts.append(f"- **{entry.label}** ({entry.entry_type.capitalize()}, Status: {entry.status.capitalize()})\n  - Original Amount: ${entry.amount:,.2f}\n  - Current Balance: ${balance:,.2f}")
        
        if all_transactions:
            context_parts.append("\n### Recent Transactions (last 10)")
            for t in sorted(all_transactions, key=lambda t: t.date_paid, reverse=True)[:10]:
                 context_parts.append(f"- {t.date_paid.strftime('%Y-%m-%d')}: {t.label} (${t.amount:,.2f})")
                 
        return "\n".join(context_parts)

    def generate_insights(self, all_entries: list[LedgerEntry], all_transactions: list[Transaction]) -> str:
        """Generates a financial health check report using a much better context."""
        
        if not all_entries and not all_transactions:
            system_prompt = """
            You are a friendly and knowledgeable financial guide from Australia. A new user is starting their financial journey from scratch. Your goal is to provide three simple, powerful, and universally applicable tips to set them up for success.

            **Core Directives:**
            1.  **Welcoming Tone:** Start with a warm welcome.
            2.  **Three-Point Structure:** Present your advice in a clear, numbered list.
            3.  **NEVER Recommend Specific Products:** Your advice must be generic.
            4.  **The Tips:** The three tips must cover: (1) A simple budgeting rule, (2) The importance of an emergency fund, and (3) The power of consistent tracking.
            """
            user_prompt = "I'm new here and want to get better with my finances. What are the first things I should know?"
            return self._call_ai(system_prompt, user_prompt)

        system_prompt = """
        You are a professional, encouraging, and detail-oriented financial analyst based in Australia. Your primary directive is to analyze the user's financial data and provide a concise, structured 'Financial Health Check'.

        **Core Directives:**
        1.  **NEVER Invent Data:** Base your entire analysis STRICTLY on the data provided in the user's context.
        2.  **Strict Structure:** Your response MUST follow this exact three-part structure, using these exact Markdown headers:
            ### Financial Summary
            ### Key Observation
            ### Actionable Suggestion
        3.  **Tone:** Maintain a positive and empowering tone. Frame suggestions as opportunities for growth.
        4.  **Conciseness:** Keep the entire response under 200 words.
        5.  **NEVER Recommend Specific Products:** Do not mention any specific brand names, financial products, or third-party applications. Your advice must be generic.
        """
        context_string = self._create_financial_context_string(all_entries, all_transactions)
        user_prompt = f"Here is my financial data. Please provide your analysis.\n\n{context_string}"
            
        return self._call_ai(system_prompt, user_prompt)

    def answer_user_question(self, question: str, all_entries: list[LedgerEntry], all_transactions: list[Transaction]) -> str:
        """Answers a specific user question with their financial data as context. Now much smarter."""
        
        system_prompt = """
        You are an expert financial Q&A assistant from Australia. Your primary goal is to be helpful and accurate.

        **Core Directives:**
        1.  **Answer from Context:** You MUST answer the user's question based ONLY on the "Current Financial Context" provided. This context includes pre-calculated totals.
        2.  **Perform Simple Math:** You are allowed and encouraged to perform simple calculations (like summing or comparing numbers) based on the provided data to answer the user's question fully. For example, if asked for total debt, use the "Total Debt Owed" figure.
        3.  **Acknowledge Limits:** If the provided data truly does not contain the information needed to answer (e.g., asking about stock prices), you MUST respond with: "Based on the data you've provided, I don't have enough information to answer that question." DO NOT invent data.
        4.  **Stay On Topic:** If the question is clearly off-topic (e.g., medical advice, politics), respond with: "I can only answer questions related to personal finance."
        5.  **NEVER Recommend Specific Products:** Your advice must be generic. Do not mention any brand names.
        """
        
        context_string = self._create_financial_context_string(all_entries, all_transactions)
        user_prompt = f"**Current Financial Context:**\n{context_string}\n\n**My question is:** \"{question}\""
        
        return self._call_ai(system_prompt, user_prompt)

    def parse_command_to_json(self, command_str: str) -> dict:
        """Converts a user's natural language command into a structured JSON object."""
        system_prompt = f"""
        You are a data extraction robot. Your ONLY job is to extract a list of financial action commands from the user's text. You MUST respond with a single JSON object containing a key "commands", which holds a list of action objects.
    
        **Core Directives:**
        1.  **JSON ONLY:** Your entire response must be a single, valid JSON object.
        2.  **Distinguish Actions:** It is critical to distinguish between adding an 'entry' and adding a 'transaction'.
            - Use `action: "add_entry"` ONLY for creating a brand new debt or loan.
            - Use `action: "add_transaction"` for recording a payment or repayment against an EXISTING entry.
        3.  **Adhere to Schema:** The `action` key and `payload` must follow the provided schema.
        4.  **Handle Ambiguity:** If a command is ambiguous or not a financial action, you MUST use `action: "unknown"`. Do not guess.

        **Example 1 (New Debt):**
        User: "add a $50 debt for groceries"
        JSON: {{"commands": [{{"action": "add_entry", "payload": {{"entry_type": "debt", "label": "groceries", "amount": 50.0}}}}]}}
    
        **Example 2 (Repayment on Existing Loan):**
        User: "I received a $100 repayment for the money I lent to John"
        JSON: {{"commands": [{{"action": "add_transaction", "payload": {{"transaction_type": "repayment", "target_entry_label": "money I lent to John", "amount": 100.0}}}}]}}
    
        **Example 3 (List Loans):**
        User: "Can you please list my loans?"
        JSON: {{"commands": [{{"action": "list", "payload": {{"filter_by_type": "loan"}}}}]}}
        
        **JSON Schema Definition:**
        ```typescript
        {{
          "action": "add_entry" | "add_transaction" | "list" | "delete_entry" | "show_summary" | "unknown",
          "payload": {{
            // for add_entry
            "entry_type"?: "debt" | "loan",
            
            // for add_transaction
            "transaction_type"?: "payment" | "repayment",
            "target_entry_label"?: string, // CRITICAL for transactions
            
            // other fields
            "label"?: string,
            "amount"?: number
          }}
        }}"""
                
        user_prompt = f"Convert this command to JSON: \"{command_str}\""
    
        ai_response_str = self._call_ai(system_prompt, user_prompt, model_key="parser", is_json_mode=True)
        try:
            return json.loads(ai_response_str)
        except json.JSONDecodeError:
            print(f"DEBUG: AI returned non-JSON response: {ai_response_str}")
            return {"commands": [{"action": "unknown", "payload": {"reason": "AI failed to generate a valid command."}}]}