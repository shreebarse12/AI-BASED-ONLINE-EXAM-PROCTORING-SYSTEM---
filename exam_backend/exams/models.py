from django.db import models
from users.models import User


# ===========================================================
#                           EXAM
# ===========================================================

class Exam(models.Model):
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "TEACHER"}
    )
    title = models.CharField(max_length=200)
    duration = models.IntegerField(help_text="Duration in minutes")
    total_marks = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ===========================================================
#                         QUESTIONS
# ===========================================================

class Question(models.Model):
    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="questions"
    )
    question_text = models.TextField()

    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)

    correct_option = models.CharField(
        max_length=1,
        choices=(("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"))
    )

    marks = models.IntegerField(default=1)

    def __str__(self):
        return self.question_text[:50]


# ===========================================================
#                     EXAM ASSIGNMENT
# ===========================================================

class ExamAssignment(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "STUDENT"}
    )

    assigned_at = models.DateTimeField(auto_now_add=True)

    submitted = models.BooleanField(default=False)
    terminated = models.BooleanField(default=False)

    warning_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.exam} -> {self.student}"


# ===========================================================
#                     STUDENT ANSWERS
# ===========================================================

class StudentAnswer(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)

    selected_option = models.CharField(max_length=1)

    def __str__(self):
        return f"{self.student} - Question {self.question.id}"


# ===========================================================
#                          RESULT
# ===========================================================

class Result(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey(User, on_delete=models.CASCADE)

    score = models.IntegerField()
    total_marks = models.IntegerField()

    is_terminated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student} - {self.exam}"


# ===========================================================
#                      WARNING LOGS
# ===========================================================

class WarningLog(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="warning_logs", null=True, blank=True)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="warning_logs", null=True, blank=True)
    object_name = models.CharField(max_length=100)
    warning_type = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Safer version to prevent 'NoneType' errors
        student_name = self.student.username if self.student else "Unknown Student"
        return f"{student_name} - {self.warning_type} ({self.timestamp.strftime('%H:%M:%S')})"