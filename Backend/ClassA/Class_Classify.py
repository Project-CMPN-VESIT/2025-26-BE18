from agno.agent import Agent, RunOutput
from agno.models.google import Gemini
import json
from typing import Dict, Any

class QueryClassifier:
    def __init__(self):
        self.agent = Agent(
            model=Gemini(id="gemini-2.5-flash"),
            # tools=[],
            markdown=False
        )

    def classify(self, query: str) -> str:
        """
        Classify the user query into ClassA, ClassB, or ClassC using LLM.
        """
        try:
            prompt = f"""
                You are a query classification agent. 
                You must classify the given query into one of these 3 categories:

                - ClassA: Normal Users → Individual/local queries about a specific place or "my location".
                Examples: 
                    - "What's the groundwater level at Rajula?"
                    - "Groundwater level at my location"

                - ClassB: Farmers → Collective queries that ask about groups, lists, or conditions across multiple regions.
                Examples:
                    - "Give me all the critical regions"
                    - "Show all over exploited regions"

                - ClassX: Authorities → Any query that does not fit ClassA or ClassB, usually administrative, policy-related, or other.

                Your task:
                1. Read the user's query carefully.
                2. Apply the above rules strictly.
                3. Respond ONLY in strict JSON format, no extra text:
                {{
                    "class": "ClassA" | "ClassB" | "ClassX"
                }}

                User Query: {query}
                """


            run_response: RunOutput = self.agent.run(prompt)
            content = run_response.content.strip()

            if content.startswith("```json"):
                content = content[7:-3].strip()

            parsed = json.loads(content)
            return parsed.get("class", "Unrecognized")

        except json.JSONDecodeError:
            return "Unrecognized"
        except Exception as e:
            return f"Error: {str(e)}"