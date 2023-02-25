from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Avg, Count
from django.forms import inlineformset_factory
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from Quiz.forms import BaseAnswerInlineFormSet, QuestionForm, ShareTeacherForm, StudentInterestsForm, StudentSignUpForm, TakeQuizForm, TeacherSignUpForm
from Quiz.models import Choice, Quiz, Question, Student, StudentAnswer, TakenQuiz, User
from Quiz.utils import student_required, teacher_required

class SignUpView(TemplateView):
    template_name = 'registration/signup.html'


class StudentSignUpView(CreateView):
    model = User
    form_class = StudentSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'student'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        '''
            Returns an HTTP Response. Called when request is POSTed
        '''
        user = form.save()
        login(self.request, user)
        return redirect('students:quiz_list')

@method_decorator([login_required, student_required], name='dispatch')
class StudentInterestsView(UpdateView):
    model = Student
    form_class = StudentInterestsForm
    template_name = 'students/interests_form.html'
    success_url = reverse_lazy('students:quiz_list')

    def get_object(self):
        return self.request.user.student

    def form_valid(self, form):
        messages.success(self.request, 'Interests updated with success!')
        return super().form_valid(form)


@method_decorator([login_required, student_required], name='dispatch')
class StudentQuizListView(ListView):
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'students/quiz_list.html'

    def get_queryset(self):
        student = self.request.user.student
        student_interests = student.interests.values_list('pk', flat=True)
        taken_quizzes = student.quizzes.values_list('pk', flat=True)
        queryset = Quiz.objects.filter(subject__in=student_interests) \
            .exclude(pk__in=taken_quizzes) \
            .annotate(questions_count=Count('questions')) \
            .filter(questions_count__gt=0)
        return queryset


@method_decorator([login_required, student_required], name='dispatch')
class TakenQuizListView(ListView):
    model = TakenQuiz
    context_object_name = 'taken_quizzes'
    template_name = 'students/taken_quiz_list.html'

    def get_queryset(self):
        queryset = self.request.user.student.taken_quizzes \
            .select_related('quiz', 'quiz__subject') \
            .order_by('quiz__name')
        return queryset


@login_required
@student_required
def take_quiz(request, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    student = request.user.student
    if student.quizzes.filter(pk=pk).exists():
        return render(request, 'students/taken_quiz.html')

    total_questions = quiz.questions.count()
    unanswered_questions = student.get_unanswered_questions(quiz)
    total_unanswered_questions = unanswered_questions.count()
    progress = 100 - round(((total_unanswered_questions - 1) / total_questions) * 100)
    question = unanswered_questions.first()

    if request.method == 'POST':
        form = TakeQuizForm(question=question, data=request.POST)
        if form.is_valid():
            with transaction.atomic():
                student_answer = form.save(commit=True, student=student)
                if student.get_unanswered_questions(quiz).exists():
                    return redirect('students:take_quiz', pk)
                else:
                    '''
                        Scoring Schema should be implemented here. Currently there is no partial/negative marking.
                    '''
                    student_correct_answers = 0
                    for question in quiz.questions.values_list('pk', flat=True):
                        if set(Choice.objects.filter(question=question, is_correct=True).values_list('pk', flat=True))\
                            == set(StudentAnswer.objects.filter(answer__question=question).distinct(). \
                                   first().answer.values_list('pk', flat=True)):
                            student_correct_answers += 1
                    score = round((student_correct_answers / total_questions) * 100.0, 2)
                    TakenQuiz.objects.create(student=student, quiz=quiz, score=score)
                    messages.success(request, 'You completed the quiz %s with %s points' % (quiz.name, score))
                    return redirect('students:quiz_list')
    else:
        form = TakeQuizForm(question=question)

    return render(request, 'students/take_quiz_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'progress': progress
    })

class TeacherSignUpView(CreateView):
    model = User
    form_class = TeacherSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'teacher'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('teachers:quiz_change_list')


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizListView(ListView):
    '''
        Basic view of all the quizzes created by or shared with the teacher.
    '''
    model = Quiz
    ordering = ('name', )
    context_object_name = 'quizzes'
    template_name = 'teachers/quiz_change_list.html'

    def get_queryset(self):
        queryset = self.request.user.quizzes.select_related('subject')
        shared_quizzes_queryset = self.request.user.shared_quizzes.select_related('subject')
        
        return (queryset | shared_quizzes_queryset) \
            .annotate(questions_count=Count('questions', distinct=True)).annotate(taken_count=Count('taken_quizzes', distinct=True))


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizCreateView(CreateView):
    '''
        Basic view for creating a quiz.
    '''
    model = Quiz
    fields = ('name', 'subject', )
    template_name = 'teachers/quiz_add_form.html'

    def form_valid(self, form):
        quiz = form.save(commit=False)
        quiz.owner = self.request.user
        quiz.save()
        messages.success(self.request, 'The quiz was created with success! Go ahead and add some questions now.')
        return redirect('teachers:quiz_change', quiz.pk)


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizUpdateView(UpdateView):
    '''
        View for updating a quiz. Delete button is not visible to Shared owners.
    '''
    model = Quiz
    fields = ('name', 'subject', )
    context_object_name = 'quiz'
    template_name = 'teachers/quiz_change_form.html'

    def get_context_data(self, **kwargs):
        kwargs['questions'] = self.get_object().questions.annotate(choices_count=Count('choices'))
        kwargs['shared_quiz'] = (self.get_object() in self.request.user.shared_quizzes.all())
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return (self.request.user.quizzes.all() | self.request.user.shared_quizzes.all())

    def get_success_url(self):
        return reverse('teachers:quiz_change', kwargs={'pk': self.object.pk})

@method_decorator([login_required, teacher_required], name='dispatch')
class QuizDeleteView(DeleteView):
    '''
        View for deleting a quiz. Shared owners can't delete the quiz.
    '''
    model = Quiz
    context_object_name = 'quiz'
    template_name = 'teachers/quiz_delete_confirm.html'
    success_url = reverse_lazy('teachers:quiz_change_list')

    def delete(self, request, *args, **kwargs):
        quiz = self.get_object()
        messages.success(request, 'The quiz %s was deleted with success!' % quiz.name)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        return (self.request.user.quizzes.all() | self.request.user.shared_quizzes.all())


@method_decorator([login_required, teacher_required], name='dispatch')
class QuizResultsView(DetailView):
    '''
        Basic view for quiz results. Shared owners can also view this.
    '''
    model = Quiz
    context_object_name = 'quiz'
    template_name = 'teachers/quiz_results.html'

    def get_context_data(self, **kwargs):
        quiz = self.get_object()
        taken_quizzes = quiz.taken_quizzes.select_related('student__user').order_by('-date')
        total_taken_quizzes = taken_quizzes.count()
        quiz_score = quiz.taken_quizzes.aggregate(average_score=Avg('score'))
        extra_context = {
            'taken_quizzes': taken_quizzes,
            'total_taken_quizzes': total_taken_quizzes,
            'quiz_score': quiz_score
        }
        kwargs.update(extra_context)
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return (self.request.user.quizzes.all() | self.request.user.shared_quizzes.all())


@login_required
@teacher_required
def question_add(request, pk):
    '''
        View for adding a question. Shared owners of the quiz can add a question.
    '''
    quiz = Quiz.objects.filter(pk=pk, owner=request.user).first()
    if not quiz:
        quiz = request.user.shared_quizzes.filter(pk=pk).first()
    if not quiz:
        return HttpResponseNotFound("Can't add question to this quiz")

    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            question.save()
            return redirect('teachers:question_change', quiz.pk, question.pk)
    else:
        form = QuestionForm()

    return render(request, 'teachers/question_add_form.html', {'quiz': quiz, 'form': form})


@login_required
@teacher_required
def share_with_teacher(request, pk):
    '''
        View for sharing a quiz with a teacher. Won't accept if the username provided doesn't match with
        any teacher's username.
    '''
    quiz = get_object_or_404(Quiz, pk=pk, owner=request.user)

    if request.method == 'POST':
        teacher_name = request.POST.get('username')
        teacher = User.objects.filter(username=teacher_name, is_teacher=True).first()
        if not teacher:
            messages.error(request, f"Teacher with username {teacher_name} does not exists")
            return redirect('teachers:quiz_share', quiz.pk)
        quiz.shared_owners.add(teacher)
        quiz.save()
        messages.success(request, f"Quiz successfully shared with {teacher_name}")
        return redirect('teachers:quiz_change', quiz.pk)
    else:
        form = ShareTeacherForm()
    
    return render(request, 'teachers/quiz_share.html', {'quiz': quiz, 'form': form})


@login_required
@teacher_required
def question_change(request, quiz_pk, question_pk):
    '''
        View for changing a question. Shared owners of the quiz can change a question.
    '''
    quiz = Quiz.objects.filter(pk=quiz_pk, owner=request.user).first()
    if not quiz:
        quiz = request.user.shared_quizzes.filter(pk=quiz_pk).first()
    if not quiz:
        return HttpResponseNotFound("Can't add question to this quiz")
    question = get_object_or_404(Question, pk=question_pk, quiz=quiz)
    
    AnswerFormSet = inlineformset_factory(
        Question,
        Choice,
        formset=BaseAnswerInlineFormSet,
        exclude=[],
        min_num=2,
        validate_min=True,
        max_num=5,
        validate_max=True
    )

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        formset = AnswerFormSet(request.POST, instance=question)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
            messages.success(request, 'Question and choices saved with success!')
            return redirect('teachers:quiz_change', quiz.pk)
    else:
        form = QuestionForm(instance=question)
        formset = AnswerFormSet(instance=question)

    return render(request, 'teachers/question_change_form.html', {
        'quiz': quiz,
        'question': question,
        'form': form,
        'formset': formset
    })

@method_decorator([login_required, teacher_required], name='dispatch')
class QuestionDeleteView(DeleteView):
    '''
        View for deleting a question. Shared owners of the quiz can also delete the question.
    '''
    model = Question
    context_object_name = 'question'
    template_name = 'teachers/question_delete_confirm.html'
    pk_url_kwarg = 'question_pk'

    def get_context_data(self, **kwargs):
        question = self.get_object()
        kwargs['quiz'] = question.quiz
        return super().get_context_data(**kwargs)

    def delete(self, request, *args, **kwargs):
        question = self.get_object()
        messages.success(request, 'The question %s was deleted with success!' % question.text)
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Question.objects.filter(quiz__owner=self.request.user)
        shared_quizzes = self.request.user.shared_quizzes.all()
        for shared_quiz in shared_quizzes:
            queryset = (queryset | Question.objects.filter(quiz=shared_quiz))
        return queryset

    def get_success_url(self):
        question = self.get_object()
        return reverse('teachers:quiz_change', kwargs={'pk': question.quiz_id})

def main(request):
    # Homepage
    if request.user.is_authenticated:
        if request.user.is_teacher:
            return redirect('teachers:quiz_change_list')
        else:
            return redirect('students:quiz_list')
    return render(request, 'main.html')