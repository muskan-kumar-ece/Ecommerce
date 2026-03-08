from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


class Vendor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vendor_profile")
    business_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("10.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("business_name",)
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
        ]

    def _generate_unique_slug(self):
        base_slug = slugify(self.business_name) or "vendor"
        candidate = base_slug
        suffix = 1
        while Vendor.objects.exclude(pk=self.pk).filter(slug=candidate).exists():
            suffix += 1
            candidate = f"{base_slug}-{suffix}"
        return candidate

    def save(self, *args, **kwargs):
        should_refresh_slug = not self.slug
        if self.pk:
            previous_business_name = (
                Vendor.objects.filter(pk=self.pk).values_list("business_name", flat=True).first()
            )
            if previous_business_name and previous_business_name != self.business_name:
                should_refresh_slug = True
        if should_refresh_slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.business_name


class VendorProduct(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="vendor_products")
    product = models.OneToOneField("products.Product", on_delete=models.CASCADE, related_name="vendor_listing")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["vendor"]),
            models.Index(fields=["product"]),
            models.Index(fields=["vendor", "created_at"]),
        ]
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.vendor.business_name} - {self.product.name}"


class VendorOrder(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="vendor_orders")
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="vendor_orders")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    commission_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    earnings_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["vendor", "order"], name="unique_vendor_order"),
        ]
        indexes = [
            models.Index(fields=["vendor"]),
            models.Index(fields=["order"]),
            models.Index(fields=["vendor", "created_at"]),
        ]
        ordering = ("-created_at",)

    def __str__(self):
        return f"VendorOrder {self.id} - {self.vendor.business_name}"
