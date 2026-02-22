from flask import render_template, request, redirect, session, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from app.models import User,Product,Order,OrderItem
from app.extensions import db
from .decorators import login_required
from.import auth
from cloudinary.uploader import upload
from app.cloudinary_config import *

def can_manage_products(user):
    if not user:
        return False
    return user.role in {"admin", "seller"}

def can_remove_product(user, product):
    if not user or not product:
        return False
    return user.role == "seller"

#home route
@auth.route('/')
def index():
    return render_template('index.html')

#buyer and seller route for registration
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        new_user = User(name=name, email=email, password=password, role='buyer')
        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

#buyer and seller route for login
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['email'] = user.email
            session['user_id']=user.id
            if can_manage_products(user):
                return redirect(url_for('auth.seller_dashboard'))
            return redirect(url_for('auth.dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password')

    return render_template('login.html')

#buyer route for dashboard
@auth.route('/dashboard')
@login_required
def dashboard():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()
        if not user:
            return redirect(url_for('auth.login'))
        products = Product.query.all()
        return render_template(
            'dashboard.html',
            user=user,
            products=products,
            can_add_product=can_manage_products(user),
            show_payments_button=user.role == 'seller'
        )

    return redirect('/login')

#buyer route for add to cart
@auth.route('/cart')
@login_required
def cart():
    if 'email' not in session:
        return redirect('/login')

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('auth.login'))
    if user.role == 'seller':
        return redirect(url_for('auth.seller_dashboard'))

    return render_template('cart.html', user=user)
#buyer route for payments
@auth.route('/payment')
@login_required
def payment():
    if 'email' not in session:
        return redirect('/login')

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('auth.login'))
    if user.role == 'seller':
        return redirect(url_for('auth.seller_dashboard'))

    return render_template('payment.html', user=user)

#seller route for dashboard
@auth.route('/seller-dashboard')
@login_required
def seller_dashboard():
    if 'email' not in session:
        return redirect('/login')

    user = User.query.filter_by(email=session['email']).first()
    if not can_manage_products(user):
        return redirect(url_for('auth.dashboard'))

    products = Product.query.all()
    return render_template(
        'dashboard.html',
        user=user,
        products=products,
        can_add_product=True,
        show_payments_button=True
    )

#seller route for dashboard
@auth.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('user_id', None)
    return redirect('/login')
#profile route for buyer
@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        user.phone = (request.form.get('phone') or '').strip()
        user.city = (request.form.get('city') or '').strip()
        user.address = (request.form.get('address') or '').strip()
        user.pincode = (request.form.get('pincode') or '').strip()
        db.session.commit()
        return redirect(url_for('auth.profile'))

    return render_template('profile.html', user=user)

#buyer route for placing order
@auth.route('/place-order', methods=['POST'])
@login_required
def place_order():
    if 'email' not in session:
        return jsonify({'ok': False, 'message': 'Please login first.'}), 401

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return jsonify({'ok': False, 'message': 'User not found.'}), 404
    if user.role == 'seller':
        return jsonify({'ok': False, 'message': 'Sellers cannot place orders.'}), 403

    data = request.get_json(silent=True) or {}
    cart_items = data.get('items') or []
    payment_mode_raw = (data.get('payment_mode') or '').strip().lower()
    transaction_id = (data.get('transaction_id') or '').strip()

    if not cart_items:
        return jsonify({'ok': False, 'message': 'Your cart is empty.'}), 400

    if payment_mode_raw not in {'upi', 'cash'}:
        return jsonify({'ok': False, 'message': 'Invalid payment mode.'}), 400

    if payment_mode_raw == 'upi' and not transaction_id:
        return jsonify({'ok': False, 'message': 'Transaction ID is required for online payment.'}), 400

    buyer_phone = (data.get('phone') or user.phone or '').strip()
    if not buyer_phone:
        return jsonify({'ok': False, 'message': 'Please add your phone number in profile before ordering.'}), 400

    total_amount = 0
    order_items = []
    for item in cart_items:
        product_name = (item.get('name') or '').strip()
        try:
            quantity = int(item.get('qty') or 0)
            price = float(item.get('price') or 0)
        except (TypeError, ValueError):
            continue
        if not product_name or quantity <= 0:
            continue
        total_amount += quantity * price
        order_items.append(
            OrderItem(
                product_name=product_name,
                quantity=quantity,
                price=price
            )
        )

    if not order_items:
        return jsonify({'ok': False, 'message': 'No valid items in order.'}), 400

    payment_mode = 'Online Payment' if payment_mode_raw == 'upi' else 'Offline Payment'
    order = Order(
        buyer_id=user.id,
        buyer_name=user.name,
        buyer_phone=buyer_phone,
        payment_mode=payment_mode,
        transaction_id=transaction_id if payment_mode_raw == 'upi' else None,
        total_amount=total_amount
    )
    order.items = order_items

    db.session.add(order)
    db.session.commit()

    return jsonify({
        'ok': True,
        'order_id': order.id,
        'redirect_url': url_for('auth.order_details', order_id=order.id)
    })

#buyer route for order details
@auth.route('/order/<int:order_id>')
@login_required
def order_details(order_id):
    if 'email' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
        return redirect(url_for('auth.login'))

    order = Order.query.get_or_404(order_id)
    if user.role != 'seller' and order.buyer_id != user.id:
        return redirect(url_for('auth.dashboard'))

    return render_template(
        'order.html',
        user=user,
        order=order,
        is_seller_view=False
    )

#seller route for payments
@auth.route('/seller/payments')
@login_required
def seller_payments():
    if 'email' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=session['email']).first()
    if not can_manage_products(user):
        return redirect(url_for('auth.dashboard'))

    orders = Order.query.filter_by(buyer_id=user.id).all()
    return render_template(
        'order.html',
        user=user,
        orders=orders,
        is_seller_view=True
    )

#seller route for adding proucts and removing products in cloudinary and data base
@auth.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    current_user = User.query.filter_by(email=session.get('email')).first()
    if not can_manage_products(current_user):
        return redirect(url_for('auth.dashboard'))

    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        description = request.form.get("description")
        image_url=None
        image=request.files.get("image")
        if image and image.filename != '':
               result=upload(image) #cloudinary upload
               image_url=result.get("secure_url")
   
    
    
        new_product = Product(
            name=name,
            price=price,
            description=description,
            image=image_url,
            seller_id=current_user.id if current_user and current_user.role == "seller" else None
        )

        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for('auth.seller_dashboard'))

    return render_template('add_product.html')

#seller route for removing products
@auth.route('/remove_product/<int:product_id>', methods=['POST'])
@login_required
def remove_product(product_id):
    current_user = User.query.filter_by(email=session.get('email')).first()
    if not current_user:
        return redirect(url_for('auth.login'))

    product = Product.query.get_or_404(product_id)
    if not can_remove_product(current_user, product):
        return redirect(url_for('auth.dashboard'))

    db.session.delete(product)
    db.session.commit()

    return redirect(url_for('auth.seller_dashboard'))

#seller route for removing payments
@auth.route('/seller/remove-payment/<int:order_id>', methods=['POST'])
@login_required
def remove_payment(order_id):
    current_user = User.query.filter_by(email=session.get('email')).first()
    if not current_user or current_user.role != 'seller':
        return redirect(url_for('auth.dashboard'))

    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()

    return redirect(url_for('auth.seller_payments'))
