import ast
from openai import AzureOpenAI
import os
from dotenv import load_dotenv
from datetime import datetime
from utils.prompt_config import get_analysis_prompt

load_dotenv()

try:
    client = AzureOpenAI(
    api_key=os.getenv("API_KEY"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("API_BASE")
)
except Exception as e:
    raise RuntimeError(f"Erreur lors de l'initialisation du client Azure OpenAI : {e}")

def format_duration(seconds):
    if seconds >= 3600:
        return f"≈ {round(seconds / 3600, 2)} h"
    elif seconds >= 60:
        return f"≈ {round(seconds / 60, 2)} min"
    else:
        return f"≈ {round(seconds, 2)} sec"

def compute_avg_ai_latency(conversation_history):
    # Sort messages chronologically
    messages = sorted(conversation_history, key=lambda m: m["timestamp"])

    for msg in messages:
        ts = msg["timestamp"].split(".")[0]  # strip microseconds
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        msg["dt"] = datetime.fromisoformat(ts)

    latencies = []
    user_count = 0

    for i, msg in enumerate(messages):
        if msg["role"] == "user":
            user_count += 1
            if user_count == 1:
                continue  # skip first user msg

            # find previous assistant
            for j in range(i - 1, -1, -1):
                if messages[j]["role"] == "assistant":
                    delta = (msg["dt"] - messages[j]["dt"]).total_seconds()
                    if delta > 0:
                        latencies.append(delta)
                    break

    if not latencies:
        return "N/A"

    avg = sum(latencies) / len(latencies)
    return format_duration(avg)

def compute_time_stats(conversation_history):
    if not conversation_history:
        return {
            "total_messages": 0,
            "total_duration_minutes": 0.0,
            "num_gaps_over_30mins": 0,
            "user_returned_after_30mins": False,
            "avg_ai_latency_seconds": 0.0
        }

    # Convert timestamps and sort
    messages = sorted(conversation_history, key=lambda m: m["timestamp"])
    for msg in messages:
        ts = msg["timestamp"]
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        msg["dt"] = datetime.fromisoformat(ts)

    total_messages = len(messages)
    total_active = 0.0
    num_gaps = 0

    # Total active duration + gaps
    for i in range(len(messages) - 1):
        dt1 = messages[i]["dt"]
        dt2 = messages[i + 1]["dt"]
        delta_min = (dt2 - dt1).total_seconds() / 60.0

        if delta_min > 30:
            num_gaps += 1
        else:
            total_active += delta_min


    avg_latency = compute_avg_ai_latency(conversation_history)

    return {
        "total_messages": total_messages,
        "total_duration_minutes": round(total_active, 2),
        "num_gaps_over_30mins": num_gaps,
        "user_returned_after_30mins": num_gaps > 0,
        "avg_ai_latency_seconds": avg_latency
    }

def compute_size_stats(conversation_history):
    """
    Calcule la taille (nombre de caractères) moyenne des messages
    pour l'utilisateur et pour l'assistant.
    """
    user_sizes = []
    assistant_sizes = []

    for msg in conversation_history:
        size = msg.get("size", len(msg["content"]))
        if msg["role"] == "user":
            user_sizes.append(size)
        elif msg["role"] == "assistant":
            assistant_sizes.append(size)

    avg_user_size = sum(user_sizes) / len(user_sizes) if user_sizes else 0
    avg_ai_size = sum(assistant_sizes) / len(assistant_sizes) if assistant_sizes else 0

    return {
        "avg_user_size": avg_user_size,
        "avg_ai_size": avg_ai_size
    }

def analyze_final_idea(conversation_history, final_idea):
    prompt = get_analysis_prompt(conversation_history, final_idea)
    try:
        response = client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un expert en évaluation d'idées. "
                        "Tu dois renvoyer UNIQUEMENT un dictionnaire Python valide."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.0
        )
        raw_response = response.choices[0].message.content
        parsed = ast.literal_eval(raw_response)
        originality_score = parsed.get('originality_score', 0)
        matching_score = parsed.get('matching_score', 0)
        assistant_influence_score = parsed.get('assistant_influence_score', 0)
        analysis_details = parsed.get('analysis_details', {})

    except Exception as e:
        originality_score = 0
        matching_score = 0
        assistant_influence_score = 0
        analysis_details = f"Erreur lors de la récupération du dict Python : {str(e)}"

    return originality_score, matching_score, analysis_details, assistant_influence_score
