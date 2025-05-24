from pydantic import BaseModel, Field


class DocumentCheck(BaseModel):
    is_cv: bool = Field(description="Is the document a CV")


class EducationsBase(BaseModel):
    degree: str = Field(description="The degree of the candidate")
    year: str = Field(description="The year of the candidate")
    institution: str = Field(description="The institution of the candidate")
    gpa: str = Field(description="The GPA of the candidate")


class WorkExperienceBase(BaseModel):
    position: str = Field(
        description="The position of the work experience of the candidate"
    )
    company: str = Field(
        description="The company of the work experience of the candidate"
    )
    duration: str = Field(
        description="The duration of the work experience of the candidate"
    )
    description: str = Field(
        description="The description of the work experience of the candidate"
    )


class SkillBase(BaseModel):
    skill: str = Field(description="The skill of the candidate")
    proficiency: str = Field(description="The proficiency of the candidate")


class LanguageBase(BaseModel):
    language: str = Field(description="The language of the candidate")
    proficiency: str = Field(description="The proficiency of the candidate")


class AchievementBase(BaseModel):
    title: str = Field(description="The title of the achievement")
    description: str = Field(description="The description of the achievement")
    year: str = Field(description="The year of the achievement")
    publisher: str = Field(description="The publisher of the achievement")


class CVBase(BaseModel):
    raw_output: str
    candidate_name: str = Field(description="The name of the candidate")
    candidate_email: str = Field(description="The email of the candidate")
    candidate_phone: str = Field(description="The phone number of the candidate")
    candidate_title: str = Field(description="The job title of the candidate")
    candidate_category: str = Field(description="The job category of the candidate, like IT, Marketing, Finance, etc.")
    description: str = Field(description="The description of the candidate")
    education: list[EducationsBase] = Field(
        description="The education of the candidate"
    )
    workexperience: list[WorkExperienceBase] = Field(
        description="The work experience of the candidate"
    )
    skills: list[SkillBase] = Field(description="The skills of the candidate")
    language: list[LanguageBase] = Field(description="The language of the candidate")
    achievements: list[AchievementBase] = Field(
        description="The achievements of the candidate"
    )
    overall_score: float = Field(description="The overall score of the candidate")
    experience_score: float = Field(description="The experience score of the candidate")
    achievement_score: float = Field(
        description="The achievement score of the candidate"
    )
    skill_score: float = Field(description="The skill score of the candidate")

class CVMatchBase(BaseModel):
    cv_id: str = Field(description="The id of the candidate")
    job_id: str = Field(description="The id of the job")
    matching_score: float = Field(description="The match score of the candidate")
    reason: str = Field(description="The reason of the match score")

class ListApplicantsBase(BaseModel):
    applicants: list[CVMatchBase] = Field(description="The list of matched applicants")

class JobMatchBase(BaseModel):
    cv_id: str = Field(description="The id of the candidate")
    job_id: str = Field(description="The id of the job")
    matching_score: float = Field(description="The match score for this job")
    reason: str = Field(description="The reason for the match score")

class ListJobMatchesBase(BaseModel):
    jobs: list[JobMatchBase] = Field(description="The list of matched jobs for the candidate")

class FollowUpPayloadBase(BaseModel):
    cv_id: str = Field(description="The id of the candidate")
    priority: str = Field(description="The priority of the candidate")
    interview_type: str = Field(description="The type of the interview")
    
class FollowupActionBase(BaseModel):
    action: str = Field(description="The action to be taken")
    message: str = Field(description="The message to be sent to the candidate")
    payload: FollowUpPayloadBase = Field(description="The payload to be sent to the candidate")


