**Setup**

Prerequisite: Install Docker (varies by OS): `https://docs.docker.com/engine/install/`

1) In the root project directory, run `docker compose up`. Note: you may have to run with elevated privileges (sudo on Linux).

    This will start mysql and chroma containers. Do not modify their data folders,
    which are also found in the root project directory.

2) Run the ETL pipeline, in the section below, if it is your first time / you want to load new data.
   Otherwise, the chatbot will not have any data to interact and so will not show product results. 

3) In another terminal, also from the root project directory, run `python chatbot.py`

    This is the interface for interacting with the dataset.

    First, describe your ideal product. This searches a vector database containing all product titles, and returns
    information on the top k, currently 5, products, that have titles semantically closest to your query.

    After describing your ideal product, you will be prompted to describe your ideal reviews. This is optional, and
    will take the top n (currently 100) products matching the first (product title) query, and display the top k
    products associated with the top k reviews closest to the review query. 


**ETL instructions (steps 1-3 for first time; 1, 3 after setup)**

*Note: Step 1 can be skipped if you are happy with the gift cards category included in this repository, just make sure to unzip them (step 2).*
1) The full dataset can be found at https://amazon-reviews-2023.github.io/, download the meta / review data of your choice.
    You must upload both the review and meta data for any category you pick, and not only one, or the chatbot will not work.
    It is recommended to start with a small category, such as giftcards. The speed depends mostly on the local computer's CPU
    , assuming enough RAM. The development computer has a relatively fast CPU: a Ryzen 7 9700x, and the ETL process for the
   gift cards category takes ~15 minutes: you will have to run etl.py, wait 15 minutes, then be able to run chatbot.py and
   interact with the data.

2) Place the downloaded data (.jsonl.gz files), into the root/new_data folder, **then unzip them, so the format is .jsonl.**

3) On first run, create a virtual environment and install the requirements before running step 4:

        a) `python3 -m venv <your_venv_name>`
   
        b)
            Mac/Linux: `source <your_venv_name>/bin/activate`
            Windows PowerShell: `.\<your_venv_name>\Scripts\Activate.ps1`
   
        c) pip install -r requirements.txt

5) From the root project directory, run `python etl.py`

    This will structure the raw data into the MySQL and Chroma databases, which the chatbot will then have access to.
    The upload process varies per

6) Optional: to reset the database at any point, deleting all structured data, run `python reset.py`


**Future work**


This project is currently in development. There are several tasks under development, including:

* Web-based UI
    Currently, the user must use the terminal to use the product, which is not user friendly for non-technical users.
    The end goal of this project is a web-based UI where products show up alongside their images, where available in
    the dataset, and can be selected for an Ollama-generated summary of their reviews. The Ollama container is
    generated in the Docker compose file, but the review summarization features is not provided, largely because it would
    be awkward to provide in a terminal UI.

    * More user friendly ETL

        A major benefit of ETL pipelines is dynamic data transformation. Currently, etl.py has to be run for the
        databases to reflect newly added data. This task would also require the completion of the web-based UI 
        as a prerequisite. The user would select the .jsonl file(s) of their choice via the frontend (and the backend
        would download the file for them), or even enter custom product information, and be able to see the results once
        the ETL updating has completed.


* ETL: Chunking jsonl upload

    When uploading MySQL data to Chroma, every batch updates the table to reflect a successful upload.
    This means that if an interrupt occurs mid-upload, only the batch will have to be re-uploaded, which typically
    takes around a second.

    However, when uploading from json to MySQL, the process is more dangerous: if the connection is interrupted
    mid-json upload, the entire file must be re-uploaded, which is costly. One solution currently that could be
    implemented is to chunk the raw data into multiple .jsonl files, and delete each of these once uploaded.

* ChromaDB: benchmarking with different chunking strategies

    For example, flat chunking is the current approach (1:1 product:vector), but others are possible (i.e. 
    each vector stores the embedding of k products' information, and on similarity search for the most relevant
    product for the user, those 10 are returned, instead of the products associated with 10 vectors).

    Also, the current filtering mechanism, on user query for review criteria, searches all reviews that have
    a parent_asin found in the list of parent_asins returned by the first query, and returns the products associated
    with the best-matching reviews. But this means that if a product has one review that perfectly matches the user's
    query, and several reviews that do not match the query, it will still return the product. This is not necessarily
    a limitation, just one approach. Another would be to embed all reviews for a product together, so the user query
    would be compared to a set of "summarized" product reviews, where each embedding it is compared to is 1 product's
    embedding for all of its reviews.

**Credits**: this is an individual project and an extension of work done in a Fall 2024 Big Data course. That project can be viewed here: https://github.com/jsherwood00/amgr, and was developed by a 5-person team and with Professor Koochaksaraei's mentorship. All team members are credited there.
