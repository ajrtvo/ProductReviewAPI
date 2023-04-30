from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc, func
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
db = SQLAlchemy(app)


class Products(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(255), nullable=False)
    review_count = db.Column(db.Integer, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    date_added = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    details = db.Column(db.String(500), nullable=False)
    overall_rating = db.Column(db.Float, nullable=True)
    reviews = db.relationship('Review', backref='products', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(50))
    author_email = db.Column(db.String(100))
    author_avatar = db.Column(db.String(100))
    title = db.Column(db.String(100))
    content = db.Column(db.Text())
    rating = db.Column(db.Integer())
    verified = db.Column(db.Boolean, default=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    likes = db.relationship('Like', backref='review', lazy=True)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)


@app.route('/products')
def get_products():
    search = request.args.get('search')
    category = request.args.get('category')
    
    products = Products.query.order_by(desc(Products.date_added)).all()
    
    if search or category:
        products = filter_products(products, search, category)
    
    result = []
    for product in products:
        result.append({
            'image_url': product.image_url,
            'name': product.name,
            'category': product.category,
            'review_count': len(product.reviews),
        })
        
    return jsonify(result), 200

@app.route('/products/<string:name>', methods=['GET'])
def get_product(name):
    product = Products.query.filter_by(name=name).first_or_404()

    reviews = Review.query.filter_by(product_id=product.id)\
    .order_by(desc(func.count(Like.id)))\
    .outerjoin(Like)\
    .group_by(Review.id)\
    .all()
    review_list = []
    for review in reviews:
        review_list.append({
            'author_name': review.author_name,
            'author_avatar': review.author_avatar,
            'author_email': review.author_email,
            'title': review.title,
            'content': review.content,
            'rating': review.rating,
            'verified': review.verified,
            'like_count': len(review.likes)
        })

    rating_count = [0] * 5
    total_rating = 0
    for review in product.reviews:
        rating_count[review.rating - 1] += 1
        total_rating += review.rating
    if len(product.reviews) > 0:
        overall_rating = round(total_rating / len(product.reviews), 1)
    else:
        overall_rating = 0

    result = {
        'name': product.name,
        'category': product.category,
        'review_count': product.review_count,
        'price_and_currency': product.currency + " " + str(product.price),
        'image_url': product.image_url,
        'details': product.details,
        'overall_ratings': overall_rating,
        'date_added': str(product.date_added),
        'reviews': review_list,
        'review_count': len(product.reviews)
    }

    return jsonify(result), 200


def filter_products(products, search, category):
    filtered = []
    for product in products:
        if search and search.lower() not in product.name.lower():
            continue
        if category and category.lower() != product.category.lower():
            continue
        filtered.append(product)
    return filtered

@app.route('/products', methods=['POST'])
def add_product():
    data = request.get_json()
    name = data.get('name')
    category = data.get('category')
    price=data.get('price')
    currency=data.get('currency')
    details=data.get('details')
    image_url = data.get('image_url')
    date_added=datetime.datetime.now()

    new_product = Products(name=name, category=category, price=price, currency=currency, details=details, image_url=image_url,date_added=date_added)

    db.session.add(new_product)
    db.session.commit()

    result = {
        'id': new_product.id,
        'name': new_product.name,
        'category': new_product.category,
        'price': new_product.price,
        'currency': new_product.currency,
        'details': new_product.details,
        'image_url': new_product.image_url,
        'date_added': new_product.date_added
    }

    return jsonify(result), 201
    
@app.route('/reviews/<string:name>', methods=['POST'])
def add_review(name):
    product = Products.query.filter_by(name=name).first_or_404()
    data = request.get_json()
    author_name = data.get('author_name')
    author_email = data.get('author_email')
    author_avatar= data.get('author_avatar')
    title= data.get('title')
    content= data.get('content')
    rating = data.get('rating')
    verified= data.get('verified')
    product_id = product.id
    new_review = Review(author_name=author_name, author_email=author_email, author_avatar=author_avatar, title=title, content=content, rating=rating,verified=verified,product_id=product_id)

    db.session.add(new_review)
    db.session.commit()

    result = {
        'author_name': new_review.author_name,
        'author_email': new_review.author_email,
        'author_avatar': new_review.author_avatar,
        'title': new_review.title,
        'content': new_review.content,
        'rating': new_review.rating,
        'verified': new_review.verified
    }

    if rating < 1 or rating > 5:
        return jsonify({'message': 'Rating must be between 1 and 5'}), 400
    
    return jsonify(result), 201

@app.route('/reviews/<string:name>/<int:id>', methods=['POST'])
def like_review(name,id):
    product = Products.query.filter_by(name=name).first_or_404()
    reviews = Review.query.filter_by(product_id=product.id,id=id).first_or_404()
    like_review = Like(review_id=id)
    db.session.add(like_review)
    db.session.commit()

    result = {
        'product_name': name,
        'review_id': id,
        'likes_count' : len(reviews.likes)
    }

    return jsonify(result), 200

@app.route('/reviews/<string:name>/<int:id>', methods=['PUT'])
def update_review(name,id):
    product = Products.query.filter_by(name=name).first_or_404()
    review = Review.query.filter_by(product_id=product.id,id=id).first_or_404()
    data = request.get_json()
    review.author_name = data.get('author_name')
    review.author_email = data.get('author_email')
    review.title= data.get('title')
    review.content= data.get('content')
    review.rating = data.get('rating')

    db.session.commit()

    result = {
        'author_name': review.author_name,
        'author_email': review.author_email,
        'title': review.title,
        'content': review.content,
        'rating': review.rating,
    }

    if review.rating < 1 or review.rating > 5:
        return jsonify({'message': 'Rating must be between 1 and 5'}), 400

    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=True)