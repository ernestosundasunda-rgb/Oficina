import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

_groq = None

def get_groq() -> ChatGroq:
    global _groq
    if _groq is None:
        _groq = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1024,
        )
    return _groq