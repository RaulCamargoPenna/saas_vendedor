from django.db import models

class Projects(models.Model):
    name = models.CharField(verbose_name='nome', max_length=250)
    description = models.CharField(verbose_name='descrição' ,max_length=250)
    link = models.URLField(verbose_name='link de acesso')
    
    def __str__(self):
        return self.name