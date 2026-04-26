from agno.agent import Agent, RunOutput
from agno.models.google import Gemini
import json
from typing import Dict, Any

class SummaryResponseAgent:
    def __init__(self):
        self.agent = Agent(
            model=Gemini(id="gemini-2.5-flash"),
            # tools=[],
            markdown=False
        )

    def summary_response(self, user_query: str, api_response: str) -> str:
        """
        Summarize and give the appropriate response from the provided response body wrt the query.
        """
        try:
            prompt = f"""
                You are a precise data interpretation agent, give the answer to the user question {user_query} and give the suitable response from data from the Api Response
                Do not invent or assume values. Only use fields that exist in the JSON.
                
                User Query: {user_query}  
                API Response: {api_response}
                
                give the output as the below example is json format
                 {{
                    "answer": "Total Groundwater Availability: Shirol has a total groundwater availability of 10,819.52 MCM (million cubic meters) for all purposes in the non-command area.
Stage of Extraction: The stage of groundwater extraction is 38.57%, indicating a "safe" category, suggesting sustainable groundwater use.
Recharge Data: The total recharge is 11,476.70 MCM, with contributions from rainfall (2,465.06 MCM), agriculture (8,686.83 MCM), surface irrigation (7,625.97 MCM), artificial structures (231.62 MCM), and water bodies (93.17 MCM).
Draft Data: The total groundwater draft is 4,172.86 MCM, primarily for agriculture (3,980.46 MCM) and domestic use (192.40 MCM), with no industrial use reported.
Availability for Future Use: 6,646.66 MCM is available for future use, indicating a significant buffer."
                }}
                
                if the ans is "The groundwater level for Shirol is not available in the provided data." then give the summary of the api response wrt the total groundwater level there and don't use the statement 'The groundwater level for Shirol is not available in the provided data' any where in the answer.
                """

            run_response: RunOutput = self.agent.run(prompt)
            content = run_response.content.strip()

            if content.startswith("```json"):
                content = content[7:-3].strip()

            parsed = json.loads(content)
            return parsed.get("answer", "Unrecognized")

        except json.JSONDecodeError:
            return "Unrecognized"
        except Exception as e:
            return f"Error: {str(e)}"
