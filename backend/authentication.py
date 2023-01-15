from passlib.context import CryptContext
from fastapi import HTTPException
import smtplib
from sqlalchemy.orm import Session
from typing import List
from models import User
import jwt as jtoken
from dotenv import dotenv_values

from http import HTTPStatus


pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

# Hash function to encrypt User: Password
def hash_password(password):
    return pwd_context.hash(password)

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

credentials = dotenv_values(".env")

# Verification mail to be sent on Sign-up   
async def send_verification(email:List,user):
    server = smtplib.SMTP_SSL(host='smtp-mail.outlook.com')
    server.ehlo()
    server.login(credentials['EMAIL'],  credentials['PASSWORD'])

    token = {
        "username" : user['username'],
    }
    
    tokengen = jtoken.encode(token,credentials["SECRET"],algorithm=credentials['Algorithm'])

    template = f"""
    <html lang="en">
    <body>
        <div style="border-radius:1rem;background-color: rgb(122, 122, 122);margin: 5%;padding :5%;">
            <div style="display: flex; align-items:center; justify-content: center; border: .1rem solid black ;border-radius:.5rem; padding:5%; background-color : white">
                <blockquote>
                    <h2 style="text-align:center; font-family: 'Franklin Gothic Medium';">Email Confirmation</h2>
                </blockquote>
                <figcaption>
                    "Thanks For Choosing Filthrift, Please Click on the Below Button to verify your account."
                </figcaption>
                <div style="text-align:center; background-color: rgb(255, 255, 255); width:50% ;margin: auto; margin-top: 3rem; border:.1rem solid black; padding: .5rem;border-radius:1rem;">
                    <a href="http://localhost:8000/user/verify/?token={tokengen}" style="text-decoration: none; color : black;">Verify your Email!</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    full_email = ("From: {0} <{1}>\n"
                  "To: {2} <{3}>\n"
                  "Subject: {4}\n\n"
                  "{5}"
                  .format("CSNB.in", credentials['EMAIL'], user['username'], email, subject='CSNB Account Verification',message=template))

    try:
        await server.sendmail(credentials['EMAIL'], [email], full_email)
        print('Email to {} successfully sent!\n\n'.format(email))
    except Exception as e:
        print('Email to {} could not be sent :( because {}\n\n'.format(email, str(e)))

# Close the smtp server
    server.close()
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

credentials = dotenv_values(".env")

# Token Verification
async def verify_user(passwordPlain,passwordEncrypted):
    return pwd_context.verify(passwordPlain,passwordEncrypted)

def verify_token(token :str,db:Session):

    print('\n verifying...')

    try:
        payload = jtoken.decode(token, credentials['SECRET'], algorithms=[credentials['Algorithm']])
        user = db.query(User).filter(User.username == payload.get('username')).first()
        
    except:
        raise HTTPException(
            status_code=HTTPStatus.NOT_ACCEPTABLE,
            detail="Invalid Token",
            headers={"WWW-Authenticate":"Bearer"}
        )
    return user


# User Authentication
async def authenticate(username,password,db:Session):
    user = db.query(User).filter(User.username == username).first()
    if user and await verify_user(password, user.password):
        return user
    return False


# Token Generation
async def token_gen(username :str, password :str,db:Session):
    user = await authenticate(username, password,db=db)
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Invalid User, Please Check Your Credentials.",
            headers={"WWW-Authenticate":"Bearer"}
        )
    
    token_data = {
        "username" : user.username,
    }
    token = jtoken.encode(token_data,credentials['SECRET'],algorithm=credentials['Algorithm'])
    return token