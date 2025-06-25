from transformers import pipeline
from Backend.core.ledger_manager import LedgerEntry
from Backend.core.transaction_manager import Transaction

class FinancialAnalyser:
    def __init__(self):
        """
        Initializes the Financial Analyser by loading the local language model.
        This may take some time and memory the first time it's run.
        """
        print("Initializing AI Analyser... (This may take a moment)")
        try:
            self.llm_pipeline = pipeline("text-generation", model="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
            print("AI Analyser ready.")
        except Exception as e:
            print(f"Error initializing AI model: {e}")
            print("The AI features will not be available. Please check your internet connection or library installation.")
            self.llm_pipeline = None
    
    def _call_ai(self, prompt: str) -> str:
        """Private helper to run the prompt through the LLM and return the clean response."""
        if not self.llm_pipeline:
            return "AI Analyser is not initialised."
        
        try:
            print("AI is analysing your data...")
            outputs = self.llm_pipeline(prompt, max_new_tokens=256, num_return_sequences=1, do_sample=True, temperature=0.5, top_k=30, top_p=0.95)
            
            ai_response = outputs[0]['generated_text']
            assistant_response_start = ai_response.find("<|assistant|>")
            if assistant_response_start != -1:
                return ai_response[assistant_response_start + len("<|assistant|>"):].strip()
            return ai_response.strip()
        except Exception as e:
            return f"An error occurred while communicating with the AI: {e}"

    def generate_insights(self, all_entries: list[LedgerEntry], all_transactions: list[Transaction]):

        debt_entries = [e for e in all_entries if e.entry_type == 'debt']

        has_debts = bool(debt_entries)
        has_transactions = bool(all_transactions)

        if has_debts and has_transactions:
            
            entries_text_block = "Current Active Debts:\n"
            active_debts = [e for e in debt_entries if e.status == 'active']
            paid_debt_count = len(debt_entries) - len(active_debts)

            if not active_debts:
                entries_text_block = "There are no active debts right now.\n"
            else:
                for entry in active_debts:
                    short_id = entry.id[:8]
                    line = f"- ID: {short_id}, Label: {entry.label}, Amount: ${entry.amount:,.2f}\n"
                    entries_text_block += line

            if paid_debt_count > 0:
                entries_text_block += f"\nNote: You have also successfully paid off {paid_debt_count} debt(s) previously. Great work!\n"
            
            transactions_text_block = "\nRecent Transaction History (last 15):\n"

            recent_transactions = sorted(all_transactions, key=lambda t: t.date_paid, reverse=True)[:15]

            for trans in recent_transactions:
                parent_short_id = trans.entry_id[:8]
                line = f"- Date: {trans.date_paid.strftime('%Y-%m-%d')}, Amount: ${trans.amount:,.2f}, Label: {trans.label}, (For Entry ID: {parent_short_id})\n"
                transactions_text_block += line

            prompt = f"""<|system|>
            You are a friendly and insightful financial assistant. Your task is to analyse the user's financial data.
            Your response should have three short sections:
            1.  **Summary:** A brief, encouraging overview of their current situation.
            2.  **Observation:** Point out one specific, interesting pattern or outlier transaction from their history.
            3.  **Suggestion:** Provide one clear, actionable tip for improvement or a question to make them think.
            Keep your entire response concise and under 150 words.</s>
            <|user|>
            Here is my financial data:
            {entries_text_block}
            {transactions_text_block}
            Please provide your analysis.</s>
            <|assistant|>
            """

            return self._call_ai(prompt)

        elif has_debts and not has_transactions:

            entries_text_block = "Current Active Debts:\n"
            active_debts = [e for e in debt_entries if e.status == 'active']
            paid_debt_count = len(debt_entries) - len(active_debts)

            if not active_debts:
                entries_text_block = "There are no active debts right now.\n"
            else:
                for entry in active_debts:
                    short_id = entry.id[:8]
                    line = f"- ID: {short_id}, Label: {entry.label}, Amount: ${entry.amount:,.2f}\n"
                    entries_text_block += line

            if paid_debt_count > 0:
                entries_text_block += f"\nNote: You have also successfully paid off {paid_debt_count} debt(s) previously. Great work!\n"

            prompt = f"""<|system|>
            You are a motivational and helpful financial coach. The user is just getting started and has listed their debts but hasn't recorded any payments yet. Your goal is to provide encouragement and a simple, actionable first step to avoid feeling overwhelmed.
            Your response should:
            1.  Acknowledge their positive first step of tracking their debts.
            2.  Briefly and simply explain the "Debt Snowball" method (focusing on paying off the smallest debt first to build momentum).
            3.  Encourage them to make their first payment, no matter how small, on their smallest debt.
            Keep your tone positive and empowering.</s>
            <|user|>
            I have the following debts but haven't made any payments yet:
            {entries_text_block}
            What's a good way to start?</s>
            <|assistant|>
            """

            return self._call_ai(prompt)
        
        elif not has_debts and not has_transactions:

            prompt = f"""<|system|>
            You are a friendly and knowledgeable financial assistant. The user is new to the app and has a blank slate. Your task is to provide them with three foundational tips for building strong financial habits.
            Structure your response clearly with three numbered points. The tips should be:
            1.  **The 50/30/20 Rule:** Briefly explain how to allocate income (50% Needs, 30% Wants, 20% Savings/Debt).
            2.  **Emergency Fund:** Explain the importance of saving a small emergency fund.
            3.  **Track Everything:** Encourage them to use this app to track all their debts and loans to get a clear picture of their finances.
            Keep the tone welcoming and simple.</s>
            <|user|>
            I'm new here and want to get better with my finances. What are the first things I should know?</s>
            <|assistant|>
            """

            return self._call_ai(prompt)
        
        else:
            return "Your data is in an usual state. Please add a debt or loan to provide context for your transactions."
        
    def answer_user_question(self, question: str, all_entries: list, all_transactions: list) -> str:
        entries_text_block = "Current Debts and Loans:\n"
        for entry in all_entries:
            entries_text_block += f"- {entry.label}: ${entry.amount:,.2f}\n"

        transactions_text_block = "Recent Transactions:\n"
        for trans in all_transactions[:15]:
            transactions_text_block += f"- {trans.label}: ${trans.amount:,.2f}\n"
            
        prompt = f"""<|system|>
        You are an expert financial assistant. Your role is to answer the user's question based on the financial context provided. Be helpful, clear, and responsible. If the question is outside the scope of personal finance, politely decline to answer.</s>
        <|user|>
        Here is my current financial situation:
        {entries_text_block}
        {transactions_text_block}
        Based on that context, please answer my question: "{question}"</s>
        <|assistant|>
        """
            
        return self._call_ai(prompt)



