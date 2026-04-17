import yaml
import logging
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings

logger = logging.getLogger(__name__)

SUBJECT_FOLDER_TO_NAME = {
    "CN": "Computer Network",
    "DIP": "Digital Image Processing",
    "EML": "Essentials of Machine Learning",
    "SCT": "Soft Computing Techniques",
    "DMW": "Data Mining and Warehousing",
    "QC": "Quantum Computing",
}

SYSTEM_PROMPT = """You are a strict binary filter for an engineering syllabus.
The user is studying: {subject_name}

Here are the syllabus topics:
{syllabus_topics}

You must determine if the user's question relates to ANY of these topics.
Consider semantic similarity - if it is a sub-topic or closely related concept, answer YES.
If the question is completely unrelated (like general knowledge, unrelated degrees like MBA, or casual chat), answer NO.

CRITICAL RULE: You must reply with EXACTLY ONE WORD: either YES or NO. Do not explain. Do not add punctuation."""

def load_syllabus_topics(subject_folder: str) -> str:
    base_dir = Path(__file__).resolve().parent.parent.parent
    syllabus_path = base_dir / "data" / "syllabus.yaml"
    
    try:
        with open(syllabus_path, "r", encoding="utf-8") as f:
            syllabus_data = yaml.safe_load(f)
    except Exception as e:
        logger.warning("Failed to load syllabus.yaml from %s: %s", syllabus_path, e)
        return ""

    subjects = syllabus_data.get("subjects", [])
    
    for subject in subjects:
        if subject.get("folder") == subject_folder:
            subject_name = subject.get("name", "Unknown")
            topics_list = []
            
            for unit in subject.get("units", []):
                for topic in unit.get("topics", []):
                    topics_list.append(f"- {topic}")
            
            if not topics_list:
                logger.warning("Topics found empty for %s in YAML.", subject_folder)
                return ""
            
            return f"Subject: {subject_name}\n\n" + "\n".join(topics_list)
    
    logger.warning("Subject %s not found in YAML.", subject_folder)
    return ""

def is_question_in_syllabus(query: str, subject: str) -> bool:
    subject_name = SUBJECT_FOLDER_TO_NAME.get(subject, subject)
    syllabus_topics = load_syllabus_topics(subject)
    
    if not syllabus_topics:
        logger.warning("Blocking request: Could not load syllabus topics for %s.", subject)
        return False
    
    try:
        llm = ChatGroq(
            api_key=settings.GROQ_API_KEY,
            temperature=0.0,
            model_name="llama-3.1-8b-instant",
            max_tokens=5,
        )
        
        messages = [
            SystemMessage(content=SYSTEM_PROMPT.format(
                subject_name=subject_name,
                syllabus_topics=syllabus_topics
            )),
            HumanMessage(content=f"User question: '{query}'\n\nIs this in the syllabus? Reply EXACTLY YES or NO.")
        ]
        
        response = llm.invoke(messages)
        
        answer = response.content.strip(' .,\n"\'').upper()
        is_valid = answer == "YES" or answer.startswith("YES")
        
        logger.info("[Syllabus Check] Subject: %s | Valid: %s | LLM Answer: '%s' | Query: '%s'",
                     subject, is_valid, answer, query)
        return is_valid
        
    except Exception as e:
        logger.warning("Syllabus check LLM call failed: %s. Blocking request.", e)
        return False