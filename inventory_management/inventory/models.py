from django.db import models
from django.contrib.auth.models import User
from django.db.models import F
from datetime import datetime, timedelta

class InventoryItem(models.Model):
    name = models.CharField(max_length=200)
    quantity = models.IntegerField(default=0)
    lower_threshold = models.IntegerField(default=0,blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank=True, null=True, default=1)
    date_created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=4,blank=True, null=True)
    image = models.ImageField(upload_to='inventory_images/', blank=True, null=True)     
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sku = models.CharField(max_length=255,default="",blank=True, null=True)
    barcodes = models.CharField(max_length=255, default="",blank=True, null=True)  # Assuming comma-separated values or a JSON string
    description = models.TextField(default="",blank=True, null=True)
    unit = models.IntegerField(default=1,blank=True, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0,blank=True, null=True)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=22,blank=True, null=True)
    location = models.CharField(max_length=255,default="",blank=True, null=True)

    def __str__(self):
        return self.name

    def barcode_list(self):
        # This method can be used to parse the comma-separated barcodes or handle JSON parsing
        return self.barcodes.split(',') if self.barcodes else []

class Category(models.Model):
    name = models.CharField(max_length=200)
    class Meta:
        verbose_name_plural = 'categories'
    def __str__(self):
        return self.name

class ClientGroup(models.Model):
    name = models.CharField(max_length=200)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0,blank=True, null=True)
    def __str__(self):
        return self.name

class Client(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    group = models.ForeignKey("ClientGroup", on_delete=models.CASCADE, null=True, blank=True,default=1)
    company_name = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=15,null=True, blank=True)  # Adjust the max length as needed
    address = models.TextField()
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=100, default="IT",blank=True, null=True )
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    tax_number = models.CharField(max_length=20, blank=True, null=True)
    salesman = models.ForeignKey("Salesman", on_delete=models.CASCADE, null=True, blank=True, default=1)
    note = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.company_name

class Salesman(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    payroll = models.DecimalField(max_digits=10, decimal_places=2, default=0,blank=True, null=True)
    def __str__(self):
        return self.name

class Order(models.Model):
    order_number = models.CharField(max_length=100, unique=True)
    client = models.ForeignKey("Client", on_delete=models.CASCADE)
    items = models.ManyToManyField("InventoryItem", through="OrderItem")
    total_price = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    status = models.ForeignKey("OrderStatus", on_delete=models.CASCADE, null=True, blank=True, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    shipping_address = models.TextField()
    billing_address = models.TextField(default="")
    payment_method = models.CharField(max_length=100, default="Cash")
    
    def __str__(self):
        return self.order_number

    def update_price(self):
        self.total_price = sum(item.price for item in self.orderitem_set.all())  

    def save(self, *args, **kwargs):
        self.update_price()
        print('Total price before Save: ',self.total_price)
        if self.pk:
            original_status = None if self.pk is None else Order.objects.get(pk=self.pk).status
            super().save(*args, **kwargs)
            print('orignal status:',original_status.id, original_status)
            print('Status:',self.status.id, self.status)
            # Status 2 means the order is confirmed
            if self.status.id == 2 and original_status.id == 1:   
                print('Order confirmed!')        
                # Update the inventory
                for item in self.orderitem_set.all():
                    print('Updating inventory...')
                    inventory_item = item.product
                    inventory_item.quantity -= item.amount
                    inventory_item.save(update_fields=['quantity'])
                '''
                # Check if the invoice alreay exist?
                if Invoice.objects.filter(invoice_number=self.order_number).exists():
                    pass
                else:
                    # Create an Invoice instance
                    print('Creating invoice...')
                    print(self.total_price)
                    invoice = Invoice(
                        invoice_number=self.order_number,  # Implement this method to generate invoice number
                        issue_date=self.created_at,  # Use the order's creation date as the issue date
                        due_date=self.created_at + timedelta(days=30),  # Set a due date (e.g., 30 days from creation)
                        billing_address=self.billing_address,  # Use the client's address as the billing address
                        #payment_status=PaymentStatus.,  # Set an initial payment status
                        total_price=self.total_price,  # Implement this method to calculate the total amount
                        order=self  # Associate the order with the invoice
                    )
                    invoice.save()
                '''  
        else:
            super().save(*args, **kwargs)
    def mark_as_checked(self):
        checked_status = OrderStatus.objects.get(pk=2)  
        self.status = checked_status
        self.save()

class OrderItem(models.Model):
    order = models.ForeignKey("Order", on_delete=models.CASCADE)
    product = models.ForeignKey("InventoryItem", on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()  # Amount of the product in the order
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0)  # Price of the product at the time of the order

    def __str__(self):
        return f"{self.amount} x {self.product.name} in order {self.order.order_number}"

    def save(self, *args, **kwargs):
        if self.amount == 0:
            self.delete()
        else:
            self.price = self.product.price * self.amount
            super().save(*args, **kwargs)
            
    def combine_with_existing(self):
        # Check if an OrderItem with the same product already exists for this order
        existing_order_item = OrderItem.objects.filter(order=self.order, product=self.product).exclude(id=self.id).first()
        if existing_order_item:
            # Update the amount and price of the existing OrderItem
            existing_order_item.amount += self.amount
            existing_order_item.price = self.price
            existing_order_item.save(update_fields=['amount', 'price'])
            # Optionally delete the current OrderItem
            self.delete()

class OrderStatus(models.Model):
    name = models.CharField(max_length=50, default="Pending")
    def __str__(self):
        return self.name

class Invoice(models.Model):
    invoice_number = models.CharField(max_length=50)
    issue_date = models.DateField()
    due_date = models.DateField()
    billing_address = models.TextField()
    payment_status = models.ForeignKey("PaymentStatus", on_delete=models.CASCADE, null=True, blank=True, default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    def __str__(self):
        return self.invoice_number

class PaymentStatus(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name
    

class Provider(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15,null=True, blank=True)  # Adjust the max length as needed
    address = models.TextField()
    note = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name
    

class PurchaseOrder(models.Model):
    purchase_number = models.CharField(max_length=100, unique=True)
    provider = models.ForeignKey("Provider", on_delete=models.CASCADE)
    purchase_date = models.DateField(auto_created=True, auto_now_add=True)
    items = models.ManyToManyField("InventoryItem", through="PurchaseItem")
    status = models.ForeignKey("PurchaseStatus", on_delete=models.CASCADE, null=True, blank=True, default=1)
    payment_method = models.CharField(max_length=100, default='Cash')
    notes = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='purchase_orders/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    def __str__(self):
        return self.purchase_number

    def save(self, *args, **kwargs):
        if self.pk:
            original_status = None if self.pk is None else PurchaseOrder.objects.get(pk=self.pk).status
            super().save(*args, **kwargs)
            print('orignal status:',original_status.id, original_status)
            print('Status:',self.status.id, self.status)
            # Status 2 means the order is confirmed
            if self.status.id == 2 and original_status.id == 1:   
                print('PurchaseOrder confirmed!')        
                # Update the inventory
                for item in self.purchaseitem_set.all():
                    print('Updating inventory...',item.product.name)
                    inventory_item = item.product
                    inventory_item.quantity += item.amount
                    inventory_item.save(update_fields=['quantity'])

    #def update_price(self):
    #    self.price = sum(item.price for item in self.orderitem_set.all())
    #    self.save()

class PurchaseItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE)
    product = models.ForeignKey('InventoryItem', on_delete=models.CASCADE)
    amount = models.IntegerField(null=True, blank=True, default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.purchase_order
    def combine_with_existing(self):
        # Check if an OrderItem with the same product already exists for this order
        existing_order_item = PurchaseItem.objects.filter(purchase_order=self.purchase_order, product=self.product).exclude(id=self.id).first()
        if existing_order_item:
            # Update the amount and price of the existing OrderItem
            existing_order_item.amount += self.amount
            existing_order_item.price = self.price
            existing_order_item.save(update_fields=['amount', 'price'])
            # Optionally delete the current OrderItem
            self.delete()
    
    #def save(self, *args, **kwargs):
    #    self.price = self.product.price * self.quantity
    #    super(OrderItem, self).save(*args, **kwargs)

class PurchaseStatus(models.Model):
    name = models.CharField(max_length=50, default="Pending")
    def __str__(self):
        return self.name