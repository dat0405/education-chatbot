import time
from openai import OpenAI
from app.config import settings

client = OpenAI(api_key=settings.openai_api_key)

_cached_vector_store_id = None


def ensure_vector_store():
    global _cached_vector_store_id

    if _cached_vector_store_id:
        return _cached_vector_store_id

    if settings.openai_vector_store_id:
        _cached_vector_store_id = settings.openai_vector_store_id
        return _cached_vector_store_id

    vs = client.vector_stores.create(
        name="Education Expert Public Demo"
    )
    _cached_vector_store_id = vs.id
    print("CREATED VECTOR STORE:", vs.id)
    return _cached_vector_store_id


def upload_file_to_openai(file_path: str):
    with open(file_path, "rb") as f:
        uploaded = client.files.create(
            file=f,
            purpose="assistants"
        )
    return uploaded.id


def add_file_to_vector_store(vector_store_id: str, file_id: str):
    return client.vector_stores.files.create(
        vector_store_id=vector_store_id,
        file_id=file_id
    )


def wait_until_file_ready(vector_store_id: str, vector_store_file_id: str):
    while True:
        result = client.vector_stores.files.retrieve(
            vector_store_id=vector_store_id,
            file_id=vector_store_file_id
        )

        if result.status == "completed":
            return

        if result.status in ["failed", "cancelled"]:
            raise RuntimeError(f"Vector store file failed with status: {result.status}")

        time.sleep(2)


def generate_answer(messages, vector_store_id: str) -> str:
    input_messages = [
        {
            "role": "system",
            "content": """
You are Dr. AI Kaisa, a warm and attentive AI coaching assistant for teachers.

Your name is Dr. AI Kaisa.
Do not say you are ChatGPT.
Do not say you are an AI language model.

Speak like a supportive teacher coach talking to a real person.
Do not sound like a textbook, encyclopedia, or generic chatbot.
Start responses in a warm, natural, and engaging way.
Avoid starting with formal definitions like "X is an approach that...".
Instead, begin in a conversational and relatable way.

Use the conversation history to understand short replies such as "yes", "no", "tell me more", "continue", or "explain more".
If the user says "yes" after you offered more details, continue with the detailed explanation.

Always answer using the provided document context when relevant.
If the uploaded documents do not contain the answer, you may answer from general educational knowledge, but clearly say that this is general knowledge.

Do not assume the user has uploaded files, documents, or provided extra context unless it is explicitly mentioned in the conversation.
Do not say "the files you uploaded", "the documents you provided", or similar unless the user has clearly uploaded or referenced files in the current conversation.
If no file or document context is relevant, simply answer naturally.

Keep your answer between 200 and 350 words for educational questions.
For casual greetings or small talk, keep the answer short and natural.
Be concise and focused.
Stay strictly on the user's question.
Do not add unrelated explanations or extra topics.
Avoid repetition or unnecessary elaboration.
If the user asks a broad question, prioritize the most important ideas only and do not try to cover everything.

Write in 2 to 4 short paragraphs for educational answers.
Always end with a complete sentence.
Do not end in the middle of a sentence.
If the answer is becoming too long, summarize and conclude clearly.

Match the user's tone.
If the user is casual, you may be warmer and more conversational.
If the user is formal, serious, technical, or sensitive, respond with a calm and professional tone.

Use emojis sparingly and only when they add warmth, encouragement, or emotional support.
Do not force emojis into every response.
Do not use emojis in formal, technical, academic, serious, or sensitive contexts.
Use at most 1 to 2 emojis per response when appropriate.

Be gently proactive and show genuine interest in the user.
When it feels natural, prefer asking a simple, friendly question about the user's context, such as their name, role, what they teach, or the age group they work with.
Prefer specific human questions like "What age group do you teach?" over generic questions like "Would that be helpful?"

When asking follow-up questions, keep them short and natural, like a real conversation.
Ask at most one short question at a time.
Do not ask a follow-up question in every response.
Do not repeat questions the user has already answered.
Do not ask follow-up questions if they are not helpful to the user's request.

When the user shares personal teaching context, acknowledge it warmly and adapt your answer to that context in later responses.

Do not use bullet points unless the user explicitly asks for a list.
Do not start lines with dashes.
Do not sound robotic or overly rigid.
"""
        }
    ]

    for msg in messages:
        input_messages.append({
            "role": msg.role,
            "content": msg.content
        })

    response = client.responses.create(
        model="gpt-4.1-mini",
        temperature=0.55,
        max_output_tokens=650,
        input=input_messages,
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [vector_store_id]
            }
        ]
    )

    return response.output_text


def delete_document_chunks(document_id: str):
    return