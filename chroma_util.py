import chromadb
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
from mysql_util import sql_query, mark_stored



chroma_client = chromadb.HttpClient(host="localhost", port=8000)
chroma_client.heartbeat()

batch_size = 166


""" Returns the chroma db object matching the specified name, if applicable """
def get_db(vdb_name):
    try:
        existing = chroma_client.get_collection(name=vdb_name)
        if existing:
            return existing
    except chromadb.errors.InvalidCollectionException:
        return None


""" Creates a new chroma db with the specified name, if available """
def vdb_new(vdb_name):
    if not get_db(vdb_name):
        return chroma_client.create_collection(name=f"{vdb_name}")


""" Deletes the chroma db matching the specified name, if applicable """
def vdb_delete(vdb_name):
    db = get_db(vdb_name)
    if db:
        chroma_client.delete_collection(name=vdb_name)

""" Inserts all newly added MySQL data to the chroma dbs, and updates them
    in MySQL as added to prevent attempting to add the same data twice """
def vdb_insert():
    """db1 is for meta, vdb_reviews is for reviews"""
    collection_meta = chroma_client.get_collection(name="db1")
    collection_reviews = chroma_client.get_collection(name="reviews_vdb")
    offset = 0
    print("  Uploading new products")
    
    while True:
        query_meta = f"SELECT title, parent_asin, details, features, description, average_rating, rating_number, price, store, bought_together FROM meta WHERE stored_vdb = 0 LIMIT {batch_size} OFFSET {offset}"
        records_meta = sql_query(query_meta)
        if not records_meta:
            print("  ----No new products found")
            break
    
        formatted_records = []
        id_list = []
        metadata_list = []
        
        for record in records_meta:
            formatted_records.append("Title: " + str(record[0]) + "Details: " +  str(record[3]) + "Features: " + str(record[4]) + "Description: " + str(record[4]))
            id_list.append(str(record[1]))
            meta_dic = {"parent_asin": record[1], "Average rating": record[5], "Rating number": record[6]}
            if record[7] is not None:
                meta_dic.update({"Price": record[7]})
            else:
                meta_dic.update({"Price": -1})
            if record[8] is not None:
                meta_dic.update({"Store": record[8]})
            else:
                meta_dic.update({"Store": -1})
            if record[9] is not None:
                meta_dic.update({"bought_together": record[9]})
            else:
                meta_dic.update({"bought_together": -1})
            metadata_list.append(meta_dic)

        collection_meta.upsert(
            documents=formatted_records,
            ids=id_list,
            metadatas = metadata_list
        )
        
        batch = (int)(offset / batch_size)
        if batch % 10 == 0:
            print(f"\t batch {batch} inserted")
        
        offset += batch_size
        
    offset = 0
    print("  Uploading new reviews")    
    """Now update reviews index"""    
    while True:
        query_reviews = f"""SELECT title, text, asin, user_id, timestamp, parent_asin
        FROM reviews
        WHERE stored_vdb = 0
        LIMIT {batch_size}
        OFFSET {offset}"""
        records = sql_query(query_reviews)
        if not records:
            print("  ----No new reviews found")
            break

        formatted_records = []
        id_list = []
        meta_list = []

        i = 0

        for record in records:
            to_append = "Title : " + record[0] + "\n Text : " + record[1]
            formatted_records.append(to_append)

            meta_dic = {"parent_asin": record[5], "asin": record[2], "user_id": record[3], "timestamp": record[4]}
            meta_list.append(meta_dic)

            id_append = "ASIN: " + str(record[2]) + "user_id : " + str(record[3]) + "timestamp : " + str(record[4])
            id_list.append(id_append)
            i += 1

        collection_reviews.upsert(
            documents=formatted_records,
            ids=id_list,
            metadatas=meta_list
        )
        batch = (int)(offset / batch_size)
        if batch % 10 == 0:
            print(f"[PROGRESS] batch {batch} inserted into vdb")
        offset += batch_size
        
    """ Reflect that the new RDS data has been stored in the vector db """
    mark_stored()
    

""" Returns the top `records` results from `vdb_name` closest to the specified query """
def vdb_query(vdb_name, query, records, condition):
    if condition:
        collection = chroma_client.get_collection(name=f"{vdb_name}")
        results = collection.query(
            query_texts=[f"{query}"],
            n_results = records,
            where={"parent_asin": {"$in": condition}}
        )
    else:
        collection = chroma_client.get_collection(name=f"{vdb_name}")
        results = collection.query(
            query_texts=[f"{query}"],
            n_results = records
        )

    return results
