-- Drop all tables beforehand
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS User;
DROP TABLE IF EXISTS Seller;
DROP TABLE IF EXISTS Category;
DROP TABLE IF EXISTS Product;
DROP TABLE IF EXISTS Wishlist;
DROP TABLE IF EXISTS WishlistItem;
DROP TABLE IF EXISTS `Order`;
DROP TABLE IF EXISTS OrderItem;
DROP TABLE IF EXISTS Review;
DROP TABLE IF EXISTS Message;
DROP TABLE IF EXISTS Subscription;
DROP TABLE IF EXISTS ProductLog;
SET FOREIGN_KEY_CHECKS = 1;
--

CREATE TABLE User (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Username VARCHAR(50) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    FirstName VARCHAR(50),
    LastName VARCHAR(50),
    Address VARCHAR(255),
    PhoneNumber VARCHAR(15),
    CHECK (Email LIKE '%_@__%.__%')
);
CREATE INDEX idx_username ON User(Username);

CREATE TABLE Seller (
    SellerID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT,
    -- Admin Level for Admin. This is just NULL for normal sellers
    AdminLevel INT,
    FOREIGN KEY (UserID) REFERENCES User(UserID)
);

CREATE TABLE Category (
    CategoryID INT PRIMARY KEY AUTO_INCREMENT,
    CategoryName VARCHAR(100) UNIQUE NOT NULL,
    ParentCategoryID INT,
    FOREIGN KEY (ParentCategoryID) REFERENCES Category(CategoryID)
);

CREATE TABLE Product (
    ProductID INT PRIMARY KEY AUTO_INCREMENT,
    SellerID INT,
    CategoryID INT,
    ProductName VARCHAR(100) NOT NULL,
    ProductImage LONGBLOB,
    Description TEXT,
    Price DECIMAL(10, 2) NOT NULL,
    StockQuantity INT NOT NULL,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (SellerID) REFERENCES Seller(SellerID),
    FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID),
    CHECK (Price >= 0),
    CHECK (StockQuantity >= 0)
);
CREATE INDEX idx_productname ON Product(ProductName);

CREATE TABLE Wishlist (
    WishlistID INT PRIMARY KEY AUTO_INCREMENT,
    WishlistName VARCHAR(100) UNIQUE NOT NULL,
    UserID INT UNIQUE,
    FOREIGN KEY (UserID) REFERENCES User(UserID)
);

CREATE TABLE WishlistItem (
    WishlistItem INT PRIMARY KEY AUTO_INCREMENT,
    WishlistID INT,
    ProductID INT,
    FOREIGN KEY (WishlistID) REFERENCES Wishlist(WishlistID),
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
);

CREATE TABLE `Order` (
    OrderID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT,
    OrderDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    TotalAmount DECIMAL(10, 2) NOT NULL,
    OrderStatus ENUM('Pending', 'Shipped', 'Delivered', 'Cancelled') NOT NULL,
    FOREIGN KEY (UserID) REFERENCES User(UserID)
);

CREATE TABLE OrderItem (
    OrderItemID INT PRIMARY KEY AUTO_INCREMENT,
    OrderID INT,
    ProductID INT,
    Quantity INT NOT NULL,
    PriceAtPurchase DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (OrderID) REFERENCES `Order`(OrderID),
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
);

CREATE TABLE Review (
    ReviewID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT,
    ProductID INT,
    Rating INT CHECK (Rating >= 1 AND Rating <= 5),
    Comment TEXT,
    ReviewDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES User(UserID),
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
);

CREATE TABLE Message (
    MessageID INT PRIMARY KEY AUTO_INCREMENT,
    SenderID INT,
    ReceiverID INT,
    MessageContent TEXT NOT NULL,
    SentDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (SenderID) REFERENCES User(UserID),
    FOREIGN KEY (ReceiverID) REFERENCES User(UserID)
);

CREATE TABLE Subscription (
    SubscriptionID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT,
    SellerID INT,
    SubscriptionDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES User(UserID),
    FOREIGN KEY (SellerID) REFERENCES Seller(SellerID)
);

CREATE TABLE ProductLog (
    ProductLogID INT PRIMARY KEY AUTO_INCREMENT,
    SellerID INT,
    ProductID INT,
    ActionType ENUM('UPDATE', 'INSERT', 'DELETE') NOT NULL,
    ChangeDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (SellerID) REFERENCES Seller(SellerID),
    FOREIGN KEY (ProductID) REFERENCES Product(ProductID)
);
CREATE INDEX idx_actiontype ON ProductLog(ActionType);
