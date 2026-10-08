from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LoginForm, ResetConfirmForm, ResetRequestForm

urlpatterns = [
    path("", views.home, name="home"),
    path("product/<int:pk>/", views.product_detail, name="product_detail"),
    path("product/<int:pk>/buy/", views.buy_product, name="buy"),
    path("product/<int:pk>/edit/", views.edit_product, name="edit_product"),
    path("product/<int:pk>/delete/", views.delete_product, name="delete_product"),
    path("sell/", views.sell_product, name="sell"),
    path("profile/", views.profile, name="profile"),
    path("seller/<str:username>/", views.profile, name="seller_profile"),
    path("orders/", views.orders, name="orders"),
    path("orders/<int:pk>/advance/", views.advance_order, name="advance_order"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # ระบบยืนยันตัวตน
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html", authentication_form=LoginForm
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),  # ต้องส่งแบบ POST
    # รีเซ็ตรหัสผ่านทางอีเมล (ชื่อ route ต้องตรงกับที่ Django คาดไว้)
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.txt",
            subject_template_name="registration/password_reset_subject.txt",
            form_class=ResetRequestForm,
        ),
        name="password_reset",
    ),
    path(
        "password-reset/sent/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            form_class=ResetConfirmForm,
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
