# Generated by Django 4.2.11 on 2024-04-03 05:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loan_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='annual_income',
            field=models.DecimalField(decimal_places=2, max_digits=15),
        ),
    ]
