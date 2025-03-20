# Assuming you have imported the User model
from models import User

# Fetch a user from the database based on some criteria
# For example, let's say you want to find a user by their email address
email_to_find = 'Kumar@Kishore.com'
user = User.query.filter_by(email=email_to_find).first()

# Check if the user exists
if user:
    # Print user ID
    print("User ID:", user.id)
else:
    print("User not found")
