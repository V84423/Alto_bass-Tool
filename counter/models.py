from django.db import models

class Counter(models.Model):
    key = models.CharField(max_length=10)
    value = models.IntegerField() 

class User(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=255)
	email = models.CharField(max_length=255)
	password = models.CharField(max_length=255)
	token = models.CharField(max_length=255)
	verfied = models.IntegerField(default=0)
	state = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		db_table = 'user'
	def __str__(self):
		return str(self.id)

class Url(models.Model):
	id = models.AutoField(primary_key=True)
	url = models.TextField()
	goods = models.CharField(max_length=255)
	company = models.CharField(max_length=255)
	onsale = models.IntegerField(default=0)
	inventory = models.IntegerField(default=0)
	status = models.IntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	class Meta:
		db_table = 'url'
	def __str__(self):
		return str(self.id)