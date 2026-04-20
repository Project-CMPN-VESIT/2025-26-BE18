from agno.agent import Agent, RunOutput
from agno.models.google import Gemini
import json
from typing import Dict, Any

class IntentClassify:
    def __init__(self):
        self.agent = Agent(
            model=Gemini(id="gemini-2.5-flash"),
            # tools=[],
            markdown=False
        )
        
    def intent_classify(self, query: str) -> str:
        """
        Extract the intent from the user's query
        """
        try:
            prompt = f"""
                You are an intent extraction agent. 
                Your task is to extract the **location/place name** mentioned in the user's query.

                Rules:
                - Only return the location mentioned explicitly in the query.
                - Analyze the query neatly and give the location, Like "What is groundwater level at Junnar" so Junnar here is the location.
                - If the query contains "my location", then return "current location".
                - Respond ONLY in strict JSON format:
                {{
                    "location": "<extracted_place>"
                }}

                User Query: {query}
                """

            run_response: RunOutput = self.agent.run(prompt)
            content = run_response.content.strip()
            
            if content.startswith("```json"):
                content = content[7:-3].strip()

            parsed = json.loads(content)
            return parsed.get("location", "Unrecognized")  # Fixed: Use "location" key

        except json.JSONDecodeError:
            return "Unrecognized"
        except Exception as e:
            return f"Error: {str(e)}"