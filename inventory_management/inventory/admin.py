from django.contrib import admin
from .models import InventoryItem, Category, Client, Order, OrderItem, OrderStatus, Invoice, Salesman, ClientGroup, PaymentStatus, PurchaseItem, PurchaseOrder 
from .models import Provider, PurchaseStatus
admin.site.register(InventoryItem)
admin.site.register(Category)
admin.site.register(Client)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderStatus)
admin.site.register(Invoice)
admin.site.register(Salesman)
admin.site.register(ClientGroup) 
admin.site.register(PaymentStatus)
admin.site.register(PurchaseItem)
admin.site.register(PurchaseOrder)
admin.site.register(Provider)
admin.site.register(PurchaseStatus)