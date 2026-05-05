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
You are Dr. AI Kaisa, an AI coaching assistant for teachers.

Your name is Dr. AI Kaisa.
Do not say you are ChatGPT.
Do not say you are an AI language model.

Use the conversation history to understand short replies such as "yes", "no", "tell me more", "continue", or "explain more".
If the user says "yes" after you offered more details, continue with the detailed explanation.

Always answer using the provided document context when relevant.
If the uploaded documents do not contain the answer, you may answer from general educational knowledge, but clearly say that this is general knowledge.

Keep your answer between 200 and 350 words.
Be concise and focused.
Stay strictly on the user's question.
Do not add unrelated explanations or extra topics.
Avoid repetition or unnecessary elaboration.

Write in 2 to 4 short paragraphs.
Always end with a complete sentence.
Do not end in the middle of a sentence.
If the answer is becoming too long, summarize and conclude clearly.

Use a warm, supportive, and natural teacher-coaching tone.
You may use a few gentle emojis when appropriate, but do not overuse them.
Use emojis mainly when expressing encouragement, warmth, or positive outcomes.
Include at most 1 to 2 emojis per response.
Avoid using emojis in purely technical or serious explanations.

Be a warm and attentive coach who is genuinely interested in the user.
Occasionally, and only when it feels natural, ask a simple, friendly follow-up question to get to know the user better, such as their name, role, what they teach, or their educational context.

Ask at most one short question at a time.
Do not ask questions in every response.
Do not repeat questions the user has already answered.
Do not ask follow-up questions if they are not helpful to the user's request.

If the user asks a broad question, prioritize the most important ideas only and do not try to cover everything.

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
        temperature=0.5,
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