from typing import Any
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View, CreateView, UpdateView, DeleteView
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import UserRegisterForm, InventoryItemForm, OrderForm, OrderItemForm, InvoiceForm, ClientForm, UploadForm, PurchaseForm
from .forms import PurchaseItemForm, PurchaseItemFormSet
from .models import InventoryItem, Category, Order, OrderItem, Client, Invoice
from .models import PurchaseOrder, PurchaseItem
from inventory_management.settings import LOW_QUANTITY
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.db.models import F,Q
from django.urls import reverse

class Index(TemplateView):
	template_name = 'inventory/index.html'

class Dashboard(LoginRequiredMixin, View):
	def get(self, request):
		selected_category_name = request.GET.get('category', None)
		# dealing with search bar
		search_query = request.GET.get('q')
		items = InventoryItem.objects.all()
		if search_query:
			items = items.filter(Q(name__icontains=search_query) | Q(sku__icontains=search_query))
    	# Filter InventoryItems based on the selected category
		if selected_category_name:
			category = get_object_or_404(Category, name=selected_category_name)
			items = items.filter(category=category)
		
		# items = InventoryItem.objects.order_by('id')		
		low_inventory = InventoryItem.objects.filter(
			quantity__lte=F('lower_threshold')
		)
		if low_inventory.count() > 0:
			if low_inventory.count() > 1:
				messages.error(request, f'{low_inventory.count()} items have low inventory')
			else:
				messages.error(request, f'{low_inventory.count()} item has low inventory')
		low_inventory_ids = InventoryItem.objects.filter(
			quantity__lte=F('lower_threshold')
		).values_list('id', flat=True)
		
		categories = Category.objects.all()


		return render(request, 'inventory/dashboard.html', {'items': items, 'low_inventory_ids': low_inventory_ids, 'categories': categories})

class SignUpView(View):
	def get(self, request):
		form = UserRegisterForm()
		return render(request, 'inventory/signup.html', {'form': form})

	def post(self, request):
		form = UserRegisterForm(request.POST)

		if form.is_valid():
			form.save()
			user = authenticate(
				username=form.cleaned_data['username'],
				password=form.cleaned_data['password1']
			)

			login(request, user)
			return redirect('index')

		return render(request, 'inventory/signup.html', {'form': form})

class AddItem(LoginRequiredMixin, CreateView):
	model = InventoryItem
	form_class = InventoryItemForm
	template_name = 'inventory/item_form.html'
	success_url = reverse_lazy('dashboard')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['categories'] = Category.objects.all()
		return context

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super().form_valid(form)

class EditItem(LoginRequiredMixin, UpdateView):
	model = InventoryItem
	form_class = InventoryItemForm
	template_name = 'inventory/item_form.html'
	success_url = reverse_lazy('dashboard')

class DeleteItem(LoginRequiredMixin, DeleteView):
	model = InventoryItem
	template_name = 'inventory/delete_item.html'
	success_url = reverse_lazy('dashboard')
	context_object_name = 'item'

class OrderDashboard(LoginRequiredMixin, View):
	def get(self, request):
		items = Order.objects.order_by('id')
		for item in items:
			item.update_price()
		return render(request, 'inventory/order_dashboard.html',{'items': items})

class OrderItemList(LoginRequiredMixin, View):
	def get(self, request, pk):
		order = Order.objects.get(pk=pk)
		items = OrderItem.objects.filter(order=pk)
		for item in items:
			item.combine_with_existing()
		items = OrderItem.objects.filter(order=pk)
		return render(request, 'inventory/order_item_list.html',{'order': order, 'items': items})

class AddOrder(LoginRequiredMixin, CreateView):
	model = Order
	fields = ['order_number', 'client', 'shipping_address', 'payment_method', 'status']
	template_name = 'inventory/order_form.html'
	success_url = reverse_lazy('order-dashboard')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['clients'] = Client.objects.all()
		return context

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super().form_valid(form)
	

def create_order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            # Save the order
            order = form.save()

            # Save the associated order items
            for item_form in form.orderitem_formset:
                if item_form.is_valid():
                    item = item_form.save(commit=False)
                    item.order = order
                    item.save()
    else:
        form = OrderForm()
    
    return render(request, 'inventory/order_create_form.html', {'form': form})

class EditOrder(LoginRequiredMixin, UpdateView):
	model = Order
	form_class = OrderForm
	template_name = 'inventory/order_form.html'
	success_url = reverse_lazy('order-dashboard')
    
	def form_valid(self, form):
		return super().form_valid(form)

class DeleteOrder(LoginRequiredMixin, DeleteView):
	model = Order
	template_name = 'inventory/delete_item.html'
	success_url = reverse_lazy('order-dashboard')
	context_object_name = 'item'

class OrderItemAdd(CreateView):
    model = OrderItem
    fields = ['product', 'amount', 'price']
    template_name = 'inventory/order_item_form.html'  # Create a template for the form
    #success_url = reverse_lazy('order-dashboard')  # Update with your actual URL for order item list
    #def get(self, request, pk):
    #    return render(request, 'inventory/order_item_form.html', {'pk': pk})
	
    def get_success_url(self):
        pk = self.kwargs.get('pk')
        return reverse('order-item-list', kwargs={'pk': pk})

    def form_valid(self, form):
        order_id = self.kwargs['pk']  # Get the order id from the URL
        form.instance.order_id = order_id  # Assign the order id to the order_item
        # Get the product and amount from the form
        product = form.cleaned_data.get('product')
        amount = form.cleaned_data.get('amount')
        # Check if the product quantity is sufficient
        if product.quantity < amount:
            messages.warning(self.request, 'Insufficient quantity for this product.')
            return self.form_invalid(form)
        else:
            return super().form_valid(form)

class OrderItemUpdate(UpdateView):
	model = OrderItem
	fields = ['product', 'amount', 'price']
	template_name = 'inventory/order_item_form.html'  # Create a template for the form
	#def get(self, request, pk):
	#	return render(request, 'inventory/order_item_form.html', {'pk': pk})
	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
        # Get the order item instance
		order_item = OrderItem.objects.get(pk=self.kwargs['order_item_id'])
		kwargs['instance'] = order_item
		return kwargs

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		order_item_id = self.kwargs.get('order_item_id')
		order_item = get_object_or_404(OrderItem, id=order_item_id)
		return context

	def get_object(self, queryset=None):
		order_item_id = self.kwargs.get('order_item_id')
		order_item = get_object_or_404(OrderItem, id=order_item_id)
		return order_item
	def get_success_url(self):
		order_id = self.kwargs.get('pk')  # Get the order id from URL kwargs
		return reverse_lazy('order-item-list', kwargs={'pk': order_id})
	def form_valid(self,form):
		order_id = self.kwargs['pk']  # Get the order id from the URL
		form.instance.order_id = order_id  # Assign the order id to the order_item
        # Get the product and amount from the form
		product = form.cleaned_data.get('product')
		amount = form.cleaned_data.get('amount')
        # Check if the product quantity is sufficient
		if product.quantity < amount:
            #print('Lower then Order quantity')
			messages.warning(self.request, 'Insufficient quantity for this product.')
			return self.form_invalid(form)
		else:
			return super().form_valid(form)

class OrderItemDelete(DeleteView):
	model = OrderItem
	template_name = 'inventory/delete_item.html'
	context_object_name = 'item'
	def get_object(self, queryset=None):
		order_item_id = self.kwargs.get('order_item_id')
		order_item = get_object_or_404(OrderItem, id=order_item_id)
		return order_item
	def get_success_url(self):
		order_id = self.kwargs.get('pk')  # Get the order id from URL kwargs
		return reverse_lazy('order-item-list', kwargs={'pk': order_id})
	
'''
Clients
'''
class ClientDashboard(LoginRequiredMixin, View):
	def get(self, request):
		clients = Client.objects.order_by('id')
		return render(request, 'inventory/client_dashboard.html',{'clients': clients})

class AddClient(LoginRequiredMixin, CreateView):
	model = Client
	form_class = ClientForm
	#fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 'city', 'country', 'postal_code']
	template_name = 'inventory/client_form.html'
	success_url = reverse_lazy('client-dashboard')

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super().form_valid(form)

class EditClient(LoginRequiredMixin, UpdateView):
	model = Client
	form_class = ClientForm
	#fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 'city', 'country', 'postal_code']
	template_name = 'inventory/client_form.html'
	success_url = reverse_lazy('client-dashboard')

	def form_valid(self, form):
		return super().form_valid(form)

class DeleteClient(LoginRequiredMixin, DeleteView):
	model = Client
	template_name = 'inventory/delete_item.html'
	success_url = reverse_lazy('client-dashboard')
	context_object_name = 'item'

'''
Invoices
'''
class InvoiceDashboard(LoginRequiredMixin, View):
	def get(self, request):
		invoices = Invoice.objects.order_by('id')
		return render(request, 'inventory/invoice_dashboard.html',{'invoices':invoices})

class AddInvoice(LoginRequiredMixin, CreateView):
	model = Invoice
	form_class = InvoiceForm
	#fields = ['invoice_number', 'client', 'order', 'payment_method', 'status']
	template_name = 'inventory/invoice_form.html'
	success_url = reverse_lazy('invoice-dashboard')

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super().form_valid(form)

class EditInvoice(LoginRequiredMixin, UpdateView):
	model = Invoice
	form_class = InvoiceForm
	#fields = ['invoice_number', 'client', 'order', 'payment_method', 'status']
	template_name = 'inventory/invoice_form.html'
	success_url = reverse_lazy('invoice-dashboard')

	def form_valid(self, form):
		return super().form_valid(form)

class DeleteInvoice(LoginRequiredMixin, DeleteView):
	model = Invoice
	template_name = 'inventory/delete_item.html'
	success_url = reverse_lazy('invoice-dashboard')
	context_object_name = 'item'

'''
Purchase
'''
class PurchaseDashboard(LoginRequiredMixin, View):
	def get(self, request):
		purchases = PurchaseOrder.objects.order_by('id')
		return render(request, 'inventory/purchase_dashboard.html',{'purchases':purchases})

class AddPurchase(LoginRequiredMixin, CreateView):
	model = PurchaseOrder
	form_class = PurchaseForm
	template_name = 'inventory/purchase_form.html'
	success_url = reverse_lazy('purchase-dashboard')

	def form_valid(self, form):
		form.instance.user = self.request.user
		return super().form_valid(form)

class EditPurchase(LoginRequiredMixin, UpdateView):
	model = PurchaseOrder
	form_class = PurchaseForm
	template_name = 'inventory/purchase_form.html'
	success_url = reverse_lazy('purchase-dashboard')

	def form_valid(self, form):
		return super().form_valid(form)


class DeletePurchase(LoginRequiredMixin, DeleteView):
	model = PurchaseOrder
	template_name = 'inventory/delete_item.html'
	success_url = reverse_lazy('purchase-dashboard')
	context_object_name = 'item'

'''
Purchase
'''
class PurchaseItemDashboard(LoginRequiredMixin, View):
	def get(self, request, pk):
		purchase_order = PurchaseOrder.objects.get(pk=pk)
		purchase_items = PurchaseItem.objects.filter(purchase_order=purchase_order)
		for purchase_item in purchase_items:
			purchase_item.combine_with_existing()
		purchase_items = PurchaseItem.objects.filter(purchase_order=purchase_order)
		return render(request, 'inventory/purchase_item_dashboard.html',{'purchase_order':purchase_order,'purchase_items':purchase_items})

class PurchaseItemAdd(LoginRequiredMixin, CreateView):
	model = PurchaseItem
	form_class = PurchaseItemForm
	template_name = 'inventory/purchase_item_form.html'
	success_url = reverse_lazy('purchase-dashboard')

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		purchase_order_id = self.kwargs.get('pk')
		purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
		context['purchase_order'] = purchase_order
		return context

	def form_valid(self, form):
		purchase_order_id = self.kwargs['pk']  # Get the order id from the URL
		form.instance.purchase_order_id = purchase_order_id  # Assign the order id to the order_item
		return super().form_valid(form)

class PurchaseItemUpdate(LoginRequiredMixin, UpdateView):
	model = PurchaseItem
	form_class = PurchaseItemForm
	template_name = 'inventory/purchase_item_form.html'
	#success_url = reverse_lazy('purchase-dashboard')
	def get_form_kwargs(self):
		kwargs = super().get_form_kwargs()
		# Get the order item instance
		purchase_item = PurchaseItem.objects.get(pk=self.kwargs['purchase_item_id'])
		kwargs['instance'] = purchase_item
		return kwargs
		#return super().get_form_kwargs()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		purchase_order_id = self.kwargs.get('pk')
		purchase_order = get_object_or_404(PurchaseOrder, id=purchase_order_id)
		context['purchase_order'] = purchase_order
		return context
	def get_object(self, queryset=None):
		purchase_item_id = self.kwargs.get('purchase_item_id')
		purchase_item = get_object_or_404(PurchaseItem, id=purchase_item_id)
		return purchase_item
	def get_success_url(self):
		purchase_order_id = self.kwargs.get('pk')  # Get the order id from URL kwargs
		return reverse_lazy('purchase-item-list', kwargs={'pk': purchase_order_id})

	def form_valid(self, form):
		return super().form_valid(form)


class PurchaseItemDelete(LoginRequiredMixin, DeleteView):
	model = PurchaseItem
	template_name = 'inventory/delete_item.html'
	#success_url = reverse_lazy('purchase-dashboard')
	context_object_name = 'item'

	def get_object(self, queryset=None):
		purchase_item_id = self.kwargs.get('purchase_item_id')
		purchase_item = get_object_or_404(PurchaseItem, id=purchase_item_id)
		return purchase_item
	def get_success_url(self):
		purchase_order_id = self.kwargs.get('pk')
		return reverse_lazy('purchase-item-list', kwargs={'pk': purchase_order_id})
		#return super().get_success_url()

'''
Export
'''
from django.http import HttpResponse
from django.shortcuts import render
from import_export import resources,results
from inventory.resources import InventoryItemResource

def export_inventory_to_csv(request):
    inventory_resource = InventoryItemResource()
    dataset = inventory_resource.export()
    response = HttpResponse(dataset.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory.csv"'
    return response

'''
Client Upload
'''
from csv import DictReader
from io import TextIOWrapper
class UploadClientView(View):

	def get(self, request, *args, **kwargs):
		return render(request, "inventory/import_csv.html", {"form": UploadForm()})
	def post(self, request, *args, **kwargs):
		products_file = request.FILES["csv_file"]
		rows = TextIOWrapper(products_file, encoding="utf-8", newline="")
		row_count = 0
		form_errors = []
		for row in DictReader(rows):
			row_count += 1
			client_id = row.get('id', None)
			print('ID to upload:',client_id)
			if client_id:
				existing_client = Client.objects.filter(id=client_id).first()
				if existing_client:
					form = ClientForm(row, instance=existing_client)
				else: 
					form = ClientForm(row)
			else:
				form = ClientForm(row)
			print('form is valid')
			if form.is_valid():
				form.save()
			else:
				form_errors.append({'row_count': row_count, 'errors': form.errors})
		return render(request, "inventory/import_csv.html", {"form": UploadForm(), "row_count": row_count, "form_errors": form_errors})

class UploadInventoryView(View):
	
	def get(self, request, *args, **kwargs):
		return render(request, "inventory/import_csv.html", {"form": UploadForm()})
	def post(self, request, *args, **kwargs):
		products_file = request.FILES["csv_file"]
		rows = TextIOWrapper(products_file, encoding="utf-8", newline="")
		row_count = 0
		form_errors = []
		for row in DictReader(rows):
			row_count += 1
			product_name = row.get('name', None)
			if product_name:
				existing_product = InventoryItem.objects.filter(name=product_name).first()
				if existing_product:
					form = InventoryItemForm(row, instance=existing_product)
				else: 
					form = InventoryItemForm(row)
			else:
				form = InventoryItemForm(row)
			if form.is_valid():
				form.save()
			else:
				form_errors.append({'row_count': row_count, 'errors': form.errors})
		return render(request, "inventory/import_csv.html", {"form": UploadForm(), "row_count": row_count, "form_errors": form_errors})

'''
Search bar
'''
# views.py
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import InventoryItem
def search_inventory_item(request):
	barcode = request.POST.get('barcode', None)
	response_data = {'success': False, 'inventory_item_id': None}
	try:
		inventory_item = get_object_or_404(InventoryItem, barcodes=barcode)
		response_data['success'] = True
		response_data['inventory_item_id'] = inventory_item.id
		response_data['inventory_item_price'] = inventory_item.price
	except:
		inventory_item = None	
	return JsonResponse(response_data)


'''
Mark order as checked
'''

from django.http import JsonResponse

def mark_order_as_checked(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        order.mark_as_checked()
        return JsonResponse({'success': True})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Order does not exist'})


from django.shortcuts import render
from django.forms import modelformset_factory
from .models import PurchaseOrder, PurchaseItem
from .forms import PurchaseItemForm

def create_purchase_order(request):
    PurchaseItemFormSet = modelformset_factory(PurchaseItem, form=PurchaseItemForm, extra=1)

    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        formset = PurchaseItemFormSet(request.POST, queryset=PurchaseItem.objects.none())

        if form.is_valid() and formset.is_valid():
            purchase_order = form.save()
            for purchase_item_form in formset:
                purchase_item = purchase_item_form.save(commit=False)
                purchase_item.purchase_order = purchase_order
                purchase_item.save()

    else:
        form = PurchaseForm()
        formset = PurchaseItemFormSet(queryset=PurchaseItem.objects.none())

    return render(request, 'inventory/purchase_order_form.html', {'form': form, 'formset': formset})


