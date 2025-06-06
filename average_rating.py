from typing import Union, Any
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Load data
book_file_path = r"books.csv"
books_df = pd.read_csv(book_file_path)

users_file_path = (
    r"users.csv"
)
users_df = pd.read_csv(users_file_path)

ratings_file_path = (
    r"ratings.csv"
)
rating_df = pd.read_csv(ratings_file_path)

# Split location into city, state, and country
list_ = users_df.Location.str.split(", ")

city = []
state = []
country = []
count_no_state = 0
count_no_country = 0

for i in range(0, len(list_)):
    if (
        list_[i][0] == " "
        or list_[i][0] == ""
        or list_[i][0] == "n/a"
        or list_[i][0] == ","
    ):  # removing invalid
        # entries too
        city.append("other")
    else:
        city.append(list_[i][0].lower())

    if len(list_[i]) < 2:
        state.append("other")
        country.append("other")
        count_no_state += 1
        count_no_country += 1
    else:
        if (
            list_[i][1] == " "
            or list_[i][1] == ""
            or list_[i][1] == "n/a"
            or list_[i][1] == ","
        ):  # removing invalid
            # entries
            state.append("other")
            count_no_state += 1
        else:
            state.append(list_[i][1].lower())

        if len(list_[i]) < 3:
            country.append("other")
            count_no_country += 1
        else:
            if (
                list_[i][2] == ""
                or list_[i][1] == ","
                or list_[i][2] == " "
                or list_[i][2] == "n/a"
            ):
                country.append("other")
                count_no_country += 1
            else:
                country.append(list_[i][2].lower())

users_df = users_df.drop("Location", axis=1)

temp = []
for ent in city:
    c = ent.split(
        "/"
    )  # handling cases where city/state entries from city list as state is already given
    temp.append(c[0])

df_city = pd.DataFrame(temp, columns=["City"])
df_state = pd.DataFrame(state, columns=["State"])
df_country = pd.DataFrame(country, columns=["Country"])

users_df = pd.concat([users_df, df_city, df_state, df_country], axis=1)

# Drop duplicate rows
users_df.drop_duplicates(keep="last", inplace=True)
users_df.reset_index(drop=True, inplace=True)

# Merging Datasets
df = pd.merge(books_df, rating_df, on="ISBN", how="inner")
df = pd.merge(df, users_df, on="User-ID", how="inner")


# Function for getting most popular recommendations
def most_popular(df, books_df, n):
    if n >= 1 and n <= len(df):
        popular = (
            df.groupby("ISBN")["Book-Rating"]
            .count()
            .reset_index()
            .sort_values(by="Book-Rating", ascending=False)
            .head(n)
        )
        popular_books = pd.merge(popular, books_df, on="ISBN")
        return popular_books
    return pd.DataFrame()


# Function to calculate weighted average and get top books
def calculate_top_books(df_relevant_data):
    # Calculating the weighted average rating of the books
    v = df_relevant_data["ratings_count"]
    R = df_relevant_data["avg_rating"]
    C = df_relevant_data["avg_rating"].mean()
    m = int(
        df_relevant_data["ratings_count"].quantile(0.90)
    )  # minimum number of votes to be listed

    df_relevant_data["weighted_average"] = round(((R * v) + (C * m)) / (v + m), 2)

    # Sorting the dataframe by weighted_average in descending order and selecting the top 10
    top_books = df_relevant_data.sort_values(
        by="weighted_average", ascending=False
    ).head(10)

    return top_books


# Streamlit UI
def main():
    st.title("Popular Book Recommendations")
    st.markdown(
        """
        <style>
        .reportview-container {
            background: url('https://cdn.pixabay.com/photo/2015/09/05/20/02/library-924584_960_720.jpg');
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;
            color: #fff;
        }
        .sidebar .sidebar-content {
            background: rgba(0, 0, 0, 0.7);
            color: #fff;
        }
        .stButton>button {
            color: #fff;
            background-color: #008CBA;
            border-color: #008CBA;
            border-radius: 5px;
        }
        .stButton>button:hover {
            background-color: #005f77;
        }
        .stTextInput>div>div>input {
            border-color: #008CBA;
        }
        .books-container {
            display: flex;
            flex-wrap: nowrap;
            overflow-x: auto;
            padding: 10px;
        }

        .book-image {
            width: 25%;
            height: auto; 
            float: left;
            margin-right: 20px;
        }
        .book-details {
            float: left;
            width: 65%;
            padding: 10px;
        }
        .book-title {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .book-info {
            font-size: 16px;
            margin-bottom: 5px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    n = st.number_input(
        "Enter the number of popular books you want to retrieve:",
        min_value=1,
        max_value=len(df),
        value=3,
        step=1,
    )
    if st.button("Get Recommendations"):
        st.markdown(
            "<h2 style='text-align: center;'>Recommended Books</h2>",
            unsafe_allow_html=True,
        )
        popular_books = most_popular(df, books_df, n)
        if not popular_books.empty:
            st.markdown('<div class="books-container">', unsafe_allow_html=True)
            for index, row in popular_books.iterrows():
                st.markdown('<div class="book">', unsafe_allow_html=True)
                # Display the book image
                try:
                    st.markdown(
                        f'<img class="book-image" src="{row["Image-URL-M"]}" alt="{row["Book-Title"]}">',
                        unsafe_allow_html=True,
                    )
                except Exception as e:
                    st.write(
                        f"Error loading image for book: {row['Book-Title']}. Error: {e}"
                    )
                # Display the book details
                st.markdown('<div class="book-details">', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="book-title">{row["Book-Title"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="book-info">ISBN: {row["ISBN"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="book-info">Author: {row["Book-Author"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="book-info">Year of Publication: {row["Year-Of-Publication"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.title("Top Books by Weighted Average Rating")

    # Calculate relevant data for weighted average
    df_relevant_data = df.groupby(["Book-Title", "Book-Author"], as_index=False).agg(
        avg_rating=("Book-Rating", "mean"), ratings_count=("Book-Rating", "count")
    )

    # Calculate weighted average and get top books
    top_books = calculate_top_books(df_relevant_data)

    # Displaying average rating and minimum number of votes required
    C = df_relevant_data["avg_rating"].mean()
    m = int(df_relevant_data["ratings_count"].quantile(0.90))
    st.write(
        f"The average rating of all the books is {C} and the minimum number of votes required by the books to be listed is {m}"
    )

    # Plotting
    st.bar_chart(top_books.set_index("Book-Title")["weighted_average"])

    # Displaying top books
    st.subheader("Top 10 Books by Weighted Average Rating")
    st.table(top_books[["Book-Title", "weighted_average"]])


if __name__ == "__main__":
    main()