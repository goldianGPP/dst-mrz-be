from django.db import models

class Gender(models.Model):
    code = models.CharField(max_length=40, primary_key=True)
    name = models.CharField(max_length=100)
    class Meta:
        db_table = 'mnt_gender'

class Country(models.Model):
    code = models.CharField(max_length=40, primary_key=True)
    alpha3 = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    class Meta:
        db_table = 'mnt_country'