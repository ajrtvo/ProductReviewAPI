import unittest
from endpoints import app, db, Products, Review, Like, filter_products
import datetime

class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

        # Create some test data
        product1 = Products(name='Product 1', category='Category 1', review_count=0, price=10.99, currency='USD', image_url='http://example.com/image1', details='Details 1', overall_rating=0, date_added =datetime.datetime.now())
        product2 = Products(name='Product 2', category='Category 2', review_count=0, price=9.99, currency='USD', image_url='http://example.com/image2', details='Details 2', overall_rating=0, date_added =datetime.datetime.now())
        review1 = Review(author_name='Author 1', author_avatar='http://example.com/avatar1', author_email='author1@example.com', title='Title 1', content='Content 1', rating=5, verified=True, product_id=1)
        review2 = Review(author_name='Author 2', author_avatar='http://example.com/avatar2', author_email='author2@example.com', title='Title 2', content='Content 2', rating=4, verified=True, product_id=2)
        like1 = Like(review_id=1)
        like2 = Like(review_id=2)
        like3 = Like(review_id=3)
        db.session.add_all([product1, product2, review1, review2, like1, like2, like3])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_get_product(self):
        response = self.app.get('/products/Product 1')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['name'], 'Product 1')
        self.assertEqual(len(data['reviews']), 1)
        self.assertEqual(data['reviews'][0]['like_count'], 1)

    def test_filter_products(self):
        products = Products.query.all()
        filtered = filter_products(products, 'product', 'category 1')
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, 'Product 1')
        filtered = filter_products(products, '2', 'category 2')
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].name, 'Product 2')

    def test_add_product(self):
        data = {
            'name': 'John Doe',
            'category': 'category 1',
            'price': 15,
            'currency': 'PHP',
            'details': 'Test',
            'image_url  ': 'http://test.com/avatar.jpg'
        }
        response = self.app.post('/products', json=data)
        self.assertEqual(response.status_code, 201)

    def test_add_review(self):
        data = {
            'author_name': 'John Doe',
            'author_email': 'johndoe@example.com',
            'author_avatar': 'http://test.com/avatar.jpg',
            'title': 'Great product!',
            'content': 'I love this product, it works great!',
            'rating': 5,
            'verified': True
        }
        response = self.app.post('/reviews/Product 1', json=data)
        self.assertEqual(response.status_code, 201)

        data = {
            'author_name': 'John Doe',
            'author_email': 'johndoe@example.com',
            'author_avatar': 'http://test.com/avatar.jpg',
            'title': 'Great product!',
            'content': 'I love this product, it works great!',
            'rating': 6, # Invalid rating
            'verified': True
        }
        response = self.app.post('/reviews/Product 1', json=data)
        self.assertEqual(response.status_code, 400)

    def test_like_review(self):
        product = Products(name='Product 1', category='Category 1', price=10.99, currency='USD', details='Details 1', image_url='https://example.com/image1.jpg',date_added =datetime.datetime.now())
        db.session.add(product)
        review = Review(author_name='Author 1', author_email='author1@example.com', title='Title 1', content='Content 1', rating=4, verified=True, product_id=1)
        db.session.add(review)
        db.session.commit()
        
        response = app.test_client().post(f'/reviews/{product.name}/{review.id}')
        
        self.assertEqual(response.status_code, 200)
        
        expected_data = {'product_name': product.name, 'review_id': review.id, 'likes_count': 2}
        self.assertEqual(response.json, expected_data)
        
        liked_review = Like.query.filter_by(review_id=review.id).first()
        self.assertIsNotNone(liked_review)

    def test_update_review(self):
        product = Products(name='Product 1', category='Category 1', price=10.99, currency='USD', details='Details 1', image_url='https://example.com/image1.jpg',date_added =datetime.datetime.now())
        db.session.add(product)
        review = Review(author_name='Author 1', author_email='author1@example.com', title='Title 1', content='New Content', rating=4, verified=True, product_id=1)
        db.session.add(review)
        db.session.commit()
        data = {
            "author_name": "AJ Test",
            "author_email": "aj1@gmail.com",
            "title": "Yum",
            "content": "Green apples",
            "rating": 3
        }
        response = app.test_client().put(f'/reviews/{product.name}/{review.id}', json=data)
        
        self.assertEqual(response.status_code, 200)
        
        liked_review = Like.query.filter_by(review_id=review.id).first()
        self.assertIsNotNone(liked_review)


if __name__ == '__main__':
    unittest.main()