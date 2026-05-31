# Import necessary components to run app
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from marshmallow import Schema, fields

# Import components for db and encryption
from config import db, bcrypt

# User model in chareg of the accounts in the db
class User(db.Model):
    __tablename__ = 'users'

    # Set up a primary unique id for users
    id = db.Column(db.Integer, primary_key=True)

    # Set up unique usernames for users ensure it cannot be blank
    username = db.Column(db.String, unique=True, nullable=False)

    # Finally hash the password and store it to the db
    _password_hash = db.Column(db.String)

    # One user might have many recipes so utilize backref to let recipe.user find the owner
    recipes = db.relationship('Recipe', backref='user')

    # Use the hybrid_property decorator to let the password_hash to be a column
    @hybrid_property
    def password_hash(self):

        # Perform error handling to prevent direct reading of the hash 
        raise AttributeError('Password hash is not readable')

    # Use setter decorator
    @password_hash.setter
    def password_hash(self, password):
        # Use bcrypt to perform the hash on passwords
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # Create a function to compare the original text password to the stored hash
    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    # Use a decorator to perform error handling to validate username upon each entry
    @validates('username')
    def validate_username(self, key, username):

        # Peroform error handling for incorrect username entry
        if not username:
            raise ValueError('Username is required')
        return username

    def __repr__(self):
        return f'User {self.username}'


# Create a class for recipes created by a user
class Recipe(db.Model):
    __tablename__ = 'recipes'

    # Create a unique primary key for each recipe
    id = db.Column(db.Integer, primary_key=True)

    # Create recipe title
    title = db.Column(db.String, nullable=False)

    # Create recipe instructions
    instructions = db.Column(db.String, nullable=False)

    # Create preparation time in minutes
    minutes_to_complete = db.Column(db.Integer)

    # Create a foreign key to link this specefic recipe to its owner in db
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Use validates decorator for each time the title is set
    @validates('title')
    def validate_title(self, key, title):

        # Perform error handling for if no title is provided
        if not title:
            raise ValueError('Title is required')
        return title

    # Use validate decorator to provide instructions for the recipe every time
    @validates('instructions')
    def validate_instructions(self, key, instructions):

        # Perform error handling if no instructions or if the length is not satisfied
        if not instructions or len(instructions) < 50:
            raise ValueError('Instructions must be at least 50 characters long')
        return instructions

    def __repr__(self):
        return f'Recipe {self.title}'


# Provide a class for the Marshmallow schema to control how the users are serialized to JSON
class UserSchema(Schema):
    id = fields.Int()
    username = fields.String()
    image_url = fields.String()
    bio = fields.String()
    recipes = fields.List(fields.Nested(lambda: RecipeSchema(exclude=('user',))))


# Provide a class for the Marshmallow schema to control how recipes are serialized into JSON
class RecipeSchema(Schema):
    id = fields.Int()
    title = fields.String()
    instructions = fields.String()
    minutes_to_complete = fields.Int()
    user = fields.Nested(UserSchema(exclude=('recipes',)))