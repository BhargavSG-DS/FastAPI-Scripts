import datetime
import secrets
from http import HTTPStatus
from analytics import analyze
import dateutil.parser as dparser
import models
import requests
import schemas
from authentication import *
from better_profanity import profanity
from database import SessionLocal, engine
from fastapi import (Depends, FastAPI, File, HTTPException, Query, Request,
                     UploadFile)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_pagination import Page, add_pagination, paginate
from PIL import Image
from sqlalchemy.orm import Session
import pandas as pd
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Intialize App
app = FastAPI()

# Creating app server port for frontend
origins = {
    "http://localhost",
    "http://localhost:3000",
}

# Adding middleware for frontend and backend communication
app.add_middleware(
   CORSMiddleware,
    allow_origins = origins,
    allow_credentials =True,
    allow_methods = ["*"],
    allow_headers= ["*"],
)

# Setting path to token to authenticate the user
oath2_scheme = OAuth2PasswordBearer(tokenUrl='token')
templates = Jinja2Templates(directory="templates")

# Root / Index 
@app.get('/',tags=['Root'])
def root():
    raise HTTPException(
            status_code=HTTPStatus.METHOD_NOT_ALLOWED,
            detail="Please Use Port 3000.",
            headers={"WWW-Authenticate":"Bearer"}
        )

app.mount('/static',StaticFiles(directory=r'C:\Users\Bharg\CyberSecNewsBlog\backend\static'),name="static")
#-----------------------------------------------------------------------------Token Api---------------------------------------------------------------------------------------------------

# Token api
@app.post('/token',tags=['Login Token'])
async def generate_token(form_data : OAuth2PasswordRequestForm = Depends(),db : Session = Depends(get_db)):
    token = await token_gen(form_data.username, form_data.password,db=db)
    return {"access_token": token, "token_type" : "Bearer"}

# Getting current authorized user
async def get_current_user(token : str = Depends(oath2_scheme),db : Session = Depends(get_db)):
    try:
        decoded_token = jtoken.decode(token,credentials['SECRET'],algorithms=[credentials['Algorithm']])
        user = db.query(models.User).filter(models.User.username==decoded_token.get('username')).first()
    except:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Invalid username or password",
            headers={"WWW-Authenticate":"Bearer"}
        )
    return user
#------------------------------------------------------------------Admin Api--------------------------------------------------------------------------------------------------------------
@app.post("/admin/register", tags=['Admin'],status_code=HTTPStatus.CREATED)
async def registerAdmin(user : schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_admin = models.Admin(userID=user.id)

    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return{
        "detail" : f"Welcome to CSNB.in Admin, {new_admin.user.fullname}."
    }

@app.post("/admin/{b_id}/approve",tags=['Admin'],status_code=HTTPStatus.ACCEPTED)
async def approveBlogs(b_id : int,user : schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.user==user).first()
    if not admin:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Not Authorised to perform this action",
        )
    qry = db.query(models.Blog).filter(models.Blog.b_id==b_id)
    qry.update({"approved":True,"approverID":admin.id})
    db.commit()
    return {
        "detail" : "Blog Approved."
    }

@app.get("/admin/blogs/{filter}",tags=['Admin'],status_code=HTTPStatus.ACCEPTED,response_model=Page[schemas.Blog])
async def filteredBlogs(filter : bool,user : schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.user==user).first()
    if not admin:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Not Authorised to perform this action",
        )
    blogs = db.query(models.Blog).filter(models.Blog.approved==filter).all()
    if not blogs:
            raise HTTPException(
            status_code=HTTPStatus.NO_CONTENT,
            detail="No Blogs.",
            ) 
    return paginate(blogs)

@app.get("/admin/users/{filter}",tags=['Admin'],status_code=HTTPStatus.ACCEPTED,response_model=Page[schemas.User])
async def filteredUsers(filter : str, user : schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.user==user).first()
    if not admin:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Not Authorised to perform this action",
        )
    users = db.query(models.User).filter(models.User.gender==filter.lower()).all()
    if not users:
        raise HTTPException(
        status_code=HTTPStatus.NO_CONTENT,
        detail="No users of that gender.",
        ) 
    return paginate(users)

#-------------------------------------------------------------User Api-------------------------------------------------------------------------------------------------------------------


@app.post("/user/register", tags=['User'],status_code=HTTPStatus.CREATED)
async def register(user : schemas.UserCreate, db: Session = Depends(get_db)):
    user_info = user.dict(exclude_unset=True)
    user_info["password"] = hash_password(user_info["password"])
    user_info["gender"] = str(user_info["gender"]).lower()
    
    if db.query(models.User).filter(models.User.username==user_info["username"]).first():
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="User already Exists.",
            headers={"WWW-Authenticate":"Bearer"}
        )
    else:
        new_user = models.User(**user_info)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return{
            "detail" : f"Welcome to CSNB.in, {new_user.fullname}, Thanks for Choosing Our Service, Please Verify your Email."
        }

@app.post("/user/login",tags=['User'],status_code=HTTPStatus.OK,response_model=schemas.User)
async def login(user : schemas.User = Depends(get_current_user)):
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Invalid username or password",
            headers={"WWW-Authenticate":"Bearer"}
        )
    return user

# Deleting User 
@app.delete("/user/remove",tags=['User'],status_code=HTTPStatus.ACCEPTED)
async def delete_account(db: Session = Depends(get_db),user : schemas.User = Depends(get_current_user)):
        db.query(models.User).filter(models.User.id == user.id).delete()
        db.commit()
        return{
            "detail" : "Your Profile has been removed, Sorry to see you go."
        }


@app.put("/user/update", tags=['User'],status_code=HTTPStatus.ACCEPTED)
async def update_user(user_info : schemas.User,user : schemas.User = Depends(get_current_user),db: Session = Depends(get_db)):
    updated_user_info = user_info.dict(exclude_unset=True)

    if db.query(models.User).filter(models.User.id!=user.id).filter(models.User.username==updated_user_info["username"]).first():
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Username already taken.",
            headers={"WWW-Authenticate":"Bearer"}
        )
    else:     
        db.query(models.User).filter(models.User.id == user.id).update(updated_user_info)
        db.commit()
    
        return {'data' : 'Blog Content is updated sucessfully!'}

@app.put("/user/resetpassword", tags=['User'],status_code=HTTPStatus.ACCEPTED)
async def reset_password(user_password : str,user : schemas.User = Depends(get_current_user),db: Session = Depends(get_db)):
    user_password = hash_password(user_password)
    db.query(models.User).filter(models.User.id == user.id).update({"password":user_password})
    db.commit()

    return {'data' : 'Password is updated sucessfully!'}        

@app.post("/user/upload/profile", tags=['User'],status_code=HTTPStatus.OK)
async def upload_profile(db: Session = Depends(get_db),file:UploadFile = File(...),user: schemas.User = Depends(get_current_user)):
    
    FILEPATH = "C:/Users/Bharg/CyberSecNewsBlog/backend/static/users/"
    filename = file.filename
    extension = filename.split(".")[1]
    
    if extension not in ['png','jpg','jpeg']:
        raise HTTPException(
            status_code=HTTPStatus.NOT_ACCEPTABLE,
            detail="Please Upload a png or jpg.",
        )
        
    if user.profilePicture == "UserDefault.jpg":
        # Generate a random hex and add to to file-name to avoid duplication of news image names
        file_name = secrets.token_hex(10) + "." + extension
        _genFilename = FILEPATH + file_name
        _content = await file.read()
        
        with open(_genFilename,'wb') as file:
            file.write(_content)
            
        #Limiting image size to save server space using PILLOW
        img = Image.open(_genFilename)
        img = img.resize(size=(470,960))
        file.close()
        
        db.query(models.User).filter(models.User.id==user.id).update({"profilePicture": file_name})
        db.commit()
        db.refresh(User)
            
        return {'status' : 'User Image Uploaded'}
    
    else:
        currentfile = FILEPATH + User.profilePicture
        _content = await file.read()

        with open(currentfile,'wb') as newfile:
            newfile.write(_content)
        
        img = Image.open(currentfile)
        img = img.resize(size=(470,960))
        await file.close()

        return {'status' : 'User Image Updated.'}
    

#------------------------------------------------------------------News Api--------------------------------------------------------------------------------------------------------------

def fetchCategoryNews(category : str):
    news = requests.get(url=f"https://newsapi.org/v2/everything?q={category}&apiKey={credentials['KEY']}")
    articles = news.json()["articles"]
    return articles

@app.post("/news/{category}", tags=['News'],status_code=HTTPStatus.CREATED)
async def fetch_News(category : str,user : schemas.User = Depends(get_current_user),db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.user==user).first()
    if not admin:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Not Authorised to perform this action",
        )
    articles = fetchCategoryNews(category=category)
    for article in articles:
        if db.query(models.News).filter(models.News.title==article['title']).first():
            continue
        article["source"] = article["source"]["name"]
        article["publishedAt"] = dparser.parse(article["publishedAt"] ,fuzzy=True)
        new_article = models.News(**article)
        db.add(new_article)
    db.commit()
    return {
        "detail" : "News Successfully Fetched."
    }

@app.get("/news/TopHeadline",tags=["News"],status_code=HTTPStatus.OK)
async def get_top_headline(user : schemas.User = Depends(get_current_user),db : Session = Depends(get_db)):
    headline = db.query(models.News).order_by(models.News.publishedAt).first()
    return headline


@app.get('/news/all',tags=["News"],status_code=HTTPStatus.OK,response_model=Page[schemas.News])
async def get_news(user : schemas.User = Depends(get_current_user),db: Session = Depends(get_db)):
        news = db.query(models.News).all()
        if not news:
            raise HTTPException(
            status_code=HTTPStatus.NO_CONTENT,
            detail="No Content.",
            ) 
        return paginate(news)

#------------------------------------------------------------------Blog Api--------------------------------------------------------------------------------------------------------------
@app.post("/blog/{newsId}/upload",tags=['Blog'],status_code=HTTPStatus.OK)
async def blog_upload(newsId : int ,blog : schemas.BlogBase ,user : models.User = Depends(get_current_user),db: Session = Depends(get_db)):
    blog_info = blog.dict(exclude_unset=True)
    news = db.query(models.News).filter(models.News.n_id==newsId).first()
    if not news:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Not Found.",
            )

    blog_info["description"] = str(profanity.censor(blog_info["description"]))
    new_blog = models.Blog(**blog_info,authorID=user.id,newsID=news.n_id)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)

    return {
        "detail" : "Blog Successfully Created."
    }

@app.post("/blog/{b_id}/banner", tags=['Blog'],status_code=HTTPStatus.OK)
async def upload_banner(b_id : int, db: Session = Depends(get_db),file:UploadFile = File(...),user: schemas.User = Depends(get_current_user)):
    qry = db.query(models.Blog).filter(models.Blog.b_id==b_id)
    blog = qry.first()
    FILEPATH = "C:/Users/Bharg/CyberSecNewsBlog/backend/static/blogs/"
    filename = file.filename
    extension = filename.split(".")[1]
    
    if extension not in ['png','jpg','jpeg']:
        raise HTTPException(
            status_code=HTTPStatus.NOT_ACCEPTABLE,
            detail="Please Upload a png or jpg.",
        )

    if blog.banner == "BlogDefault.png":
        # Generate a random hex and add to to file-name to avoid duplication of news image names
        file_name = secrets.token_hex(10) + "." + extension
        _genFilename = FILEPATH + file_name
        _content = await file.read()
        
        with open(_genFilename,'wb') as file:
            file.write(_content)
            
        #Limiting image size to save server space using PILLOW
        img = Image.open(_genFilename)
        img = img.resize(size=(470,960))
        file.close()
        
        qry.update({"banner": file_name})
        db.commit()
        db.refresh(User)
            
        return {'status' : 'Blog Banner Uploaded'}
    
    else:
        currentfile = FILEPATH + blog.banner
        _content = await file.read()

        with open(currentfile,'wb') as newfile:
            newfile.write(_content)
        
        img = Image.open(currentfile)
        img = img.resize(size=(470,960))
        await file.close()

        return {'status' : 'Blog Banner Updated.'}

@app.get('/blog/all',tags=["Blog"],status_code=HTTPStatus.OK,response_model=Page[schemas.Blog])
async def get_blogs(user : models.User = Depends(get_current_user),db: Session = Depends(get_db)):
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="You are not Authorized.",
            )
        blogs = db.query(models.Blog).filter(models.Blog.approved == True).all()
        if not blogs:
            raise HTTPException(
            status_code=HTTPStatus.NO_CONTENT,
            detail="No Content.",
            ) 
        return paginate(blogs)

@app.get('/blog/{b_id}',tags=["Blog"],status_code=HTTPStatus.OK,response_model=schemas.Blog)
async def get_blog(b_id : int,user : models.User = Depends(get_current_user) ,db: Session = Depends(get_db)):
        if not user:
            raise HTTPException(
                status_code=HTTPStatus.UNAUTHORIZED,
                detail="You are not Authorized.",
            )
        blog = db.query(models.Blog).filter(models.Blog.b_id==b_id).first()
        if not blog:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail="Not Found.",
            ) 
        return blog

@app.post("/blog/{b_id}/like",tags=['Blog'],status_code=HTTPStatus.ACCEPTED)
async def likeBlog(b_id : int,user : schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    
    qry = db.query(models.Blog).filter(models.Blog.b_id==b_id)
    qry.update({"likes":qry.first().likes + 1})
    db.commit()
    return {
        "detail" : "Blog Liked."
    }

@app.delete('/blog/{b_id}/remove',tags=['Blog'],status_code=HTTPStatus.OK)
async def blog_remove(b_id: int,user : schemas.User = Depends(get_current_user),db: Session = Depends(get_db)):
    qry = db.query(models.Blog).filter(models.Blog.b_id==b_id)
    blog = qry.first()
    if blog.authorID != user.id:    
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Not Authorized to perform this action.",
        )

    qry.delete()
    db.commit()
    return{'data' : 'The requested blog has been removed.'}
#------------------------------------------------------------------Comment Api--------------------------------------------------------------------------------------------------------------
@app.post("/blog/{b_id}/comment/upload",tags=['Comments'],status_code=HTTPStatus.OK)
async def comment_upload(b_id : int,comment : schemas.CommentBase, user : models.User = Depends(get_current_user),db: Session = Depends(get_db)):
    comment_content = comment.dict(exclude_unset=True)
    blog = db.query(models.Blog).filter(models.Blog.b_id==b_id).first()
    if not blog:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="Not Found.",
        )
    
    comment_content["description"] = profanity.censor(comment_content["description"])

    new_comment = models.Comment(**comment_content,userID=user.id,blogID=blog.b_id)
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return {
        "detail" : "Comment uploaded."
    }

@app.delete('/comment/{c_id}/remove',tags=['Comments'],status_code=HTTPStatus.OK)
async def comment_remove(c_id: int,user : schemas.User = Depends(get_current_user),db: Session = Depends(get_db)):
    qry = db.query(models.Comment).filter(models.Comment.c_id==c_id)
    comment = qry.first()
    if comment.userID != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Not Authorized to perform this action.",
        )
    
    qry.delete()
    db.commit()
    return{'data' : 'The requested comment has been removed.'}

@app.put('/comment/{c_id}/update',tags=['Comments'],status_code=HTTPStatus.OK)
async def comment_remove(c_id: int,comment_content : schemas.CommentBase,user : schemas.User = Depends(get_current_user),db: Session = Depends(get_db)):
    new_comment_content = comment_content.dict(exclude_unset=True)
    qry = db.query(models.Comment).filter(models.Comment.c_id==c_id)
    comment = qry.first()
    if comment.userID != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Not Authorized to perform this action.",
        )
    
    qry.update(new_comment_content)
    db.commit()
    db.refresh(comment)
    return{'data' : 'Comment content updated.'}

@app.get('/blog/{blogID}/comment/analytics',tags=['Comments'],status_code=HTTPStatus.OK)
async def get_analytics(blogID : int,user : schemas.User = Depends(get_current_user),db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.b_id==blogID).first()
    if blog.authorID != user.id:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail="Not Authorized to perform this action.",
        )
    
    comments = pd.read_sql_query(sql=f"SELECT [description] FROM comments WHERE [blogID] == {blog.b_id};",con=db.connection())
    comments = comments["description"].to_list()
    analysis = analyze(comments)
    valDict = {
        1 : "positive",
        0 : "neutral",
        -1: "negative" 
    }
    analytics = {comments[i]: valDict[analysis[i]] for i in range(0, len(comments), 1)}

    return analytics

# Adding Pagitation to app for blogs
add_pagination(app)