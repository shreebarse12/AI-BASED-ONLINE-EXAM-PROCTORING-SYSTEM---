from django.urls import path

from users import views
from .views import (
    admin_dashboard,
    all_integrity_logs,
    teacher_assign_exam,
    exam_results,
    student_result,
    teacher_dashboard,
    student_dashboard,
    create_exam,
    add_question,
    attempt_exam,
    video_feed,
    view_questions,
    
)

urlpatterns = [
    path("admin/dashboard/", admin_dashboard, name="admin_dashboard"),
    path("teacher/dashboard/", teacher_dashboard, name="teacher_dashboard"),
    path("student/dashboard/", student_dashboard, name="student_dashboard"),

    path("teacher/create-exam/", create_exam, name="create_exam"),
    path("teacher/add-question/<int:exam_id>/", add_question, name="add_question"),

    path("student/exam/<int:exam_id>/", attempt_exam, name="attempt_exam"),
    path("admin/assign-exam/", teacher_assign_exam, name="teacher_assign_exam"),
    path("teacher/results/<int:exam_id>/", exam_results, name="exam_results"),
    path("student/result/<int:exam_id>/", student_result, name="student_result"),
    path("teacher/exam/<int:exam_id>/questions/", view_questions, name="view_questions"),
    # path("teacher/logs/",teacher_logs,name="teacher_logs"),
    path("video_feed/", video_feed, name="video_feed"),
    path('teacher/integrity-logs/', all_integrity_logs, name='all_integrity_logs'),

]
