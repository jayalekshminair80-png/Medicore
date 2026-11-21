from django.forms import models
from django.shortcuts import render, redirect
from django.shortcuts import render, redirect, get_object_or_404
from django.db import models

from PulsePoint.models import Bill, EmergencyCase, Medicine, RegisterModel,Appointment,Doctor,MedicalRecord,Prescription,LabReport,Bed
from . forms import EmergencyCaseForm, RegisterForm,LoginForm,AppointmentForm,MedicineForm,BedForm
from django.utils import timezone

def home(request):
    return render(request, 'home.html')

def login(request):
    if request.method=="POST":
        form=LoginForm(request.POST)
        if form.is_valid():
            patient = RegisterModel.objects.filter(
                username=form.cleaned_data['username']
            ).first()
            if patient is not None:
                request.session['patient_id'] = patient.id
                return redirect('patient_dashboard')
            form.add_error(None, 'Account could not be found. Please try again.')
    else:
            form=LoginForm()
    return render(request,"login.html",{'form':form})

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST,request.FILES)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})


def patient_dashboard(request):

    patient_id = request.session.get('patient_id')

    if not patient_id:
        return redirect('login')

    patient = RegisterModel.objects.get(id=patient_id)

    context = {
        'username': patient.full_name,
        'patient': patient,
        'appointments': Appointment.objects.filter(
            patient=patient,
            appointment_date__gte=timezone.now(),
            status="Scheduled"
        ).order_by("appointment_date")
    }

    return render(request, 'patient_dashboard.html', context)


def patient_profile(request):
    patient_id = request.session.get('patient_id')

    if not patient_id:
        return redirect('login')

    patient = get_object_or_404(RegisterModel, id=patient_id)

    return render(request, 'patient_profile.html', {'patient': patient})

def book_appointment(request):
    patient_id = request.session.get("patient_id")

    if not patient_id:
        return redirect("login")

    patient = get_object_or_404(RegisterModel, id=patient_id)

    if request.method == "POST":
        form = AppointmentForm(request.POST)

        if form.is_valid():
            appointment = form.save(commit=False)

            doctor = get_object_or_404(
                Doctor,
                id=form.cleaned_data["doctor_name"],
                is_available=True
            )

            appointment.doctor_name = doctor.full_name
            appointment.doctor_specialization = doctor.specialization
            appointment.patient = patient
            appointment.save()

            return redirect("book_appointment")
    else:
        form = AppointmentForm()

    return render(request, "book_appointment.html", {"form": form})

def cancel_appointment(request, appointment_id):
    patient_id = request.session.get("patient_id")

    if not patient_id:
        return redirect("login")

    if request.method != "POST":
        return redirect("patient_dashboard")

    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        patient_id=patient_id,
        status="Scheduled"
    )

    appointment.status = "Cancelled"
    appointment.save(update_fields=["status"])

    return redirect("patient_dashboard")


def medical_records(request):
    patient_id = request.session.get("patient_id")

    if not patient_id:
        return redirect("login")

    patient = get_object_or_404(RegisterModel, id=patient_id)
    records = MedicalRecord.objects.filter(
        patient=patient
    ).select_related("doctor").order_by("-record_date")

    return render(
        request,
        "medical_records.html",
        {"patient": patient, "records": records}
    )


def prescriptions(request):
    patient_id = request.session.get("patient_id")

    if not patient_id:
        return redirect("login")

    patient = get_object_or_404(RegisterModel, id=patient_id)
    prescriptions = Prescription.objects.filter(
        patient=patient
    ).select_related("doctor").order_by("-prescribed_date")

    return render(
        request,
        "prescriptions.html",
        {"patient": patient, "prescriptions": prescriptions}
    )


def lab_reports(request):
    patient_id = request.session.get("patient_id")

    if not patient_id:
        return redirect("login")

    patient = get_object_or_404(RegisterModel, id=patient_id)
    reports = LabReport.objects.filter(
        patient=patient
    ).order_by("-report_date")

    return render(
        request,
        "lab_reports.html",
        {"patient": patient, "reports": reports}
    )



def pharmacy_dashboard(request):
    medicines = Medicine.objects.all().order_by("name")
    return render(
        request,
        "pharmacy_dashboard.html",
        {"medicines": medicines}
    )


def pharmacy(request):
    search = request.GET.get("search", "").strip()
    medicines = Medicine.objects.all().order_by("name")

    if search:
        medicines = medicines.filter(name__icontains=search)

    return render(
        request,
        "pharmacy.html",
        {"medicines": medicines}
    )



# Placeholder handlers for sub-actions to ensure all template reverse URLs resolve safely
def placeholder_action(request, *args, **kwargs):
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('home')


def add_medicine(request):
    if request.method == "POST":
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("pharmacy")
    else:
        form = MedicineForm()

    return render(request, "add_medicine.html", {"form": form})


def edit_medicine(request, id):
    medicine = get_object_or_404(Medicine, id=id)

    if request.method == "POST":
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            return redirect("pharmacy")
    else:
        form = MedicineForm(instance=medicine)

    return render(
        request,
        "edit_medicine.html",
        {"form": form, "medicine": medicine}
    )

def delete_medicine(request, id):
    medicine = get_object_or_404(Medicine, id=id)

    if request.method == "POST":
        medicine.delete()
        return redirect("pharmacy")

    return render(
        request,
        "delete_medicine.html",
        {"medicine": medicine}
    )


def billing(request):
    patient_id = request.session.get("patient_id")

    if not patient_id:
        return redirect("login")

    patient = get_object_or_404(RegisterModel, id=patient_id)
    bills = Bill.objects.filter(
        patient=patient
    ).order_by("-bill_date")

    return render(
        request,
        "billing.html",
        {"patient": patient, "bills": bills}
    )


def beds(request):
    beds = Bed.objects.all().order_by("ward", "bed_number")
    return render(request, "beds.html", {"beds": beds})


def add_bed(request):
    if request.method == "POST":
        form = BedForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("beds")
    else:
        form = BedForm()

    return render(request, "add_bed.html", {"form": form})


def edit_bed(request, id):
    bed = get_object_or_404(Bed, id=id)

    if request.method == "POST":
        form = BedForm(request.POST, instance=bed)
        if form.is_valid():
            form.save()
            return redirect("beds")
    else:
        form = BedForm(instance=bed)

    return render(request, "edit_bed.html", {"form": form, "bed": bed})


def emergency(request):
    cases = EmergencyCase.objects.all().order_by("-reported_at")
    return render(request, "emergency.html", {"cases": cases})


def register_emergency(request):
    if request.method == "POST":
        form = EmergencyCaseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("emergency")
    else:
        form = EmergencyCaseForm()

    return render(
        request,
        "register_emergency.html",
        {"form": form}
    )


def receptionist_dashboard(request):
    today = timezone.localdate()
    appointments = Appointment.objects.filter(
        appointment_date__date=today
    ).select_related("patient").order_by("appointment_date")

    return render(
        request,
        "receptionist_dashboard.html",
        {"appointments": appointments}
    )
    return render(request, 'receptionist_dashboard.html', context)




def admin_dashboard(request):
    context = {
        "total_patients": RegisterModel.objects.count(),
        "total_doctors": Doctor.objects.count(),
        "total_appointments": Appointment.objects.count(),
        "available_beds": Bed.objects.filter(status="Available").count(),
        "pending_payments": Bill.objects.filter(status="Pending").count(),
        "emergency_cases": EmergencyCase.objects.filter(
            status__in=["Open", "In Progress"]
        ).count(),
    }

    return render(request, "admin_dashboard.html", context)



def patient_list(request):
    patients = RegisterModel.objects.all().order_by("full_name")
    return render(request, "patient_list.html", {"patients": patients})


def doctors(request):
    search = request.GET.get("search", "").strip()
    doctor_list = Doctor.objects.filter(is_available=True)

    if search:
        doctor_list = doctor_list.filter(
            models.Q(full_name__icontains=search)
            | models.Q(specialization__icontains=search)
        )

    return render(request, "doctors.html", {"doctors": doctor_list})


def doctor_dashboard(request):
    context={'appointments':[]}
    return render(request, 'doctor_dashboard.html', context)



def laboratory_dashboard(request):
    context={'lab_tests':[]}
    return render(request, 'laboratory_dashboard.html', context)






