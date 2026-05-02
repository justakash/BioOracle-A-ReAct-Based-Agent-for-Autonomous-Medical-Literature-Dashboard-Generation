"""
RAG Index Seeder
Loads background biomedical documents into the FAISS vector index.
Run once before starting the server: python scripts/seed_rag.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from loguru import logger

load_dotenv()

from rag.retriever import RAGRetriever

SAMPLE_DOCUMENTS = [
    {
        "text": "Type 2 diabetes mellitus is a chronic metabolic disorder characterized by hyperglycemia resulting from insulin resistance and inadequate insulin secretion. It is one of the fastest-growing global health challenges.",
        "source": "seed_corpus",
        "topic": "diabetes",
    },
    {
        "text": "GLP-1 receptor agonists such as semaglutide and liraglutide have demonstrated significant efficacy in reducing HbA1c levels and promoting weight loss in patients with type 2 diabetes.",
        "source": "seed_corpus",
        "topic": "diabetes_treatment",
    },
    {
        "text": "Non-alcoholic fatty liver disease (NAFLD) is the most common chronic liver disease worldwide, affecting approximately 25% of the global population. It encompasses a spectrum from simple steatosis to non-alcoholic steatohepatitis (NASH).",
        "source": "seed_corpus",
        "topic": "liver_disease",
    },
    {
        "text": "CRISPR-Cas9 genome editing technology has opened new avenues for treating genetic disorders including sickle cell disease, beta-thalassemia, and Duchenne muscular dystrophy.",
        "source": "seed_corpus",
        "topic": "gene_therapy",
    },
    {
        "text": "Chimeric antigen receptor T-cell (CAR-T) therapy represents a breakthrough in the treatment of hematologic malignancies, with FDA-approved therapies for certain B-cell lymphomas and multiple myeloma.",
        "source": "seed_corpus",
        "topic": "immunotherapy",
    },
    {
        "text": "Alzheimer's disease is characterized by the accumulation of amyloid-beta plaques and neurofibrillary tau tangles, leading to progressive neurodegeneration and cognitive decline.",
        "source": "seed_corpus",
        "topic": "neurodegenerative",
    },
    {
        "text": "PD-1 and PD-L1 immune checkpoint inhibitors have revolutionized treatment of multiple solid tumors including non-small cell lung cancer, melanoma, and urothelial carcinoma.",
        "source": "seed_corpus",
        "topic": "oncology",
    },
    {
        "text": "mRNA vaccine technology, demonstrated successfully in COVID-19 vaccines by Pfizer-BioNTech and Moderna, offers a rapid and flexible platform for future infectious disease and oncology applications.",
        "source": "seed_corpus",
        "topic": "vaccines",
    },
]


def main():
    logger.info(f"Seeding RAG index with {len(SAMPLE_DOCUMENTS)} documents...")
    retriever = RAGRetriever()
    retriever.index_documents(SAMPLE_DOCUMENTS, text_field="text")
    logger.info("RAG index seeding complete.")


if __name__ == "__main__":
    main()
