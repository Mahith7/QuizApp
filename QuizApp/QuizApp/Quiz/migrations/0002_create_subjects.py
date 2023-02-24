from django.db import migrations


def create_subjects(apps, schema_editor):
    Subject = apps.get_model('Quiz', 'Subject')
    Subject.objects.create(name='CS101', color='#343a40')
    Subject.objects.create(name='Computer Networks', color='#007bff')
    Subject.objects.create(name='Compilers', color='#28a745')
    Subject.objects.create(name='Databases', color='#ffc107')


class Migration(migrations.Migration):

    dependencies = [
        ('Quiz', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_subjects),
    ]