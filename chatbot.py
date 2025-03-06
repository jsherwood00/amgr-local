import os
from mysql_util import num_rows, sql_query, structure, list_tables, drop_table, create_family, \
create_meta, create_reviews, new_db, db1_setup, retrieve_product_data
from chroma_util import vdb_new, vdb_insert, vdb_query, vdb_delete, chroma_client

db1_setup()

NUM_DISPLAY = 5 # number of products printed for the user
NUM_PRODUCTS_TO_SORT = 100 # number of products to retrieve, and pass to review search

while True:
    user_input = input("Describe your product>> ")
    review_filter = input("Describe ideal reviews (enter to skip)>> ")
    ids = None


    """ If no review criteria specified, obtain the most similar 5 products and print """
    if review_filter == "":
        results = vdb_query("db1", user_input, NUM_DISPLAY, None)
        ids = results["ids"][0] # list of parent_asins
    else:
        results = vdb_query("db1", user_input, NUM_PRODUCTS_TO_SORT, None)
        ids = results["ids"][0] # list of parent_asins

        """ See additional_documentation.txt -> "long chatbot comment" for a note here """
        refined_results = vdb_query("reviews_vdb", review_filter, NUM_DISPLAY, ids)
        ids = [result.get("parent_asin") for result in refined_results["metadatas"][0]]    

    """ This section contains the logic for printing the results to the terminal """
    product_info = retrieve_product_data(ids)
    i = 1
    print("\n")
    for product in product_info:
        print(f"{i}) {product[0]}")

        rating_num = product[1]
        rating_desc = ""
        if rating_num is None or rating_num == 0:
            rating_desc = "Not available"
        elif rating_num == 1:
            rating_desc = f"\t Rating: {product[2]}/5 ({rating_num} review)"
        else:
            rating_desc = f"\t Rating: {product[2]}/5 ({rating_num}) reviews)"

        print(rating_desc)

        price = product[3]
        price = price if price is not None else "Not available"
        print(f"\t Price: {price}")

        detail_1 = product[4]
        detail_2 = product[5]
        details = ""
        if ((detail_1 is None or detail_1 == "") and (detail_2 is None or detail_2 == "")):
            details = "Not available"
        else:
            if detail_1 is not None and detail_1 != "":
                details += detail_1 + " "
            if detail_2 is not None and detail_2 != "":
                details += detail_2
        
        print(f"\t Details: {details}")

        specs = product[6]
        specs = specs if (specs is not None and specs != "") else "Not available"
        print(f"\t Specifications: {specs}\n")
        i += 1