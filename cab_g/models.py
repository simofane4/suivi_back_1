from django.db import models
from django.contrib.auth.models import User


gendelist = [('Female','Femal'),('Male','Male')]

class Specialite(models.Model):
    name = models.CharField(max_length=250)
    def __str__(self):
        return f'{self.name} ' 

class Cabinet(models.Model):
    name = models.CharField(max_length=255)
    number = models.CharField(max_length=255,unique=True)
    address = models.CharField(max_length=500,blank=True,null=True)
    def __str__(self):
        return f'{self.name} ' 


class Doctor(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    cabinet= models.ForeignKey(Cabinet,on_delete=models.CASCADE)
    img = models.ImageField(upload_to='media/doctor/',default="media/doctor/default.png")
    inp = models.CharField(max_length=255)
    gender = models.CharField(max_length=255,choices=gendelist)
    phone = models.CharField(max_length=255,unique=True)
    address = models.CharField(max_length=500,blank=True,null=True)
    specialiste = models.ForeignKey(Specialite,on_delete=models.RESTRICT)
    def __str__(self):
        return f'doc, {self.user.first_name} {self.user.last_name} ' 

class Assistant(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    cabinet= models.ForeignKey(Cabinet,on_delete=models.CASCADE)
    img = models.ImageField(upload_to='media/assistant/',default="media/assistant/default.png")
    cin = models.CharField(max_length=25,unique=True,null=True, blank=True)
    gender = models.CharField(max_length=255,choices=gendelist)
    phone = models.CharField(max_length=255,unique=True)
    address = models.CharField(max_length=500,blank=True,null=True)
    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} ' 


class Patient(models.Model):
    cabinet = models.ForeignKey(Cabinet,on_delete=models.CASCADE)
    cin = models.CharField(max_length=25,unique=True)
    img = models.ImageField(default="media/patient/default.png",upload_to='media/patient/')
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    gender = models.CharField(max_length=255,choices=gendelist)
    age = models.IntegerField(blank=True,null=True)
    phone = models.CharField(max_length=25,unique=True)
    address = models.CharField(max_length=500)
    child = models.BooleanField(default=False)
    def __str__(self):
        return f'  {self.firstname} {self.lastname}'

class PatientFile(models.Model):
    patient = models.ForeignKey(Patient ,on_delete=models.CASCADE)
    file = models.FileField(upload_to ='uploads/')

class ActeDemander(models.Model):
    cabinet = models.ForeignKey(Cabinet,on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    def __str__(self):
        return f'{self.title} {self.cabinet} ' 

class ActeFait(models.Model):
    cabinet = models.ForeignKey(Cabinet,on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    def __str__(self):
        return f'{self.title} {self.cabinet} ' 

class Medicament(models.Model):
    cabinet = models.ForeignKey(Cabinet,on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    def __str__(self):
        return f'{self.name} {self.cabinet} ' 


    

class Appointment(models.Model):
    patient = models.ForeignKey(Patient,on_delete=models.CASCADE)
    date = models.DateField()
    fm = models.TimeField()
    To = models.TimeField()
    description = models.TextField(max_length=500)
    payed = models.BooleanField()

    def __str__(self):
        return f'{self.patient} {self.date}' 

class Ordonnance(models.Model):
    cabinet = models.ForeignKey(Cabinet,on_delete=models.CASCADE)
    appointment = models.ForeignKey(Patient,on_delete=models.CASCADE)
    actedemander = models.ForeignKey(ActeDemander,on_delete=models.CASCADE,blank=True,null=True)
    actefait = models.ForeignKey(ActeFait,on_delete=models.CASCADE,blank=True,null=True)
    medicament = models.ManyToManyField(Medicament)
    description = models.TextField()
    def __str__(self):
        return f'{self.appointment} {self.medicament}' 


class Invoice(models.Model):
    appointment = models.ForeignKey(Appointment,on_delete=models.CASCADE)
    date = models.DateTimeField()
    recipient = models.ForeignKey(User,on_delete=models.CASCADE)
    amount = models.IntegerField()
    payed = models.BooleanField(default=False)
    def __str__(self):
        return f'{self.appointment} {self.date} {self.amount} {self.status}'  




