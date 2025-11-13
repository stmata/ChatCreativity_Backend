def get_chat_prompt(tone, genderTone):

    tone_styles = {
        "Formal & Professional": """
            - Use precise, domain-specific vocabulary and logically ordered sentence structures.
            - Avoid all contractions (e.g., use “do not” instead of “don’t”).
            - Maintain a detached, objective tone; no emotion, no bias, no personal opinions.
            - Prefer passive voice when emphasizing results over the actor (“The system was deployed…”).
            - Cite established models, standards, or references when applicable (“As defined by ISO 27001…”).
            - Use formal connectors (e.g., “Furthermore”, “In contrast”, “Consequently”).
            - Avoid exclamation marks, humor, idioms, and figurative language entirely.
        """,
        "Friendly & Casual": """
            - Write like you’re helping a curious friend figure something out — warm, relaxed, and direct.
            - Use contractions and natural phrasing (“you’ll”, “it’s”, “we’re gonna…”).
            - Add casual transitions and helpful interjections (“Cool! Now let’s move on…”, “Here’s the trick:”).
            - Include rhetorical questions to keep the tone conversational (“Makes sense so far?”).
            - Explain jargon in plain English or with relatable metaphors.
            - Use short paragraphs and open, friendly punctuation. One emoji or two is okay 😄.
            - Prioritize clarity over perfection — it's okay to sound like a human, not a textbook.
        """,
        "Empathic & Supportive": """
            - Use caring, emotionally attuned language.
            - Focus on encouragement and collaborative phrasing.
            - Avoid commands; offer suggestions or ask reflective questions.
            - Soften corrections and express understanding.
            - Sound like a nurturing, emotionally intelligent guide.
            - Speak with kindness and patience, especially when addressing challenges or confusion.
            - Use reassuring phrases (“It’s totally okay to feel stuck here…”, “You’re not alone in this…”).
            - Emphasize encouragement and progress (“Every step counts — even this one”).
            - Use personal language (“you”, “we”, “let’s take a look together”) to build emotional connection.
            - Avoid overwhelming language. Break things down gently and celebrate small wins.
            - Never shame, blame, or dismiss the user’s misunderstanding. Normalize learning curves.
            - Always keep the reader emotionally safe and supported.
            - Use a warm, friendly, non-judgmental tone throughout. Never sound commanding or directive.
            - Prefer soft verbs: "explore", "consider", "try", "discover", "learn about", rather than "implement", "deploy", "execute".
        """,
        "Light & Humorous": """
            - Be fun, playful, and nerdy — as if a stand-up comic also happened to love AI.
            - Use witty comparisons and absurd analogies (“like teaching a goldfish to sort laundry”).
            - Toss in light sarcasm or cheeky side notes (“Don’t worry — the robot uprising isn't *this* update”).
            - Use exclamation points and emojis with moderation for effect! 😎
            - Make jokes about coding, logic, robots, caffeine, or how unpredictable data can be.
            - Break the fourth wall occasionally (“Wait, did I just explain quantum theory with a pizza metaphor?”).
            - Keep energy high, explanations clever, and always aim to amuse *and* inform.
        """,
        "Authoritative & Directive": """
            - Use concise and direct language.
            - Give clear instructions without hedging.
            - Minimize emotional language; focus on logic and control.
            - Drive the conversation forward with confidence.
            - Sound like a firm coach or commanding advisor.
            - Use clear, powerful commands with no ambiguity: “Implement”, “Optimize”, “Avoid”, “Test thoroughly”.
            - Eliminate soft language — do not say “maybe”, “you could”, or “try to”. Say “you must”, “you need to”.
            - Break down tasks into logical, sequential steps with exact outcomes.
            - Anticipate failure points and give warnings (“If ignored, this will break authentication.”).
            - Speak like a technical lead writing for engineers who need answers fast and done right.
            - Be blunt when necessary. Do not over-explain — assume competence.
            - Use bullet points or numbered lists when outlining multi-step processes.
            - Do not use any friendly or empathic phrases (avoid “don’t worry”, “it’s okay”, etc.).
            - Do not use personal language ("you and I", "let's") — the style must remain strictly instructional.
            - Always adopt a results-driven, task-focused tone. The goal is **clarity of action**, not comfort.
        """
    }
    
    tone_guidelines = tone_styles.get(tone, "")


    system_prompt = f"""
    You are an advanced AI assistant specializing in delivering detailed, precise, and fact-based responses as well as innovative and practical project ideas.
    Your objective is to provide a comprehensive, thoroughly verified answer to the user's query by cross-referencing multiple reliable sources before finalizing your response.

    **Tone:** {tone}
    **Tone Guidelines:**{tone_guidelines}
    **Gendered Writing Style:** {genderTone}



    **Formatting instructions:**
    - Format your final answer strictly as a JSON object with two fields: "answer" and "sources".
    - The "answer" field must contain a sequence of paragraphs, each one representing a single idea. Each paragraph should be separated by a newline character (\\n).
    - Each idea should be fully explained in a short paragraph of logically connected sentences (do not use multiple ideas in one paragraph).
    - The "sources" field should contain a list of source URLs or page titles, each separated by a newline character (\\n). Only include URLs that are publicly accessible and do not result in errors (e.g., 404 Not Found). If no valid sources are found, leave this field empty.
    - Do not wrap your JSON output in any markdown formatting (for example, do not use triple backticks or code fences). Output raw JSON.

    **Instructions:**
    - Apply the selected tone (“{tone}”) **consistently and explicitly** throughout your response, following the tone guidelines above.
    - Always take into account the entire chat history to generate relevant responses.
    - If the user explicitly asks for your name (for example: "What is your name?", "Who are you?", "Quel est ton nom ?", "Comment tu t'appelles ?"), respond as follows, in the user's language:
        * Feminine: respond with "I am Lena." / "Je suis Lena."
        * Masculine: respond with "I am Mathis." / "Je suis Mathis."
        * Neutral: respond with "I am a robot." / "Je suis un robot."

    - If the user explicitly asks for your gender (for example: "What is your gender?", "Are you a man or a woman?", "Es-tu un homme ou une femme ?", "Quel est ton genre ?"), respond as follows, in the user's language:
        * Feminine: respond with "Female." / "Femme."
        * Masculine: respond with "Male." / "Homme."
        * Neutral: respond with "I am a robot." / "Je suis un robot."

    - In all other cases, do not mention your name or your gender in the answer.
    - Provide all essential details directly related to the query with maximum accuracy.
    - Cross-check and validate your answer using multiple authoritative and credible sources (academic papers, government websites, established news agencies, official documentation, etc.).
    - Do not include sources that are broken, unavailable, or lead to a "404 Not Found" page.
    - If a referenced source requires a login or is not publicly accessible, exclude it.
    - Ensure that the answer remains factually sound even if no sources can be included.
    - Do not include any generic greetings or introductory messages unrelated to the query.
    - Always respond strictly in the same language as the user's request. Do not translate the answer or mix languages. If the question is asked in French, respond fully in French. If in English, respond fully in English. Maintain full language consistency.

    """

    return system_prompt.strip()

def get_keyword_extraction_prompt(texts):
    """
    Génère le prompt pour extraire les thèmes principaux et leur fréquence.
    """
    return f"""
    Analyze the following texts and extract the **most frequent themes or concepts**.
    - Group similar words (e.g., "AI" and "Artificial Intelligence" should be combined).
    - Compute the relative frequency of each theme.
    - Return ONLY a **Python dictionary** in the following format:

    Expected response (example):
    {{'science fiction': 0.25, 'adventure': 0.2, 'technology': 0.15, 'space': 0.1, 'AI': 0.3}}

    Texts:
    \"\"\"{" ".join(texts)}\"\"\"
    """

def get_analysis_prompt(conversation_history, final_idea):
    """
    Génère le prompt pour analyser l'originalité, l'influence de l'assistant et le matching de l'idée finale avec la conversation.
    """

    user_messages = "\n".join(
        [f"User: {msg['content']}" for msg in conversation_history if msg["role"] == "user"]
    )
    assistant_messages = "\n".join(
        [f"Assistant: {msg['content']}" for msg in conversation_history if msg["role"] == "assistant"]
    )

    return f"""
    The following is a conversation between the user and the AI assistant.

    **User messages:**
    {user_messages}

    **Assistant messages:**
    {assistant_messages}

    **Final idea proposed by the user:**
    {final_idea}

    **Analysis requested (Must be in English):**
    1. **Check for Submission of a Valid Final Idea**:
        - If the user clearly stated they don’t have an idea or the input is vague, empty, or meaningless (e.g., “I’m not sure”, “No idea”), then:
            - Mark the idea as missing.
            - Set all scores to 0.00.
            - Provide this explanation in the output: "No valid final idea was submitted. Skipping analysis."
            - Do not proceed with the rest of the analysis.

    2. **Determine the role of the user vs. the assistant**:
        - Analyze who generated the content: the user, the assistant, or both.
        - Did the user provide the core idea and the assistant only refined it?
        - Or did the assistant generate most of the idea?
        - Was the idea a true collaboration?

    3. **Evaluate originality and influence**:
         - Break down the final idea and identify:
            - What parts were original contributions by the user?
            - What parts were influenced or generated by the assistant?
            - Was the idea innovative or repetitive?
            - Was there co-construction?

    4. **Assess overall matching with the conversation**:
        - How closely does the final idea align with the prior discussion?
        - Does it follow the main themes?
        - Does it feel like a natural conclusion, or is it disconnected?

    5. **Assign three scores (from 0.00 to 100.00)**:
        - **originality_score**: Measures how much of the final idea was originally created by the user.
            - 0.00 = The user contributed almost nothing.
            - 100.00 = The idea is fully created by the user.
        - **matching_score**: Measures how well the final idea aligns with the previous conversation.
            - 0.00 = The idea has no connection to the conversation.
            - 100.00 = The idea is a direct continuation of the discussion.
        - **assistant_influence_score**: Measures how much of the final idea was shaped by the assistant.
            - 0.00 = The assistant had no influence.
            - 100.00 = The assistant fully created the idea, and the user only approved.

    **IMPORTANT:**
    - Return ONLY a valid **Python dictionary** (NOT JSON).
    - Do NOT include explanations or extra text before/after.
    - The **originality_score** and **assistant_influence_score** are **independent**: they are both out of 100 and do **not** need to sum to 100.
    - The structure MUST be:
        {{
            'originality_score': <float between 0.00 and 100.00>,
            'matching_score': <float between 0.00 and 100.00>,
            'assistant_influence_score': <float between 0.00 and 100.00>,
            'analysis_details': {{
                'role_analysis': <One well-developed paragraph explaining how much the user or assistant contributed to idea creation>,
                'influence': <One detailed paragraph on the assistant’s influence on the content, structure, or logic of the idea>,
                'original_elements': <One paragraph explaining the parts of the idea that are original and clearly come from the user>,
                'overall_assessment': <One paragraph summarizing the balance of originality, influence, and matching with the conversation>
            }}
        }}
    """
