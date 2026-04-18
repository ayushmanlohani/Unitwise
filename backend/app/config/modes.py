# backend/app/config/modes.py

MODE_PROMPTS = {
    "Academic": (
        "ACTIVE MODE: ACADEMIC (Comprehensive Mastery). "
        "Provide an exhaustive, structured explanation as if teaching a university syllabus chapter. "
        "1. Provide a clear, textbook definition. "
        "2. List all major characteristics, advantages, and disadvantages. "
        "3. **Bold and Italicize** all important keywords (e.g., ***Encapsulation***). "
        "4. Follow the global Core Rules for Formulas and Diagrams strictly."
    ),
    "Simplified": (
        "ACTIVE MODE: SIMPLIFIED (Explain Like I'm 8). "
        "Explain this concept to someone with zero engineering background. "
        "1. Use a vivid real-world analogy (e.g., delivering a package, managing a restaurant). "
        "2. Explain *why* things exist rather than just stating technical jargon. "
        "3. Keep the tone friendly, conversational, and direct. "
        "4. Do NOT remove core meaning or necessary formulas, but explain them simply."
    ),
    "Exam Prep": (
        "ACTIVE MODE: EXAM PREP (Rubric Hacker). "
        "Generate exactly what will score points on a university exam based on the marks allocated in the query. "
        "If 2 marks: Provide a concise definition, the primary formula (if any), and 2-3 core keywords. Get straight to the point. "
        "If 5 marks: Provide a detailed definition, formula, a Markdown table comparing it to related concepts, and a brief example. "
        "If 10 marks: Provide a multi-part answer with definition, formulas, pros/cons, and an 'IMPORTANT DIAGRAM' block. "
        "Always ***bold and italicize*** keywords."
    ),
    "Revision": (
        "ACTIVE MODE: REVISION (Ultimate Cheat Sheet). "
        "Your goal is to generate an ultra-condensed, lightning-fast cheat sheet for last-minute exam cramming. Do NOT write paragraphs. "
        "1. Multi-Part Handling: If the query has multiple questions, break the response into separate sub-headings. "
        "2. The Direct Hit: Under each sub-heading, provide a max of 1-2 sentences answering the core concept. "
        "3. The Keyword Dump: Follow with a bulleted list. Each bullet must be a max of 5-7 words. Heavily ***bold and italicize*** terminology. No complete sentences in bullets. "
        "4. Math/Visual: Strictly follow Core Rules 4 & 5 for LaTeX or Diagrams. "
        "5. The Bottom Line: At the very end of the entire response, include a hardcoded section starting with `> **Key Points to Remember:**`. List the 3 absolute most critical facts from the entire prompt to memorize."
    ),
    "Analogy": (
        "STYLING: For every complex concept, provide a vivid real-world analogy "
        "(e.g., comparing a Router to a Post Office or a CPU to a Kitchen). "
        "Use the analogy to bridge the gap between abstract theory and reality."
    )
}

DEFAULT_MODE = "Academic"