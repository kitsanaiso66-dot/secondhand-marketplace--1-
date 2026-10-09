from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    """ผู้ใช้งาน — ใช้ทั้งเป็นผู้ซื้อและผู้ขาย (คนเดียวทำได้ทั้งสองบทบาท)"""

    phone = models.CharField("เบอร์โทรศัพท์", max_length=20, blank=True)

    class Meta:
        verbose_name = "ผู้ใช้"
        verbose_name_plural = "ผู้ใช้"


class Product(models.Model):
    """สินค้ามือสองที่ผู้ใช้ลงขาย: User 1 คน ขายได้หลายชิ้น (1 : N)"""

    class Status(models.TextChoices):
        AVAILABLE = "available", "มีของ"
        SOLD = "sold", "ขายแล้ว"

    class Category(models.TextChoices):
        ELECTRONICS = "electronics", "เครื่องใช้ไฟฟ้า / อิเล็กทรอนิกส์"
        FASHION = "fashion", "เสื้อผ้า / แฟชั่น"
        FURNITURE = "furniture", "เฟอร์นิเจอร์ / ของใช้ในบ้าน"
        BOOKS = "books", "หนังสือ / การ์ตูน"
        SPORTS = "sports", "กีฬา / จักรยาน"
        OTHER = "other", "อื่น ๆ"

    class Condition(models.TextChoices):
        LIKE_NEW = "like_new", "เหมือนใหม่"
        GOOD = "good", "สภาพดี"
        FAIR = "fair", "พอใช้"
        WORN = "worn", "มีตำหนิ"

    seller = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="products", verbose_name="ผู้ขาย"
    )
    name = models.CharField("ชื่อสินค้า", max_length=120)
    category = models.CharField(
        "หมวดหมู่", max_length=20, choices=Category.choices, default=Category.OTHER
    )
    condition = models.CharField(
        "สภาพสินค้า", max_length=20, choices=Condition.choices, default=Condition.GOOD
    )
    negotiable = models.BooleanField("ต่อรองราคาได้", default=False)
    description = models.TextField("รายละเอียด")
    price = models.DecimalField("ราคา (บาท)", max_digits=10, decimal_places=2)
    image = models.ImageField("รูปสินค้า", upload_to="products/%Y/%m/")
    status = models.CharField(
        "สถานะ", max_length=10, choices=Status.choices, default=Status.AVAILABLE
    )
    created_at = models.DateTimeField("ลงขายเมื่อ", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "สินค้า"
        verbose_name_plural = "สินค้า"

    def __str__(self):
        return self.name

    @property
    def is_sold(self):
        return self.status == self.Status.SOLD

    def get_absolute_url(self):
        return reverse("product_detail", args=[self.pk])


class Order(models.Model):
    """คำสั่งซื้อ: User 1 คน สั่งได้หลายรายการ (1 : N) / สินค้า 1 ชิ้น ถูกสั่งได้ครั้งเดียว"""

    class Status(models.TextChoices):
        ORDERED = "ordered", "รอจัดส่ง"
        SHIPPED = "shipped", "จัดส่งแล้ว"
        COMPLETED = "completed", "สำเร็จ"

    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="orders", verbose_name="ผู้ซื้อ"
    )
    # PROTECT: ห้ามลบสินค้าที่มีคำสั่งซื้อแล้ว เพื่อรักษาประวัติ
    product = models.OneToOneField(
        Product, on_delete=models.PROTECT, related_name="order", verbose_name="สินค้า"
    )
    # เก็บราคา ณ วันที่ซื้อไว้ แม้ภายหลังแก้ราคาสินค้า ประวัติก็ไม่เปลี่ยน
    price = models.DecimalField("ราคาที่ซื้อ", max_digits=10, decimal_places=2)
    address = models.TextField("ที่อยู่จัดส่ง")
    status = models.CharField(
        "สถานะ", max_length=10, choices=Status.choices, default=Status.ORDERED
    )
    created_at = models.DateTimeField("สั่งซื้อเมื่อ", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "คำสั่งซื้อ"
        verbose_name_plural = "คำสั่งซื้อ"

    def __str__(self):
        return f"#{self.pk} {self.buyer} → {self.product}"
class Conversation(models.Model):
    """ห้องแชท: ผู้ซื้อ 1 คน คุยกับผู้ขายของสินค้า 1 ชิ้น ได้ 1 ห้อง"""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="conversations", verbose_name="สินค้า"
    )
    buyer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="conversations", verbose_name="ผู้ซื้อ"
    )
    created_at = models.DateTimeField("เริ่มคุยเมื่อ", auto_now_add=True)
    updated_at = models.DateTimeField("ข้อความล่าสุดเมื่อ", auto_now_add=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["product", "buyer"], name="unique_chat_per_buyer_product")
        ]
        verbose_name = "ห้องแชท"
        verbose_name_plural = "ห้องแชท"

    def __str__(self):
        return f"{self.buyer} ↔ {self.product.seller} ({self.product})"

    @property
    def seller(self):
        return self.product.seller

    def includes(self, user):
        return user.is_authenticated and user.id in (self.buyer_id, self.product.seller_id)

    def other_party(self, user):
        return self.product.seller if user.id == self.buyer_id else self.buyer


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages", verbose_name="ห้องแชท"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages", verbose_name="ผู้ส่ง"
    )
    body = models.TextField("ข้อความ", max_length=1000)
    created_at = models.DateTimeField("ส่งเมื่อ", auto_now_add=True)
    is_read = models.BooleanField("อ่านแล้ว", default=False)

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name = "ข้อความ"
        verbose_name_plural = "ข้อความ"

    def __str__(self):
        return f"{self.sender}: {self.body[:30]}"
