from django.contrib import admin
from .models import CustomUser, Address, BuyerProfile, RentRequest, SellerProfile, Cloth, Category


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'contact', 'is_buyer', 'is_seller', 'is_active')
    list_filter = ('is_buyer', 'is_seller', 'is_active')
    search_fields = ('username', 'email', 'contact')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('building', 'taluka', 'city', 'state', 'pincode')
    search_fields = ('building', 'city', 'state', 'pincode')


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'address', 'created_at')
    search_fields = ('user__username', 'user__email')


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'user', 'is_verified', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('store_name', 'user__username', 'user__email')


@admin.register(Cloth)
class ClothAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "seller",
        "display_categories",
        "quantity",
        "rent_per_day",
        "availability_status",
        "created_at",
    )

    list_filter = (
        "categories",
        "condition",
        "created_at",
    )

    search_fields = (
        "name",
        "seller__username",
    )

    filter_horizontal = ("categories",)  # ✅ Best UX for M2M

    ordering = ("-created_at",)

    # -------- CUSTOM ADMIN METHODS -------- #

    def display_categories(self, obj):
        return ", ".join(
            [cat.name for cat in obj.categories.all()]
        )

    display_categories.short_description = "Categories"

    def availability_status(self, obj):
        return obj.is_available

    availability_status.boolean = True
    availability_status.short_description = "Available"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(RentRequest)
class RentRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "cloth",
        "buyer",
        "seller",
        "quantity",
        "status",
        "created_at",
    )

    list_filter = ("status", "created_at")
    search_fields = (
        "cloth__name",
        "buyer__username",
        "seller__username",
    )