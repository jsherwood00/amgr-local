from mysql_util import drop_table, new_db, db1_setup
from chroma_util import vdb_delete

if __name__ == "__main__":    
    """ These create the mysql cursor to enable deletion"""
    new_db('db1')
    db1_setup()

    """ Delete all databases """
    vdb_delete("reviews_vdb")
    vdb_delete("db1")
    drop_table("reviews")
    drop_table("meta")