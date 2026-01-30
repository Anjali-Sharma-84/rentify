from email.headerregistry import Address
from django import forms
from .models import BuyerProfile, Cloth, Category, CustomUser, RentRequest, SellerProfile,Address
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


class ClothForm(forms.ModelForm):

    # ✅ MULTI CATEGORY FIELD
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        error_messages={
            "required": "Please select at least one category."
        }
    )

    condition = forms.ChoiceField(
        choices=[("", "Select condition")] + Cloth.CONDITION_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    class Meta:
        model = Cloth
        fields = [
            "categories",
            "name",
            "image",
            "quantity",
            "rent_per_day",
            "condition",
            "description",
        ]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter cloth name"
            }),
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control"
            }),
            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter quantity"
            }),
            "rent_per_day": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter rent per day"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Describe the cloth (optional)"
            }),
        }

    # ---------------- FIELD VALIDATIONS ---------------- #

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if not name or len(name) < 3:
            raise ValidationError(
                "Cloth name must be at least 3 characters long."
            )
        return name

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity is None or quantity <= 0:
            raise ValidationError(
                "Quantity must be greater than 0."
            )
        return quantity

    def clean_rent_per_day(self):
        rent = self.cleaned_data.get("rent_per_day")
        if rent is None or rent <= 0:
            raise ValidationError(
                "Rent per day must be greater than 0."
            )
        return rent

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if not image:
            raise ValidationError("Cloth image is required.")

        # Validate size only for new uploads
        if isinstance(image, UploadedFile):
            max_size = 2 * 1024 * 1024  # 2 MB
            if image.size > max_size:
                raise ValidationError(
                    "Image size must be less than 2 MB."
                )

        return image

    def clean_description(self):
        desc = self.cleaned_data.get("description")
        if desc and len(desc) > 500:
            raise ValidationError(
                "Description cannot exceed 500 characters."
            )
        return desc




class RentRequestForm(forms.ModelForm):

    class Meta:
        model = RentRequest
        fields = [
            "quantity",
            "start_date",
            "end_date",
            "buyer_requested_pickup_date",
            "buyer_note",
        ]

        widgets = {
            "quantity": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
                "id": "quantityInput"
            }),
            "start_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
                "id": "startDate"
            }),
            "end_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
                "id": "endDate"
            }),
            "buyer_requested_pickup_date": forms.DateTimeInput(attrs={
                "type": "datetime-local",
                "class": "form-control"
            }),
            "buyer_note": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional note for seller"
            }),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")

        if start and end and start >= end:
            raise ValidationError("End date must be after start date.")

        return cleaned


class BuyerProfileForm(forms.ModelForm):
    class Meta:
        model = BuyerProfile
        fields = ["address"]

        widgets = {
            "address": forms.Select(attrs={
                "class": "form-select"
            })
        }


class BuyerUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "contact"]

        widgets = {
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "First name"
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Last name"
            }),
            "contact": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Contact number"
            }),
        }


class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = ["store_name"]


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ["building", "taluka", "city", "state", "pincode"]