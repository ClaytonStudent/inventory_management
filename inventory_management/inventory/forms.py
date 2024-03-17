from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Category, InventoryItem, Order, Client, OrderItem, Invoice
from .models import PurchaseOrder, PurchaseItem, Provider
from django.forms import FileField
from django.forms import formset_factory



class UserRegisterForm(UserCreationForm):
	email = forms.EmailField()

	class Meta:
		model = User
		fields = ['username', 'email', 'password1', 'password2']

class InventoryItemForm(forms.ModelForm):
	category = forms.ModelChoiceField(queryset=Category.objects.all(), initial=0)
	class Meta:
		model = InventoryItem
		fields =  '__all__'
		#fields = ['name','quantity','lower_threshold','price','sku','barcodes']

class OrderForm(forms.ModelForm):
	class Meta:
		model = Order
		fields = ['order_number','client', 'status','shipping_address','billing_address', 'payment_method']
	#def __init__(self, *args, **kwargs):
	#	super(OrderForm, self).__init__(*args, **kwargs)
#		self.orderitem_formset = OrderItemFormSet(*args, **kwargs)


class OrderItemForm(forms.ModelForm):
	product = forms.ModelChoiceField(queryset=InventoryItem.objects.all(), initial=0)
	class Meta:
		model = OrderItem
		fields = ['product', 'amount','price']


OrderItemFormSet = formset_factory(OrderItemForm, extra=1)

class ClientForm(forms.ModelForm):
	class Meta:
		model = Client
		fields = '__all__'
		#fields = ['name', 'email', 'phone_number', 'address', 'city', 'country', 'postal_code']

class InvoiceForm(forms.ModelForm):
	class Meta:
		model = Invoice
		fields = ['invoice_number', 'billing_address', 'payment_status', 'total_price','order']

class UploadForm(forms.Form):
    products_file = FileField()

class PurchaseItemForm(forms.ModelForm):
	product = forms.ModelChoiceField(queryset=InventoryItem.objects.all(), initial=0)
	class Meta:
		model = PurchaseItem
		fields = '__all__'
		
class PurchaseForm(forms.ModelForm):
	provider = forms.ModelChoiceField(queryset=Provider.objects.all(), initial=0)
	class Meta:
		model = PurchaseOrder
		fields = ['purchase_number','provider', 'status', 'payment_method', 'notes','file']
		#fields = ['client', 'status','shipping_address','billing_address', 'payment_method']

from django.forms import inlineformset_factory

PurchaseItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseItem,
    form=PurchaseItemForm,
    extra=1,  # Number of empty forms to display
    can_delete=True
)
