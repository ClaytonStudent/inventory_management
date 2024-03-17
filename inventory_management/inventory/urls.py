from django.contrib import admin
from django.urls import path
from .views import Index, SignUpView, Dashboard, AddItem, EditItem, DeleteItem
from .views import OrderDashboard, AddOrder, EditOrder, DeleteOrder
from .views import OrderItemList, OrderItemAdd, OrderItemUpdate, OrderItemDelete
from .views import ClientDashboard, AddClient, EditClient, DeleteClient
from .views import InvoiceDashboard, AddInvoice, EditInvoice, DeleteInvoice
from .views import export_inventory_to_csv, UploadClientView, UploadInventoryView
from .views import PurchaseDashboard, AddPurchase, EditPurchase, DeletePurchase
from .views import PurchaseItemDashboard, PurchaseItemAdd, PurchaseItemUpdate, PurchaseItemDelete
from .views import create_purchase_order
from django.contrib.auth import views as auth_views
from .views import search_inventory_item, mark_order_as_checked, create_order

urlpatterns = [
    path('', Index.as_view(), name='index'),
    # Inventory URLs
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('add-item/', AddItem.as_view(), name='add-item'),
    path('edit-item/<int:pk>', EditItem.as_view(), name='edit-item'),
    path('delete-item/<int:pk>', DeleteItem.as_view(), name='delete-item'),
    # User URLs
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='inventory/logout.html'), name='logout'),
    # OrderItem URLs
    path('order-dashboard/<int:pk>', OrderItemList.as_view(), name='order-item-list'),
    path('order-dashboard/<int:pk>/add-item/', OrderItemAdd.as_view(), name='add-order-item'),
    path('order-dashboard/<int:pk>/edit-item/<int:order_item_id>', OrderItemUpdate.as_view(), name='edit-order-item'),
    path('order-dashboard/<int:pk>/delete-item/<int:order_item_id>', OrderItemDelete.as_view(), name='delete-order-item'),
    # Order URLs
    path('order-dashboard/', OrderDashboard.as_view(), name='order-dashboard'),
    path('add-order/', AddOrder.as_view(), name='add-order'),
    #path('add-order/', create_order, name='add-order'),
    path('edit-order/<int:pk>', EditOrder.as_view(), name='edit-order'),
    path('delete-order/<int:pk>', DeleteOrder.as_view(), name='delete-order'),
    # Client URLs
    path('client-dashboard/', ClientDashboard.as_view(), name='client-dashboard'),
    path('add-client/', AddClient.as_view(), name='add-client'),
    path('edit-client/<int:pk>', EditClient.as_view(), name='edit-client'),
    path('delete-client/<int:pk>', DeleteClient.as_view(), name='delete-client'),
    # Invoice URLs
    path('invoice-dashboard/', InvoiceDashboard.as_view(), name='invoice-dashboard'),
    path('add-invoice/', AddInvoice.as_view(), name='add-invoice'),
    path('edit-invoice/<int:pk>', EditInvoice.as_view(), name='edit-invoice'),
    path('delete-invoice/<int:pk>', DeleteInvoice.as_view(), name='delete-invoice'),
    # Export 
    path('export-csv/', export_inventory_to_csv, name='export_inventory_to_csv'),
    # Import Clien
    path('import-client-csv/', UploadClientView.as_view(), name='import-client-csv'),
    # Import Inventory
    path('import-inventory-csv/', UploadInventoryView.as_view(), name='import-inventory-csv'),
    # Seach bar
    path('order-dashboard/search-inventory-item/', search_inventory_item, name='search_inventory_item'),
    # Mark order as checked
    path('order-dashboard/<int:order_id>/mark_checked/', mark_order_as_checked, name='mark-order-checked'),

    # Purchase Order
    path('purchase-dashboard/', PurchaseDashboard.as_view(), name='purchase-dashboard'),
    path('add-purchase/', AddPurchase.as_view(), name='add-purchase'),
    path('edit-purchase/<int:pk>', EditPurchase.as_view(), name='edit-purchase'),
    path('delete-purchase/<int:pk>', DeletePurchase.as_view(), name='delete-purchase'),

    # PurchaseItem URLs
    path('purchase-dashboard/<int:pk>', PurchaseItemDashboard.as_view(), name='purchase-item-list'),
    path('purchase-dashboard/<int:pk>/add-item/', PurchaseItemAdd.as_view(), name='add-purchase-item'),
    path('purchase-dashboard/<int:pk>/edit-item/<int:purchase_item_id>', PurchaseItemUpdate.as_view(), name='edit-purchase-item'),
    path('purchase-dashboard/<int:pk>/delete-item/<int:purchase_item_id>', PurchaseItemDelete.as_view(), name='delete-purchase-item'),


    path('create_purchase_order/', create_purchase_order, name='create_purchase_order'),
]