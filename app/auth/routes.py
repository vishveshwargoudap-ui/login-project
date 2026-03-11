from flask import render_template, request, redirect, session, url_for, jsonify,flash,current_app
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from app.models import User,Product,Order,OrderItem
from app.extensions import db,mail
from .decorators import login_required
from.import auth
from cloudinary.uploader import upload
from app.cloudinary_config import *
from flask_mail import Message
import traceback
from threading import Thread
from app import mail
import smtplib
from email.mime.text import MIMEText

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

        existing_user=User.query.filter_by(email=email).first()
        if existing_user:
            return render_template("register.html",error="Email already registered")

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

    cart = session.get('cart', [])

    cart_items = []
    grand_total = 0

    for item in cart:
        item_total = float(item['price']) * int(item.get('qty', 1))
        grand_total += item_total

        cart_items.append({
            "product_id": item['id'],
            "name": item['name'],
            "price": item['price'],
            "image": item['image'],
            "qty": item.get('qty', 1)
        })

    return render_template(
        'cart.html',
        user=user,
        cart_items=cart_items,
        grand_total=grand_total
    )
       
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
        user.village = (request.form.get('village') or '').strip()
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

def send_order_email(user, payment_mode_raw):
            try:
                msg = Message(
                    subject="New Order Received",

        recipients=[current_app.config.get("MAIL_USERNAME")]
                )

                msg.body = f"""
New Order Received

Customer: {user.email}
Payment Mode: {payment_mode_raw}
Phone Number: {user.phone}

Check seller dashboard for details.
"""

                mail.send(msg)
                print("Email sent successfully")

            except Exception as e:
                print("EMAIL FAILED:", e)
#buyer route for placing order
@auth.route('/place-order', methods=['POST'])
@login_required
def place_order():
    try:
        # ---- Check login ----
        if 'email' not in session:
            return jsonify({'ok': False, 'message': 'Please login first.'}), 401

        user = User.query.filter_by(email=session['email']).first()
        if not user:
            return jsonify({'ok': False, 'message': 'User not found.'}), 404

        if user.role == 'seller':
            return jsonify({'ok': False, 'message': 'Sellers cannot place orders.'}), 403

        # ---- Read JSON ----
        data = request.get_json()
        if not data:
            return jsonify({'ok': False, 'message': 'Invalid request data.'}), 400

        payment_mode_raw = (data.get('payment_mode') or '').strip().lower()
        transaction_id = (data.get('transaction_id') or '').strip()

        cart_items = session.get('cart', [])
        if not cart_items:
            return jsonify({'ok': False, 'message': 'Your cart is empty.'}), 400

        if payment_mode_raw not in {'upi', 'cash'}:
            return jsonify({'ok': False, 'message': 'Invalid payment mode.'}), 400

        if payment_mode_raw == 'upi' and not transaction_id:
            return jsonify({'ok': False, 'message': 'Transaction ID required for UPI.'}), 400

        if not user.phone:
            return jsonify({'ok': False, 'message': 'Add phone number in profile first.'}), 400

        # ---- Process Cart ----
        total_amount = 0
        order_items = []

        for item in cart_items:
            product_id = item.get('id')
            quantity = int(item.get('qty', 1))  # make sure key is correct

            product = Product.query.get(int(product_id))
            if not product:
                continue

            total_amount += quantity * float(product.price)

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price
                )
            )

        if not order_items:
            return jsonify({'ok': False, 'message': 'No valid items found.'}), 400

        # ---- Create Order ----
        payment_mode = 'Online Payment' if payment_mode_raw == 'upi' else 'Offline Payment'

        order = Order(
            user_id=user.id,
            total_amount=total_amount,
            payment_mode=payment_mode,
            transaction_id=transaction_id if payment_mode_raw == 'upi' else None
        )

        db.session.add(order)
        db.session.flush()  # get order.id before commit

        # ---- Attach Items ----
        for oi in order_items:
            oi.order_id = order.id
            db.session.add(oi)

            db.session.commit()
            
            send_order_email(user,payment_mode_raw)
        
        # ---- Clear Cart ----
        session['cart'] = []
        session.modified = True

        return jsonify({
            'ok': True,
            'order_id': order.id,
            'redirect_url': url_for('auth.payment', order_id=order.id)
        })

    except Exception as e:
        db.session.rollback()
        print("PLACE ORDER ERROR:", e)
        return jsonify({'ok': False, 'message': 'Internal server error'}), 500
    
@auth.route('/confirm-payment/<int:order_id>', methods=['POST'])
@login_required
def confirm_payment(order_id):
    order= Order.query.get_or_404(order_id)

    method=request.form.get("method")
    transaction_id=request.form.get("transaction_id")

    order.payment_mode="Online Payment" if method=="upi" else "Offline Payment"

    if method == "upi" and not transaction_id:
        flash("Transaction ID is required for UPI payments.", "error")
        return redirect(url_for('auth.payment', order_id=order_id))
    
    order.payment_mode = "Online Payment" if method == "upi" else "Offline Payment"
    order.transaction_id = transaction_id if method == "upi" else None

    db.session.commit()


    flash("Payment details updated successfully.", "success")
    return redirect(url_for('auth.order_details', order_id=order.id))

    
    
@auth.route('/payment/<int:order_id>')
@login_required
def payment(order_id):
        if 'email' not in session:
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(email=session['email']).first()
        if not user:
            return redirect(url_for('auth.login'))

        order = Order.query.get(order_id)
        if not order:
            return redirect(url_for('auth.dashboard'))
        if order.user_id != user.id:
            return redirect(url_for('auth.dashboard'))

        return render_template('payment.html',order=order,user=user)
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
    if order.user_id != user.id:
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

    seller = User.query.filter_by(email=session['email']).first()

    if not can_manage_products(seller):
        return redirect(url_for('auth.dashboard'))

    # Get seller's products
    seller_products = Product.query.filter_by(seller_id=seller.id).all()
    product_ids = [p.id for p in seller_products]

    if not product_ids:
        return render_template(
            'seller_payment.html',
            user=seller,
            orders=[],
            buyers_by_id={}
        )

    # Get order items for seller products
    order_items = OrderItem.query.filter(
        OrderItem.product_id.in_(product_ids)
    ).all()
    order_products = {}
    for item in order_items:
        if not item.product:
            continue
        order_products.setdefault(item.order_id, [])
        order_products[item.order_id].append(f"{item.product.name} x{item.quantity}")

    # Get related orders
    order_ids = list(set([item.order_id for item in order_items]))
    orders = Order.query.filter(Order.id.in_(order_ids)).all()
    buyer_ids = list(set([order.user_id for order in orders]))
    buyers = User.query.filter(User.id.in_(buyer_ids)).all() if buyer_ids else []
    buyers_by_id = {buyer.id: buyer for buyer in buyers}

    return render_template(
        'seller_payment.html',
        user=seller,
        orders=orders,
        buyers_by_id=buyers_by_id,
        order_products=order_products,
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

@auth.route('/update-cart-quantity', methods=['POST'])
@login_required
def update_cart_quantity():

    item_id = request.form.get("item_id")
    action = request.form.get("action")

    cart = session.get('cart', [])

    for item in cart:
        if str(item.get("id")) == str(item_id):
            if action == "increase":
                item['qty'] += 1
            elif action == "decrease":
                if item['qty'] > 1:
                    item['qty'] -= 1
                else:
                    cart.remove(item)
            break

    session['cart'] = cart
    session.modified = True

    return redirect(url_for('auth.cart'))
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

@auth.route("/test-email")
def test_email():
    try:
        sender = current_app.config.get("MAIL_USERNAME")
        password = current_app.config.get("MAIL_PASSWORD")

        msg = MIMEText("This is a test email from Flask.")
        msg["Subject"] = "Test Email"
        msg["From"] = sender
        msg["To"] = sender

        with smtplib.SMTP("smtp-relay.brevo.com", 2525, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, [sender], msg.as_string())

        return "Email sent successfully"

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Email failed: {str(e)}"