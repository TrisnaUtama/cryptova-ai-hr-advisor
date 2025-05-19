from agents import function_tool
from apps.cv.models import CV
from asgiref.sync import sync_to_async
from django.forms.models import model_to_dict

@function_tool()
async def get_list_of_highest_cv_score(max_count: int):
    """Get the list of highest CV score"""
    print(f"Getting the list of highest CV score with max_count: {max_count}")
    if max_count:
        max_count = 10

    try:
        cvs = await sync_to_async(list)(
            CV.objects.all().order_by("-overall_score")[:max_count]
        )
        # Serialize the queryset to a list of dicts
        return [
            {
                "id": cv.id,
                "name": cv.candidate_name,  # adjust fields as needed
                "overall_score": cv.overall_score,
                # add other fields you want to expose
            }
            for cv in cvs
        ]
    except Exception as e:
        print(f"Error getting the list of highest CV score: {e}")
        return []


@function_tool()
async def get_cv_by_job_category(job_category: str):
    """Get the list of CV by job category"""
    print(f"Getting the list of CV by job category: {job_category}")
    try:
        cvs = await sync_to_async(list)(
            CV.objects.filter(candidate_category__icontains=job_category).order_by("-overall_score")
        )
        # Serialize the queryset to a list of dicts
        return [
            {
                "id": cv.id,
                "name": cv.candidate_name,  # adjust fields as needed
                "overall_score": cv.overall_score,
                "candidate_category": cv.candidate_category,
            }
            for cv in cvs
        ]
    except Exception as e:
        print(f"Error getting the list of CV by job category: {e}")
        return []

@function_tool()
async def get_cv_by_id(id: str):
    """
        Get the CV by id
        Always use the 'id' field from the candidate list tool output when calling this tool.
    """
    print(f"Getting the CV by id: {id}")
    try:
        cv = await sync_to_async(CV.objects.get)(id=id)
        return model_to_dict(cv)
    except Exception as e:
        print(f"Error getting the CV by id: {e}")
        return None
