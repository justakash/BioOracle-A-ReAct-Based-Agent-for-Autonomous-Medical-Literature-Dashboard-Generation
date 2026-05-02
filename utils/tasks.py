"""
Celery Background Tasks
Async versions of the pipeline steps for long-running operations.
"""

from loguru import logger

from utils.celery_app import celery_app


@celery_app.task(bind=True, name="tasks.run_query_pipeline")
def run_query_pipeline(self, user_query: str, session_id: str) -> dict:
    """
    Run the full ReAct agent pipeline as a background Celery task.
    """
    from agent.react_agent import BioOracleAgent
    try:
        logger.info(f"[Celery] Starting pipeline for session {session_id}")
        agent = BioOracleAgent()
        result = agent.run(user_query=user_query, session_id=session_id)
        logger.info(f"[Celery] Pipeline complete for session {session_id}, status={result.get('status')}")
        return result
    except Exception as e:
        logger.exception(f"[Celery] Pipeline failed for session {session_id}: {e}")
        self.retry(exc=e, countdown=10, max_retries=2)


@celery_app.task(name="tasks.send_scheduled_report")
def send_scheduled_report(config_id: str, recipient_email: str) -> bool:
    """
    Scheduled task to email a dashboard report.
    """
    from utils.emailer import send_report_email
    from utils.exporter import export_pdf
    import os
    try:
        pdf_path = export_pdf(config_id)
        send_report_email(
            csv_path=pdf_path,
            config_id=config_id,
            recipient=recipient_email,
        )
        return True
    except Exception as e:
        logger.exception(f"[Celery] Scheduled report failed for config {config_id}: {e}")
        return False


@celery_app.task(name="tasks.rebuild_rag_index")
def rebuild_rag_index(documents: list) -> bool:
    """
    Background task to rebuild the FAISS RAG index.
    """
    from rag.retriever import RAGRetriever
    try:
        retriever = RAGRetriever()
        retriever.index_documents(documents)
        return True
    except Exception as e:
        logger.exception(f"[Celery] RAG index rebuild failed: {e}")
        return False
