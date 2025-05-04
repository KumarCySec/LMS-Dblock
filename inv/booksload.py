import pandas as pd
import sqlite3
from datetime import datetime
import numpy as np

# Path to your files
DB_PATH = 'Kishorebase.db'  # Ensure the path to your .db file is correct
EXCEL_PATH = 'booksinv.xlsx'  # Path to your Excel file

# Connect to your SQLite database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Read the Excel file into a DataFrame
df = pd.read_excel(EXCEL_PATH)

# Clean or fill missing data
df['title'] = df['title'].fillna('Unknown')  # Fill missing titles with 'Unknown'
df['author'] = df['author'].fillna('Unknown')  # Fill missing authors with 'Unknown'
df['quantity'] = df['quantity'].fillna(0).astype(int)  # Fill missing quantities with 0, and cast to int
df['language'] = df['language'].fillna('Unknown')  # Fill missing languages with 'Unknown'

# Handle missing date_of_donation (if NaT, fill with the current date)
df['date_of_donation'] = pd.to_datetime(df['date_of_donation'], errors='coerce')  # Convert to datetime
df['date_of_donation'].fillna(datetime.utcnow(), inplace=True)  # Use current datetime for missing dates

# Handle missing donor_id, fill with np.nan (which is used for NULL in DB)
df['donor_id'] = df['donor_id'].fillna(np.nan)

# Loop through rows and insert or update in DB
for index, row in df.iterrows():
    # Check if the book already exists by title and author
    cursor.execute(
        "SELECT id, quantity FROM book WHERE title = ? AND author = ?",
        (row['title'], row['author'])
    )
    result = cursor.fetchone()
    
    if result:
        # Book exists, update quantity
        book_id, current_quantity = result
        new_quantity = current_quantity + row['quantity']  # Add new quantity to existing quantity
        cursor.execute(
            "UPDATE book SET quantity = ? WHERE id = ?",
            (new_quantity, book_id)
        )
        print(f"Book '{row['title']}' by {row['author']} exists. Quantity updated to {new_quantity}.")
    else:
        # Book doesn't exist, insert new book
        cursor.execute(
            """
            INSERT INTO book (title, author, quantity, language, date_of_donation, donor_id, student_id, isbn, published_date, added_at)
            VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?)
            """,
            (
                row['title'],
                row['author'],
                row['quantity'],
                row['language'],
                row['date_of_donation'].strftime('%Y-%m-%d %H:%M:%S'),
                row['donor_id'] if pd.notnull(row['donor_id']) else None,
                datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),  # Current timestamp for 'added_at'
            )
        )
        print(f"Book '{row['title']}' by {row['author']} added to the database.")

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Book data imported/updated successfully.")
