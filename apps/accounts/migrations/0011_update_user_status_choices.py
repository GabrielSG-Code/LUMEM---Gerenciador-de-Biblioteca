# Generated to update user status choices to include INACTIVE option

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_userregularization'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='status',
            field=models.CharField(
                choices=[
                    ('active', 'Ativo'), 
                    ('inactive', 'Inativo'), 
                    ('blocked', 'Bloqueado')
                ],
                default='active',
                max_length=15
            ),
        ),
    ]