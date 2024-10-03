import streamlit as st
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

# ElasticSearch Connection
indexName = "all_products"

try:
    es = Elasticsearch(
        "https://localhost:9200",
        basic_auth=("elastic", "pDjStGnelbMpjssD9QqR"),
        ca_certs="/Users/someshs/Desktop/internship workspace 2024/elasticsearch-8.15.2/config/certs/http_ca.crt"
    )
except ConnectionError as e:
    print("Connection Error:", e)

if es.ping():
    print("Successfully connected to Elasticsearch!!")
else:
    print("Oops!! Cannot connect to Elasticsearch!")


# Search function with filters based on new mapping
def search(input_keyword, category=None, price_range=None, brand=None, gender=None, primary_color=None):
    model = SentenceTransformer('all-mpnet-base-v2')
    vector_of_input_keyword = model.encode(input_keyword)

    # KNN query
    knn_query = {
        "field": "DescriptionVector",
        "query_vector": vector_of_input_keyword,
        "k": 10,
        "num_candidates": 500
    }

    # Filter section of the query
    filter_query = []
    if category:
        filter_query.append({"term": {"ProductName": category}})
    if price_range:
        filter_query.append({
            "range": {
                "Price (INR)": {
                    "gte": price_range[0],
                    "lte": price_range[1]
                }
            }
        })
    if brand:
        filter_query.append({"term": {"ProductBrand": brand}})
    if gender:
        filter_query.append({"term": {"Gender": gender}})
    if primary_color:
        filter_query.append({"term": {"PrimaryColor": primary_color}})

    # Full query with filters
    full_query = {
        "knn": knn_query,
        "filter": {
            "bool": {
                "must": filter_query
            }
        }
    }

    res = es.knn_search(index=indexName, knn=knn_query, source=["ProductName", "Description", "Price (INR)", "ProductBrand", "PrimaryColor", "Gender"])
    results = res["hits"]["hits"]

    return results


# Streamlit App
def main():
    # Create two columns: left for filters, right for search bar and results
    col1, col2 = st.columns([1, 3])

    # Filters in the left column
    with col1:
        st.header("Filters")
        
        # Additional Filters
        category = st.text_input("Product Name (Category)")
        price_range = st.slider("Price Range (INR)", 0, 5000, (500, 3000))
        brand = st.text_input("Brand (optional)")
        gender = st.selectbox("Gender", ["All", "Male", "Female", "Unisex"])
        primary_color = st.text_input("Primary Color (optional)")
        
    # Search bar and results in the right column
    with col2:
        st.title("Search Myntra Fashion Products")

        # Input: User enters search query
        search_query = st.text_input("Enter your search query")

        # Button: User triggers the search
        if st.button("Search"):
            if search_query:
                # If "All" is selected for gender, treat it as no filter
                selected_gender = None if gender == "All" else gender

                # Perform the search and get results
                results = search(search_query, category, price_range, brand, selected_gender, primary_color)

                # Display search results
                st.subheader("Search Results")
                for result in results:
                    with st.container():
                        if '_source' in result:
                            try:
                                st.header(f"{result['_source']['ProductName']}")
                            except Exception as e:
                                print(e)

                            try:
                                st.write(f"Description: {result['_source']['Description']}")
                            except Exception as e:
                                print(e)

                            # Display price, brand, primary color, and gender if available
                            try:
                                st.write(f"Price (INR): ₹{result['_source']['Price (INR)']}")
                            except Exception as e:
                                print(e)
                            try:
                                st.write(f"Brand: {result['_source']['ProductBrand']}")
                            except Exception as e:
                                print(e)
                            try:
                                st.write(f"Primary Color: {result['_source']['PrimaryColor']}")
                            except Exception as e:
                                print(e)
                            try:
                                st.write(f"Gender: {result['_source']['Gender']}")
                            except Exception as e:
                                print(e)

                            st.divider()


if __name__ == "__main__":
    main()
