# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models.functions import TruncMonth, Cast
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from .models import *
from .forms import *
from django.db.models import Avg
from django.http import JsonResponse
import json
from django.db.models import Q
import logging
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import DateField
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.safestring import mark_safe
from decimal import Decimal

logger = logging.getLogger(__name__)



def format_purchase_history(purchase_history):
    return [{
        'product__name': item['product__name'],
        'purchase_date': item['purchase_date'].isoformat(),  # Convert datetime to ISO 8601 format
        'product__price': float(item['product__price'])  # Convert Decimal to float
    } for item in purchase_history]

def format_monthly_spending(monthly_spending):
    return [{
        'month': item['month'].isoformat(),  # Convert datetime to ISO 8601 format
        'spent': float(item['spent'])  # Convert Decimal to float
    } for item in monthly_spending]

class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, TruncMonth):
            return obj.isoformat()
        return super().default(obj)

def home(request):
    # Get search query from the request
    search_query = request.GET.get('q', '')  # Search query (optional)
    filter_vendor = request.GET.get('vendor', '')  # Vendor filter (optional)
    min_price = request.GET.get('min_price', '')  # Minimum price filter (optional)
    max_price = request.GET.get('max_price', '')  # Maximum price filter (optional)

    # Start with all products
    products = Product.objects.filter(status='Available')
    vendors = Vendor.objects.all()

    # Apply search query if present
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Apply vendor filter if present
    if filter_vendor:
        products = products.filter(vendor__id=filter_vendor)

    # Apply price filters if present
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    context = {
        'MEDIA_URL': settings.MEDIA_URL,
        'products': products,
        'search_query': search_query,
        'filter_vendor': filter_vendor,
        'min_price': min_price,
        'max_price': max_price,
        'vendors': vendors,
    }
    return render(request, 'home.html', context)

@login_required
def update_user_details(request):
    user = request.user  # Get the currently logged-in user
    
    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Vendor),
        recipient_object_id=request.user.vendor.id,
        read=False
    ).count()

    if request.method == 'POST':
        form = UpdateUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()  # Save the updated user details
            messages.success(request, 'Your details have been successfully updated.')
            return redirect('update_user_details')  # Redirect back to the form after saving
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UpdateUserForm(instance=user)  # Populate the form with the current user data

    context = {
        'form': form,
        'unread_message_count': unread_message_count,
    }
    return render(request, 'update_user_details.html', context)

@login_required
def update_user_details1(request):
    user = request.user  # Get the currently logged-in user
    
    # Unread messages count
    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Client),
        recipient_object_id=user.client.id,
        read=False
    ).count()

    if request.method == 'POST':
        form = UpdateUserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()  # Save the updated user details
            messages.success(request, 'Your details have been successfully updated.')
            return redirect('update_user_details')  # Redirect back to the form after saving
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UpdateUserForm(instance=user)  # Populate the form with the current user data

    context = {
        'form': form,
        'unread_message_count': unread_message_count,
    }
    return render(request, 'update_user_details1.html', context)

def product_detail(request, product_id):
    # Fetch the product by its ID or return a 404 if it does not exist
    product = get_object_or_404(Product, id=product_id)
    
    # Prepare the context with the product details
    context = {
        'product': product
    }
    
    # Render the product detail template with the product data
    return render(request, 'product_detail.html', context)

# Vendor Views

@login_required
def vendor_dashboard(request):
    # Get the current vendor
    vendor = Vendor.objects.get(user=request.user)

    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Vendor),
        recipient_object_id=vendor.id,
        read=False
    ).count()

    total_products = Product.objects.filter(vendor=vendor).count()
    total_ratings = Rating.objects.filter(vendor=vendor).count()
    average_rating = Rating.objects.filter(vendor=vendor).aggregate(Avg('score'))['score__avg'] or 0

    total_products = Product.objects.filter(vendor=vendor).count()
    total_sales = Purchase.objects.filter(product__vendor=vendor).count()
    total_revenue = Purchase.objects.filter(product__vendor=vendor).aggregate(Sum('product__price'))['product__price__sum'] or 0
    average_rating = Rating.objects.filter(vendor=vendor).aggregate(Avg('score'))['score__avg'] or 0

    # Product performance data
    product_performance = list(Product.objects.filter(vendor=vendor).annotate(
        sales_count=Count('purchase'),
        revenue=Sum('purchase__product__price')
    ).values('name', 'sales_count', 'revenue'))

    # Monthly sales data
    monthly_sales = list(Purchase.objects.filter(product__vendor=vendor).annotate(
        month=Cast(TruncMonth('purchase_date'), output_field=DateField())
    ).values('month').annotate(sales=Count('id')).order_by('month'))

    # Debug print statements
    print("Raw Product Performance Data:")
    print(product_performance)
    print("Raw Monthly Sales Data:")
    print(monthly_sales)

    # Convert to JSON
    product_performance_json = json.dumps(product_performance, cls=CustomJSONEncoder)
    monthly_sales_json = json.dumps(monthly_sales, cls=CustomJSONEncoder)

    print("Product Performance JSON:")
    print(product_performance_json)
    print("Monthly Sales JSON:")
    print(monthly_sales_json)

    context = {
        'total_products': total_products,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'average_rating': average_rating,
        'product_performance': mark_safe(product_performance_json),
        'monthly_sales': mark_safe(monthly_sales_json),
        'total_products': total_products,
        'total_ratings': total_ratings,
        'average_rating': round(average_rating, 2),
        'user': vendor.user,
        'unread_message_count': unread_message_count,
    }

    return render(request, 'vendor_dashboard.html', context)

@login_required
def delete_product(request, product_id):

    Product.objects.filter(id=product_id).delete()
    
    return redirect('view_products')

@login_required
def vendor_signup(request):
    if request.method == 'POST':
        form = VendorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Vendor.objects.create(user=user)
            login(request, user)
            
            return redirect('vendor_dashboard')
    else:
        form = VendorRegistrationForm()
    return render(request, 'vendor_signup.html', {'form': form})

@login_required
def view_ratings(request):
    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Vendor),
        recipient_object_id=request.user.vendor.id,
        read=False
    ).count()
    if hasattr(request.user, 'vendor'):
        vendor = request.user.vendor
        ratings = Rating.objects.filter(vendor=vendor).order_by('-created_at')
    else:
        return redirect('login')  # Redirect to login if not a vendor
    
    return render(request, 'view_ratings.html', {'ratings': ratings, 
        'unread_message_count': unread_message_count,})

def vendor_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and hasattr(user, 'vendor'):
            login(request, user)
            return redirect('vendor_dashboard')
        else:
            messages.error(request, 'Invalid credentials.')
    return render(request, 'vendor_login.html')

def vendor_logout(request):
    # Log the user out
    logout(request)
    # Redirect the user to the vendor login page or home page
    return redirect('vendor_login')

@login_required
def post_product(request):
    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Vendor),
        recipient_object_id=request.user.vendor.id,
        read=False
    ).count()
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)  # Include request.FILES
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user.vendor
            product.save()
            return redirect('vendor_dashboard')
    else:
        form = ProductForm()
    return render(request, 'post_product.html', {'form': form, 'unread_message_count': unread_message_count,})

@login_required
def view_products(request):
    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Vendor),
        recipient_object_id=request.user.vendor.id,
        read=False
    ).count()
    products = Product.objects.filter(vendor=request.user.vendor)
    return render(request, 'view_products.html', {'products': products, 
        'unread_message_count': unread_message_count,})

# Client Views

def client_signup(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # This saves both User and Client
            login(request, user)  # Log the user in after signup
            return redirect('client_dashboard')
    else:
        form = ClientRegistrationForm()
    return render(request, 'client_signup.html', {'form': form})

def client_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and hasattr(user, 'client'):
            login(request, user)
            return redirect('client_dashboard')
        else:
            messages.error(request, 'Invalid credentials.')
    return render(request, 'client_login.html')

def client_logout(request):
    # Log the user out
    logout(request)
    # Redirect the user to the vendor login page or home page
    return redirect('client_login')

@login_required
def view_products_for_clients(request):
    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Vendor),
        recipient_object_id=request.user.vendor.id,
        read=False
    ).count()
    products = Product.objects.filter(status='Available')
    return render(request, 'view_products_for_clients.html', {'products': products, 
        'unread_message_count': unread_message_count,})

@login_required
def purchase_product(request, product_id):
        # Unread messages count
    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Client),
        recipient_object_id=request.user.client.id,
        read=False
    ).count()
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        purchase = Purchase.objects.create(client=request.user.client, product=product)
        product.status= 'Ordered'
        product.save()
        return redirect('client_dashboard')
    return render(request, 'purchase_product.html', {'product': product, 
        'unread_message_count': unread_message_count,})

@login_required
def rate_vendor(request, vendor_id):
    # Fetch the vendor by ID
    vendor = get_object_or_404(Vendor, id=vendor_id)
    
    # Unread messages count
    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Client),
        recipient_object_id=request.user.client.id,
        read=False
    ).count()

    # Check if the client has made a completed purchase with this vendor
    has_completed_purchase = Purchase.objects.filter(
        client=request.user.client,  # Assuming the user has a one-to-one relationship with the Client model
        product__vendor=vendor,
        status='Completed'  # Filter only completed purchases
    ).exists()

    if not has_completed_purchase:
        # If the client has no completed purchases with this vendor, redirect or show a message
        return render(request, 'error.html', {
            'message': 'You can only rate vendors with whom you have completed a purchase.'
        })

    if request.method == 'POST':
        # Check if the client has already rated this vendor
        existing_rating = Rating.objects.filter(vendor=vendor, client=request.user).first()

        if existing_rating:
            # Update the existing rating
            form = RatingForm(request.POST, instance=existing_rating)
            if form.is_valid():
                form.save()
                return redirect('client_dashboard')
        else:
            # Create a new rating
            form = RatingForm(request.POST)
            if form.is_valid():
                rating = form.save(commit=False)
                rating.vendor = vendor
                rating.client = request.user  # Associate the logged-in user as the client
                rating.save()
                return redirect('client_dashboard')

    else:
        # If it's a GET request and there's an existing rating, populate the form with it
        existing_rating = Rating.objects.filter(vendor=vendor, client=request.user).first()
        if existing_rating:
            form = RatingForm(instance=existing_rating)
        else:
            form = RatingForm()

    return render(request, 'rate_vendor.html', {'form': form, 'vendor': vendor,  'unread_message_count': unread_message_count,})

# Communication between Clients and Vendors

@login_required
def send_message(request, vendor_id):
    vendor = get_object_or_404(Vendor, id=vendor_id)
    if request.method == 'POST':
        content = request.POST['content']
        Message.objects.create(client=request.user.client, vendor=vendor, content=content)
        return redirect('client_dashboard')
    return render(request, 'send_message.html', {'vendor': vendor})

@login_required
def view_messages(request):
    messages_list = []
    selected_vendor = None

    # Unread messages count
    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Client),
        recipient_object_id=request.user.client.id,
        read=False
    ).count()

    if hasattr(request.user, 'client'):  # Check if the user is a client
        client = request.user.client
        vendor_id = request.GET.get('vendor_id')

        if vendor_id:
            selected_vendor = get_object_or_404(Vendor, id=vendor_id)
            # Use ContentType to filter messages
            messages_list = (Message.objects.filter(
                sender_content_type=ContentType.objects.get_for_model(Client),
                sender_object_id=client.id,
                recipient_content_type=ContentType.objects.get_for_model(Vendor),
                recipient_object_id=selected_vendor.id
            ) | Message.objects.filter(
                sender_content_type=ContentType.objects.get_for_model(Vendor),
                sender_object_id=selected_vendor.id,
                recipient_content_type=ContentType.objects.get_for_model(Client),
                recipient_object_id=client.id
            )).order_by('timestamp')

            messages_list.filter(
                recipient_content_type=ContentType.objects.get_for_model(Client),
                recipient_object_id=client.id,
                read=False
            ).update(read=True)

        if request.method == 'POST':
            vendor_id = request.POST.get('vendor_id')
            content = request.POST['content']
            vendor = get_object_or_404(Vendor, id=vendor_id)
            # Create a message from client to vendor
            message = Message.objects.create(
                sender_content_type=ContentType.objects.get_for_model(Client),
                sender_object_id=client.id,
                recipient_content_type=ContentType.objects.get_for_model(Vendor),
                recipient_object_id=vendor.id,
                content=content
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Message sent successfully!',
                    'id': message.id,
                    'content': message.content,
                    'timestamp': message.timestamp.strftime('%H:%M %p')
                })
            else:
                messages.success(request, 'Message sent successfully!')

    elif hasattr(request.user, 'vendor'):
        vendor = request.user.vendor
        client_id = request.GET.get('client_id')

        if client_id:
            selected_client = get_object_or_404(Client, id=client_id)
            messages_list = Message.objects.filter(
                recipient_content_type=ContentType.objects.get_for_model(Vendor),
                recipient_object_id=vendor.id
            ) | Message.objects.filter(
                sender_content_type=ContentType.objects.get_for_model(Client),
                sender_object_id=selected_client.id
            )

        if request.method == 'POST':
            client_id = request.POST.get('client_id')
            content = request.POST['content']
            client = get_object_or_404(Client, id=client_id)
            # Create a message from vendor to client
            Message.objects.create(
                sender_content_type=ContentType.objects.get_for_model(Vendor),
                sender_object_id=vendor.id,
                recipient_content_type=ContentType.objects.get_for_model(Client),
                recipient_object_id=client.id,
                content=content
            )
            messages.success(request, 'Message sent successfully!')

    else:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('login')

    return render(request, 'view_messages.html', {
        'messages': messages_list,
        'vendors': Vendor.objects.all(),
        'selected_vendor': selected_vendor,
        'unread_message_count': unread_message_count,
    })

from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required
def check_new_messages(request):
    client = request.user.client
    vendor_id = request.GET.get('vendor_id')

    if vendor_id:
        selected_vendor = get_object_or_404(Vendor, id=vendor_id)
        # Use ContentType to filter messages
        messages_list = Message.objects.filter(
            sender_content_type=ContentType.objects.get_for_model(Client),
            sender_object_id=client.id,
            recipient_content_type=ContentType.objects.get_for_model(Vendor),
            recipient_object_id=selected_vendor.id
        ) | Message.objects.filter(
            sender_content_type=ContentType.objects.get_for_model(Vendor),
            sender_object_id=selected_vendor.id,
            recipient_content_type=ContentType.objects.get_for_model(Client),
            recipient_object_id=client.id
        )
        
        # Mark messages as read after fetching
        unread_messages.update(read=True)

        # Render the messages to HTML
        new_messages_html = render_to_string('partials/messages_list.html', {
            'messages': unread_messages
        })

        return JsonResponse({
            'new_messages': True,
            'new_messages_html': new_messages_html
        })

    return JsonResponse({
        'new_messages': False
    })


@login_required
def view_messages1(request):
    messages_list = []
    selected_client = None

    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Vendor),
        recipient_object_id=request.user.vendor.id,
        read=False
    ).count()

    if hasattr(request.user, 'vendor'):  # Check if the user is a vendor
        vendor = request.user.vendor
        client_id = request.GET.get('client_id')

        # Fetch clients who have initiated conversations with this vendor
        clients_with_messages = Client.objects.filter(
            id__in=Message.objects.filter(
                recipient_content_type=ContentType.objects.get_for_model(Vendor),
                recipient_object_id=vendor.id
            ).values_list('sender_object_id', flat=True)
        )

        if client_id:
            selected_client = get_object_or_404(Client, id=client_id)
            # Fetch messages between the vendor and the selected client
            messages_list = (Message.objects.filter(
                sender_content_type=ContentType.objects.get_for_model(Client),
                sender_object_id=selected_client.id,
                recipient_content_type=ContentType.objects.get_for_model(Vendor),
                recipient_object_id=vendor.id
            ) | Message.objects.filter(
                sender_content_type=ContentType.objects.get_for_model(Vendor),
                sender_object_id=vendor.id,
                recipient_content_type=ContentType.objects.get_for_model(Client),
                recipient_object_id=selected_client.id
            )).order_by('timestamp')

            messages_list.filter(
                recipient_content_type=ContentType.objects.get_for_model(Vendor),
                recipient_object_id=vendor.id,
                read=False
            ).update(read=True)

            if request.method == 'POST':
                client_id = request.POST.get('client_id')
                content = request.POST['content']
                client = get_object_or_404(Client, id=client_id)

                # Create a message from vendor to client
                message = Message.objects.create(
                    sender_content_type=ContentType.objects.get_for_model(Vendor),
                    sender_object_id=vendor.id,
                    recipient_content_type=ContentType.objects.get_for_model(Client),
                    recipient_object_id=client.id,
                    content=content
                )
                
                # Check if the request is an AJAX request
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'message': 'Message sent successfully!',
                        'id': message.id,  # Fix here: Now `message` is defined
                        'content': message.content,
                        'timestamp': message.timestamp.strftime('%H:%M %p')
                    })
                else:
                    messages.success(request, 'Message sent successfully!')


    else:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('login')

    return render(request, 'view_messages1.html', {
        'messages': messages_list,
        'clients_with_messages': clients_with_messages,
        'selected_client': selected_client,
        'unread_message_count': unread_message_count,
    })

from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required
def check_new_messages1(request):
    client_id = request.GET.get('client_id')
    vendor = request.user.vendor

    if client_id:
        selected_client = get_object_or_404(Client, id=client_id)
        # Fetch the unread messages between the vendor and the client
        unread_messages = Message.objects.filter(
            sender_content_type=ContentType.objects.get_for_model(Client),
            sender_object_id=selected_client.id,
            recipient_content_type=ContentType.objects.get_for_model(Vendor),
            recipient_object_id=vendor.id,
            read=False
        )
        
        # Mark messages as read after fetching
        unread_messages.update(read=True)

        # Render the messages to HTML
        new_messages_html = render_to_string('E_Waste_App/partials/messages_list.html', {
            'messages': unread_messages
        })

        return JsonResponse({
            'new_messages': True,
            'new_messages_html': new_messages_html
        })

    return JsonResponse({
        'new_messages': False
    })


@login_required
@require_POST
@ensure_csrf_cookie
def delete_message(request, message_id):
    logger.info(f"Attempting to delete message {message_id} for user {request.user}")
    try:
        if hasattr(request.user, 'client'):
            content_type = ContentType.objects.get_for_model(Client)
            object_id = request.user.client.id
        elif hasattr(request.user, 'vendor'):
            content_type = ContentType.objects.get_for_model(Vendor)
            object_id = request.user.vendor.id
        else:
            raise ValueError("User is neither a Client nor a Vendor")

        message = Message.objects.get(
            id=message_id,
            sender_content_type=content_type,
            sender_object_id=object_id
        )
        message.delete()
        logger.info(f"Successfully deleted message {message_id}")
        return JsonResponse({'success': True})
    except Message.DoesNotExist:
        logger.warning(f"Message {message_id} not found or user {request.user} doesn't have permission")
        return JsonResponse({'success': False, 'error': 'Message not found or you do not have permission to delete it.'}, status=404)
    except Exception as e:
        logger.exception(f"Error deleting message {message_id}: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Order Management Views

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Purchase, id=order_id, client=request.user.client)
    product = get_object_or_404(Product, id=order.product.id)
    product.status ='Available'
    product.save()    
    order.delete()
    return redirect('view_orders_for_client')

@login_required
def complete_order(request, order_id):
    order = get_object_or_404(Purchase, id=order_id, product__vendor=request.user.vendor)
    order.status = 'Completed'  # Update the status field
    order.save()
    product = get_object_or_404(Product, id=order.product.id)
    product.status ='Sold'
    product.save()
    return redirect('view_orders')

@login_required
def accept_order(request, order_id):
    order = get_object_or_404(Purchase, id=order_id, product__vendor=request.user.vendor)
    order.status = 'Accepted'  # Update the status field
    order.save()
    return redirect('view_orders')

@login_required
def reject_order(request, order_id):
    order = get_object_or_404(Purchase, id=order_id, product__vendor=request.user.vendor)
    order.status = 'Rejected'  # Update the status field
    product = get_object_or_404(Product, id=order.product.id)
    product.status = 'Sold'
    product.save()
    order.save()
    return redirect('view_orders')

@login_required
def view_orders(request):
    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Vendor),
        recipient_object_id=request.user.vendor.id,
        read=False
    ).count()
    orders = Purchase.objects.filter(product__vendor=request.user.vendor)
    return render(request, 'view_orders.html', {'orders': orders, 
        'unread_message_count': unread_message_count,})

@login_required
def view_orders_for_client(request):
    orders = Purchase.objects.filter(client=request.user.client)
        # Unread messages count
    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Client),
        recipient_object_id=request.user.client.id,
        read=False
    ).count()
    return render(request, 'view_orders_for_clients.html', {'orders': orders, 'unread_message_count': unread_message_count,})

# Dashboards

@login_required
def client_dashboard(request):
    # Get client-specific metrics
    client = request.user.client  # Assuming the user is the client

    # Total purchases
    total_purchases = Purchase.objects.filter(client=client).count()

    # Total spent
    total_spent = Purchase.objects.filter(client=client).aggregate(Sum('product__price'))['product__price__sum'] or 0

    # Favorite vendors
    favorite_vendors = Vendor.objects.filter(product__purchase__client=client).annotate(
        purchase_count=Count('product__purchase')
    ).order_by('-purchase_count')[:5]

    # Purchase history data
    purchase_history = Purchase.objects.filter(client=client).values(
        'product__name', 'purchase_date', 'product__price'
    ).order_by('-purchase_date')

    # Monthly spending data
    monthly_spending = Purchase.objects.filter(client=client).annotate(
        month=TruncMonth('purchase_date')
    ).values('month').annotate(spent=Sum('product__price')).order_by('month')

    # Total ratings given
    client_ratings_count = Rating.objects.filter(client=client.user).count()

    # Average purchase amount
    average_purchase_amount = Purchase.objects.filter(client=client).aggregate(
        Avg('product__price')
    )['product__price__avg'] or 0

    # Get search query from the request
    search_query = request.GET.get('q', '')  # Search query (optional)
    filter_vendor = request.GET.get('vendor', '')  # Vendor filter (optional)
    min_price = request.GET.get('min_price', '')  # Minimum price filter (optional)
    max_price = request.GET.get('max_price', '')  # Maximum price filter (optional)

    # Start with all products
    products = Product.objects.filter(status='Available')
    vendors = Vendor.objects.all()

    # Apply search query if present
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Apply vendor filter if present
    if filter_vendor:
        products = products.filter(vendor__id=filter_vendor)

    # Apply price filters if present
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Unread messages count
    unread_message_count = Message.objects.filter(
        recipient_content_type=ContentType.objects.get_for_model(Client),
        recipient_object_id=client.id,
        read=False
    ).count()

    # Context data for rendering the dashboard
    context = {
        'total_purchases': total_purchases,
        'total_spent': total_spent,
        'favorite_vendors': favorite_vendors,
        'purchase_history': json.dumps(format_purchase_history(purchase_history)),
        'monthly_spending': json.dumps(format_monthly_spending(monthly_spending)),
        'client_ratings_count': client_ratings_count,
        'average_purchase_amount': average_purchase_amount,
        'MEDIA_URL': settings.MEDIA_URL,
        'products': products,
        'search_query': search_query,
        'filter_vendor': filter_vendor,
        'min_price': min_price,
        'max_price': max_price,
        'vendors': vendors,
        'user': request.user,
        'unread_message_count': unread_message_count,
    }

    return render(request, 'client_dashboard.html', context)