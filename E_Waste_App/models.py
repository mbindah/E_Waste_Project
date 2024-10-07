# models.py
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import User

class Administrator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"Administrator: {self.user.username}"

class Message(models.Model):
    sender_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='sender_messages', null=True, blank=True)
    sender_object_id = models.PositiveIntegerField(null=True, blank=True)
    sender = GenericForeignKey('sender_content_type', 'sender_object_id')

    recipient_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='recipient_messages', null=True, blank=True)
    recipient_object_id = models.PositiveIntegerField(null=True, blank=True)
    recipient = GenericForeignKey('recipient_content_type', 'recipient_object_id')

    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}: {self.content[:20]}"

class Vendor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=255)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    messages = GenericRelation(Message, content_type_field='sender_content_type', object_id_field='sender_object_id', related_query_name='vendor')

    def __str__(self):
        return f"Vendor: {self.company_name} ({self.user.email})"

class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    messages = GenericRelation(Message, content_type_field='sender_content_type', object_id_field='sender_object_id', related_query_name='client')

    def __str__(self):
        return f"Client: {self.user.username} ({self.user.email})"

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='Availble')

    def __str__(self):
        return self.name

class Purchase(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='Pending')
    purchase_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.client.user.username} purchased {self.product.name}"

class Rating(models.Model):
    vendor = models.ForeignKey('Vendor', on_delete=models.CASCADE)
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.PositiveIntegerField()  # Assuming a rating scale (e.g., 1 to 5)
    comment = models.TextField(blank=True, null=True)  # Optional comment
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for when the rating was created

    class Meta:
        unique_together = ('vendor', 'client')  # Ensure each client can only rate a vendor once

    def __str__(self):
        return f'Rating({self.score}) by {self.client.username} for {self.vendor.name}'
