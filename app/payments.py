from flask import Blueprint, request, jsonify
import razorpay
import hmac
import hashlib

payment_bp = Blueprint("payment", __name__)

# 🔴 REPLACE WITH YOUR TEST KEYS FROM DASHBOARD
RAZORPAY_KEY_ID = "rzp_test_xxxxxxxxx"
RAZORPAY_SECRET = "xxxxxxxxxxxxxxxx"

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_SECRET))


# ---------------- CREATE ORDER ----------------
@payment_bp.route("/create_order", methods=["POST"])
def create_order():

    # amount in paise (₹100 = 10000)
    amount = 500 * 100   # temporary fixed amount for testing

    order = client.order.create({
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    })

    return jsonify({
        "order_id": order["id"],
        "amount": amount,
        "key": RAZORPAY_KEY_ID
    })


# ---------------- VERIFY PAYMENT ----------------
@payment_bp.route("/verify_payment", methods=["POST"])
def verify_payment():

    data = request.json

    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    generated_signature = hmac.new(
        bytes(RAZORPAY_SECRET, 'utf-8'),
        bytes(razorpay_order_id + "|" + razorpay_payment_id, 'utf-8'),
        hashlib.sha256
    ).hexdigest()

    if generated_signature == razorpay_signature:
        return jsonify({"status": "Payment Verified"})
    else:
        return jsonify({"status": "Invalid Signature"}), 400