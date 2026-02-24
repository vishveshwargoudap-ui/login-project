from flask import render_template, request, redirect, session, url_for, jsonify,flash
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
        products = Product.query.filter_by(seller_id=user.id).all() if user.role == 'seller' else Product.query.all()
        return render_template(
            'dashboard.html',
            user=user,
            products=products,
            can_add_product=can_manage_products(user),
            show_payments_button=user.role == 'seller'
        )

    return redirect('/login')

@auth.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():

    data = request.get_json(force=True)
    if not data:
        return jsonify({"message": "no data received"}), 400
    id = data.get("id")
    name = data.get("name")
    price = data.get("price")
    image = data.get("image")

    if not name:
        return jsonify({"message":"product name is required"}),400

    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append({
        "id": id,
        "name": name,
        "price": float(data['price']),
        "qty": 1,
        "image": image
    })

    session.modified = True

    return jsonify({"message": f"{name} added to cart"})

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
    
    cart_items =session.get('cart',[])
    grand_total = sum(item['price']*item['qty']for item in cart_items)

    return render_template('cart.html', user=user, cart_items=cart_items, grand_total=grand_total)
       
#buyer route for payments
#removed payments from here (due to confusion for seller and buyer payments) and added in place-order route

#seller route for dashboard
@auth.route('/seller-dashboard')
@login_required
def seller_dashboard():
    if 'email' not in session:
        return redirect('/login')

    user = User.query.filter_by(email=session['email']).first()
    if not can_manage_products(user):
        return redirect(url_for('auth.dashboard'))
    
    seller_products = Product.query.filter_by(seller_id=user.id).all()
    seller_items=(db.session.query(OrderItem).join(Product).filter(Product.seller_id==user.id).all())
    return render_template(
        'dashboard.html',
        user=user,
        products=seller_products,
        orders=seller_items,
        show_payments_button=True,
        can_add_product=True,
        is_seller_view=True
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

@auth.route('/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    item_id = request.form.get('id')

    cart = session.get('cart', [])
    cart = [item for item in cart if str(item.get('id')) != str(item_id)]

    session['cart'] = cart
    session.modified = True

    return redirect(url_for('auth.cart'))


#buyer route for placing order
@auth.route('/place-order', methods=['POST'])
@login_required
def place_order():

    if 'email' not in session:
        flash('please login')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=session['email']).first()
    if not user:
       flash('user not found')
       return redirect(url_for('auth.login'))
    if user.role == 'seller':
        flash('seller can not place order ')
        return redirect(url_for('auth.dashboard'))

    payment_mode_raw = (request.form.get('method')or'').strip().lower()
    transaction_id = (request.form.get('utr') or '').strip()
    cart_items=session.get('cart',[])
    if not cart_items:
        flash('your cart is empty')
        return redirect(url_for('auth.cart'))

    if payment_mode_raw not in {'upi', 'cash'}:
        flash('Invalid payment mode.')
        return redirect(url_for('auth.payment'))

    if payment_mode_raw == 'upi' and not transaction_id:
        flash('Transaction ID is required for online payment.')
        return redirect(url_for('auth.payment'))

    buyer_phone = (user.phone or"").strip()
    if not buyer_phone:
        flash('Please add your phone number in profile before ordering.')
        return redirect(url_for('auth.profile'))

    total_amount = 0
    order_items = []
    for item in cart_items:
       product_id = item.get('id')
       quantity = int(item.get('qty', 1))

       product= Product.query.get(product_id)
       if not product:
              continue
       
       total_amount += quantity * float(product.price)

       order_items.append(OrderItem(
           product_id=product.id,
           quantity=quantity,
           price=product.price
       ))

    if not order_items:
        flash('no valid items in cart')
        return redirect(url_for('auth.cart'))

    if payment_mode_raw =='upi':
        payment_mode="Manual UPI"
        payment_status="Verification pending"
    else:
        payment_mode="pay on delivery"
        payment_status="Pending"

        order=Order(
            user_id=user.id,
            total_amount=total_amount,
            payment_mode=payment_mode,
            payment_status=payment_status,
            transaction_id=transaction_id if
            payment_mode_raw == 'upi'else None,
            order_status="placed"

       
    )
    db.session.add(order)
    db.session.flush()  # Ensure order is assigned an ID before adding items

    for oi in order_items:
        oi.order_id = order.id
        db.session.add(oi)

    db.session.commit()
    session['cart'] = []
    session.modified = True

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
    if user.role != 'seller' and order.user_id != user.id:
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

    orders = Order.query.filter_by(user_id=user.id).all()
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

