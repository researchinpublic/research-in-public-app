"""
Kaggle Notebook: Research In Public - Agentic Support Ecosystem

This is a Python script version of the Jupyter notebook.
To convert to .ipynb, use: jupytext --to notebook research_in_public_notebook.py

Or copy the code into Kaggle notebook cells directly.
"""

# Cell 1: Markdown
"""
# Research In Public: Agentic Support Ecosystem

**Capstone Project for:** Kaggle's 5-Day GenAI Intensive Course with Google

This notebook demonstrates a multi-agent AI system designed to support PhD students.
"""

# Cell 2: Setup
# Install required packages
# !pip install -q google-generativeai langchain langchain-google-genai faiss-cpu numpy pandas

# Cell 3: Import and Setup
import sys
import os
from pathlib import Path

# Setup Kaggle environment
try:
    from kaggle_secrets import UserSecretsClient
    client = UserSecretsClient()
    os.environ['GEMINI_API_KEY'] = client.get_secret('GEMINI_API_KEY')
    print('✅ API key loaded from Kaggle secrets')
except:
    print('⚠️ Please add GEMINI_API_KEY to Kaggle User Secrets')

os.environ['USE_LOCAL_VECTOR_STORE'] = 'True'

# Cell 4: Core Imports
import google.generativeai as genai
import json
import numpy as np
from typing import List, Dict

# Initialize Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
print('✅ Modules imported and Gemini configured')

# Cell 5: Day 1 - Vent Validator
VENT_VALIDATOR_PROMPT = """You are an empathetic academic peer specializing in supporting PhD students.
Use active listening, validate emotions, and differentiate between technical and emotional blocks.
Only offer advice when asked."""

model_flash = genai.GenerativeModel('gemini-2.5-flash')

def vent_validator_chat(user_message: str, history: List[Dict] = None):
    if history is None:
        history = []
    chat = model_flash.start_chat(history=history)
    response = chat.send_message(f"{VENT_VALIDATOR_PROMPT}\n\nUser: {user_message}")
    return response.text

# Test
test_message = "My Western Blot failed again for the third time this week. I'm so frustrated."
response = vent_validator_chat(test_message)
print("User:", test_message)
print("\nVent Validator:", response)

# Cell 6: Day 2 - Embeddings
def generate_embedding(text: str):
    result = genai.embed_content(
        model='text-embedding-004',
        content=text,
        task_type='RETRIEVAL_DOCUMENT'
    )
    return result['embedding']

struggles = [
    "My Western Blot keeps failing. I've tried everything.",
    "Everyone in my lab publishes faster than me. I feel like an imposter.",
    "My PI keeps changing the project direction. I can't make progress.",
    "I'm in my 3rd year and still don't have publishable results.",
    "Lab culture is toxic. I feel isolated."
]

struggle_embeddings = [generate_embedding(s) for s in struggles]
print(f'✅ Generated {len(struggle_embeddings)} embeddings')

# Cell 7: Semantic Search
def cosine_similarity(vec1, vec2):
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    dot_product = np.dot(vec1_np, vec2_np)
    norm1 = np.linalg.norm(vec1_np)
    norm2 = np.linalg.norm(vec2_np)
    return dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0

def find_similar_struggles(query_text: str, top_k: int = 3):
    query_embedding = generate_embedding(query_text)
    similarities = []
    for i, struggle_emb in enumerate(struggle_embeddings):
        sim = cosine_similarity(query_embedding, struggle_emb)
        similarities.append((sim, i))
    similarities.sort(reverse=True)
    return [(struggles[idx], sim) for sim, idx in similarities[:top_k]]

query = "I feel like an imposter because everyone publishes faster than me"
matches = find_similar_struggles(query)
print(f"Query: {query}")
print("\nSimilar struggles:")
for struggle, sim in matches:
    print(f"  [{sim:.3f}] {struggle}")

# Cell 8: Day 3 - The Scribe
def draft_social_post(topic: str, mood: str, platform: str = "linkedin"):
    prompt = f"""Transform this research insight into a professional {platform} post.

Topic: {topic}
Mood: {mood}

Requirements:
- Professional but authentic
- Remove specific data/names
- Include 3-5 academic hashtags
- Length: {'280 chars' if platform == 'twitter' else '500-1000 chars'}

Generate the post:"""
    model_pro = genai.GenerativeModel('gemini-2.5-pro')
    response = model_pro.generate_content(prompt)
    return response.text

draft = draft_social_post(
    topic="Learning resilience from failed experiments",
    mood="reflective",
    platform="linkedin"
)
print("Drafted Social Post:")
print(draft)

# Cell 9: Scribe Agent
def scribe_agent(conversation: str):
    keywords = ["learned", "realized", "understood", "breakthrough", "finally worked"]
    if any(kw in conversation.lower() for kw in keywords):
        model_pro = genai.GenerativeModel('gemini-2.5-pro')
        prompt = f"Extract the key insight from: {conversation}\n\nProvide topic and mood."
        insight = model_pro.generate_content(prompt).text
        return draft_social_post(
            topic=insight.split('\n')[0] if '\n' in insight else insight[:100],
            mood="reflective",
            platform="linkedin"
        )
    return None

conversation = "I finally figured out why my experiments kept failing. It was a temperature issue. I learned so much about patience and troubleshooting."
draft = scribe_agent(conversation)
if draft:
    print("The Scribe detected a shareable moment!")
    print("\nDraft:", draft)

# Cell 10: Day 4 - PI Simulator
PI_PROMPT = """You are a supportive Principal Investigator.
Provide constructive critique on grant proposals.
Be supportive but honest, specific and actionable."""

def pi_simulator_critique(grant_text: str):
    model_pro = genai.GenerativeModel('gemini-2.5-pro')
    prompt = f"{PI_PROMPT}\n\nGrant Proposal:\n{grant_text}\n\nProvide critique:"
    response = model_pro.generate_content(prompt)
    return response.text

grant_example = """
Title: Novel Approaches to Protein Folding

We propose to study protein folding using computational methods.
Our approach will combine machine learning with molecular dynamics.
This research will advance understanding of disease mechanisms.
"""

critique = pi_simulator_critique(grant_example)
print("Grant Proposal:")
print(grant_example)
print("\nPI Simulator Critique:")
print(critique)

# Cell 11: Day 5 - The Guardian
GUARDIAN_PROMPT = """You are an IP safety agent.
Scan content for: chemical structures, genomic sequences, PI names, institutions.
Return risk level: LOW, MEDIUM, or HIGH."""

def guardian_scan(content: str):
    model_pro = genai.GenerativeModel('gemini-2.5-pro')
    prompt = f"{GUARDIAN_PROMPT}\n\nContent:\n{content}\n\nRisk assessment:"
    response = model_pro.generate_content(prompt)
    return response.text

test_cases = [
    "I've been working on my research and learning about resilience.",
    "I'm struggling with reagent X-1234 from Company Y.",
    "Western Blot troubleshooting has been challenging."
]

for i, test in enumerate(test_cases, 1):
    result = guardian_scan(test)
    print(f"Test {i}: {test[:50]}...")
    print(f"Guardian: {result}\n")

# Cell 12: Empathy Scoring
def score_empathy(user_message: str, agent_response: str):
    prompt = f"""Evaluate this agent response for empathy (1-5 scale).

User: {user_message}
Agent: {agent_response}

Score (1-5) and reasoning:"""
    model_flash = genai.GenerativeModel('gemini-2.5-flash')
    response = model_flash.generate_content(prompt)
    return response.text

user_msg = "My experiment failed again. I'm so frustrated."
agent_msg = "I hear your frustration. That sounds really challenging. Can you tell me more about what happened?"
score = score_empathy(user_msg, agent_msg)
print("Empathy Evaluation:")
print(score)

# Cell 13: Full Demo
def full_agent_demo(user_message: str):
    print(f"\n{'='*60}")
    print(f"User: {user_message}")
    print(f"{'='*60}\n")
    
    print("1️⃣ Vent Validator:")
    vent_response = vent_validator_chat(user_message)
    print(vent_response)
    print()
    
    print("2️⃣ Semantic Matchmaker:")
    matches = find_similar_struggles(user_message, top_k=2)
    if matches:
        print("Similar struggles found:")
        for struggle, sim in matches:
            print(f"  [{sim:.3f}] {struggle}")
    print()
    
    print("3️⃣ The Scribe:")
    draft = scribe_agent(user_message)
    if draft:
        print("Shareable moment detected! Draft:")
        print(draft)
    print()
    
    print("4️⃣ The Guardian:")
    if draft:
        guardian_result = guardian_scan(draft)
        print(guardian_result)
    print()
    
    print("5️⃣ Empathy Evaluation:")
    empathy_score = score_empathy(user_message, vent_response)
    print(empathy_score)

demo_message = "I finally figured out why my Western Blot kept failing. It was a blocking buffer issue. I learned so much about troubleshooting and patience."
full_agent_demo(demo_message)

