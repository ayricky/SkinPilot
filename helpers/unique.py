import sqlite3


def get_unique_button_text():
    # Connect to the database
    connection = sqlite3.connect("data/cs_items.db")
    cursor = connection.cursor()

    # Query to get unique values in the button_text column of the buff163 table
    query = "SELECT DISTINCT button_text FROM buff163"
    cursor.execute(query)

    # Fetch the unique values and print them
    unique_values = cursor.fetchall()
    for value in unique_values:
        print(value[0])

    # Close the connection
    connection.close()


if __name__ == "__main__":
    get_unique_button_text()
