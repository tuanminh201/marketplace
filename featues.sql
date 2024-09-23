-- Advanced SQL Features (Triggers,views,etc) 

-- Product Deletion or Reavailable
-- Changes the states if product becomes unavailable/available
-- This procedure Transaction gets called in product triggers
DELIMITER $$
DROP PROCEDURE IF EXISTS DeleteProductAndWishlistItem;
CREATE PROCEDURE DeleteProductAndWishlistItem(IN prod_id INT)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
    END;

    START TRANSACTION;

    CALL LogProductChange('DELETE', (SELECT SellerID
                                    FROM Product
                                    WHERE ProductID = prod_id),
                                    prod_id);
    UPDATE Product
    SET Available = FALSE, StockQuantity = 0
    WHERE ProductID = prod_id;

    DELETE FROM WishlistItem
    WHERE ProductID = prod_id;

    COMMIT;
END $$
DELIMITER ;


DELIMITER $$
DROP PROCEDURE IF EXISTS CreateDefaultWishlist;
CREATE PROCEDURE CreateDefaultWishlist(IN userid INT)
BEGIN
    INSERT INTO Wishlist (WishlistName, UserID)
    VALUES (
        CONCAT(
            (SELECT Username FROM User u WHERE u.UserID = userid), 
            "'s wishlist"
        ), 
        userid
    );
END $$
DELIMITER ;
DELIMITER $$
DROP TRIGGER IF EXISTS AfterUserCreation;
CREATE TRIGGER AfterUserCreation
AFTER INSERT ON User
FOR EACH ROW
BEGIN
    CALL CreateDefaultWishlist(NEW.UserID);
END $$
DELIMITER ;

-- LOGGING procedure and triggers
DELIMITER $$
DROP PROCEDURE IF EXISTS LogProductChange;
CREATE PROCEDURE LogProductChange(IN ActionType ENUM('UPDATE', 'INSERT', 'DELETE'), IN SellerID INT, IN ProductID INT)
BEGIN
    INSERT INTO ProductLog (ActionType, SellerID, ProductID)
    VALUES (ActionType, SellerID, ProductID);
END $$
DELIMITER ;
DELIMITER $$
DROP TRIGGER IF EXISTS AfterProductInsert;
CREATE TRIGGER AfterProductInsert
AFTER INSERT ON Product
FOR EACH ROW
BEGIN
    CALL LogProductChange('INSERT', NEW.SellerID, NEW.ProductID);
END $$
DELIMITER ;
DELIMITER $$
DROP TRIGGER IF EXISTS BeforeProductUpdate;
CREATE TRIGGER BeforeProductUpdate
BEFORE UPDATE ON Product
FOR EACH ROW
BEGIN
    IF OLD.Available = 0 AND NEW.Available = 0 THEN
        -- Raise an error and rollback to prevent any changes to Unavailable Products
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Update failed: The product was deleted and cant be changed';
    END IF;
    CALL LogProductChange('UPDATE', NEW.SellerID, NEW.ProductID);
END $$
DELIMITER ;


-- Trigger: Update stock quantity after an order is placed
DELIMITER $$

DROP TRIGGER IF EXISTS UpdateStockAfterOrder;
CREATE TRIGGER UpdateStockAfterOrder
AFTER INSERT ON OrderItem
FOR EACH ROW
BEGIN
    UPDATE Product 
    SET StockQuantity = StockQuantity - NEW.Quantity
    WHERE ProductID = NEW.ProductID;
END $$

DELIMITER ;

-- Trigger: Message Thank you for subscribing to 
DELIMITER //

DROP TRIGGER IF EXISTS after_subscription;
CREATE TRIGGER after_subscription
AFTER INSERT ON Subscription
FOR EACH ROW
BEGIN
    INSERT INTO Message (SenderID, ReceiverID, MessageContent)
    VALUES (1, NEW.UserID, CONCAT('Thank you for subscribing to ', (SELECT Username FROM User JOIN Seller ON Seller.UserID = User.UserID WHERE Seller.SellerID = NEW.SellerID)));
END //

DELIMITER ;


-- Trigger: Message New Product

DELIMITER $$

DROP TRIGGER IF EXISTS notify_subscribers_after_product_addition;
CREATE TRIGGER notify_subscribers_after_product_addition
AFTER INSERT ON Product
FOR EACH ROW
BEGIN

    DECLARE done INT DEFAULT FALSE;
    DECLARE subscriber_id INT;
    DECLARE subscriber_cursor CURSOR FOR
        SELECT UserID
        FROM Subscription
        WHERE SellerID = NEW.SellerID;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN subscriber_cursor;

    read_loop: LOOP
        FETCH subscriber_cursor INTO subscriber_id;
        IF done THEN
            LEAVE read_loop;
        END IF;

        INSERT INTO Message (SenderID, ReceiverID, MessageContent)
        VALUES (1, subscriber_id, CONCAT('A new product has been added by the seller! Product Name: ', NEW.ProductName));

    END LOOP;

    CLOSE subscriber_cursor;
END$$

DELIMITER ;


-- View: Display detailed order information including products and quantities
DROP VIEW IF EXISTS OrderDetails;
CREATE VIEW OrderDetails AS
SELECT o.OrderID, u.Username, p.ProductName, oi.Quantity, oi.PriceAtPurchase, o.OrderDate, o.OrderStatus
FROM `Order` o
JOIN OrderItem oi ON o.OrderID = oi.OrderID
JOIN Product p ON oi.ProductID = p.ProductID
JOIN User u ON o.UserID = u.UserID;