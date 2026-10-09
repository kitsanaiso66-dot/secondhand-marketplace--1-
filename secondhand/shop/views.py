from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, OuterRef, ProtectedError, Q, Subquery, Sum
from django.db.models.functions import TruncMonth
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CheckoutForm, MessageForm, ProductForm, RegisterForm
from .models import Conversation, Message, Order, Product, User

THAI_MONTHS = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.",
               "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."]


def home(request):
    """หน้าหลัก: แกลเลอรีสินค้าที่ยังมีของ + ค้นหา + กรองหมวดหมู่ + แบ่งหน้า"""
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("category", "")
    products = Product.objects.filter(status=Product.Status.AVAILABLE).select_related("seller")
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if cat in Product.Category.values:
        products = products.filter(category=cat)
    else:
        cat = ""

    page = Paginator(products, 12).get_page(request.GET.get("page"))

    # query string เดิม (ไม่รวม page) ไว้ต่อท้ายลิงก์แบ่งหน้า
    params = request.GET.copy()
    params.pop("page", None)
    context = {
        "page": page,
        "q": q,
        "cat": cat,
        "categories": Product.Category.choices,
        "qs": params.urlencode(),
    }
    return render(request, "home.html", context)


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related("seller"), pk=pk)
    return render(request, "product_detail.html", {"product": product, "form": CheckoutForm()})


@login_required
@require_POST
def buy_product(request, pk):
    """สั่งซื้อสินค้า — ทำใน transaction เดียว กันคนสองคนซื้อชิ้นเดียวกันพร้อมกัน"""
    form = CheckoutForm(request.POST)
    if not form.is_valid():
        messages.error(request, "กรุณากรอกที่อยู่จัดส่ง")
        return redirect("product_detail", pk=pk)

    with transaction.atomic():
        # select_for_update ล็อกแถวสินค้าไว้จนกว่า transaction จะจบ
        product = get_object_or_404(Product.objects.select_for_update(), pk=pk)

        if product.seller_id == request.user.id:
            messages.error(request, "ไม่สามารถซื้อสินค้าของตัวเองได้")
            return redirect("product_detail", pk=pk)
        if product.is_sold:
            messages.error(request, "ขออภัย สินค้าชิ้นนี้ถูกซื้อไปแล้ว")
            return redirect("home")

        Order.objects.create(
            buyer=request.user,
            product=product,
            price=product.price,  # บันทึกราคา ณ ตอนซื้อ
            address=form.cleaned_data["address"],
        )
        product.status = Product.Status.SOLD
        product.save(update_fields=["status"])

    messages.success(request, f"สั่งซื้อ “{product.name}” เรียบร้อยแล้ว")
    return redirect("orders")


@login_required
def sell_product(request):
    """หน้าขายสินค้า (Create) — ต้องใส่ request.FILES เพื่อรับรูปที่อัปโหลด"""
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        product = form.save(commit=False)
        product.seller = request.user  # ผูกสินค้ากับผู้ใช้ที่ล็อกอินอยู่ ไม่รับจากฟอร์ม
        product.save()
        messages.success(request, "ลงขายสินค้าเรียบร้อยแล้ว")
        return redirect("product_detail", pk=product.pk)
    return render(request, "sell.html", {"form": form, "product": None})


@login_required
def edit_product(request, pk):
    """แก้ไขสินค้า (Update) — เฉพาะเจ้าของ และเฉพาะสินค้าที่ยังไม่ขาย"""
    # ใส่ seller=request.user ใน query: ถ้าไม่ใช่เจ้าของจะได้ 404 ทันที
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if product.is_sold:
        messages.error(request, "สินค้าที่ขายแล้วไม่สามารถแก้ไขได้")
        return redirect("product_detail", pk=pk)

    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "บันทึกการแก้ไขเรียบร้อยแล้ว")
        return redirect("product_detail", pk=product.pk)
    return render(request, "sell.html", {"form": form, "product": product})


@login_required
@require_POST
def delete_product(request, pk):
    """ลบสินค้า (Delete) — เฉพาะเจ้าของ ลบได้เมื่อยังไม่มีคำสั่งซื้อ"""
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    try:
        # Order.product เป็น PROTECT: ถ้ามีคำสั่งซื้ออยู่ Django จะ raise ProtectedError
        product.delete()
    except ProtectedError:
        messages.error(request, "ลบไม่ได้ เพราะสินค้านี้มีคำสั่งซื้อแล้ว")
        return redirect("product_detail", pk=pk)
    messages.success(request, f"ลบ “{product.name}” เรียบร้อยแล้ว")
    return redirect("profile")


def profile(request, username=None):
    """โปรไฟล์: ไม่ระบุ username = ดูของตัวเอง, ระบุ = ดูโปรไฟล์ผู้ขายคนอื่น"""
    if username is None:
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        owner = request.user
    else:
        owner = get_object_or_404(User, username=username)

    is_me = owner == request.user
    products = owner.products.all()
    context = {
        "owner": owner,
        "is_me": is_me,
        "products": products,
        "sold_count": products.filter(status=Product.Status.SOLD).count(),
    }
    return render(request, "profile.html", context)


@login_required
def orders(request):
    """ประวัติ: แท็บ 'ที่ฉันซื้อ' (ค่าเริ่มต้น) และ 'ที่ฉันขายได้'"""
    tab = request.GET.get("tab", "bought")
    if tab == "sold":
        items = Order.objects.filter(product__seller=request.user).select_related("product", "buyer")
    else:
        tab = "bought"
        items = Order.objects.filter(buyer=request.user).select_related("product", "product__seller")
    return render(request, "orders.html", {"orders": items, "tab": tab})


@login_required
@require_POST
def advance_order(request, pk):
    """อัปเดตสถานะคำสั่งซื้อ แยกตามบทบาท
    - ผู้ขาย: รอจัดส่ง → จัดส่งแล้ว
    - ผู้ซื้อ: จัดส่งแล้ว → สำเร็จ (ยืนยันว่าได้รับของ)
    """
    order = get_object_or_404(Order.objects.select_related("product"), pk=pk)
    tab = "sold" if request.POST.get("tab") == "sold" else "bought"

    is_seller = order.product.seller_id == request.user.id
    is_buyer = order.buyer_id == request.user.id

    if order.status == Order.Status.ORDERED and is_seller:
        order.status = Order.Status.SHIPPED
        messages.success(request, "อัปเดตเป็น “จัดส่งแล้ว” เรียบร้อย")
    elif order.status == Order.Status.SHIPPED and is_buyer:
        order.status = Order.Status.COMPLETED
        messages.success(request, "ขอบคุณ! ยืนยันได้รับสินค้าเรียบร้อยแล้ว")
    else:
        messages.error(request, "คุณไม่มีสิทธิ์เปลี่ยนสถานะรายการนี้")
        return redirect(f"{reverse('orders')}?tab={tab}")

    order.save(update_fields=["status"])
    return redirect(f"{reverse('orders')}?tab={tab}")


@login_required
def dashboard(request):
    """แดชบอร์ดผู้ขาย: สรุปตัวเลข + กราฟ Chart.js (ยอดขายรายเดือน / สินค้าตามหมวดหมู่)"""
    user = request.user
    mine = Product.objects.filter(seller=user)
    sales = Order.objects.filter(product__seller=user)

    stats = {
        "listed": mine.count(),
        "available": mine.filter(status=Product.Status.AVAILABLE).count(),
        "sold": mine.filter(status=Product.Status.SOLD).count(),
        "revenue": sales.aggregate(t=Sum("price"))["t"] or 0,
    }

    # ยอดขาย 6 เดือนล่าสุด (เติม 0 ให้เดือนที่ไม่มีการขาย)
    now = timezone.localtime()
    ym = []
    y, m = now.year, now.month
    for _ in range(6):
        ym.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    ym.reverse()

    rows = (
        sales.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum("price"), n=Count("id"))
    )
    by_month = {(r["month"].year, r["month"].month): r for r in rows}

    monthly = {
        "labels": [f"{THAI_MONTHS[m - 1]} {str(y + 543)[-2:]}" for y, m in ym],
        "revenue": [float(by_month[k]["total"]) if k in by_month else 0 for k in ym],
        "orders": [by_month[k]["n"] if k in by_month else 0 for k in ym],
    }

    names = dict(Product.Category.choices)
    cat_rows = mine.values("category").annotate(n=Count("id")).order_by("-n")
    categories = {
        "labels": [names.get(r["category"], r["category"]) for r in cat_rows],
        "counts": [r["n"] for r in cat_rows],
    }

    context = {
        "stats": stats,
        "monthly": monthly,
        "categories": categories,
    }
    return render(request, "dashboard.html", context)


def register(request):
    if request.user.is_authenticated:
        return redirect("home")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)  # สมัครเสร็จล็อกอินให้เลย
        messages.success(request, "ยินดีต้อนรับ! สมัครสมาชิกเรียบร้อยแล้ว")
        return redirect("home")
    return render(request, "registration/register.html", {"form": form})

def _get_my_conversation(request, pk):
    """เฉพาะผู้ซื้อหรือผู้ขายของห้องนั้นเท่านั้น คนอื่นได้ 404"""
    conv = get_object_or_404(
        Conversation.objects.select_related("product", "product__seller", "buyer"), pk=pk
    )
    if not conv.includes(request.user):
        raise Http404
    return conv


@login_required
@require_POST
def start_chat(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.seller_id == request.user.id:
        messages.error(request, "ไม่สามารถแชทกับตัวเองได้")
        return redirect("product_detail", pk=pk)
    conv, _ = Conversation.objects.get_or_create(product=product, buyer=request.user)
    return redirect("chat_room", pk=conv.pk)


@login_required
def chat_list(request):
    last = Message.objects.filter(conversation=OuterRef("pk")).order_by("-created_at", "-id")
    convs = (
        Conversation.objects.filter(Q(buyer=request.user) | Q(product__seller=request.user))
        .select_related("product", "product__seller", "buyer")
        .annotate(
            last_body=Subquery(last.values("body")[:1]),
            last_at=Subquery(last.values("created_at")[:1]),
            unread=Count(
                "messages",
                filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user),
            ),
        )
        .order_by("-updated_at")
    )
    rows = [{"conv": c, "other": c.other_party(request.user)} for c in convs]
    return render(request, "chat_list.html", {"rows": rows})

@login_required
def chat_room(request, pk):
    conv = _get_my_conversation(request, pk)

    form = MessageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        Message.objects.create(conversation=conv, sender=request.user, body=form.cleaned_data["body"])
        Conversation.objects.filter(pk=conv.pk).update(updated_at=timezone.now())
        return redirect("chat_room", pk=conv.pk)

    conv.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    context = {
        "conv": conv,
        "other": conv.other_party(request.user),
        "chat_messages": conv.messages.select_related("sender"),
        "form": form,
    }
    return render(request, "chat_room.html", context)


@login_required
def chat_messages(request, pk):
    """JSON สำหรับ polling ทุก 3 วินาที"""
    conv = _get_my_conversation(request, pk)
    try:
        after = int(request.GET.get("after", 0))
    except ValueError:
        after = 0
    new = list(conv.messages.filter(id__gt=after).select_related("sender"))
    conv.messages.filter(id__in=[m.id for m in new if m.sender_id != request.user.id]).update(is_read=True)
    return JsonResponse({
        "messages": [
            {
                "id": m.id,
                "body": m.body,
                "mine": m.sender_id == request.user.id,
                "time": timezone.localtime(m.created_at).strftime("%H:%M"),
            }
            for m in new
        ]
    })