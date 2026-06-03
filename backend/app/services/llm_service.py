from groq import Groq

from backend.app.core.config import settings

client = Groq(
    api_key=settings.GROQ_API_KEY
)


def build_chat_prompt(
    question: str,
    context: str,
    history: str
) -> str:
    if history:
        history_section = f"Conversation History:\n{history}\n\n"
    else:
        history_section = "Conversation History:\nNone\n\n"

    return f"""
{history_section}Retrieved Context:
{context}

Current Question:
{question}

Instructions:
- Use conversation history to resolve references such as: it, its, they, them, that concept, the model.
- Use retrieved context as the primary source of truth.
- If history conflicts with retrieved context, trust retrieved context.
- If answer is not found in context, say so.
"""


def generate_answer(
    question: str,
    context: str,
    history: str
):
    prompt = build_chat_prompt(
        question,
        context,
        history
    )

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],

        temperature=0
    )

    return response.choices[0].message.content