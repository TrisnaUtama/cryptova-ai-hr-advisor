from agents import function_tool
from apps.cv.models import CV
from asgiref.sync import sync_to_async

@function_tool()
async def fetch_weather(location: str) -> str:
    """Fetch the weather for a given location"""
    print(f"Fetching weather for {location}")
    return f"The weather in {location} is sunny"

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




