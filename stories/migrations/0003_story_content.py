# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='content',
            field=models.TextField(blank=True, verbose_name='Texte'),
        ),
    ]


