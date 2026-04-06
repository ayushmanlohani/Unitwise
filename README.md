# AKTU-Brain (Prototype)

A Retrieval-Augmented Generation (RAG) based academic chatbot built specifically for AKTU university B.Tech students. 

## Features
* Answers questions strictly based on the syllabus.
* Cites specific textbooks and page numbers.
* Built with FastAPI, LangChain, ChromaDB, and Streamlit.

## Setup
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Rename `.env.example` to `.env` and add your Groq API key.
4. Place textbook PDFs in `backend/data/raw/{subject_folder}/`.
5. Run ingestion: `python -m backend.scripts.run_ingestion`
6. Start UI: `streamlit run prototype/streamlit_app.py`