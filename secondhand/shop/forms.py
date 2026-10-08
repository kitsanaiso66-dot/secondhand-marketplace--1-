from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

from .models import Product, User

# คลาส Tailwind ที่ใช้กับช่องกรอกทุกช่อง (กำหนดที่เดียว ใช้ซ้ำทุกฟอร์ม)
INPUT_CLASS = (
    "w-full rounded-xl border border-stone-300 bg-white px-4 py-3 "
    "outline-none transition focus:border-moss focus:ring-2 focus:ring-moss/30"
)
FILE_CLASS = (
    "block w-full text-sm text-stone-600 file:mr-4 file:rounded-lg file:border-0 "
    "file:bg-moss file:px-4 file:py-2.5 file:font-medium file:text-white "
    "hover:file:bg-moss-dark"
)
# Radio / Checkbox ต้องเป็นกล่องเล็ก ๆ ไม่ใช่ w-full
CHOICE_CLASS = "h-5 w-5 shrink-0 accent-moss"


class StyledFormMixin:
    """ใส่ class ของ Tailwind ให้ทุกฟิลด์อัตโนมัติ (เลือกคลาสตามชนิดของ widget)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.FileInput):  # รวม ClearableFileInput
                css = FILE_CLASS
            elif isinstance(widget, (forms.RadioSelect, forms.CheckboxInput)):
                css = CHOICE_CLASS
            else:
                css = INPUT_CLASS
            widget.attrs["class"] = css


class LoginForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "ชื่อผู้ใช้"
        self.fields["password"].label = "รหัสผ่าน"
        self.fields["username"].widget.attrs["autofocus"] = True


class RegisterForm(StyledFormMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "phone")
        labels = {"username": "ชื่อผู้ใช้", "email": "อีเมล", "phone": "เบอร์โทรศัพท์"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "รหัสผ่าน"
        self.fields["password2"].label = "ยืนยันรหัสผ่าน"
        self.fields["email"].required = True


class ResetRequestForm(StyledFormMixin, PasswordResetForm):
    """ฟอร์มขอรีเซ็ตรหัสผ่าน (กรอกอีเมล)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = "อีเมลที่ใช้สมัคร"


class ResetConfirmForm(StyledFormMixin, SetPasswordForm):
    """ฟอร์มตั้งรหัสผ่านใหม่ (หลังกดลิงก์ในอีเมล)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = "รหัสผ่านใหม่"
        self.fields["new_password2"].label = "ยืนยันรหัสผ่านใหม่"


class ProductForm(StyledFormMixin, forms.ModelForm):
    """ฟอร์มลงขาย/แก้ไขสินค้า — มี Textfield, Number, Dropdown, Radio, Checkbox, Textarea, File"""

    class Meta:
        model = Product
        fields = (
            "name",
            "category",
            "condition",
            "price",
            "negotiable",
            "description",
            "image",
        )
        widgets = {
            "category": forms.Select(),  # Dropdown
            "condition": forms.RadioSelect(),  # Radio
            "negotiable": forms.CheckboxInput(),  # Checkbox
            "description": forms.Textarea(attrs={"rows": 5}),
            "price": forms.NumberInput(attrs={"min": 1, "step": "1"}),
            # FileInput (ไม่ใช่ Clearable) เพื่อไม่ให้มีข้อความ "Currently:" รก ๆ ตอนแก้ไข
            "image": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price <= 0:
            raise forms.ValidationError("ราคาต้องมากกว่า 0 บาท")
        return price


class CheckoutForm(StyledFormMixin, forms.Form):
    address = forms.CharField(
        label="ที่อยู่จัดส่ง",
        widget=forms.Textarea(attrs={"rows": 3, "placeholder": "บ้านเลขที่ ถนน แขวง/ตำบล เขต/อำเภอ จังหวัด รหัสไปรษณีย์"}),
    )
