from django.test import TestCase
from Quiz.models import (Quiz, Question, Choice, Student, StudentAnswer,
                              Subject, User, TakenQuiz)

class ModelsTestCase(TestCase):
    def setUp(self):
        self.teacher1 = User.objects.create(username='teacher1', is_teacher=True)
        self.user = User.objects.create(username='student1', is_student=True)
        self.subject1 = Subject.objects.create(name='subject1')
        self.quiz1 = Quiz.objects.create(owner=self.teacher1, name='quiz1', subject=self.subject1)
        self.student1 = Student.objects.create(user=self.user)
        self.student1.interests.add(self.subject1)
        self.student1.save()
        self.question1 = Question.objects.create(quiz=self.quiz1, text='question1')
        self.choice11 = Choice.objects.create(question=self.question1, text='choice11', is_correct=True)
        self.choice12 = Choice.objects.create(question=self.question1, text='choice12', is_correct=True)
        self.choice13 = Choice.objects.create(question=self.question1, text='choice13', is_correct=False)
        self.question2 = Question.objects.create(quiz=self.quiz1, text='question2')
        self.choice21 = Choice.objects.create(question=self.question2, text='choice21', is_correct=False)
        self.choice22 = Choice.objects.create(question=self.question2, text='choice22', is_correct=True)
        self.choice23 = Choice.objects.create(question=self.question2, text='choice23', is_correct=False)
        self.choice24 = Choice.objects.create(question=self.question2, text='choice24', is_correct=True)
        self.studentanswer1 = StudentAnswer.objects.create(student=self.student1)
        self.studentanswer1.answer.add(self.choice11)
        self.studentanswer1.answer.add(self.choice12)
        self.studentanswer1.save()

    def test_get_unanswered_questions(self):
        # Student answered only question1.
        unanswered_questions = list(self.student1.get_unanswered_questions(self.quiz1))
        self.assertEqual(unanswered_questions, [self.question2])

        # Student now attempted question2 as well.
        studentanswer2 = StudentAnswer.objects.create(student=self.student1)
        studentanswer2.answer.add(self.choice21)
        studentanswer2.answer.add(self.choice22)
        unanswered_questions = list(self.student1.get_unanswered_questions(self.quiz1))
        self.assertEqual(unanswered_questions, [])