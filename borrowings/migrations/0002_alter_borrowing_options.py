# Generated by Django 5.1.1 on 2024-09-20 14:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("borrowings", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="borrowing",
            options={"ordering": ["id"]},
        ),
    ]
