from django.contrib import admin
from django.utils.html import format_html, mark_safe
from .models import Exam, Question, ExamAssignment, StudentAnswer, Result

# We use mark_safe for static CSS to avoid the format_html error
class ModernAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': [
                "data:text/css, " + 
                ".module { border-radius: 12px !important; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1) !important; border: none !important; }" +
                "thead th { background: #f8fafc !important; color: #64748b !important; text-transform: uppercase !important; font-size: 11px !important; }" +
                "input[type=submit], .button { background: #2563eb !important; border-radius: 8px !important; padding: 10px 20px !important; border: none !important; }" +
                "input, select, textarea { border-radius: 8px !important; border: 1px solid #e2e8f0 !important; padding: 5px !important; }"
            ]
        }
@admin.register(Exam)
class ExamAdmin(ModernAdmin):
    list_display = ('title', 'teacher', 'duration_badge', 'total_marks', 'question_count_display')
    
    def duration_badge(self, obj):
        return format_html('<span style="color: #64748b; font-weight: bold;">{} mins</span>', obj.duration)
    duration_badge.short_description = "Duration"

    def question_count_display(self, obj):
        # This counts questions linked to this exam without needing 'question_set'
        from .models import Question
        count = Question.objects.filter(exam=obj).count()
        return format_html('<b style="color: #2563eb;">{} Questions</b>', count)
    question_count_display.short_description = "Items"

@admin.register(Question)
class QuestionAdmin(ModernAdmin):
    list_display = ('question_text_short', 'exam', 'correct_option', 'marks')
    
    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text

@admin.register(ExamAssignment)
class ExamAssignmentAdmin(ModernAdmin):
    list_display = ('student', 'exam', 'status_pill')

    def status_pill(self, obj):
        color = "#10b981" if obj.submitted else "#f59e0b"
        text = "Submitted" if obj.submitted else "Pending"
        # Correctly passing variables to avoid the TypeError
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; border-radius:12px; font-size:10px; font-weight:bold; text-transform:uppercase;">{}</span>',
            color, text
        )

@admin.register(Result)
class ResultAdmin(ModernAdmin):
    list_display = ('student', 'exam', 'score_display', 'termination_status')

    def score_display(self, obj):
        percentage = (obj.score / obj.total_marks) * 100 if obj.total_marks > 0 else 0
        color = "#10b981" if percentage >= 40 else "#ef4444"
        # Ensure all variables are passed as arguments
        return format_html(
            '<span style="color: {}; font-weight:bold;">{} / {}</span>', 
            color, obj.score, obj.total_marks
        )

    def termination_status(self, obj):
        if obj.is_terminated:
            return mark_safe('<span style="color: #ef4444; font-weight:bold;">⚠️ Terminated</span>')
        return mark_safe('<span style="color: #10b981;">✅ Normal</span>')

@admin.register(StudentAnswer)
class StudentAnswerAdmin(ModernAdmin):
    list_display = ('student', 'exam', 'question', 'selected_option')
    


from .models import WarningLog

@admin.register(WarningLog)
class WarningLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'exam', 'warning_type', 'object_name', 'timestamp')
    list_filter = ('exam', 'warning_type', 'student') # Adds a filter sidebar
    search_fields = ('student__username', 'object_name')