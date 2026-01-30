from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    # Auth
    path("login/", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.logout_view, name="logout"),

    # Buyer
    path("buyer/dashboard/", views.buyer_dashboard, name="buyer_dashboard"),
    path("buyer/request/<int:pk>/edit/", views.edit_rent_request, name="edit_rent_request"),
path("buyer/request/<int:pk>/cancel/", views.cancel_rent_request, name="cancel_rent_request"),
    path("buyer/rent/", views.rent_clothes, name="rent_clothes"),

    # Seller
    path("seller/dashboard/", views.seller_dashboard, name="seller_dashboard"),
    path("seller/list/", views.list_clothes, name="list_clothes"),

    path("cloth/edit/<int:cloth_id>/", views.edit_cloth, name="edit_cloth"),
    path("cloth/delete/<int:cloth_id>/", views.delete_cloth, name="delete_cloth"),

    
path("cloth/<int:cloth_id>/", views.cloth_detail, name="cloth_detail"),
path(
    "cloth/<int:cloth_id>/rent/",
    views.request_cloth,
    name="request_cloth"
),
path(
    "buyer/request/<int:pk>/delete/",
    views.delete_rent_request,
    name="delete_rent_request"
),
path("seller/request/<int:pk>/accept/", views.accept_rent_request, name="accept_rent"),
path("seller/request/<int:pk>/reject/", views.reject_rent_request, name="reject_rent"),
path("seller/request/<int:pk>/paid/", views.mark_payment_paid, name="mark_paid"),
path("seller/request/<int:pk>/complete/", views.complete_rental, name="complete_rental"),

    path("forgot-password/", views.forgot_password, name="forgot_password"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
    path("reset-password/", views.reset_password, name="reset_password"),
]
