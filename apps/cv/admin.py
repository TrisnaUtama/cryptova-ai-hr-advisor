from django.contrib import admin

from .models import CV, Achievement, Education, Language, Skill, WorkExperience


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 0


class LanguageInline(admin.TabularInline):
    model = Language
    extra = 0


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0


class WorkExperienceInline(admin.TabularInline):
    model = WorkExperience
    extra = 0


class AchievementInline(admin.TabularInline):
    model = Achievement
    extra = 0


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "file_path",
        "file_name",
        "candidate_name",
        "candidate_email",
        "overall_score",
        "sync_status",
        "created_at",
        "updated_at",
    )
    search_fields = ("candidate_name", "candidate_email", "file_name")
    list_filter = ("sync_status", "created_at", "updated_at")
    ordering = ("-created_at",)
    inlines = [
        SkillInline,
        LanguageInline,
        EducationInline,
        WorkExperienceInline,
        AchievementInline,
    ]

    def file_path(self, obj):
        return obj.file.name

    file_path.short_description = "File Path"
