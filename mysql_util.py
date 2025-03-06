import mysql.connector
import os
from glob import glob
import json

"""etl1.py provides the utilities for the ETL pipeline's MySQL aspect"""

ROWS_PER_BATCH = 1000
db1_conn = None
db1_cur = None

all_dbs_conn = mysql.connector.connect(
  host="localhost",
  port=4000,
  user="root",
  password="dy1l]bVx6I&fT0{vHZ2",
)

mysql_cur = all_dbs_conn.cursor()  # local MySQL with all dbs


def db1_setup():
    global db1_conn, db1_cur
    db1_conn = mysql.connector.connect(
        host="localhost",
        port=4000,
        user="root",
        password="dy1l]bVx6I&fT0{vHZ2",
        database="db1"
    )
    db1_cur = db1_conn.cursor()  # db1: this codebase's db


""" Num rows in specified table """
def num_rows(table_name):
    if table_name in list_tables():
        query = f"SELECT COUNT(*) FROM {table_name};"
        db1_cur.execute(query)
        rows = db1_cur.fetchall()
        return rows[0][0]
    return -1


""" Prints the numebr of rows specified from the specified table """
def print_rows(table_name, num_rows):
    query = f"SELECT * FROM {table_name} LIMIT {num_rows}"
    db1_cur.execute(query)
    rows = db1_cur.fetchall()
    for row in rows:
        print(row)

""" Creates the metadata table """
def create_meta():
    db1_cur.execute("""
    CREATE TABLE IF NOT EXISTS meta (
        parent_asin VARCHAR(20),
        main_category VARCHAR(255),
        title TEXT,
        rating_number INT,
        description LONGTEXT, 
        features LONGTEXT, 
        price FLOAT,
        details LONGTEXT,
        stored_vdb BOOLEAN,
        average_rating FLOAT,
        store TEXT,
        images TEXT,
        bought_together LONGTEXT,
        PRIMARY KEY (parent_asin)
    ); """)

""" Creates the reviews table """
def create_reviews():
    db1_cur.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        parent_asin VARCHAR(20),
        asin VARCHAR(20),
        user_id VARCHAR(50),
        timestamp BIGINT,
        text LONGTEXT,
        title TEXT,
        rating FLOAT,
        verified_purchase boolean,
        helpful_vote int,
        stored_vdb BOOLEAN,
        PRIMARY KEY(asin, user_id, timestamp)
    ); """)


""" Parent / child product relationship store """
def create_family():
    db1_cur.execute("""
    CREATE TABLE IF NOT EXISTS family (
        parent_asin VARCHAR(20),
        asin VARCHAR(20),
        PRIMARY KEY(parent_asin, asin)
    ); """)


""" Where stored_vdb is 0, update to 1 """
def mark_stored():
    db1_cur.execute("""
    UPDATE meta
    SET stored_vdb = 1
    WHERE stored_vdb = 0""")
    
    db1_cur.execute("""
    UPDATE reviews
    SET stored_vdb = 1
    WHERE stored_vdb = 0""")

    db1_conn.commit()


""" 1st upload to reviews table, then update the family table 
    with  asin/parent_asin pair not already in """
def insert_meta(json_file):
    with open(json_file, 'r') as f:
        data = [json.loads(line) for line in f]
    
        insert_query = """INSERT IGNORE INTO meta 
        (parent_asin, main_category, title, rating_number, description, 
        features, price, details, stored_vdb, average_rating, store, images, bought_together) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,  %s, %s, %s, %s);"""
        batch_size = 0
        iteration = 0
        batch = []
        
        for product in data:
            """ Collect details """
            images = json.dumps(product.get('images', []))
            details_dict = product.get('details')
            details_text = ""
            if details_dict is None or not isinstance(details_dict, (list, dict, str)):
                details_text = None
            else:
                for key, value in details_dict.items():
                    value = json.dumps(value) # for some reason, some specs are like "attribute: {some dict type}}"
                    next = key + ": " + value + ", "
                    details_text += next
            
            """ Collect description """
            description_list = product.get('description', None)
            description_text = ""
            for description in description_list:
                description_text += description
            
            """ Collect features """
            features_list = product.get('features', None)   
            features_text = ""
            for feature in features_list:
                features_text += feature
            
            """ Collect price """
            price = product.get('price', None)
            if price is not None and type(price) != float:
                price = None

            bought_together = json.dumps(product.get('images', []))
        
            """ Add to a list, where each row is a tuple of strings """
            batch.append((
                product.get('parent_asin', None),
                product.get('main_category', None),
                product.get('title', None),
                product.get('rating_number', None),
                description_text,
                features_text,
                price,
                details_text,
                0,
                product.get('average_rating', None),
                product.get('store', None),
                images,
                bought_together
            ))

            """ Add to the database """
            if batch_size == ROWS_PER_BATCH or product == data[-1]:
                if iteration %10 == 0:
                    print(f"[INFO] Batch {iteration} uploaded")
                try:
                    db1_cur.executemany(insert_query, batch) # mysql version
                    db1_conn.commit()
                    sql_query("SELECT * FROM meta")
                    
                    batch_size = 0
                    iteration += 1
                    batch.clear()
            
                except Exception as e:
                    print(f"Insertion Error: {e}")
                    db1_conn.rollback()
                    batch.clear()
                    quit()
            batch_size += 1

""" Insert reviews from json_file specified into the reviews table in the global db """
def insert_reviews(json_file):
    with open(json_file, 'r') as f:
        data = [json.loads(line) for line in f]
        
        """ About 2k/152k (for musical instruments) have repeat
            child product / user / timestamp and were not inserted """
        review_query = """INSERT IGNORE INTO reviews
        (parent_asin, asin, user_id, timestamp, text, title, rating,
        verified_purchase, helpful_vote, stored_vdb) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        family_query = """INSERT IGNORE INTO family
        (parent_asin, asin) VALUES (%s, %s) """
        
        batch_size = 0
        iteration = 0
        batch_review = []
        batch_family = []
        
        for review in data:
            batch_review.append((
                review.get('parent_asin', None),
                review.get('asin', None),
                review.get('user_id', None),
                review.get('timestamp', None),
                review.get('text', None),
                review.get('title', None),
                review.get('rating', None),
                review.get('verified_purchase', None),
                review.get('helpful_vote', None),
                0
            ))
            
            batch_family.append((
                review.get('parent_asin', None),
                review.get('asin', None)
            ))
            
            """ Add to the database """
            if batch_size == ROWS_PER_BATCH or review == data[-1]:
                if iteration %10 == 0:
                  print(f"[INFO] Batch {iteration} uploaded")
                try:
                    db1_cur.executemany(review_query, batch_review)
                    db1_cur.executemany(family_query, batch_family)
                    db1_conn.commit()
                    sql_query("SELECT * FROM reviews")
                    batch_size = 0
                    iteration += 1
                    batch_review.clear()
                    batch_family.clear()
                except Exception as e:
                    print(f"Insertion Error: {e}")
                    db1_conn.rollback()
                    quit()
            batch_size += 1

""" Check if any new data have been added to the folder, if so structures into the db """
def structure(directory_path):
    file_pattern = os.path.join(directory_path, "*.jsonl")
    json_files = glob(file_pattern)
    
    for json_file in json_files:
        print('[UPLOADING] ' + json_file)
        
        if os.path.basename(json_file).startswith('meta'):  
            prev_size = num_rows("meta")
            insert_meta(json_file)
            uploaded = num_rows("meta") - prev_size
        else:
            prev_size = num_rows("reviews")
            insert_reviews(json_file)
            uploaded = num_rows("reviews") - prev_size

        os.remove(json_file)
        print(f"\t[UPLOADED] {uploaded} rows")   
    

""" Drops the specified table from the global db """
def drop_table(table_name):
    db1_cur.execute(f"""
    DROP TABLE IF EXISTS {table_name}""")


""" Creates the specified db """
def new_db(db_name):
    mysql_cur.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")


""" Drops the specified db """
def drop_db(db_name):
    mysql_cur.execute(f"DROP DATABASE IF EXISTS {db_name}")


""" Executes the specified query and returns the results """
def sql_query(query):
    db1_cur.execute(query)
    records = db1_cur.fetchall()
    return records

""" Return a matrix of data, where each index is a product's info """
def retrieve_product_data(ids):
    product_info = []
    for id in ids:
        query = f"SELECT title, rating_number, average_rating, price, description, features, details FROM meta WHERE parent_asin = \"{id}\""
        db1_cur.execute(query)
        result = db1_cur.fetchone()
        product_info.append(result)
    return product_info

""" Returns all tables in the global DB """
def list_tables():
    db1_cur.execute("SHOW TABLES")
    tables = []
    for table in db1_cur:
        tables += table
    return tables


""" Lists all MySQL dbs on the local machine """
def list_dbs():
    mysql_cur.execute("SHOW DATABASES")
    dbs = []
    for db in mysql_cur:
        dbs += db
    return dbs
