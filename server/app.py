#!/usr/bin/env python3

# Import necessary components to run app
from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from config import app, db, api
from models import User, Recipe, UserSchema, RecipeSchema

# Create a signup class to create user accounts
class Signup(Resource):

    # Create a function to obtain the data sent
    def post(self):
        data = request.get_json()

        # Perform error handling using try catch
        try:
            # Create users with username, image_url, and bio attributes from the request
            user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )

            # The setter in models.py will trigger here it is in charge of hashing the password from bcrypt
            user.password_hash = data.get('password')

            # Add the user to the session
            db.session.add(user)

            # Make sure to commit
            db.session.commit()

            # Set the user_id for the session
            session['user_id'] = user.id

            # Serialized the new user with JSON
            return UserSchema().dump(user), 201
        
        # Error handling: control for if the username already exists
        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username already taken']}, 422
        
        # Error handling: controling for other errors
        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422


# Create a class to allow the frontend to verify if user is loggedin
class CheckSession(Resource):

    # Create a function to check if no user
    def get(self):
        user_id = session.get('user_id')

        # Control flow if user_id found to return their data
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            return UserSchema().dump(user), 200

        # Otherwise nobody was logged in to begin with
        return {'errors': ['Unauthorized']}, 401

# Create a login class to authenticates a user and stores their id with each session
class Login(Resource):

    # Create a function to get the usernames and passwords
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        # Search for the user by username
        user = User.query.filter(User.username == username).first()

        # Perform error handlign and control flow for if passwords match to saave user_id to session
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return UserSchema().dump(user), 200

        # Return message
        return {'errors': ['Invalid username or password']}, 401

# Create a class to logout user and clear the session
class Logout(Resource):
    
    # Create a function to check if user is logged in
    def delete(self):

        # Perform error handling
        if not session.get('user_id'):
            return {'errors': ['Unauthorized']}, 401

        # Set to none to force log out
        session['user_id'] = None
        return {}, 204



# Create a class to view or create recipes
class RecipeIndex(Resource):
    
    # Create a function so that only logged in users can view recipes
    def get(self):
        # Perform error handling
        if not session.get('user_id'):
            return {'errors': ['Unauthorized']}, 401

        # Search recipes and serialize to JSON
        recipes = [RecipeSchema().dump(r) for r in Recipe.query.all()]
        return recipes, 200
    
    # Create a function so that logged-in users create recipes
    def post(self):

        # Perform error handling
        if not session.get('user_id'):
            return {'errors': ['Unauthorized']}, 401
        
        # JSONIFY the data
        data = request.get_json()

        # Perform control flow to create new recipes from users
        try:
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=session.get('user_id')
            )

            # Add to db and commit
            db.session.add(recipe)
            db.session.commit()

            # Return the recipe serialized and in JSON
            return RecipeSchema().dump(recipe), 201
        
        # Error handling: controling for other errors
        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422


# Register each Resource class to its URL route and endpoint
api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)