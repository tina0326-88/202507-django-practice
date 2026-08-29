from django.contrib import admin
from .models import Teacher, Student, Course, Enrollment

class EnrollmentInline(admin.TabularInline):
    """
    在 Course 的編輯頁面裡，直接顯示/編輯報名紀錄
    """
    model = Enrollment
    extra = 0
    readonly_fields = ("enrolled_at",)
    autocomplete_fields = ("student",)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "course_count")
    search_fields = ("name", "email")
    list_per_page = 20

    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = "教授課程數"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "level", "enrolled_course_count")
    list_filter = ("level",)
    search_fields = ("name", "email")
    list_per_page = 20

    def enrolled_course_count(self, obj):
        return obj.courses.count()
    enrolled_course_count.short_description = "已報名課程數"


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "created_at", "teacher_list", "student_count")
    list_filter = ("teachers",)
    search_fields = ("title", "description")
    filter_horizontal = ("teachers",) 
    inlines = [EnrollmentInline]
    list_per_page = 20

    def teacher_list(self, obj):
        return ", ".join(t.name for t in obj.teachers.all())
    teacher_list.short_description = "授課老師"

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = "報名人數"


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "enrolled_at")
    list_filter = ("course",)
    search_fields = ("student__name", "course__title")
    autocomplete_fields = ("student", "course")
    date_hierarchy = "enrolled_at"