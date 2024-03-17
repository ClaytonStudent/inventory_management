# inventory/resources.py
from import_export import resources
from inventory.models import InventoryItem, Client

class InventoryItemResource(resources.ModelResource):
    class Meta:
        model = InventoryItem
        # Define fields to export, or use '__all__' to export all fields
        fields = ('id','name','quantity','lower_threshold','category','date_created','image','price','sku','barcodes','description')
