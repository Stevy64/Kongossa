# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_message_file_message_file_name_alter_message_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='video',
            field=models.FileField(blank=True, null=True, upload_to='messages/videos/', verbose_name='Vidéo'),
        ),
        migrations.AddField(
            model_name='message',
            name='audio',
            field=models.FileField(blank=True, null=True, upload_to='messages/audios/', verbose_name='Audio'),
        ),
    ]


