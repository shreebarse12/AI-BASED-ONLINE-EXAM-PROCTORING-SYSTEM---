# ========================= IMPORTS =========================

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Count

from .models import Exam, ExamAssignment, Question, Result, WarningLog
from users.models import User


from django.http import JsonResponse, StreamingHttpResponse
import cv2

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from ultralytics import YOLO


# ===========================================================
#                       ADMIN DASHBOARD
# ===========================================================

@login_required
def admin_dashboard(request):
    if request.user.role != "ADMIN":
        return redirect("login")

    teachers = User.objects.filter(role="TEACHER")
    students = User.objects.filter(role="STUDENT")

    return render(request, "admin_dashboard.html", {
        "teachers": teachers,
        "students": students,
    })


# ===========================================================
#                       TEACHER DASHBOARD
# ===========================================================

@login_required
def teacher_dashboard(request):
    if request.user.role != "TEACHER":
        return redirect("login")

    exams = (
        Exam.objects
        .filter(teacher=request.user)
        .annotate(question_count=Count("questions"))
        .order_by("-id")
    )

    return render(request, "teacher_dashboard.html", {
        "exams": exams
    })


# ===========================================================
#                       STUDENT DASHBOARD
# ===========================================================

@login_required
def student_dashboard(request):
    if request.user.role != "STUDENT":
        return redirect("login")

    assignments = ExamAssignment.objects.filter(student=request.user)

    return render(request, "student_dashboard.html", {
        "assignments": assignments
    })


# ===========================================================
#                       CREATE EXAM
# ===========================================================

@login_required
def create_exam(request):
    if request.user.role != "TEACHER":
        return redirect("login")

    if request.method == "POST":
        Exam.objects.create(
            teacher=request.user,
            title=request.POST["title"],
            duration=request.POST["duration"],
            total_marks=request.POST["total_marks"]
        )
        return redirect("teacher_dashboard")

    return render(request, "create_exam.html")


# ===========================================================
#                       ADD QUESTION
# ===========================================================

@login_required
def add_question(request, exam_id):
    if request.user.role != "TEACHER":
        return redirect("login")

    exam = get_object_or_404(Exam, id=exam_id, teacher=request.user)

    if request.method == "POST":
        Question.objects.create(
            exam=exam,
            question_text=request.POST["question"],
            option_a=request.POST["a"],
            option_b=request.POST["b"],
            option_c=request.POST["c"],
            option_d=request.POST["d"],
            correct_option=request.POST["correct"],
            marks=request.POST["marks"]
        )
        return redirect("teacher_dashboard")

    return render(request, "add_question.html", {"exam": exam})


# ===========================================================
#                       ASSIGN EXAM
# ===========================================================

@login_required
def teacher_assign_exam(request):
    if request.user.role != "TEACHER":
        return redirect("login")

    exams = Exam.objects.filter(teacher=request.user)
    students = User.objects.filter(role="STUDENT")

    if request.method == "POST":
        ExamAssignment.objects.get_or_create(
            exam_id=request.POST["exam"],
            student_id=request.POST["student"]
        )
        return redirect("teacher_dashboard")

    return render(request, "assign_exam.html", {
        "exams": exams,
        "students": students
    })

from .models import StudentAnswer
# ===========================================================
#                       ATTEMPT EXAM
# ===========================================================
@login_required
def attempt_exam(request, exam_id):
    if request.user.role != "STUDENT": 
        return redirect("login")

    # 1. Fetch the assignment and validate
    assignment = ExamAssignment.objects.filter(exam_id=exam_id, student=request.user).first()
    
    if not assignment or assignment.submitted: 
        return redirect("student_dashboard")

    exam = assignment.exam
    questions = Question.objects.filter(exam=exam)

    # 2. AJAX WARNING FETCH + AUTO-SUBMIT CHECK
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        warnings_qs = WarningLog.objects.filter(student=request.user, exam_id=exam_id).order_by('-timestamp')
        count = warnings_qs.count()
        
        data = [{
            "object_name": w.object_name,
            "warning_type": w.warning_type,
            "timestamp": w.timestamp.strftime("%H:%M:%S")
        } for w in warnings_qs[:10]]

        return JsonResponse({
            "warnings": data, 
            "total_count": count,
            "should_submit": count >= 10  # This signals the frontend to auto-submit
        })

    # 3. HANDLING EXAM SUBMISSION (POST Request)
    if request.method == "POST":
        score = 0
        total_m = 0

        for q in questions:
            selected = request.POST.get(str(q.id))
            total_m += q.marks
            if selected == q.correct_option:
                score += q.marks
            
            # Save individual answers if you want to track them
            StudentAnswer.objects.create(
                exam=exam,
                question=q,
                student=request.user,
                selected_option=selected if selected else ""
            )

        # Create the Result record
        # Note: If count >= 10, you can flag this as 'is_terminated=True'
        warning_count = WarningLog.objects.filter(student=request.user, exam_id=exam_id).count()
        
        Result.objects.create(
            exam=exam,
            student=request.user,
            score=score,
            total_marks=total_m,
            is_terminated=(warning_count >= 10)
        )

        # Mark assignment as finished
        assignment.submitted = True
        assignment.warning_count = warning_count
        assignment.save()

        return redirect("student_dashboard")

    # 4. INITIAL PAGE LOAD (GET Request)
    request.session["exam_id"] = exam.id
    request.session["student_id"] = request.user.id
    
    initial_warnings = WarningLog.objects.filter(student=request.user, exam_id=exam_id).order_by('-timestamp')[:10]

    return render(request, "exam_page.html", {
        "exam": exam,
        "questions": questions,
        "warnings": initial_warnings,
    })

# ===========================================================
#                       TEACHER VIEW RESULTS
# ===========================================================

@login_required
def exam_results(request, exam_id):
    if request.user.role != "TEACHER":
        return redirect("login")

    exam = get_object_or_404(Exam, id=exam_id, teacher=request.user)
    results = Result.objects.filter(exam=exam)

    return render(request, "results.html", {
        "exam": exam,
        "results": results
    })


# ===========================================================
#                       STUDENT RESULT
# ===========================================================

@login_required
def student_result(request, exam_id):
    if request.user.role != "STUDENT":
        return redirect("login")

    result = (
        Result.objects
        .filter(exam_id=exam_id, student=request.user)
        .order_by("-id")
        .first()
    )

    if not result:
        return redirect("student_dashboard")

    return render(request, "student_result.html", {
        "result": result
    })


# ===========================================================
#                       VIEW QUESTIONS
# ===========================================================

@login_required
def view_questions(request, exam_id):
    if request.user.role != "TEACHER":
        return redirect("login")

    exam = get_object_or_404(Exam, id=exam_id, teacher=request.user)
    questions = exam.questions.all().order_by("id")

    return render(request, "view_questions.html", {
        "exam": exam,
        "questions": questions
    })


# ===========================================================
#                       PROCTORING VIEW (AJAX)
# ===========================================================

def proctoring_view(request):
    # AJAX request → return JSON warning logs
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        warnings = WarningLog.objects.order_by('-timestamp')[:20]

        data = [
            {
                "object_name": w.object_name,
                "warning_type": w.warning_type,
                "time": w.timestamp.strftime("%H:%M:%S"),
            }
            for w in warnings
        ]

        return JsonResponse({"warnings": data})

    return render(request, "exam_page.html")


# ===========================================================
#                       YOLO MODEL + VIDEO STREAM
# ===========================================================

channel_layer = get_channel_layer()
model = YOLO("yolo26n.pt")


# ... (Imports remain same)

import time # Add this at the top of views.py

def gen_frames(student_id, exam_id):
    cap = cv2.VideoCapture(0)
    student = User.objects.get(id=student_id)
    exam = Exam.objects.get(id=exam_id)
    
    frame_count = 0
    last_log_time = 0
    log_cooldown = 2  # Minimum seconds between saving warnings

    while True:
        ret, frame = cap.read()
        if not ret: break

        frame_count += 1
        
        # 1. ONLY PROCESS EVERY 10th FRAME (Reduces CPU load)
        if frame_count % 10 == 0:
            results = model(frame, stream=True)
            
            for r in results:
                for box in r.boxes:
                    cls = int(box.cls[0])
                    label = model.names[cls]
                    ALERT_OBJECTS = ["cell phone", "book", "notebook"]

                    if label in ALERT_OBJECTS:
                        current_time = time.time()
                        
                        # 2. COOLDOWN: Only save to DB if 2 seconds have passed
                        if current_time - last_log_time > log_cooldown:
                            WarningLog.objects.create(
                                student=student,
                                exam=exam,
                                object_name=label,
                                warning_type=f"{label.capitalize()} detected!"
                            )
                            
                            assignment = ExamAssignment.objects.filter(student=student, exam=exam).first()
                            if assignment:
                                assignment.warning_count += 1
                                assignment.save()
                                
                            last_log_time = current_time # Reset cooldown timer

        # Stream the frame (always stream, even if we skip detection)
        ret, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

def video_feed(request):
    # Get IDs from session set in attempt_exam
    student_id = request.session.get("student_id")
    exam_id = request.session.get("exam_id")
    return StreamingHttpResponse(gen_frames(student_id, exam_id), 
                                 content_type="multipart/x-mixed-replace; boundary=frame")



from django.db.models import Count

# In your views.py

from django.db.models import Count

from django.db.models import Count
from .models import WarningLog, Result

import json
from django.db.models import Count
from .models import WarningLog, Result

import json
from django.db.models import Count
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import WarningLog, Result

@login_required
def all_integrity_logs(request):
    if request.user.role != "TEACHER":
        return redirect("login")

    # 1. Group WarningLogs by Student and Exam
    raw_summary = WarningLog.objects.filter(exam__teacher=request.user) \
        .values('student__username', 'exam__title', 'student_id', 'exam_id') \
        .annotate(log_count=Count('id')) \
        .order_by('-log_count')

    summary_logs = []
    for entry in raw_summary:
        # 2. Fetch specific logs for the popup timeline
        session_logs = WarningLog.objects.filter(
            student_id=entry['student_id'], 
            exam_id=entry['exam_id']
        ).order_by('timestamp')
        
        log_details = [
            {
                'object': str(log.object_name), 
                'time': log.timestamp.strftime("%H:%M:%S")
            } for log in session_logs
        ]
        
        # 3. Fetch the student's score
        result = Result.objects.filter(
            student_id=entry['student_id'], 
            exam_id=entry['exam_id']
        ).first()
        
        summary_logs.append({
            'student_name': entry['student__username'],
            'exam_title': entry['exam__title'],
            'log_count': entry['log_count'],
            'score': result.score if result else "N/A",
            'details_json': json.dumps(log_details) # Prepared for JS
        })

    return render(request, "all_integrity_logs.html", {
        "summary_logs": summary_logs
    })