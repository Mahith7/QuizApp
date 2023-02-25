# QuizApp

Basically, In this quiz app, Users can register as either Teacher or Student. <br />
Teachers create quizzes and Students take the quizzes.<br />
Each quiz contains some number of multiple choice questions.<br />
A student gets the question correct only if he marks all the correct choices pertaining to the same.<br />
No negative/partial marking.<br />
<br />
# Requirements: <br /> <br />
`Django` <br />
`django-crispy-forms` <br />
`crispy_bootstrap5` <br />
<br />
# Running it locally: <br />
<br />
Clone the repo. <br />
Create and activate a virtual environment. <br />
Install the requirements. <br />
Run `python manage.py runserver` to start the server.<br />
Change the `ALLOWED_HOSTS` variable in `settings.py` file.<br />
Do `python manage.py makemigrations` to create the tables and create subjects as well.<br />
