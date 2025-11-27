from dotenv import load_dotenv
import os

load_dotenv()

print("RESULTADO:", os.getenv("GEMINI_API_KEY"))
