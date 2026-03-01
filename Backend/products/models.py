import uuid

from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=150, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "categories"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["slug"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            while Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    class ConditionGrade(models.TextChoices):
        A = "A", "A"
        B = "B", "B"
        C = "C", "C"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products", db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    stock_quantity = models.IntegerField(default=0)
    is_refurbished = models.BooleanField(default=False)
    condition_grade = models.CharField(max_length=1, choices=ConditionGrade.choices, null=True, blank=True)
    battery_health_percent = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "is_active"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.sku})"


class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images", db_index=True)
    image_url = models.URLField(max_length=2048)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "product_images"
        ordering = ["-is_primary", "created_at"]
        indexes = [
            models.Index(fields=["product", "is_primary"]),
        ]

    def __str__(self):
        return f"{self.product.name} image"


class Inventory(models.Model):
    class ChangeType(models.TextChoices):
        PURCHASE = "PURCHASE", "Purchase"
        RESTOCK = "RESTOCK", "Restock"
        MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT", "Manual Adjustment"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="inventory_entries", db_index=True)
    change_type = models.CharField(max_length=30, choices=ChangeType.choices, db_index=True)
    quantity_changed = models.IntegerField()
    reference_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventory_transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "created_at"]),
        ]

    def __str__(self):
        return f"{self.product.sku} {self.change_type} ({self.quantity_changed})"
