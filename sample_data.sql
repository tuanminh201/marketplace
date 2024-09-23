-- Insert sample users
INSERT INTO User (Username, Password, Email, FirstName, LastName, Address, PhoneNumber)
VALUES 
('My_Store', 'My_Store', 'My_Store@example.com', 'My_Store', 'My_Store', 'My_Store', 'My_Store'),
('john_doe', 'password123', 'john@example.com', 'John', 'Doe', '123 Elm St', '123-456-7890'),
('jane_smith', 'password456', 'jane@example.com', 'Jane', 'Smith', '456 Maple Ave', '987-654-3210'),
('alice_jones', 'password789', 'alice@example.com', 'Alice', 'Jones', '789 Oak Blvd', '555-123-4567');

INSERT INTO Wishlist (WishlistName, UserID)
VALUES
('john_does wishlist', 2),
('jane_smith wishlist', 3),
('alice_jones wishlist', 4);

-- Insert sample sellers (Assuming UserID 1 and 2 are sellers)
-- Insert sample sellers (Assuming UserID 2 and 3 are sellers)
INSERT INTO Seller (UserID) VALUES 
(2),  -- John Doe
(3);  -- Jane Smith

-- Insert sample categories
INSERT INTO Category (CategoryName, ParentCategoryID) VALUES
('Electronics', NULL),
('Computers', 1),
('Smartphones', 1),
('Home Appliances', NULL);

-- Insert sample products (Assuming SellerID 1 and 2)
INSERT INTO Product (SellerID, CategoryID, ProductName, ProductImage, Description, Price, StockQuantity)
VALUES
(1, 2, 'Laptop', NULL, 'High-performance laptop', 1200.00, 10),
(1, 3, 'Smartphone', NULL, 'Latest model smartphone', 800.00, 25),
(2, 4, 'Microwave Oven', NULL, 'Compact microwave oven', 150.00, 30);

-- Insert sample orders (Assuming UserID 3 is Alice Jones)
INSERT INTO `Order` (UserID, TotalAmount, OrderStatus)
VALUES 
(4, 2000.00, 'Pending'),
(4, 150.00, 'Shipped');

-- Insert sample order items (Assuming OrderID 1 and 2)
INSERT INTO OrderItem (OrderID, ProductID, Quantity, PriceAtPurchase)
VALUES
(1, 1, 1, 1200.00),  -- Laptop
(1, 2, 1, 800.00),   -- Smartphone
(2, 3, 1, 150.00);   -- Microwave Oven

-- Insert sample reviews (Assuming UserID 4is Alice Jones)
INSERT INTO Review (UserID, ProductID, Rating, Comment)
VALUES
(4, 1, 5, 'Excellent laptop!'),
(4, 3, 4, 'Good value for money.');

-- Insert sample messages (Assuming UserID 4 is Alice Jones)
INSERT INTO Message (SenderID, ReceiverID, MessageContent)
VALUES
(2, 4, 'Your order is confirmed.'),
(4, 2, 'Thank you!');

-- Insert sample subscriptions (Assuming UserID 4 is Alice Jones)
INSERT INTO Subscription (UserID, SellerID)
VALUES
(4, 1),  -- Alice Jones subscribes to John Doe's store
(4, 2);  -- Alice Jones subscribes to Jane Smith's store
