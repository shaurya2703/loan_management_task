# Generated by Django 4.2.11 on 2024-04-03 07:31

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('loan_app', '0002_remove_user_aadhar_id_alter_user_annual_income_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='unique_user_id',
            field=models.CharField(default=uuid.UUID('d07da95f-7465-417f-852a-daf6dba64343'), editable=False, max_length=20, primary_key=True, serialize=False),
        ),
    ]
