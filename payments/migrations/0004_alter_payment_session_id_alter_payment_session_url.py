# Generated by Django 5.1.1 on 2024-09-20 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0003_alter_payment_session_id_alter_payment_session_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="session_id",
            field=models.TextField(max_length=500),
        ),
        migrations.AlterField(
            model_name="payment",
            name="session_url",
            field=models.URLField(max_length=500),
        ),
    ]
