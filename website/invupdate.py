import sys
print("PYTHONPATH:", sys.path)  # Print the Python path for debugging

import pandas as pd
from sqlalchemy.orm import sessionmaker
from website import db
from website.models import Donor

# Database connection
engine = db.engine
Session = sessionmaker(bind=engine)
session = Session()

# Create all tables in the database which are defined by Base's subclasses
db.create_all()

# Read the Excel file
file_path = 'donors.xlsx'  # Update the file path as needed
df = pd.read_excel(file_path)

# Iterate over the rows in the DataFrame and add them to the database
for index, row in df.iterrows():
    donor = Donor(
        id=row['id'],
        name=row['name'],
        department=row['department'],
        year_of_graduation=row['year of graduation']
    )
    session.add(donor)

# Commit the session to save the data
session.commit()

# Close the session
session.close()
