import os
from mysql_util import num_rows, sql_query, structure, list_tables, drop_table, create_family, \
create_meta, create_reviews, new_db, db1_setup
from chroma_util import vdb_new, vdb_insert, vdb_query, vdb_delete, chroma_client

"""Any new data in thew new_data folder is formatted into MySQL and removed from the folder"""
if __name__ == "__main__":
    """ ETL Part 1: transfer jsonl data to MySQL """
    
    """ Creates `db1`, the global database for all tables, if it does not already exist """
    new_db('db1')
    db1_setup()

    """ Creates the meta table if it does not already exist """
    create_meta()

    """ Creates the reviews table if it does not already exist """
    create_reviews()

    """ Creates the family table if it does not already exist """
    create_family()

    print("[ETL] json -> MySQL")

    """ Moves the raw data from the new_data folder to the appropriate
        tables, based on the file names, deleting once completed. """
    structure(os.path.join(os.getcwd(), "new_data"))

    """ ETL Part 2: copy MySQL data to Chroma """

    print("[ETL] MySQL -> ChromaDB")

    """ Creates `db1` vector store in ChromaDB, for products """     
    vdb_new("db1")

    """ Creates `review_vdb` vector store in ChromaDB, for reviews """
    vdb_new("reviews_vdb")

    """ Copies the MySQL data to Chroma Any MySQL. Rows with flag 
        stored_vdb as 0 are uploaded to appropriate VDB: this indicates
        that they have not yet been copied to Chroma """
    vdb_insert()
