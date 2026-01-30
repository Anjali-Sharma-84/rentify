from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

# Create your models here.
class Address(models.Model):
    building = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    taluka = models.CharField(max_length=100)
    pincode = models.CharField(
        max_length=6,
        validators=[
            RegexValidator(
                regex=r'^\d{6}$',
                message="Enter a valid 6-digit pincode"
            )
        ]
    )

    def __str__(self):
        return f"{self.building}, {self.taluka}, {self.city}, {self.state} - {self.pincode}"



class CustomUser(AbstractUser):
    is_buyer = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)

    contact = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message="Contact number must be 10 digits"
            )
        ]
    )

    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class BuyerProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='buyer_profile'
    )

    address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Buyer: {self.user.username}"



class SellerProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='seller_profile'
    )

    store_name = models.CharField(max_length=150)

    pickup_address = models.ForeignKey(
        Address,
        on_delete=models.SET_NULL,
        null=True
    )

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Seller: {self.store_name}"



class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Cloth(models.Model):

    CONDITION_CHOICES = [
        ("new", "New"),
        ("like_new", "Like New"),
        ("good", "Good"),
        ("fair", "Fair"),
    ]

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listed_clothes"
    )

    # ✅ MULTIPLE CATEGORIES
    categories = models.ManyToManyField(
        Category,
        related_name="clothes"
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    image = models.ImageField(
        upload_to="clothes/",
        default="clothes/default.png"
    )

    quantity = models.PositiveIntegerField(default=1)

    rent_per_day = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default="good"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    # ✅ COMPUTED AVAILABILITY (NO DB FIELD)
    @property
    def is_available(self):
        return self.quantity > 0

    def available_stock(self):
        return self.quantity if self.is_available else 0



class RentRequest(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
    ]

    PAYMENT_STATUS = [
        ("pending", "Pending"),
        ("paid", "Paid"),
    ]

    

    payment_mode = models.CharField(
        max_length=20,
        default="cash"
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS,
        default="pending"
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rent_requests"
    )

    cloth = models.ForeignKey(
        Cloth,
        on_delete=models.CASCADE,
        related_name="rent_requests"
    )

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_requests"
    )

    quantity = models.PositiveIntegerField()

    start_date = models.DateField()
    end_date = models.DateField()

    total_days = models.PositiveIntegerField()
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    # Pickup flow
    buyer_requested_pickup_date = models.DateTimeField(null=True, blank=True)
    seller_confirmed_pickup_date = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    seller_note = models.TextField(blank=True)
    buyer_note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer} → {self.cloth.name} ({self.status})"
