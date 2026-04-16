# backend/app/config/modes.py

MODE_PROMPTS = {
    "Academic": (
        "STYLING: Use formal, technical language. Provide exhaustive explanations "
        "with deep theoretical background. Use standard academic headings and "
        "maintain a professional professor-like persona."
    ),
    "Simplified": (
        "STYLING: Explain like I'm 15. Avoid heavy jargon where possible, or explain it "
        "immediately. Use short sentences and a friendly, encouraging mentor tone. "
        "Focus on clarity over complexity."
    ),
    "Exam Prep": (
        "STYLING: Focus on 'High-Yield Topics'. Use bold text for keywords that "
        "examiners look for. Structure everything into bullet points, 5-mark, or "
        "10-mark formats. Include a 'Key Points to Remember' section at the end."
    ),
    "Quick Summary": (
        "STYLING: Provide a 'TL;DR' (Too Long; Didn't Read) version. Be extremely concise. "
        "Use a table for comparisons if applicable. Get straight to the point without "
        "long introductions."
    ),
    "Analogy": (
        "STYLING: For every complex concept, provide a vivid real-world analogy "
        "(e.g., comparing a Router to a Post Office or a CPU to a Kitchen). "
        "Use the analogy to bridge the gap between abstract theory and reality."
    )
}

DEFAULT_MODE = "Academic"
