#ainko    https://generativelanguage.googleapis.com/v1beta/openai 

#Gemini API Key

from agent import AsyncOpenAi, OpenAIChatCompletionModel, Agent, Runner

#key = config("GEMINI_API_KEY")
#base_url = config("BASE_URL")

key = "AIzaSyBZjpcR5YzONUsit_S8flfwm24aerBY9Lw"
base_url = "https://generativelanguage.googleapis.com/v1beta/openai"

gemini_client = AsyncOpenAI(api_key=key, base_url=base_url)
MODEL = OpenAIChatComplationsModel(model="gemini-2.5-flash", openai_client=gemini_client)

agent = Agent(name="Ratan lal",instructions="good ai",model=MODEL)
res = Runner.run_sync(starting_agent=agent,input="2+2=?")
print(res.final_output)