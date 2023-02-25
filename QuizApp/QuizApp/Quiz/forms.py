from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError

from Quiz.models import (Question, Student, StudentAnswer,
                              Subject, User)


class TeacherSignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_teacher = True
        if commit:
            user.save()
        return user


class StudentSignUpForm(UserCreationForm):
    interests = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_student = True
        user.save()
        student = Student.objects.create(user=user)
        student.interests.add(*self.cleaned_data.get('interests'))
        return user


class StudentInterestsForm(forms.ModelForm):
    '''
        Basic form for students to fill out their interests.
    '''
    class Meta:
        model = Student
        fields = ('interests', )
        widgets = {
            'interests': forms.CheckboxSelectMultiple
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('text', )


class ShareTeacherForm(forms.ModelForm):
    '''
        Form for sharing the selected quiz with another teacher. Contains only username.
    '''
    class Meta:
        model = User
        fields = ('username', )


class BaseAnswerInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        has_one_correct_answer = False
        for form in self.forms:
            if not form.cleaned_data.get('DELETE', False):
                if form.cleaned_data.get('is_correct', False):
                    has_one_correct_answer = True
                    break
        if not has_one_correct_answer:
            raise ValidationError('Mark at least one answer as correct.', code='no_correct_answer')

class TakeQuizForm(forms.ModelForm):
    '''
        Form for students to take quizzes.
    '''
    answer = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=True)

    class Meta:
        model = StudentAnswer
        fields = ('answer', )

    def __init__(self, *args, **kwargs):
        try:
            question = kwargs.pop('question')
            super().__init__(*args, **kwargs)
            self.fields['answer'].queryset = question.choices
        except Exception as e:
            print(e)

    def save(self, commit=True, student=None, *args, **kwargs):
        try:
            model = StudentAnswer.objects.create(student=student)
            model.answer.add(*self.cleaned_data.get('answer'))
            if commit:
                model.save()
            return model
        except Exception as e:
            print(e)
