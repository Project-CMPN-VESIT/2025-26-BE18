from agno.agent import Agent, RunOutput  # noqa
from agno.models.google import Gemini

agent = Agent(model=Gemini(id="gemini-2.5-flash"), markdown=True)

# Get the response in a variable
# run: RunOutput = agent.run("Share a 2 sentence horror story")
# print(run.content)

# Print the response in the terminal
agent.print_response("Share a 2 sentence horror story")