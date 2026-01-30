from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.conf import settings
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors


from app1.forms import AddressForm, BuyerProfileForm, BuyerUserForm, ClothForm, RentRequestForm, SellerProfileForm
from .models import Cloth, RentRequest

from .models import CustomUser, Address, BuyerProfile, SellerProfile,  Cloth, Category


# Create your views here.
def home(request):
    return render(request, "index.html")

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import CustomUser


def login_view(request):
    # 🔥 BLOCK LOGGED-IN USERS
    if request.user.is_authenticated:
        if request.user.is_buyer:
            return redirect("buyer_dashboard")
        elif request.user.is_seller:
            return redirect("seller_dashboard")
        else:
            return redirect("home")

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "Invalid email or password")
            return redirect("login")

        user = authenticate(
            request,
            username=user_obj.username,
            password=password
        )

        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully")

            # 🔥 ROLE BASED REDIRECT
            if user.is_buyer:
                return redirect("buyer_dashboard")
            elif user.is_seller:
                return redirect("seller_dashboard")
            else:
                return redirect("home")

        messages.error(request, "Invalid email or password")
        return redirect("login")

    return render(request, "login.html")



def register(request):
    if request.method == "POST":

        # ---------------- USER DATA ----------------
        role = request.POST.get("role")
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        contact = request.POST.get("contact")
        password = request.POST.get("password")

        # ---------------- ADDRESS DATA ----------------
        building = request.POST.get("building")
        taluka = request.POST.get("taluka")
        city = request.POST.get("city")
        state = request.POST.get("state")
        pincode = request.POST.get("pincode")

        # ---------------- SELLER DATA ----------------
        store_name = request.POST.get("store_name", "").strip()

        # ---------------- VALIDATION ----------------
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("register")

        if role not in ["buyer", "seller"]:
            messages.error(request, "Invalid role selected")
            return redirect("register")

        # ---------------- CREATE USER ----------------
        user = CustomUser.objects.create(
            username=email,
            email=email,
            first_name=full_name,
            contact=contact,
            password=make_password(password)
        )

        # ---------------- ROLE FLAGS ----------------
        if role == "buyer":
            user.is_buyer = True
        else:
            user.is_seller = True

        user.save()

        # ---------------- CREATE ADDRESS ----------------
        address = Address.objects.create(
            building=building,
            taluka=taluka,
            city=city,
            state=state,
            pincode=pincode
        )

        # ---------------- CREATE PROFILE ----------------
        if role == "buyer":
            BuyerProfile.objects.create(
                user=user,
                address=address
            )

        elif role == "seller":

            # 🔥 DEFAULT STORE NAME FOR INDIVIDUAL SELLERS
            if not store_name:
                store_name = f"{full_name} Wardrobe"

            SellerProfile.objects.create(
                user=user,
                store_name=store_name,
                pickup_address=address
            )

        # ---------------- SEND EMAIL ----------------
        send_mail(
            subject="Welcome to Rentify 🎉",
            message=f"""
Hello {full_name},

Welcome to Rentify!

Your account has been successfully created as a {role.capitalize()}.

You can now login and start using Rentify.

– Team Rentify
            """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )

        messages.success(request, "Registration successful. Please login.")
        return redirect("login")

    return render(request, "register.html")



def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out")
    return redirect("home")


from datetime import date, datetime
from .models import Address

@login_required
def buyer_dashboard(request):

    if not request.user.is_buyer:
        messages.error(request, "Access denied.")
        return redirect("home")

    buyer_profile, _ = BuyerProfile.objects.get_or_create(
        user=request.user
    )

    address = buyer_profile.address

    full_address = ""
    if address:
        full_address = (
            f"{address.building}, "
            f"{address.taluka}, "
            f"{address.city}, "
            f"{address.state}, "
            f"{address.pincode}"
        )

    requests = (
        RentRequest.objects
        .filter(buyer=request.user)
        .select_related("cloth")
        .order_by("-created_at")
    )

    user_form = BuyerUserForm(instance=request.user)

    if request.method == "POST":

        user_form = BuyerUserForm(
            request.POST,
            instance=request.user
        )

        # 🔹 GET ADDRESS DATA
        building = request.POST.get("building", "").strip()
        taluka = request.POST.get("taluka", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        pincode = request.POST.get("pincode", "").strip()

        if user_form.is_valid():

            user_form.save()

            # 🔐 ONLY SAVE ADDRESS IF AT LEAST ONE FIELD FILLED
            if any([building, taluka, city, state, pincode]):

                if buyer_profile.address:
                    addr = buyer_profile.address
                else:
                    addr = Address()

                addr.building = building
                addr.taluka = taluka
                addr.city = city
                addr.state = state
                addr.pincode = pincode
                addr.save()

                buyer_profile.address = addr
                buyer_profile.save()

            messages.success(request, "Profile updated successfully.")
            return redirect("buyer_dashboard")

        messages.error(request, "Please correct the errors.")

    return render(request, "buyer_dashboard.html", {
        "requests": requests,
        "user_form": user_form,
        "buyer_profile": buyer_profile,
        "address": buyer_profile.address,
        "full_address": full_address,
        "today": date.today().isoformat()
    })


@login_required
def edit_rent_request(request, pk):

    rent = get_object_or_404(
        RentRequest,
        pk=pk,
        buyer=request.user,
        status="pending"
    )

    cloth = rent.cloth

    if request.method == "POST":

        quantity = int(request.POST.get("quantity", 0))
        start_date = date.fromisoformat(request.POST.get("start_date"))
        end_date = date.fromisoformat(request.POST.get("end_date"))

        if quantity <= 0 or quantity > cloth.quantity:
            messages.error(request, "Quantity not available.")
            return redirect("buyer_dashboard")

        if end_date < start_date:
            messages.error(request, "Invalid date range.")
            return redirect("buyer_dashboard")

        total_days = (end_date - start_date).days + 1
        total_price = total_days * quantity * cloth.rent_per_day

        rent.quantity = quantity
        rent.start_date = start_date
        rent.end_date = end_date
        rent.total_days = total_days
        rent.total_price = total_price
        rent.save()

        messages.success(request, "Rental request updated successfully.")
        return redirect("buyer_dashboard")




@login_required
def delete_rent_request(request, pk):

    rent = get_object_or_404(
        RentRequest,
        pk=pk,
        status__in=["cancelled", "rejected"]
    )

    if request.user not in [rent.buyer, rent.seller]:
        messages.error(request, "Unauthorized")
        return redirect("home")

    if request.method == "POST":
        rent.delete()
        messages.success(request, "Rental request deleted.")

    return redirect(request.META.get("HTTP_REFERER", "home"))



@login_required
def cancel_rent_request(request, pk):

    rent = get_object_or_404(
        RentRequest,
        pk=pk,
        buyer=request.user
    )

    if rent.status not in ["pending", "approved"]:
        messages.error(request, "Cannot cancel this request.")
        return redirect("buyer_dashboard")

    cloth = rent.cloth

    # 🔁 RESTOCK ONLY IF ALREADY APPROVED
    if rent.status == "approved":
        cloth.quantity += rent.quantity
        cloth.save()

    rent.status = "cancelled"
    rent.save()

    messages.success(request, "Rental request cancelled.")
    return redirect("buyer_dashboard")





@login_required
def seller_dashboard(request):

    if not request.user.is_seller:
        messages.error(request, "Access denied.")
        return redirect("home")

    profile = (
        SellerProfile.objects
        .select_related("pickup_address")
        .filter(user=request.user)
        .first()
    )

    address = profile.pickup_address if profile else None

    # ---------- HANDLE PROFILE UPDATE ----------
    if request.method == "POST" and request.POST.get("action") == "update_profile":

        profile_form = SellerProfileForm(
            request.POST,
            instance=profile
        )

        address_form = AddressForm(
            request.POST,
            instance=address
        )

        if profile_form.is_valid() and address_form.is_valid():

            addr = address_form.save()
            prof = profile_form.save(commit=False)
            prof.pickup_address = addr
            prof.save()

            messages.success(request, "Profile updated successfully.")
            return redirect("seller_dashboard")

        messages.error(request, "Please correct the errors below.")

    else:
        profile_form = SellerProfileForm(instance=profile)
        address_form = AddressForm(instance=address)

    # ---------- MAP ----------
    full_address = ""
    if address:
        full_address = (
            f"{address.building}, "
            f"{address.taluka}, "
            f"{address.city}, "
            f"{address.state}, "
            f"{address.pincode}"
        )

    # ---------- RENT REQUESTS ----------
    requests = (
        RentRequest.objects
        .filter(seller=request.user)
        .select_related("buyer", "cloth")
        .order_by("-created_at")
    )

    return render(request, "seller_dashboard.html", {
        "requests": requests,
        "profile": profile,
        "address": address,
        "full_address": full_address,
        "profile_form": profile_form,
        "address_form": address_form,
    })




@login_required
def accept_rent_request(request, pk):

    rent = get_object_or_404(
        RentRequest,
        pk=pk,
        seller=request.user,
        status="pending"
    )

    cloth = rent.cloth

    # 🔐 Safety check
    if rent.quantity > cloth.quantity:
        messages.error(request, "Insufficient stock.")
        return redirect("seller_dashboard")

    # ✅ REDUCE STOCK HERE
    cloth.quantity -= rent.quantity
    cloth.save()

    rent.status = "approved"
    rent.save()
    send_mail(
    subject="Your Rent Request is Approved ✅",
    message=f"""
Hello {rent.buyer.first_name},

Good news! Your rental request has been approved.

Item: {cloth.name}
Quantity: {rent.quantity}
Rental Period: {rent.start_date} to {rent.end_date}
Total Amount: ₹{rent.total_price}

Please proceed with payment.

– Team Rentify
""",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[rent.buyer.email],
    fail_silently=False
)


    messages.success(request, "Request accepted & stock updated.")
    return redirect("seller_dashboard")



@login_required
def reject_rent_request(request, pk):

    rent = get_object_or_404(
        RentRequest,
        pk=pk,
        seller=request.user,
        status="pending"
    )

    rent.status = "rejected"
    rent.save()
    send_mail(
    subject="Rent Request Rejected ❌",
    message=f"""
Hello {rent.buyer.first_name},

Unfortunately, your rental request has been rejected.

Item: {rent.cloth.name}

You can browse other available clothes on Rentify.

– Team Rentify
""",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[rent.buyer.email],
    fail_silently=False
)

    messages.success(request, "Request rejected.")
    return redirect("seller_dashboard")



@login_required
def mark_payment_paid(request, pk):

    rent = get_object_or_404(
        RentRequest,
        pk=pk,
        seller=request.user,
        status="approved"
    )

    rent.payment_status = "paid"
    rent.save()

    # ================= PDF RECEIPT =================
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>RENTIFY – PAYMENT RECEIPT</b>", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f"<b>Order ID:</b> RENT{rent.id}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Payment Status:</b> PAID", styles["Normal"]))
    elements.append(Spacer(1, 12))

    data = [
        ["Item Name", rent.cloth.name],
        ["Seller", rent.seller.first_name],
        ["Buyer", rent.buyer.first_name],
        ["Quantity", str(rent.quantity)],
        ["Rental Period", f"{rent.start_date} to {rent.end_date}"],
        ["Total Days", str(rent.total_days)],
        ["Amount Paid", f"₹{rent.total_price}"],
    ]

    table = Table(data, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            "Thank you for choosing Rentify. This receipt confirms successful payment.",
            styles["Italic"]
        )
    )

    doc.build(elements)
    buffer.seek(0)

    # ================= EMAIL WITH PDF =================
    email = EmailMessage(
        subject="Payment Confirmation Receipt 🧾",
        body=f"""
Hello {rent.buyer.first_name},

Your payment has been successfully received.

Please find the attached PDF receipt for your records.

Thank you for choosing Rentify.

– Team Rentify
""",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[rent.buyer.email],
    )

    email.attach(
        f"Rentify_Receipt_RENT{rent.id}.pdf",
        buffer.read(),
        "application/pdf"
    )

    email.send(fail_silently=False)

    messages.success(request, "Payment marked as received and receipt emailed.")
    return redirect("seller_dashboard")



@login_required
def complete_rental(request, pk):

    rent = get_object_or_404(
        RentRequest,
        pk=pk,
        seller=request.user,
        status="approved",
        payment_status="paid"
    )

    cloth = rent.cloth

    # 🔁 RESTOCK AFTER RETURN
    cloth.quantity += rent.quantity
    cloth.save()

    rent.status = "completed"
    rent.save()
    send_mail(
    subject="Rental Completed Successfully 🎉",
    message=f"""
Hello {rent.buyer.first_name},

Your rental has been completed successfully.

Item: {rent.cloth.name}
Thank you for returning the item.

We hope to see you again on Rentify!

– Team Rentify
""",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[rent.buyer.email],
    fail_silently=False
)


    messages.success(request, "Rental completed & stock restored.")
    return redirect("seller_dashboard")





from app1.models import RentRequest

def rent_clothes(request):
    if request.user.is_authenticated and not request.user.is_buyer:
        messages.error(request, "Only buyers can rent clothes")
        return redirect("home")

    selected_category = request.GET.get("category", "all")
    pincode = request.GET.get("pincode")

    clothes = (
        Cloth.objects
        .filter(quantity__gt=0)
        .prefetch_related("categories", "seller")
        .order_by("-created_at")
    )

    if selected_category != "all":
        clothes = clothes.filter(categories__id=selected_category).distinct()

    if pincode:
        clothes = clothes.filter(
            seller__seller_profile__pickup_address__pincode=pincode
        )

    # ✅ buyer active requests
    requested_cloth_ids = []
    if request.user.is_authenticated and request.user.is_buyer:
        requested_cloth_ids = list(
            RentRequest.objects.filter(
                buyer=request.user,
                status__in=["pending", "approved"]
            ).values_list("cloth_id", flat=True)
        )

    categories = Category.objects.filter(is_active=True)

    return render(request, "rent_clothes.html", {
        "clothes": clothes,
        "categories": categories,
        "selected_category": selected_category,
        "requested_cloth_ids": requested_cloth_ids,
    })







def list_clothes(request):
    if not request.user.is_authenticated:
        return render(request, "list_clothes.html")
    # 🚫 Buyer restriction
    if not request.user.is_seller:
        messages.error(request, "Only sellers can list clothes.")
        return redirect("home")

    # 🔎 CATEGORY FILTER
    selected_category = request.GET.get("category", "all")

    clothes = (
        Cloth.objects
        .filter(seller=request.user)
        .prefetch_related("categories")
        .order_by("-created_at")
    )

    if selected_category != "all":
        clothes = clothes.filter(
            categories__id=selected_category
        ).distinct()

    # 🟢 HANDLE POST (ADD CLOTH)
    if request.method == "POST":
        form = ClothForm(request.POST, request.FILES)

        if form.is_valid():
            cloth = form.save(commit=False)
            cloth.seller = request.user
            cloth.save()
            form.save_m2m()  # 🔑 REQUIRED

            messages.success(
                request, "Cloth listed successfully!"
            )
            return redirect("list_clothes")

        messages.error(
            request, "Please correct the errors below."
        )

    else:
        form = ClothForm()

    categories = Category.objects.filter(is_active=True)

    return render(request, "list_clothes.html", {
        "form": form,
        "clothes": clothes,
        "categories": categories,
        "selected_category": selected_category,
    })




@login_required(login_url="login")
def edit_cloth(request, cloth_id):

    cloth = get_object_or_404(
        Cloth,
        id=cloth_id,
        seller=request.user
    )

    if request.method == "POST":

        quantity = int(request.POST.get("quantity", 0))
        rent = float(request.POST.get("rent_per_day", 0))

        # ❌ Validation
        if quantity < 0:
            messages.error(
                request, "Quantity cannot be negative."
            )
            return redirect("list_clothes")

        if rent <= 0:
            messages.error(
                request, "Rent per day must be greater than 0."
            )
            return redirect("list_clothes")

        # ✅ Update fields
        cloth.name = request.POST.get("name")
        cloth.quantity = quantity          # 🔑 ONLY THIS
        cloth.rent_per_day = rent
        cloth.condition = request.POST.get("condition")
        cloth.description = request.POST.get("description")

        if request.FILES.get("image"):
            cloth.image = request.FILES["image"]

        cloth.save()

        # 🔁 Update categories (ManyToMany)
        category_ids = request.POST.getlist("categories")
        cloth.categories.set(category_ids)

        messages.success(
            request, "Cloth updated successfully!"
        )

    return redirect("list_clothes")






@login_required(login_url="login")
def delete_cloth(request, cloth_id):
    cloth = get_object_or_404(
        Cloth,
        id=cloth_id,
        seller=request.user  # 🔐 security
    )

    if request.method == "POST":
        cloth.delete()
        messages.success(request, "Cloth deleted successfully.")

    return redirect("list_clothes")



@login_required(login_url="login")
def cloth_detail(request, cloth_id):
    cloth = get_object_or_404(Cloth, id=cloth_id)

    already_requested = RentRequest.objects.filter(
        buyer=request.user,
        cloth=cloth,
        status__in=["pending", "approved"]
    ).exists()

    return render(request, "cloth_detail.html", {
        "cloth": cloth,
        "already_requested": already_requested,
    })



from django.utils import timezone
from django.utils.timezone import now, make_aware
@login_required(login_url="login")
def request_cloth(request, cloth_id):

    if not request.user.is_buyer:
        messages.error(request, "Only buyers can rent clothes.")
        return redirect("home")

    cloth = get_object_or_404(Cloth, id=cloth_id)

    # ================= SELLER LOCATION (FOR MAP) =================
    seller_profile = None
    address = None
    full_address = ""

    if hasattr(cloth.seller, "seller_profile"):
        seller_profile = cloth.seller.seller_profile
        address = seller_profile.pickup_address

        if address:
            full_address = (
                f"{address.building}, "
                f"{address.taluka}, "
                f"{address.city}, "
                f"{address.state}, "
                f"{address.pincode}"
            )

    # ================= POST LOGIC =================
    if request.method == "POST":

        quantity = int(request.POST.get("quantity", 0))
        start_date_raw = request.POST.get("start_date")
        end_date_raw = request.POST.get("end_date")
        pickup_raw = request.POST.get("buyer_requested_pickup_date")
        note = request.POST.get("buyer_note", "")

        # ---------- BASIC VALIDATIONS ----------
        if quantity <= 0:
            messages.error(request, "Quantity must be greater than 0.")
            return redirect("request_cloth", cloth_id=cloth.id)

        if quantity > cloth.quantity:
            messages.error(request, "Requested quantity not available.")
            return redirect("request_cloth", cloth_id=cloth.id)

        # ---------- DATE VALIDATION ----------
        try:
            start_date = date.fromisoformat(start_date_raw)
            end_date = date.fromisoformat(end_date_raw)
        except:
            messages.error(request, "Invalid dates.")
            return redirect("request_cloth", cloth_id=cloth.id)

        today = date.today()
        if start_date < today:
            messages.error(request, "Start date cannot be in the past.")
            return redirect("request_cloth", cloth_id=cloth.id)

        if end_date < start_date:
            messages.error(request, "End date cannot be before start date.")
            return redirect("request_cloth", cloth_id=cloth.id)

        # ---------- PICKUP TIME VALIDATION ----------
        pickup_datetime = None
        if pickup_raw:
            pickup_datetime = make_aware(datetime.fromisoformat(pickup_raw))
            if pickup_datetime < now():
                messages.error(request, "Pickup time cannot be in the past.")
                return redirect("request_cloth", cloth_id=cloth.id)

        # ---------- CALCULATIONS ----------
        total_days = (end_date - start_date).days + 1
        total_price = total_days * quantity * cloth.rent_per_day

        # ---------- SAVE REQUEST (NO STOCK CHANGE) ----------
        RentRequest.objects.create(
            buyer=request.user,
            seller=cloth.seller,
            cloth=cloth,
            quantity=quantity,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            total_price=total_price,
            buyer_requested_pickup_date=pickup_datetime,
            buyer_note=note,
            status="pending"
        )
        send_mail(
    subject="New Rental Request Received 🧥",
    message=f"""
Hello {cloth.seller.first_name},

You have received a new rental request.

Item: {cloth.name}
Quantity: {quantity}
Rental Period: {start_date} to {end_date}
Total Amount: ₹{total_price}

Please login to your seller dashboard to take action.

– Team Rentify
""",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[cloth.seller.email],
    fail_silently=False
)
        messages.success(
            request,
            "Rent request sent successfully. Waiting for seller approval."
        )

        return redirect("buyer_dashboard")

    # ================= GET RENDER =================
    return render(request, "request_cloth.html", {
        "cloth": cloth,
        "seller_profile": seller_profile,
        "address": address,
        "full_address": full_address,
        "today": date.today().isoformat(),
    })


import random
def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")
        if CustomUser.objects.filter(email=email).exists():
            otp = random.randint(100000, 999999)
            request.session["reset_email"] = email
            request.session["reset_otp"] = str(otp)

            send_mail(
                "Your Rentify OTP",
                f"Your OTP for password reset is: {otp}",
                "noreply@rentify.com",
                [email],
            )
            return redirect("verify_otp")
        else:
            messages.error(request, "Email not registered")
    return render(request, "forgot_password.html")


def verify_otp(request):
    if request.method == "POST":
        user_otp = request.POST.get("otp")
        if user_otp == request.session.get("reset_otp"):
            return redirect("reset_password")
        else:
            messages.error(request, "Invalid OTP")
    return render(request, "verify_otp.html")


def reset_password(request):
    if request.method == "POST":
        p1 = request.POST.get("password")
        p2 = request.POST.get("confirm")

        if p1 != p2:
            messages.error(request, "Passwords do not match")
        else:
            email = request.session.get("reset_email")
            user = CustomUser.objects.get(email=email)
            user.set_password(p1)
            user.save()
            del request.session["reset_email"]
            del request.session["reset_otp"]
            messages.success(request, "Password reset successful")
            return redirect("login")

    return render(request, "reset_password.html")