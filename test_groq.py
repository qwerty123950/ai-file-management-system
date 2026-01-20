# test_groq.py

from backend.services.chat_service import groq_chat

doc = "Apache Pig is a high-level platform for creating MapReduce programs."
instruction = "Summarize this in 20 words."

print(groq_chat(doc, instruction))

