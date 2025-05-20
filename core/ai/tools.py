from agents import function_tool
from apps.cv.models import CV
from asgiref.sync import sync_to_async
from django.forms.models import model_to_dict
from apps.cv.tasks import CV_COLLECTION_NAME
from core.ai.chroma import chroma, openai_ef

@function_tool()
async def get_list_of_cvs():
    """Get a list of all CVs"""
    cvs = await sync_to_async(list)(CV.objects.all())
    return [model_to_dict(cv) for cv in cvs]

@function_tool()
async def get_cv_information(query: str):
    """Get information about a candidate based on their CV"""
    collection = chroma.get_collection(name=CV_COLLECTION_NAME, embedding_function=openai_ef)
    result = collection.query(query_texts=[query], n_results=3, include=["documents", "metadatas"])
    context = ""
    for doc in result["documents"]:
        context += doc[0]
    
    return {
        "context": context,
        "metadata": result["metadatas"]
    }

@function_tool()
async def get_list_of_cv_match_with_job_description(job_description: str):
    """Get a list of CVs that match the job description"""
    collection = chroma.get_collection(name=CV_COLLECTION_NAME, embedding_function=openai_ef)
    result = collection.query(query_texts=[job_description], n_results=3, include=["documents", "metadatas"])
    context = ""
    for doc in result["documents"]:
        context += doc[0]
    
    return {
        "context": context,
        "metadata": result["metadatas"]
    }