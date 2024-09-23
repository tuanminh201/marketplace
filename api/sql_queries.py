import database_handler
from mysql.connector.types import MySQLConvertibleType, RowItemType, RowType
from typing import Union, Sequence, List, Dict, Optional
from flask import render_template, request
from mysql.connector import Error
import magic
import base64

SingleQueryType = Union[RowType, Dict[str, RowItemType]]
QueryType = List[SingleQueryType]

class SqlQueries(database_handler.DatabaseHandler):

    def __init__(self):
        super().__init__()

    def __del__(self):
        super().__del__()

    def account(self, userid: int) -> QueryType:
        return self.query_sql("""
            SELECT Username, FirstName, LastName, Email, Address, PhoneNumber
            FROM User
            WHERE UserID = %s
            """, (userid,))

    def login(self, username:str, password:str) -> QueryType:
        return self.query_sql("""
            SELECT UserID
            FROM User
            WHERE Username = %s
            AND Password = %s
            """, (username, password))
    
    def search_product(self, search: Optional[str], seller_id: Optional[int], category_id: Optional[int],
                   min_price: Optional[float], max_price: Optional[float]) -> List[Dict[str, any]]:
        query = """
            SELECT ProductID, ProductName, Description, Price, StockQuantity
            FROM Product
            WHERE (%s IS NULL OR LOWER(ProductName) LIKE LOWER(%s))
            AND (%s IS NULL OR SellerID = %s)
            AND (%s IS NULL OR CategoryID = %s)
            AND (%s IS NULL OR Price >= %s)
            AND (%s IS NULL OR Price <= %s)
            AND Available = TRUE
        """
        
        params = [
            search,  # Search term
            f'%{search}%' if search else '%',  # For search term
            seller_id,  # SellerID
            seller_id,  # Comparison
            category_id,  # CategoryID
            category_id,  # Comparison
            min_price,  # Min Price
            min_price,  # Comparison
            max_price,   # Max Price
            max_price   # Comparison
        ]
    
        return self.query_sql(query, params)



    def product_categories(self, ) -> QueryType:
        return self.query_sql("SELECT CategoryID, CategoryName FROM Category", ())

    def product_details(self, product_id: int) -> QueryType:
        result = self.query_sql("""
            SELECT ProductID, ProductName, Description, Price, StockQuantity, Username, ProductImage, Seller.SellerID
            FROM Product
            JOIN Seller ON Seller.SellerID = Product.SellerID
            JOIN User ON User.UserID = Seller.UserID
            WHERE ProductID = %s
            """, (product_id,))[0]
        if result['ProductImage']:
            base64_image = base64.b64encode(result['ProductImage']).decode('utf-8')
            result['ProductImage'] = f"data:{magic.Magic(mime=True).from_buffer(base64_image)};base64,{base64_image}"
        return [result]

    def minimal_product_details(self, product_id: int) -> QueryType:
        return self.query_sql("""
            SELECT ProductID, ProductName, Description, Price, StockQuantity, Username, Seller.SellerID
            FROM Product
            JOIN Seller ON Seller.SellerID = Product.SellerID
            JOIN User ON User.UserID = Seller.UserID
            WHERE ProductID = %s
            """, (product_id,))

    def orders(self, userid: int) -> QueryType:
        return self.query_sql("""
            SELECT OrderID, OrderDate, TotalAmount
            FROM `Order`
            WHERE UserID = %s
            ORDER BY 1 DESC
            """, (userid,))
    
    def is_user_seller(self, user_id: int) -> bool:
        query = "SELECT COUNT(*) FROM Seller WHERE UserID = %s"
        params = (user_id,)
        result = self.query_sql(query, params)
        return result[0]['COUNT(*)'] > 0

    def order_details(self, orderid: int, userid: int) -> QueryType:
        return self.query_sql("""
            SELECT o.OrderID, o.OrderDate, o.TotalAmount, o.OrderStatus, p.ProductID, p.ProductName, p.Price, p.Description
            FROM `Order` o
            JOIN OrderItem oi ON o.OrderID = oi.OrderID
            JOIN Product p ON oi.ProductID = p.ProductID
            WHERE o.OrderID = %s AND o.UserID = %s
            """, (orderid, userid))

    def new_order(self, userid:int, total_amount:float, order_status:str, cart_data:List[dict]) -> QueryType:
        try:
            order_id = self.query_sql("""
                INSERT INTO `Order` (UserID, TotalAmount, OrderStatus)
                VALUES (%s, %s, %s)
            """, (userid, total_amount, order_status))[0]
            for item in cart_data:
                self.query_sql("""
                    INSERT INTO OrderItem (OrderID, ProductID, Quantity, PriceAtPurchase)
                    VALUES (%s, %s, %s, %s)
                """, (order_id, item['ProductID'], item['Amount'], item['Price']))
        except Error as e:
            # Revert changes if failed
            self.query_sql("""
                DELETE FROM `Order`
                WHERE OrderID = %s
                """, (order_id,))
            self.query_sql("""
                DELETE FROM OrderItem
                WHERE OrderID = %s
                """, (order_id,))
            raise e
        return [order_id]

    def edit_profile(self, first_name: str, last_name:str, email:str, address:str, phone_number:str, userid:int) -> QueryType:
        return self.query_sql("""
            UPDATE User
            SET FirstName = %s, LastName = %s, Email = %s, Address = %s, PhoneNumber = %s
            WHERE UserID = %s
        """, (first_name, last_name, email, address, phone_number, userid))

    def get_wishlist(self, userid: int) -> QueryType:
        return self.query_sql("""
            SELECT WishlistID 
            FROM Wishlist
            WHERE UserID = %s
            """, (userid,))

    def add_product_to_wishlist(self, wishlist_id: int, product_id: int) -> QueryType:
        self.query_sql("""
            INSERT INTO WishlistItem (WishlistID, ProductID)
            VALUES (%s, %s)
        """, (wishlist_id, product_id))

    def get_wishlist_items(self, userid: int) -> QueryType:
        return self.query_sql("""
            SELECT p.ProductID, p.ProductName, p.Description, p.Price
            FROM WishlistItem wi
            JOIN Wishlist w ON wi.WishlistID = w.WishlistID
            JOIN Product p ON wi.ProductID = p.ProductID
            WHERE w.UserID = %s
            """, (userid,))

    def product_in_wishlist(self, wishlist_id: int, product_id: int) -> bool:
        result = self.query_sql("""
            SELECT COUNT(*) as count 
            FROM WishlistItem 
            WHERE WishlistID = %s AND ProductID = %s
            """, (wishlist_id, product_id))

        return result[0]['count'] > 0

    def remove_product_from_wishlist(self, wishlist_id: int, product_id: int) -> QueryType:
        query = """
        DELETE FROM WishlistItem 
        WHERE WishlistID = %s AND ProductID = %s
        """
        self.query_sql(query, (wishlist_id, product_id))
        
    def user_message_sselection(self, userid: int) -> QueryType:
        return self.query_sql("""
            SELECT UserID, Username
            FROM User
            WHERE UserID IN (
                SELECT DISTINCT value
                FROM (
                    SELECT ReceiverID AS value FROM Message WHERE SenderID = %s 
                    UNION
                    SELECT SenderID AS value FROM Message WHERE ReceiverID = %s 
                ) AS value
            )
        """, (userid, userid))
    
    def user_message_selection(self, userid: int) -> QueryType:
        return self.query_sql("""
            SELECT User.UserID, User.Username, MAX(Message.SentDate) as LastMessageDate
            FROM User
            JOIN Message ON User.UserID = Message.ReceiverID OR User.UserID = Message.SenderID
            WHERE User.UserID IN (
                SELECT DISTINCT value
                FROM (
                    SELECT ReceiverID AS value FROM Message WHERE SenderID = %s 
                    UNION
                    SELECT SenderID AS value FROM Message WHERE ReceiverID = %s 
                ) AS value
            )
            GROUP BY User.UserID, User.Username
            ORDER BY LastMessageDate DESC
        """, (userid, userid))


    def message_get(self, userid:int, other_userid:int) -> QueryType:
        return self.query_sql("""
            SELECT SentDate, MessageContent, SenderID
            FROM Message
            WHERE (SenderID = %s AND ReceiverID = %s)
            OR (ReceiverID = %s AND SenderID = %s)
            ORDER BY SentDate ASC
            """, (userid, other_userid, userid, other_userid))

    def message_send(self, userid:int, receiver_id:int, message_input:str) -> QueryType:
        return self.query_sql("""
            INSERT INTO Message (SenderID, ReceiverID, MessageContent)
            VALUES (%s, %s, %s)
            """, (userid, receiver_id, message_input))

    def get_id_from_name(self, user_name:str) -> QueryType:
        return self.query_sql("""
            SELECT UserID
            FROM User
            WHERE Username = %s
            """, (user_name,))

    def get_seller_products(self, seller_id: int) -> QueryType:
        query = """SELECT *
            FROM Product
            WHERE SellerID = %s
            AND Available = True
            """
        return self.query_sql(query, (seller_id,))

    def get_user_sellerid(self, user_id: int) -> int:
        return self.query_sql("""
            SELECT SellerID
            FROM Seller
            WHERE UserID = %s
            """,(user_id,))[0]['SellerID']

    def add_product(self, user_id: int, name: str, description: str, price: float, stock_quantity: int, category_id: int, image):
        if not image:
            return self.query_sql("""
                INSERT INTO Product (SellerID, ProductName, Description, Price, StockQuantity, CategoryID, ProductImage)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (self.get_user_sellerid(user_id), name, description, price, stock_quantity, category_id, image))
        else:
            return self.query_sql("""
                INSERT INTO Product (SellerID, ProductName, Description, Price, StockQuantity, CategoryID)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (self.get_user_sellerid(user_id), name, description, price, stock_quantity, category_id))


    def update_product(self, product_id: int, name: str, description: str, price: float, stock_quantity: int, category_id: int, image):
        if not image:
            return self.query_sql("""UPDATE Product SET ProductName = %s, Description = %s, Price = %s, StockQuantity = %s, CategoryID = %s
                WHERE ProductID = %s""", (name, description, price, stock_quantity, category_id, product_id))
        else:
            return self.query_sql("""UPDATE Product SET ProductName = %s, Description = %s, Price = %s, StockQuantity = %s, CategoryID = %s, ProductImage = %s
                WHERE ProductID = %s""", (name, description, price, stock_quantity, category_id, image, product_id))


    def delete_product(self, product_id: int):
        query = "CALL DeleteProductAndWishlistItem(%s)"
        self.query_sql(query, (product_id,))

    def get_reviews(self, product_id: int):
        query = """
            SELECT R.ReviewID, R.Rating, R.Comment, R.ReviewDate, U.Username
            FROM Review R
            LEFT JOIN User U ON U.UserID = R.UserID
            WHERE R.ProductID = %s
        """
        return self.query_sql(query, (product_id,))
    
    def has_purchased_product(self, user_id: int, product_id: int) -> bool:
        query = """
            SELECT COUNT(*)
            FROM OrderItem oi
            JOIN `Order` o ON oi.OrderID = o.OrderID
            WHERE o.UserID = %s AND oi.ProductID = %s
        """
        result = self.query_sql(query, (user_id, product_id))
        return result[0]['COUNT(*)'] > 0

    def add_review(self, user_id: int, product_id: int, rating: int, comment: str) -> QueryType:
        query = "INSERT INTO Review (UserID, ProductID, Rating, Comment) VALUES (%s, %s, %s, %s)"
        self.query_sql(query, (user_id, product_id, rating, comment))
        
    def is_review_author(self, user_id: int, review_id: int) -> bool:
        query = "SELECT COUNT(*) FROM Review WHERE ReviewID = %s AND UserID = %s"
        result = self.query_sql(query, (review_id, user_id))
        return result[0]['COUNT(*)'] > 0

    def delete_review(self, review_id: int) -> QueryType:
        query = "DELETE FROM Review WHERE ReviewID = %s"
        self.query_sql(query, (review_id,))


    def orders_for_seller(self, seller_id: int):
            query = """
                SELECT DISTINCT o.OrderID, o.OrderDate, o.TotalAmount, o.OrderStatus
                FROM `Order` o
                JOIN OrderItem oi ON o.OrderID = oi.OrderID
                JOIN Product p ON oi.ProductID = p.ProductID
                WHERE p.SellerID = %s
                ORDER BY o.OrderDate DESC
            """
            return self.query_sql(query, (seller_id,))

    def get_order_details(self, order_id: int):
        query = """
            SELECT o.OrderID, o.OrderDate, o.TotalAmount, o.OrderStatus, u.Username, u.Email
            FROM `Order` o
            JOIN User u ON o.UserID = u.UserID
            WHERE o.OrderID = %s
            ORDER BY o.OrderDate DESC
        """
        result = self.query_sql(query, (order_id,))
        return result[0] if result else None
    
    def seller_has_access_to_order(self, seller_id: int, order_id: int) -> bool:
        query = """
            SELECT COUNT(*)
            FROM OrderItem oi
            JOIN Product p ON oi.ProductID = p.ProductID
            WHERE p.SellerID = %s AND oi.OrderID = %s
        """
        result = self.query_sql(query, (seller_id, order_id))
        return result[0]['COUNT(*)'] > 0


    def update_order_status(self, order_id: int, new_status: str) -> QueryType:
        query = """
            UPDATE `Order`
            SET OrderStatus = %s
            WHERE OrderID = %s
        """
        self.query_sql(query, (new_status, order_id))

    def add_user(self, username: str, password: str, email: str, first_name: str, last_name: str, address: str, phone_number: str) -> QueryType:
        query = """
            INSERT INTO User (Username, Password, Email, FirstName, LastName, Address, PhoneNumber)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.query_sql(query, (username, password, email, first_name, last_name, address, phone_number))

    def become_seller(self, userid:int) -> QueryType:
        return self.query_sql("""
            INSERT INTO Seller (UserID)
            VALUES (%s)
            """, (userid,))

    def create_trigger_update_stock(self):
        query = """
        CREATE TRIGGER trigger_update_stock
        AFTER INSERT ON OrderItem
        FOR EACH ROW
        BEGIN
            UPDATE Product
            SET StockQuantity = StockQuantity - NEW.Quantity
            WHERE ProductID = NEW.ProductID;
        END;
        """
        self.query_sql(query, ())

    def create_trigger_log_order(self):
        query = """
        CREATE TRIGGER trigger_log_order
        AFTER INSERT ON `Order`
        FOR EACH ROW
        BEGIN
            INSERT INTO OrderAudit (OrderID, OrderDate, UserID, TotalAmount)
            VALUES (NEW.OrderID, NEW.OrderDate, NEW.UserID, NEW.TotalAmount);
        END;
        """
        self.query_sql(query, ())
    def create_view_order_summary(self) -> None:
        query = """
            CREATE VIEW IF NOT EXISTS View_OrderSummary AS
            SELECT 
                o.OrderID,
                o.OrderDate,
                o.TotalAmount,
                o.OrderStatus,
                u.Username AS Customer,
                GROUP_CONCAT(p.ProductName SEPARATOR ', ') AS Products,
                GROUP_CONCAT(oi.Quantity SEPARATOR ', ') AS Quantities,
                GROUP_CONCAT(p.Price SEPARATOR ', ') AS Prices
            FROM 
                `Order` o
                JOIN User u ON o.UserID = u.UserID
                JOIN OrderItem oi ON o.OrderID = oi.OrderID
                JOIN Product p ON oi.ProductID = p.ProductID
            GROUP BY 
                o.OrderID, o.OrderDate, o.TotalAmount, o.OrderStatus, u.Username;
        """
        self.query_sql(query, ())

    def view_order_summary(self) -> QueryType:
        query = "SELECT * FROM View_OrderSummary"
        return self.query_sql(query, ())

    def create_view_product_stock(self) -> None:
        query = """
            CREATE VIEW IF NOT EXISTS View_ProductStock AS
            SELECT 
                p.ProductID,
                p.ProductName,
                p.Description,
                p.Price,
                p.StockQuantity,
                c.CategoryName
            FROM 
                Product p
                JOIN Category c ON p.CategoryID = c.CategoryID
            WHERE 
                p.StockQuantity > 0;
        """
        self.query_sql(query, ())

    def view_product_stock(self) -> QueryType:
        query = "SELECT * FROM View_ProductStock"
        return self.query_sql(query, ())
    
    def get_user_subscriptions(self, user_id: int):
        query = """
            SELECT s.SubscriptionID, u.Username, s.SubscriptionDate,  s.SellerID 
            FROM Subscription s
            JOIN Seller ON s.SellerID = Seller.SellerID
            JOIN User u ON Seller.UserID = u.UserID
            WHERE s.UserID = %s
        """
        return self.query_sql(query, (user_id,))
    
    
    def add_subscription(self, user_id: int, seller_id: int) -> None:
        query = """
            INSERT INTO Subscription (UserID, SellerID)
            VALUES (%s, %s)
        """
        self.query_sql(query, (user_id, seller_id))

    def is_user_subscribed(self, user_id: int, seller_id: int) -> bool:
        query = """
            SELECT COUNT(*)
            FROM Subscription
            WHERE UserID = %s AND SellerID = %s
        """
        result = self.query_sql(query, (user_id, seller_id))
        return result[0]['COUNT(*)'] > 0
    
    def get_seller_details(self, seller_id: int) -> Optional[SingleQueryType]:
        query = """
        SELECT SellerID, Username, Email, PhoneNumber, Address, FirstName, LastName
        FROM Seller s
        JOIN User u ON u.UserID = s.UserId
        WHERE SellerID = %s
        """
        result = self.query_sql(query, (seller_id,))
        return result[0] if result else None
    
    def get_seller_details_user(self, user_id: int) -> Optional[SingleQueryType]:
        query = """
        SELECT SellerID, Username, Email, PhoneNumber, Address, FirstName, LastName
        FROM Seller s
        JOIN User u ON u.UserID = s.UserId
        WHERE u.UserID = %s
        """
        result = self.query_sql(query, (user_id,))
        return result[0] if result else None



    def remove_subscription(self, user_id, seller_id):
        query = """
        DELETE FROM Subscription
        WHERE UserID = %s AND SellerID = %s;
        """
        params = (user_id, seller_id)
        result = self.query_sql(query, params)
        return result[0] if result else None
    
    def get_subscribers(self, seller_id: int) -> QueryType:
        query = """
            SELECT UserID
            FROM Subscription
            WHERE SellerID = %s
        """
        return self.query_sql(query, (seller_id,))
    
##                                  STATISTICS                                 ##

        
    
    # 1. Total number of products sold by a seller
    def total_products_sold(self, sellerid: int, start_date: str, end_date: str) -> QueryType:
        return self.query_sql("""
            SELECT SUM(OrderItem.Quantity) AS TotalProductsSold
            FROM OrderItem
            JOIN Product ON OrderItem.ProductID = Product.ProductID
            WHERE Product.SellerID = %s 
            AND OrderItem.OrderID IN (
                SELECT OrderID FROM `Order` WHERE OrderDate BETWEEN %s AND %s
            )
        """, (sellerid, start_date, end_date))

    # 2. Total revenue generated by a seller
    def total_revenue(self, sellerid: int, start_date: str, end_date: str) -> QueryType:
        return self.query_sql("""
            SELECT SUM(OrderItem.Quantity * OrderItem.PriceAtPurchase) AS TotalRevenue
            FROM OrderItem
            JOIN Product ON OrderItem.ProductID = Product.ProductID
            WHERE Product.SellerID = %s 
            AND OrderItem.OrderID IN (
                SELECT OrderID FROM `Order` WHERE OrderDate BETWEEN %s AND %s
            )
        """, (sellerid, start_date, end_date))

    # 3. Total number of orders received by a seller
    def total_orders(self, sellerid: int, start_date: str, end_date: str) -> QueryType:
        return self.query_sql("""
            SELECT COUNT(DISTINCT `Order`.OrderID) AS TotalOrders
            FROM `Order`
            JOIN OrderItem ON `Order`.OrderID = OrderItem.OrderID
            JOIN Product ON OrderItem.ProductID = Product.ProductID
            WHERE Product.SellerID = %s 
            AND `Order`.OrderDate BETWEEN %s AND %s
        """, (sellerid, start_date, end_date))

    # 4. Total quantity of each product sold by a seller
    def total_quantity_sold_per_product(self, sellerid: int, start_date: str, end_date: str) -> QueryType:
        return self.query_sql("""
            SELECT Product.ProductName, SUM(OrderItem.Quantity) AS TotalQuantitySold
            FROM OrderItem
            JOIN Product ON OrderItem.ProductID = Product.ProductID
            WHERE Product.SellerID = %s 
            AND OrderItem.OrderID IN (
                SELECT OrderID FROM `Order` WHERE OrderDate BETWEEN %s AND %s
            )
            GROUP BY Product.ProductName
            ORDER BY 2 DESC
        """, (sellerid, start_date, end_date))

    # 5. Average price per order for a seller
    def average_order_price(self, sellerid: int, start_date: str, end_date: str) -> QueryType:
        return self.query_sql("""
            SELECT AVG(`Order`.TotalAmount) AS AverageOrderPrice
            FROM `Order`
            WHERE `Order`.OrderID IN (
                SELECT OrderItem.OrderID 
                FROM OrderItem 
                JOIN Product ON OrderItem.ProductID = Product.ProductID
                WHERE Product.SellerID = %s
            )
            AND `Order`.OrderDate BETWEEN %s AND %s
        """, (sellerid, start_date, end_date))

    # 6. Total number of distinct products sold by a seller
    def total_distinct_products_sold(self, sellerid: int, start_date: str, end_date: str) -> QueryType:
        return self.query_sql("""
            SELECT COUNT(DISTINCT OrderItem.ProductID) AS TotalDistinctProductsSold
            FROM OrderItem
            JOIN Product ON OrderItem.ProductID = Product.ProductID
            WHERE Product.SellerID = %s 
            AND OrderItem.OrderID IN (
                SELECT OrderID FROM `Order` WHERE OrderDate BETWEEN %s AND %s
            )
        """, (sellerid, start_date, end_date))

    # 7. The most sold product by a seller
    def most_sold_product(self, sellerid: int, start_date: str, end_date: str) -> QueryType:
        return self.query_sql("""
            SELECT Product.ProductName, SUM(OrderItem.Quantity) AS TotalQuantitySold
            FROM OrderItem
            JOIN Product ON OrderItem.ProductID = Product.ProductID
            WHERE Product.SellerID = %s 
            AND OrderItem.OrderID IN (
                SELECT OrderID FROM `Order` WHERE OrderDate BETWEEN %s AND %s
            )
            GROUP BY Product.ProductName
            ORDER BY TotalQuantitySold DESC
            LIMIT 1
        """, (sellerid, start_date, end_date))

    # 8. The highest revenue generating product by a seller
    def highest_revenue_product(self, sellerid: int, start_date: str, end_date: str) -> QueryType:
        return self.query_sql("""
            SELECT Product.ProductName, SUM(OrderItem.Quantity * OrderItem.PriceAtPurchase) AS TotalRevenueGenerated
            FROM OrderItem
            JOIN Product ON OrderItem.ProductID = Product.ProductID
            WHERE Product.SellerID = %s 
            AND OrderItem.OrderID IN (
                SELECT OrderID FROM `Order` WHERE OrderDate BETWEEN %s AND %s
            )
            GROUP BY Product.ProductName
            ORDER BY TotalRevenueGenerated DESC
            LIMIT 1
        """, (sellerid, start_date, end_date))

    # 9. Average product rating received by a seller
    def average_product_rating(self, sellerid: int) -> QueryType:
        return self.query_sql("""
            SELECT AVG(Review.Rating) AS AverageProductRating
            FROM Review
            JOIN Product ON Review.ProductID = Product.ProductID
            WHERE Product.SellerID = %s
        """, (sellerid,))

    # 10. Total number of reviews received by a seller
    def total_reviews_received(self, sellerid: int) -> QueryType:
        return self.query_sql("""
            SELECT COUNT(Review.ReviewID) AS TotalReviewsReceived
            FROM Review
            JOIN Product ON Review.ProductID = Product.ProductID
            WHERE Product.SellerID = %s
        """, (sellerid,))
