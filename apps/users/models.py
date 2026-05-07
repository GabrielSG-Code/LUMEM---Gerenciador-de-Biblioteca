from django.db import models

class Usuarios(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    username = models.CharField(max_length=255)
    senha = models.CharField(max_length=255)
    privilegio = models.CharField(max_length=20, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'usuarios'