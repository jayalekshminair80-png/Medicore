from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.db.models import Sum
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout as auth_logout


from PulsePoint.models import Bill, Department, EmergencyCase, Medicine, PendingRegistration, RegisterModel,Appointment,Doctor,MedicalRecord,Prescription,LabReport,Bed, StaffMember
from . forms import AppointmentStatusForm, BillForm, DepartmentForm, EmergencyCaseForm, LabReportForm, OTPVerificationForm, RegisterForm,LoginForm,AppointmentForm,MedicineForm,BedForm,StaffMemberForm
from django.utils import timezone



import secrets
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail

from datetime import timedelta

def home(request):
    return render(request, 'home.html')

def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            patient = RegisterModel.objects.filter(username=username).first()

            if patient and check_password(password, patient.password):
                pass
            elif patient and patient.password == password:
                patient.password = make_password(password)
                patient.save(update_fields=["password"])
            else:
                patient = None

            if patient:
                request.session["patient_id"] = patient.id
                return redirect("patient_dashboard")

            form.add_error(None, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, "login.html", {"form": form})

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)

        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]

            if RegisterModel.objects.filter(username=username).exists():
                form.add_error("username", "This username is already registered.")
            elif RegisterModel.objects.filter(email=email).exists():
                form.add_error("email", "This email is already registered.")
            else:
                PendingRegistration.objects.filter(
                    username=username
                ).delete()

                otp = f"{secrets.randbelow(1_000_000):06d}"

                pending = PendingRegistration.objects.create(
                    profile=form.cleaned_data["profile"],
                    full_name=form.cleaned_data["full_name"],
                    username=username,
                    email=email,
                    phone=form.cleaned_data["phone"],
                    password=make_password(form.cleaned_data["password"]),
                    otp_hash=make_password(otp),
                )

                request.session["pending_registration_id"] = pending.id

                send_mail(
                    "Your MediCore verification code",
                    f"Your email verification code is {otp}. It expires in 10 minutes.",
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                )

                return redirect("verify_otp")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})

def verify_otp(request):
    pending_id = request.session.get("pending_registration_id")
    pending = get_object_or_404(PendingRegistration, id=pending_id)

    if timezone.now() - pending.created_at > timedelta(minutes=10):
        pending.delete()
        request.session.pop("pending_registration_id", None)
        messages.error(request, "The OTP expired. Please register again.")
        return redirect("register")

    if request.method == "POST":
        form = OTPVerificationForm(request.POST)

        if form.is_valid():
            otp = form.cleaned_data["otp"]

            if check_password(otp, pending.otp_hash):
                RegisterModel.objects.create(
                    profile=pending.profile,
                    full_name=pending.full_name,
                    username=pending.username,
                    email=pending.email,
                    phone=pending.phone,
                    password=pending.password,
                )

                send_mail(
                    "MediCore account created",
                    f"Hello {pending.full_name}, your MediCore account has been created successfully.",
                    settings.DEFAULT_FROM_EMAIL,
                    [pending.email],
                )

                pending.delete()
                request.session.pop("pending_registration_id", None)
                messages.success(request, "Email verified. Your account has been created.")
                return redirect("login")

            form.add_error("otp", "The OTP is incorrect.")
    else:
        form = OTPVerificationForm()

    return render(request, "verify_otp.html", {"form": form})



@staff_member_required(login_url="admin_login")
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




@staff_member_required(login_url="admin_login")
def beds(request):
    beds = Bed.objects.all().order_by("ward", "bed_number")
    return render(request, "beds.html", {"beds": beds})



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

@staff_member_required(login_url="admin_login")
def admin_billing(request):
    if request.method == "POST":
        form = BillForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("admin_billing")
    else:
        form = BillForm()

    bills = Bill.objects.select_related("patient").order_by("-bill_date")
    return render(
        request,
        "admin_billing.html",
        {"bills": bills, "form": form},
    )


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


def doctor_dashboard(request):
    context={'appointments':[]}
    return render(request, 'doctor_dashboard.html', context)



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


def pharmacy_dashboard(request):
    medicines = Medicine.objects.all().order_by("name")
    return render(
        request,
        "pharmacy_dashboard.html",
        {"medicines": medicines}
    )



def laboratory_dashboard(request):
    context={'lab_tests':[]}
    return render(request, 'laboratory_dashboard.html', context)




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


@staff_member_required(login_url="admin_login")
def emergency(request):
    cases = EmergencyCase.objects.all().order_by("-reported_at")
    return render(request, "emergency.html", {"cases": cases})



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



def patient_profile(request):
    patient_id = request.session.get('patient_id')

    if not patient_id:
        return redirect('login')

    patient = get_object_or_404(RegisterModel, id=patient_id)

    return render(request, 'patient_profile.html', {'patient': patient})


@staff_member_required(login_url="admin_login")
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





def doctors(request):
    search = request.GET.get("search", "").strip()
    doctor_list = Doctor.objects.filter(is_available=True)

    if search:
        doctor_list = doctor_list.filter(
            models.Q(full_name__icontains=search)
            | models.Q(specialization__icontains=search)
        )

    return render(request, "doctors.html", {"doctors": doctor_list})



# Placeholder handlers for sub-actions to ensure all template reverse URLs resolve safely
def placeholder_action(request, *args, **kwargs):
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('home')

@staff_member_required(login_url="admin_login")
def add_medicine(request):
    if request.method == "POST":
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("pharmacy")
    else:
        form = MedicineForm()

    return render(request, "add_medicine.html", {"form": form})

@staff_member_required(login_url="admin_login")
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



@staff_member_required(login_url="admin_login")
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




@staff_member_required(login_url="admin_login")
def add_bed(request):
    if request.method == "POST":
        form = BedForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("beds")
    else:
        form = BedForm()

    return render(request, "add_bed.html", {"form": form})

@staff_member_required(login_url="admin_login")
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



@staff_member_required(login_url="admin_login")
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





def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            auth_login(request, user)
            return redirect("admin_dashboard")

        messages.error(request, "Invalid admin username or password.")

    return render(request, "admin_login.html")



@staff_member_required(login_url="admin_login")
def patient_list(request):
    patients = RegisterModel.objects.all().order_by("full_name")
    return render(request, "patient_list.html", {"patients": patients})





@staff_member_required(login_url="admin_login")
def staff_list(request):
    if request.method == "POST":
        form = StaffMemberForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("staff_list")
    else:
        form = StaffMemberForm()

    staff_members = StaffMember.objects.all()
    return render(
        request,
        "staff_list.html",
        {"staff_members": staff_members, "form": form},
    )



@staff_member_required(login_url="admin_login")
def staff_edit(request, pk):
    staff_member = get_object_or_404(StaffMember, pk=pk)

    if request.method == "POST":
        form = StaffMemberForm(request.POST, instance=staff_member)
        if form.is_valid():
            form.save()
            return redirect("staff_list")
    else:
        form = StaffMemberForm(instance=staff_member)

    return render(
        request,
        "staff_edit.html",
        {"form": form, "staff_member": staff_member},
    )



@staff_member_required(login_url="admin_login")
def staff_delete(request, pk):
    staff_member = get_object_or_404(StaffMember, pk=pk)

    if request.method == "POST":
        staff_member.delete()
        return redirect("staff_list")

    return render(
        request,
        "staff_delete.html",
        {"staff_member": staff_member},
    )


@staff_member_required(login_url="admin_login")
def department_list(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("department_list")
    else:
        form = DepartmentForm()

    departments = Department.objects.all().order_by("name")
    return render(
        request,
        "department_list.html",
        {"departments": departments, "form": form},
    )

@staff_member_required(login_url="admin_login")
def department_edit(request, pk):
    department = get_object_or_404(Department, pk=pk)

    if request.method == "POST":
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            return redirect("department_list")
    else:
        form = DepartmentForm(instance=department)

    return render(
        request,
        "department_edit.html",
        {"form": form, "department": department},
    )


@staff_member_required(login_url="admin_login")
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)

    if request.method == "POST":
        department.delete()
        return redirect("department_list")

    return render(
        request,
        "department_delete.html",
        {"department": department},
    )

@staff_member_required(login_url="admin_login")
def appointment_list(request):
    appointments = (
        Appointment.objects
        .select_related("patient")
        .order_by("appointment_date")
    )
    return render(
        request,
        "appointment_list.html",
        {"appointments": appointments},
    )


@staff_member_required(login_url="admin_login")
def appointment_update_status(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    if request.method == "POST":
        form = AppointmentStatusForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()

    return redirect("appointment_list")

@staff_member_required(login_url="admin_login")
def analytics(request):
    context = {
        "total_patients": RegisterModel.objects.count(),
        "total_doctors": Doctor.objects.count(),
        "total_staff": StaffMember.objects.count(),
        "total_appointments": Appointment.objects.count(),
        "scheduled_appointments": Appointment.objects.filter(status="Scheduled").count(),
        "completed_appointments": Appointment.objects.filter(status="Completed").count(),
        "cancelled_appointments": Appointment.objects.filter(status="Cancelled").count(),
        "total_lab_reports": LabReport.objects.count(),
        "available_beds": Bed.objects.filter(status="Available").count(),
        "occupied_beds": Bed.objects.filter(status="Occupied").count(),
        "maintenance_beds": Bed.objects.filter(status="Maintenance").count(),
        "paid_bills": Bill.objects.filter(status="Paid").count(),
        "pending_bills": Bill.objects.filter(status="Pending").count(),
        "total_billed_amount": Bill.objects.aggregate(total=Sum("amount"))["total"] or 0,
        "pending_amount": Bill.objects.filter(status="Pending").aggregate(
            total=Sum("amount")
        )["total"] or 0,
        "open_emergencies": EmergencyCase.objects.filter(
            status__in=["Open", "In Progress"]
        ).count(),
        "resolved_emergencies": EmergencyCase.objects.filter(status="Resolved").count(),
        "total_medicines": Medicine.objects.count(),
    }
    return render(request, "analytics.html", context)


@staff_member_required(login_url="admin_login")
def lab_requests(request):
    if request.method == "POST":
        form = LabReportForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lab_requests")
    else:
        form = LabReportForm()

    reports = LabReport.objects.select_related("patient").order_by("-report_date")
    return render(
        request,
        "admin_lab_reports.html",
        {"reports": reports, "form": form},
    )


def admin_logout(request):
    if request.method == "POST":
        auth_logout(request)
    return redirect("admin_login")


def patient_logout(request):
    if request.method == "POST":
        request.session.pop("patient_id", None)
    return redirect("login")







