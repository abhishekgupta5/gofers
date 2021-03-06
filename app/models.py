#app/models.py

from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from app import db
from app import login_manager

class User(UserMixin, db.Model):
    '''
    Table for users.
    '''
    __tablename__ = 'users'

    #Columns
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, unique=True, index=True)
    email = db.Column(db.String(64), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_confirmed = db.Column(db.Boolean, default=False)
    #role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    @property
    def password(self):
        '''Prevent password from being accessed'''
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        '''Set password hash'''
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        '''Verify password hash'''
        return check_password_hash(self.password_hash, password)

    #Generating confirmation token from itsdangerous for email confirmation
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm':self.id})

    #Form confirming email is verified
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.is_confirmed = True
        db.session.add(self)
        db.session.commit()
        return True

    #Generating confirmation token from itsdangerous for password reset
    def generate_reset_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset':self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('reset') != self.id:
            return False
        self.password = new_password
        db.session.add(self)
        db.session.commit()
        return True

    #Generate token for email change request
    def generate_email_change_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email':self.id, 'new_email': new_email})

    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        db.session.commit()
        return True

    def __repr__(self):
        return '<User {0}>'.format(self.email)

#Setting up user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
