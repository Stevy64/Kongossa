# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0006_groupmessage_file_groupmessage_file_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='video',
            field=models.FileField(blank=True, null=True, upload_to='posts/videos/', verbose_name='Vidéo'),
        ),
        migrations.AddField(
            model_name='post',
            name='audio',
            field=models.FileField(blank=True, null=True, upload_to='posts/audios/', verbose_name='Audio'),
        ),
        migrations.AddField(
            model_name='groupmessage',
            name='video',
            field=models.FileField(blank=True, null=True, upload_to='group_messages/videos/', verbose_name='Vidéo'),
        ),
        migrations.AddField(
            model_name='groupmessage',
            name='audio',
            field=models.FileField(blank=True, null=True, upload_to='group_messages/audios/', verbose_name='Audio'),
        ),
    ]


