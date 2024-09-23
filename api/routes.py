from flask import Flask, render_template, request, session, redirect, url_for, Blueprint, Response, flash
from sql_queries import SqlQueries
from app import app
from typing import Union, Tuple
from mysql.connector import Error

FlaskReturnType = Union[
    str,
    Response,
    Tuple[str, int],
    Tuple[str, int, dict],
    dict  # For jsonify() which returns a Response with JSON data
]

sql_queries = SqlQueries()

@app.route('/')
def home() -> FlaskReturnType:
    return render_template('base.html')

@app.route('/orders')
def orders() -> FlaskReturnType:
    if 'UserID' not in session:
        return redirect(url_for('login'))

    result = sql_queries.orders(session['UserID'])
    
    return render_template('orders.html', orders=result)

@app.route('/order/<int:order_id>')
def order_details(order_id: int) -> FlaskReturnType:
    if 'UserID' not in session:
        return redirect(url_for('login'))

    result = sql_queries.order_details(order_id, session['UserID'])

    if result:
        return render_template('order_details.html', order=result[0], items=result)
    else:
        return "Order not found", 404

@app.route('/user_message_selection')
def user_message_selection() -> FlaskReturnType:
    if 'UserID' not in session:
        return redirect(url_for('login'))
    result = sql_queries.user_message_selection(session['UserID'])
    return render_template('user_message_selection.html', users=result)

@app.route('/message', methods=['GET', 'POST'])
def message() -> FlaskReturnType:
    if 'UserID' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        message_input = request.form['message']
        receiver_id = request.form['receiver_id']
        receiver_name = request.form['receiver_name']
        sql_queries.message_send(session['UserID'], receiver_id, message_input)
        return redirect(url_for('message', user_name=receiver_name))
    other_username = request.args.get('user_name')
    other_userid = sql_queries.get_id_from_name(other_username)[0]['UserID']
    this_userid = session['UserID']
    result = sql_queries.message_get(this_userid, other_userid)
    return render_template('message.html', other_username=other_username, other_userid=other_userid, messages=result)

    

@app.route('/shopping_cart', methods=['GET', 'POST'])
def shopping_cart() -> FlaskReturnType:
    if 'UserID' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'shopping_cart' not in session:
            session['shopping_cart'] = []
        product_id = request.form['product_id']
        # There can max be 1 index, since ProductID is unique
        indices = [i for i, item in enumerate(session['shopping_cart']) if int(item['ProductID']) == int(product_id)]
        if indices:
            session['shopping_cart'][indices[0]]['Amount'] += 1
        else:
            result = sql_queries.minimal_product_details(product_id)
            result[0]['Amount'] = 1
            session['shopping_cart'].append(result[0])
        session.modified = True
        flash("Product added to cart")
        app.logger.info(f"{session['UserID']} added Product {product_id} to cart")
    
    return render_template('shopping_cart.html', data=session['shopping_cart'])

@app.route('/checkout', methods=['POST'])
def checkout():
    cart_data = session['shopping_cart']
    if not cart_data:
        return "Order failed on empty cart", 404
    total_amount = sum([float(i['Price'])*int(i['Amount']) for i in cart_data])
    order_status = 'Pending'
    try:
        order_id = sql_queries.new_order(session['UserID'], total_amount, order_status, cart_data)[0]
    except Error as e:
        flash("Order failed! Please try again")
        app.logger.error(f"{session['UserID']} failed to make a new Order")
        return redirect(url_for('home'))
    flash("Order successful")
    app.logger.info(f"{session['UserID']} made a new Order with ID: {order_id}")
    return redirect(url_for('home'))
    

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        address = request.form['address']
        username = request.form['username']
        password = request.form['password']
        
        sql_queries.add_user(username, password, email, first_name, last_name, address, phone_number)

        return redirect(url_for('login'))
    
    return render_template('sign_up.html')

@app.route('/account')
def account() -> FlaskReturnType:
    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    user_id = session['UserID']

    # Fetch user details
    user_data = sql_queries.account(user_id)
    if user_data:
        user_data = user_data[0] 
    
    # Fetch user subscriptions
    subscriptions = sql_queries.get_user_subscriptions(user_id)

    return render_template('account.html', data=user_data, subscriptions=subscriptions)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile() -> FlaskReturnType:
    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        first_name = request.form['FirstName']
        last_name = request.form['LastName']
        email = request.form['Email']
        address = request.form['Address']
        phone_number = request.form['PhoneNumber']

        sql_queries.edit_profile(first_name, last_name, email, address, phone_number, session['UserID'])

        return redirect(url_for('account'))

    result = sql_queries.account(session['UserID'])
    
    return render_template('edit_profile.html', data=result[0])


@app.route('/login', methods=['POST', 'GET'])
def login() -> FlaskReturnType:
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        result = sql_queries.login(username, password)
        if result:
            session['UserID'] = result[0]['UserID']
            session['shopping_cart'] = []
            flash('Login successful')
            app.logger.info(f"{username} successfully logged in")
            return redirect(url_for('home'))
        else:
            flash('Username or password is wrong', 'warning')
            app.logger.error(f"Invalid login attempt from {username}")
    return render_template('login.html')

@app.route('/logout')
def logout() -> FlaskReturnType:
    session.pop('UserID', None)
    return redirect(url_for('home'))


@app.route('/search_product', methods=['GET'])
def search_product() -> FlaskReturnType:
    search = request.args.get('search', '').strip()
    seller_id = request.args.get('seller_id', None)
    category_id = request.args.get('category_id', None)
    min_price = request.args.get('min_price', None)
    max_price = request.args.get('max_price', None)

    try:
        seller_id = int(seller_id) if seller_id else None
        category_id = int(category_id) if category_id else None
        min_price = float(min_price) if min_price and min_price != '' else None
        max_price = float(max_price) if max_price and max_price != '' else None
    except ValueError:
        return "Invalid filter values", 400

    result = sql_queries.search_product(search, seller_id, category_id, min_price, max_price)
    categories = sql_queries.product_categories()
    
    return render_template('product_table.html', data=result, search_query=search, seller_id=seller_id, category_id=category_id, min_price=min_price, max_price=max_price, categories=categories)


@app.route('/product_details/<int:product_id>')
def product_detail(product_id: int) -> FlaskReturnType:
    product = sql_queries.product_details(product_id)
    reviews = sql_queries.get_reviews(product_id)
    
    if product:
        order = request.args.get('order')
        wishlist = request.args.get('wishlist', type=bool)
        order = int(order) if order and order.isdigit() else None
        return render_template('product_detail.html', product=product[0], reviews=reviews, order=order, wishlist=wishlist)
    else:
        return "Product not found", 404

@app.context_processor
def inject_user_info() -> dict:
    user_id = session.get('UserID')
    is_authenticated = user_id is not None
    is_seller = False

    if is_authenticated:
        is_seller = sql_queries.is_user_seller(user_id)
    
    return dict(is_authenticated=is_authenticated, is_seller=is_seller)

@app.route('/wishlist')
def wishlist() -> FlaskReturnType:
    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    result = sql_queries.get_wishlist_items(session['UserID'])
    return render_template('wishlist.html', items=result)

@app.route('/add_to_wishlist/<int:product_id>', methods=['POST'])
def add_to_wishlist(product_id: int) -> FlaskReturnType:
    if 'UserID' not in session:
        return redirect(url_for('login'))

    wishlist = sql_queries.get_wishlist(session['UserID'])

    if not wishlist:
        return "No wishlist found", 404

    wishlist_id = wishlist[0]['WishlistID']

    if sql_queries.product_in_wishlist(wishlist_id, product_id):
        flash('This product is already in your wishlist.', 'info')
        return redirect(url_for('wishlist'))

    sql_queries.add_product_to_wishlist(wishlist_id, product_id)
    flash('Product added to wishlist!', 'success')
    return redirect(url_for('wishlist'))

@app.route('/remove_from_wishlist/<int:product_id>', methods=['POST'])
def remove_from_wishlist(product_id: int) -> FlaskReturnType:
    if 'UserID' not in session:
        return redirect(url_for('login'))

    wishlist = sql_queries.get_wishlist(session['UserID'])

    if not wishlist:
        app.logger.error(f"{session['UserID']} tried to access invalid wishlist")
        return "No wishlist found", 404

    wishlist_id = wishlist[0]['WishlistID']

    if sql_queries.product_in_wishlist(wishlist_id, product_id):
        sql_queries.remove_product_from_wishlist(wishlist_id, product_id)
        app.logger.info('sdf')
        flash('Product removed from wishlist!', 'success')
    else:
        flash('Product not found in your wishlist.', 'error')

    return redirect(url_for('wishlist'))


@app.route('/seller_dashboard')
def seller_dashboard() -> FlaskReturnType:
    if 'UserID' not in session or not sql_queries.is_user_seller(session['UserID']):
        return redirect(url_for('login'))
    
    user_id = session['UserID']
    
    seller = sql_queries.get_seller_details_user(user_id)
    
    seller_id = seller['SellerID']

    products = sql_queries.get_seller_products(seller_id)
    
    orders = sql_queries.orders_for_seller(seller_id)
    
      # Fetch statistics
    total_products_sold = sql_queries.total_products_sold(seller_id, '2024-01-01', '2024-12-31')
    total_revenue = sql_queries.total_revenue(seller_id, '2024-01-01', '2024-12-31')
    total_orders = sql_queries.total_orders(seller_id, '2024-01-01', '2024-12-31')
    total_quantity_sold_per_product = sql_queries.total_quantity_sold_per_product(seller_id, '2024-01-01', '2024-12-31')
    average_order_price = sql_queries.average_order_price(seller_id, '2024-01-01', '2024-12-31')
    total_distinct_products_sold = sql_queries.total_distinct_products_sold(seller_id, '2024-01-01', '2024-12-31')
    most_sold_product = sql_queries.most_sold_product(seller_id, '2024-01-01', '2024-12-31')
    highest_revenue_product = sql_queries.highest_revenue_product(seller_id, '2024-01-01', '2024-12-31')
    average_product_rating = sql_queries.average_product_rating(seller_id)
    total_reviews_received = sql_queries.total_reviews_received(seller_id)

    return render_template('seller_dashboard.html', 
                           products=products, 
                           orders=orders,
                           total_products_sold=total_products_sold,
                           total_revenue=total_revenue,
                           total_orders=total_orders,
                           total_quantity_sold_per_product=total_quantity_sold_per_product,
                           average_order_price=average_order_price,
                           total_distinct_products_sold=total_distinct_products_sold,
                           most_sold_product=most_sold_product,
                           highest_revenue_product=highest_revenue_product,
                           average_product_rating=average_product_rating,
                           total_reviews_received=total_reviews_received)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product() -> FlaskReturnType:
    if 'UserID' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        product_name = request.form['product_name']
        description = request.form['description']
        price = request.form['price']
        stock_quantity = request.form['stock_quantity']
        category_id = request.form['category']
        product_image = request.files['product_image']
        if product_image and product_image.filename != '':
            product_image = product_image.read()
        else:
            product_image = None

        sql_queries.add_product(session['UserID'], product_name, description, price, stock_quantity, category_id, product_image)

        flash('Product added successfully', 'success')
        return redirect(url_for('seller_dashboard'))

    categories = sql_queries.product_categories()

    return render_template('add_product.html', categories=categories)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id: int) -> FlaskReturnType:
    if 'UserID' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        product_name = request.form['product_name']
        description = request.form['description']
        price = request.form['price']
        stock_quantity = request.form['stock_quantity']
        category_id = request.form['category_id']
        product_image = request.files['product_image']
        if product_image and product_image.filename != '':
            product_image = product_image.read()
        else:
            product_image = None

        sql_queries.update_product(product_id, product_name, description, price, stock_quantity, category_id, product_image)

        flash('Product updated successfully', 'success')
        return redirect(url_for('seller_dashboard'))

    product = sql_queries.product_details(product_id)
    

    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('seller_dashboard'))
    
    categories = sql_queries.product_categories()

    return render_template('edit_product.html', product=product[0], categories=categories)


@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if 'UserID' not in session or not sql_queries.is_user_seller(session['UserID']):
        return redirect(url_for('login'))
    
    sql_queries.delete_product(product_id)
    flash('Product deleted successfully')
    return redirect(url_for('seller_dashboard'))


@app.route('/delete_review/<int:review_id>', methods=['POST'])
def delete_review(review_id: int) -> FlaskReturnType:
    user_id = session.get('UserID') 
    if not user_id:
        flash('You need to be logged in to delete a review.', 'error')
        return redirect(request.referrer or url_for('home'))

    if not sql_queries.is_review_author(user_id, review_id):
        flash('You can only delete your own reviews.', 'error')
        return redirect(request.referrer or url_for('home'))

    sql_queries.delete_review(review_id)
    flash('Review deleted successfully.', 'success')
    return redirect(request.referrer or url_for('home'))

@app.route('/add_review/<int:product_id>', methods=['POST'])
def add_review(product_id: int) -> FlaskReturnType:
    user_id = session.get('UserID')

    if not user_id:
        flash('You need to be logged in to add a review.', 'error')
        return redirect(url_for('login'))
    rating = request.form.get('rating')
    comment = request.form.get('comment')

    if not rating or not comment:
        flash('Rating and comment are required.', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))
    
    if not sql_queries.has_purchased_product(user_id, product_id):
        flash('You can only review products you have purchased.', 'warning')
        return redirect(url_for('product_detail', product_id=product_id))

    sql_queries.add_review(user_id, product_id, int(rating), comment)
    flash('Review added successfully.', 'success')

    return redirect(url_for('product_detail', product_id=product_id))




@app.route('/update_order_status_bulk', methods=['POST'])
def update_order_status_bulk():
    if 'UserID' not in session or not sql_queries.is_user_seller(session['UserID']):
        return redirect(url_for('login'))
    
    user_id = session['UserID']
    
    seller = sql_queries.get_seller_details_user(user_id)
    
    seller_id = seller['SellerID']

    for key, value in request.form.items():
        if key.startswith('order_status_'):
            order_id = int(key.split('_')[2])
            new_status = value

            if sql_queries.seller_has_access_to_order(seller_id, order_id):
                sql_queries.update_order_status(order_id, new_status)

    flash('Order status updated successfully.', 'success')
    return redirect(url_for('seller_dashboard'))

@app.route('/become_seller')
def become_seller():
    if 'UserID' not in session :
        return redirect(url_for('login'))
    if sql_queries.is_user_seller(session['UserID']):
        flash('User is already a Seller')
        return redirect(url_for('account'))
    try:
        sql_queries.become_seller(session['UserID'])
    except Error as e:
        flash('Failed to become Seller')
        app.logger.error(f"{session['UserID']} failed to become Seller")
        return redirect(url_for('account'))
    flash('You became a Seller!')
    app.logger.info(f"{session['UserID']} became a Seller")
    return redirect(url_for('home'))

@app.route('/order_summary')
def order_summary():
    if 'UserID' not in session:
        return redirect(url_for('login'))

    try:
        order_summary_data = sql_queries.view_order_summary()
        return render_template('order_summary.html', data=order_summary_data)
    except Error as e:
        flash('Failed to retrieve order summary')
        app.logger.error(f"Failed to retrieve order summary for user {session['UserID']}: {str(e)}")
        return redirect(url_for('home'))

@app.route('/product_stock')
def product_stock():
    if 'UserID' not in session:
        return redirect(url_for('login'))

    try:
        product_stock_data = sql_queries.view_product_stock()
        return render_template('product_stock.html', data=product_stock_data)
    except Error as e:
        flash('Failed to retrieve product stock')
        app.logger.error(f"Failed to retrieve product stock for user {session['UserID']}: {str(e)}")
        return redirect(url_for('home'))


@app.route('/seller/<int:seller_id>')
def seller_profile(seller_id):
    
    # Get seller details
    seller = sql_queries.get_seller_details(seller_id)
    if not seller:
        return "Seller not found", 404
    
    if 'UserID' not in session:
        return redirect(url_for('login'))

    # Check if the current user is subscribed to this seller
    user_id = session['UserID']
    is_subscribed = user_id and sql_queries.is_user_subscribed(user_id, seller_id)
    
    # Get the seller's products
    seller_products = sql_queries.get_seller_products(seller_id)
    
    return render_template('seller_profile.html', 
                           seller=seller, 
                           is_subscribed=is_subscribed, 
                           seller_products=seller_products)

@app.route('/subscribe/<int:seller_id>', methods=['POST'])
def subscribe(seller_id):
    if 'UserID' not in session:
        return redirect(url_for('login'))
    user_id =session['UserID']  
    if not sql_queries.is_user_subscribed(user_id, seller_id):
        sql_queries.add_subscription(user_id, seller_id)
        flash('Successfully subscribed to the seller!', 'success')
    else:
        flash('You are already subscribed to this seller.', 'info')
    
    return redirect(url_for('seller_profile', seller_id=seller_id))

@app.route('/unsubscribe/<int:seller_id>', methods=['POST'])
def unsubscribe(seller_id):

    if 'UserID' not in session:
        return redirect(url_for('login'))
    
    user_id = session['UserID']  

    if sql_queries.is_user_subscribed(user_id, seller_id):
        sql_queries.remove_subscription(user_id, seller_id)
        flash('Successfully unsubscribed from the seller.', 'success')
    else:
        flash('You are not subscribed to this seller.', 'info')
    
    return redirect(url_for('seller_profile', seller_id=seller_id))

