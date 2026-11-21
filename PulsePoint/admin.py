from django.contrib import admin
from .models import Prescription, RegisterModel,LabReport
from .models import Doctor,MedicalRecord,Medicine,Bill,Bed,EmergencyCase

admin.site.register(Doctor)

admin.site.register(RegisterModel)

admin.site.register(MedicalRecord)

admin.site.register(Prescription)

admin.site.register(LabReport)

admin.site.register(Medicine)

admin.site.register(Bill)

admin.site.register(Bed)

admin.site.register(EmergencyCase)