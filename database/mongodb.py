from pymongo import MongoClient
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from models.user_schema import UserSchema
from models.workout_schema import WorkoutSchema
import os
load_dotenv()
mongurl = (os.getenv("MONGO_URL"))


@st.cache_resource
def get_database():
    client = MongoClient(mongurl)

    db = client["gymcoach"]

    return db


db = get_database()

users = db["users"]
workouts = db["workouts"]


def get_user(username):
    return users.find_one({"username": username})


def create_user(username):
    user = UserSchema(username=username)
    users.insert_one(user.model_dump())

    return get_user(username)


def get_or_create_user(username):

    user = get_user(username)

    if user is None:

        user = create_user(username)

    return user


def add_exercise(user_id, exercise_name, reps, sets, time):

    today = datetime.now().strftime("%Y-%m-%d")
    existing_workout = workouts.find_one(
        {"user_id": user_id, "exercise_name": exercise_name, "date": today}
    )

    if existing_workout:
        workouts.update_one(
            {"_id": existing_workout["_id"]},
            {"$inc": {"reps": reps, "sets": sets, "time": time}},
        )
    else:
        workout = WorkoutSchema(
            user_id=user_id,
            exercise_name=exercise_name,
            reps=reps,
            sets=sets,
            time=time,
        )
        workout_data = workout.model_dump()
        workout_data["date"] = today
        workouts.insert_one(workout_data)


def get_users_exercises(user_id):

    workouts = workouts.find({"user_id": user_id})

    return list(workouts)
