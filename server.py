from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
import json

app = Flask(__name__)

# Enable CORS for all domains
CORS(app)

# Connect to MongoDB running in the Docker container
client = MongoClient('mongodb://mongodb:27017/')  # 'mongodb' is the service name in docker-compose
db = client['mydatabase']  # Use the database named 'mydatabase'
carts_collection = db['carts']  # Use the 'carts' collection
products_collection = db['products']

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/manage_cart')
def manage_cart_page():
    return render_template('add-to-cart.html')

# curl -X GET http://localhost:5000/api/carts
@app.route('/api/carts')
def get_carts():
    # Retrieve all carts from the MongoDB collection
    carts = carts_collection.find()  # This returns a cursor, not a list

    # Convert the MongoDB documents to a list of dictionaries
    carts_list = list(carts)

    # Convert ObjectId to string for serialization
    for cart in carts_list:
        cart['_id'] = str(cart['_id'])  # MongoDB _id is ObjectId, so we convert it to string

    return jsonify(carts_list)

@app.route('/api/carts', methods=['POST', 'PUT'])
def manage_cart():
    data = request.get_json()

    # Validate input
    if 'user_id' not in data or 'items' not in data:
        return jsonify({'error': 'Invalid input. user_id and items are required.'}), 400

    user_id = int(data['user_id'])
    # Check if a cart for this user exists
    existing_cart = carts_collection.find_one({'user_id': user_id})

    if request.method == 'POST':
        if existing_cart:
            # If the cart exists, update it
            carts_collection.update_one(
                {'user_id': user_id},
                {'$set': {'items': data['items']}}
            )
            return jsonify({'message': 'Cart updated'}), 200
        else:
            # If the cart doesn't exist, create a new one
            new_cart = {
                'user_id': user_id,
                'items': data['items']
            }
            carts_collection.insert_one(new_cart)
            return jsonify({'message': 'Cart created'}), 201

# curl -X DELETE http://localhost:5000/api/carts/1
@app.route('/api/carts/<int:cart_id>', methods=['DELETE'])
def delete_cart(cart_id):
    # Delete the cart document where the 'user_id' matches the provided cart_id
    result = carts_collection.delete_one({'user_id': cart_id})

    if result.deleted_count > 0:
        return jsonify({'message': 'Cart deleted'}), 200
    else:
        return jsonify({'message': 'Cart not found'}), 404

# Get all products
@app.route('/api/products')
def get_products():
    # Retrieve all products from the MongoDB collection
    products = products_collection.find()  # This returns a cursor, not a list

    # Convert the MongoDB documents to a list of dictionaries
    products_list = list(products)

    # Convert ObjectId to string for serialization
    for product in products_list:
        product['_id'] = str(product['_id'])  # MongoDB _id is ObjectId, so we convert it to string

    return jsonify(products_list)

# Get a single product by ID
@app.route('/api/products/<int:product_id>')
def get_product(product_id):
    # Retrieve a product by its ID from MongoDB
    product = products_collection.find_one({'id': product_id})

    if product:
        # Convert ObjectId to string for serialization
        product['_id'] = str(product['_id'])
        return jsonify(product)
    else:
        return jsonify({'message': 'Product not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)