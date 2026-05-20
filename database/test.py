from models.user_schema import UserSchema
from database.mongodb import users

user = UserSchema(username="Vardhan")

users.insert_one(user.model_dump())
