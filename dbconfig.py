from dotenv import load_dotenv
import os 
import mysql.connector 
from mysql.connector import pooling

load_dotenv()

class Database:
    pool = pooling.MySQLConnectionPool(
        pool_name = "mypool",
        pool_size = 10,  
        pool_reset_session = True,
        host = "localhost",
        database = "TaipeiDayTrip",
        user = "root",
        password = os.getenv("mypassword"),
    )

    def execute_query(query, params = None, dictionary = False):
        try:
            cnx = Database.pool.get_connection()
            if cnx.is_connected():
                cursor = cnx.cursor(dictionary = dictionary)
                cursor.execute(query, params)
                if query.strip().lower().startswith("select"):
                    data = cursor.fetchall()
                    return data
                else:
                    cnx.commit()
        except mysql.connector.Error as error:
            print("Error while connecting to MySQL", error)
        finally:
            if cnx.is_connected():
                cursor.close()
                cnx.close()