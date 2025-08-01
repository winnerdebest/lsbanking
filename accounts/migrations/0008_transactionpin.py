# Generated by Django 5.2.1 on 2025-07-22 03:23

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_user_profile_picture'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransactionPIN',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pin_hash', models.CharField(max_length=128)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='transaction_pin', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
