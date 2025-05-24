from agents import function_tool, RunContextWrapper
from apps.cv.models import CV
from asgiref.sync import sync_to_async
from django.forms.models import model_to_dict
from apps.cv.tasks import CV_COLLECTION_NAME
from core.ai.chroma import chroma, openai_ef
from typing import Any

@function_tool()
async def get_list_of_cvs(ctx: RunContextWrapper[Any]):
    """Get a list of all CVs
    
        Args:
            params (any): The parameters to pass to the function
    """
    list_cv_id = ctx.context["list_cv_id"]
    cvs = await sync_to_async(list)(CV.objects.filter(id__in=list_cv_id))
    return [model_to_dict(cv) for cv in cvs]

@function_tool()
async def get_cv_information(ctx: RunContextWrapper[Any],query: str, n_result: int = 1):
    """
        Get information about a candidate based on their CV

        Args:
            query (str): The query to search for
            user_id (int, optional): The ID of the user to filter CVs for. If None, returns all matching CVs.
            n_result (int) : 1 for single result, others is multiple results
    """
    list_cv_id = ctx.context["list_cv_id"]
    filter_cv_id = []
    for cv_id in list_cv_id:
        filter_cv_id.append({
            "cv_id": {
                "$eq": cv_id
            }
        })
    query_filter = {
        "$or": filter_cv_id
    }
    print(query_filter)
    collection = chroma.get_collection(name=CV_COLLECTION_NAME, embedding_function=openai_ef)
    result = collection.query(query_texts=[query], n_results=n_result, include=["documents", "metadatas"], where=query_filter)

    print(result)

    context = ""
    if len(result["documents"]) > 0:
        for doc in result["documents"]:
            context += doc[0]
            
    return {
        "context": context,
        "metadata": result["metadatas"]
    }

@function_tool()
async def get_list_of_cv_match_with_job_description(ctx: RunContextWrapper[Any],job_description: str):
    """Get a list of CVs that match the job description
    
    Args:
        job_description (str): The job description to match against
        user_id (int, optional): The ID of the user to filter CVs for. If None, returns all matching CVs.
    """
    user_id = str(ctx.context["user_id"])
    collection = chroma.get_collection(name=CV_COLLECTION_NAME, embedding_function=openai_ef)
    
    result = collection.query(
        query_texts=[job_description], 
        n_results=3, 
        include=["documents", "metadatas"],
        where={"user_id": user_id}
    )
    
    context = ""
    for doc in result["documents"]:
        context += doc[0]
    
    return {
        "context": context,
        "metadata": result["metadatas"]
    }