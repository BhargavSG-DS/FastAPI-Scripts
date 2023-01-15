from database import Base
from sqlalchemy import Column, ForeignKey, Integer, Boolean, String, Date, DateTime
from sqlalchemy.orm import relationship,ONETOMANY,MANYTOONE
from datetime import datetime
from pydantic import validator

# User Orm Model
class User(Base):
    __tablename__ = "users"

    # fields
    id = Column(Integer, primary_key=True)
    profilePicture = Column(String,default="UserDefault.jpg")
    fullname = Column(String)
    username = Column(String)
    description = Column(String)
    email = Column(String)
    gender = Column(String)
    isAdmin = Column(Boolean, default=False)
    password = Column(String)
    createdAt = Column(DateTime, default=datetime.now())

    @validator('gender')
    def valid_gender(cls,val):
        if val not in ['male','female','other','rather not say']:
            raise ValueError('Invalid Gender Value')
        return val
    

class Admin(Base):
    __tablename__ = "admin"

    # fields
    id = Column(Integer, primary_key=True)
    userID = Column(Integer,ForeignKey("users.id"))
    createdAt = Column(DateTime, default=datetime.now())

    user = relationship("User", back_populates = "admin")


class News(Base):
    __tablename__ = "news"

    # fields
    n_id = Column(Integer, primary_key=True)
    author = Column(String)
    title = Column(String)
    description = Column(String)
    url = Column(String)
    urlToImage = Column(String)
    source = Column(String)
    content = Column(String)
    publishedAt = Column(DateTime, default=datetime.now())


class Blog(Base):
    __tablename__ = "blogs"

    # fields
    b_id = Column(Integer, primary_key=True)
    bannner = Column(String, default="BlogDefault.png")
    title = Column(String)
    description = Column(String)
    authorID = Column(Integer,ForeignKey("users.id"))
    newsID = Column(Integer,ForeignKey("news.n_id"))
    approverID = Column(Integer,ForeignKey("admin.id"))
    approved = Column(Boolean, default = False)
    likes = Column(Integer,default=0)
    publishedAt = Column(DateTime, default=datetime.now())

    newsItem = relationship("News", back_populates = "blogs")
    author = relationship("User", back_populates = "blogs")
    approvedBy = relationship("Admin", back_populates = "approvedblogs")
    

class Comment(Base):
    __tablename__ = "comments"

    # fields
    c_id = Column(Integer, primary_key=True)
    description = Column(String)
    userID = Column(Integer,ForeignKey("users.id"))
    blogID = Column(Integer,ForeignKey("blogs.b_id"))
    publishedAt = Column(DateTime, default=datetime.now())
    likes = Column(Integer,default=0)

    blog = relationship("Blog", back_populates = "comments")
    author = relationship("User", back_populates = "comments")

News.blogs = relationship("Blog", order_by = Blog.b_id, back_populates = "newsItem")

User.blogs = relationship("Blog", order_by = Blog.b_id, back_populates = "author")
User.comments = relationship("Comment", order_by = Comment.c_id, back_populates = "author")
User.admin = relationship("Admin",back_populates="user")

Blog.comments = relationship("Comment", order_by = Comment.c_id, back_populates = "blog")

Admin.approvedblogs = relationship("Blog", order_by = Blog.b_id, back_populates = "approvedBy")