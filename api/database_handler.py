import mysql.connector
from mysql.connector import Error
from mysql.connector.types import MySQLConvertibleType, RowItemType, RowType
from typing import Union, Sequence, List, Dict


class DatabaseHandler():
    def __init__(self):
        self.connection = mysql.connector.connect(
            host="localhost",
            user="user",
            passwd="passwd_user",
            database="db_praktikum",
            collation="utf8mb4_unicode_ci"
        )
        if self.connection is None:
            raise ConnectionError("Connection to MariaDB failed!")
        self.connection.autocommit = False
        print("Connection to MySQL DB successful")

    def __del__(self):
        self.connection.close()

    def query_sql(self,
        query: str,
        data: Union[
            Sequence[MySQLConvertibleType], Dict[str, MySQLConvertibleType]
            ]) -> List[Union[RowType, Dict[str, RowItemType]]]:
        result = []
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, data)
            if query.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
            else:
            # Get last id of inserted row
                result = [cursor.lastrowid]
                self.connection.commit()  # Commit changes for UPDATE, INSERT, DELETE
        except Error as e:
            print(f"Error reading or executing SQL query: {e}")
            raise e
        cursor.close()
        return result