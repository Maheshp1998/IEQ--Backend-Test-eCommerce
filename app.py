from flask import Flask, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required,create_refresh_token
from models import User, Product, Order
from flask import json
from flask_bcrypt import Bcrypt
import logging
from flask_jwt_extended import JWTManager
from mongoengine.errors import DoesNotExist
from werkzeug.security import check_password_hash
from flask_caching import Cache
from bson import ObjectId 
app = Flask(__name__)

logger = logging.getLogger(__name__)


bcrypt = Bcrypt()


jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = 'project-secret-key'  
app.config['JWT_TOKEN_LOCATION'] = ['headers', 'cookies']


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app.config['CACHE_TYPE'] = 'redis'  
app.config['CACHE_KEY_PREFIX'] = 'test01'
app.config['CACHE_DEFAULT_TIMEOUT'] = 60 

cache = Cache(app)
ORDER_CACHE_EXPIRATION=60


@app.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    password = bcrypt.generate_password_hash(password)
    email = data.get('email')
    phone_number = data.get('phone_number')

    if not username or not password or not email or not phone_number:
        return jsonify({"message": "All fields are required"}), 400

    if User.objects(username=username):
        return jsonify({"message": "Username already exists"}), 400

    user = User(username=username, password=password, email=email, phone_number=phone_number)
    user.save()
    return jsonify({"message": "User created successfully"}), 201

@app.route('/login', methods=['POST'])
@jwt_required(optional=True)
def login_user():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"message": "Username and password are required"}), 400

        user_data = User.objects.get(username=username)
        
        if bcrypt.check_password_hash(user_data.password,password):
            auth_token = create_access_token(identity=str(user_data.id), fresh=True)
            refresh_token = create_refresh_token(str(user_data.id))

            response_data = {
                "access_token": auth_token,
                "refresh_token": refresh_token,
                "message": "User Login Successfully"
            }

            return jsonify(response_data), 200

        else:
            return jsonify({"message": "Invalid username or password"}), 401

    except DoesNotExist:
        return jsonify({"message": "User Not Found"}), 404

    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500




@app.route('/create-products', methods=['POST'])
def create_product():
    try:
        data = request.get_json()
        new_product = Product(**data)
        new_product.save()
        logger.info(f"Product created: {new_product}")
        return jsonify({"message": "Product created successfully"}), 201
    except Exception as e:
        logger.error(f"Error creating product: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/get-products', methods=['GET'])
def get_all_products():
    try:
        product_list = cache.get(f'all_product')
        if product_list is None:
            products = Product.objects.all()
            product_list = [product.to_dict() for product in products]
            logger.info("Retrieved all products")
            cache.set(f'order_{order_id}', order_data, timeout=ORDER_CACHE_EXPIRATION)
        return jsonify(product_list), 200
    except Exception as e:
        logger.error(f"Error retrieving products: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/update-products/<product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = cache.get(f'product_{product_id}')
        if product is None:
            product = Product.objects.get(id=ObjectId(product_id))
            cache.set(f'order_{order_id}', order_data, timeout=ORDER_CACHE_EXPIRATION)
        logger.info(f"Retrieved product: {product}")
        return jsonify(product.to_json()), 200
    except Product.DoesNotExist:
        logger.error(f"Product not found with id: {product_id}")
        return jsonify({"message": "Product not found"}), 404
    except Exception as e:
        logger.error(f"Error retrieving product: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        product=f'product_{product_id}'
        cache.delete(product)
        data = request.get_json()
        product_id_obj = ObjectId(product_id)
        updated_product = Product.objects.get(id=product_id_obj)
        updated_product.modify(**data)
        logger.info(f"Updated product: {updated_product}")
        return jsonify({"message": "Product updated successfully"}), 200
    except Product.DoesNotExist:
        logger.error(f"Product not found with id: {product_id}")
        return jsonify({"message": "Product not found"}), 404
    except Exception as e:
        logger.error(f"Error updating product: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product=f'product_{product_id}'
        cache.delete(product)
        deleted_product = Product.objects.get(id=product_id)
        deleted_product.delete()
        logger.info(f"Deleted product: {deleted_product}")
        return jsonify({"message": "Product deleted successfully"}), 200
    except Product.DoesNotExist:
        logger.error(f"Product not found with id: {product_id}")
        return jsonify({"message": "Product not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting product: {str(e)}")
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/products-searching', methods=['GET'])
def get_products():
    query_params = request.args.to_dict()

    products = Product.objects.filter(**query_params)
    if 'sort_by' in query_params:
        sort_by = query_params.pop('sort_by')
        products = products.order_by(sort_by)

    products_data = [product.to_dict() for product in products]

    return jsonify(products_data)



@app.route('/orders', methods=['GET'])
def get_all_orders():
    try:
        order_list = cache.get('all_orders')
        if order_list is None:
            orders = Order.objects.all()
            order_list = [
                {"id": str(order.id), "quantity": order.quantity, "status": order.status} for order in orders
            ]

            cache.set('all_orders', order_list, timeout=ORDER_CACHE_EXPIRATION)
        return jsonify(order_list), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    try:
        
        order_data = cache.get(f'order_{order_id}')
        if order_data is None:
            order = Order.objects.get(id=ObjectId(order_id))
            order_data = {
                "id": str(order.id),
                "customer_name": order.customer.name if order.customer else None,
                "product_name": order.product.name if order.product else None,
                "quantity": order.quantity,
                "order_date": order.order_date.isoformat(),
                "status": order.status,
                "total_price": order.total_price
            }

            
            cache.set(f'order_{order_id}', order_data, timeout=ORDER_CACHE_EXPIRATION)
        return jsonify(order_data), 200
    except Order.DoesNotExist:
        return jsonify({"message": "Order not found"}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/create-orders', methods=['POST'])
def create_order():
    try:
        cache.delete(all_orders)
        data = request.get_json()
        customer_id = data.get('customer_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        shipping_address=data.get('shipping_address')
        customer = User.objects.get(pk=ObjectId(customer_id)) if customer_id else None
        product = Product.objects.get(pk=ObjectId(product_id)) if product_id else None
        
        if customer and product:
            total_price = product.price * quantity
            new_order = Order(customer=customer, product=product, quantity=quantity, total_price=total_price,shipping_address=shipping_address)
            new_order.save()
            cache.clear() 
            return jsonify({"message": "Order created successfully"}), 201
        else:
            return jsonify({"message": "Customer or Product not found"}), 404

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/update-orders/<order_id>', methods=['PUT'])
def update_order(order_id):
    try:
        data = request.get_json()
        quantity = data.get('quantity')
        order_id=f'oreder_{order_id}'
        cache.delete(order_id)

        order = Order.objects.get(id=ObjectId(order_id))
        order.quantity = quantity
        order.total_price = order.product.price * quantity
        order.save()
        cache.clear() 
        return jsonify({"message": "Order updated successfully"}), 200

    except Order.DoesNotExist:
        return jsonify({"message": "Order not found"}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/orders/<order_id>', methods=['DELETE'])
def delete_order(order_id):
    try:
        order_id=f'oreder_{order_id}'
        cache.delete(order_id)
        order = Order.objects.get(id=ObjectId(order_id))
        order.delete()
        cache.clear()  
        return jsonify({"message": "Order deleted successfully"}), 200

    except Order.DoesNotExist:
        return jsonify({"message": "Order not found"}), 404
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route('/orders-searching', methods=['GET'])
def serach_orders():
    
    query_params = request.args.to_dict()

    orders = Order.objects.filter(**query_params)

    if 'sort_by' in query_params:
        sort_by = query_params.pop('sort_by')
        orders = orders.order_by(sort_by)

    orders_data = [{
        'customer_name': order.customer.name,
        'product_name': order.product.name,
        'quantity': order.quantity,
        'order_date': order.order_date
    } for order in orders]

    return jsonify(orders_data)


if __name__ == '__main__':
    app.run(debug=True)
