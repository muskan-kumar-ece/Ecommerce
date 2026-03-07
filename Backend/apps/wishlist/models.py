from django.db import models


class Wishlist(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['product']),
        ]
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user.email} - {self.product.name}'
