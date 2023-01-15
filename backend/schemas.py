from datetime import datetime
from pydantic import BaseModel
from typing import List

# User Pydantic models
class UserBase(BaseModel):
    username : str
    fullname : str
    description : str | None
    email : str
    gender : str
    
class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    profilePicture : str
    createdAt : datetime    
    class Config:
        orm_mode = True

# News Pydantic models
class News(BaseModel):
    n_id: int
    author : str | None
    title : str
    description : str
    content : str
    source : str
    url : str
    urlToImage : str | None
    publishedAt : datetime
    
    class Config:
        orm_mode = True

# Comment Pydantic models
class CommentBase(BaseModel):
    description: str

class Comment(CommentBase):
    c_id: int
    author : User
    publishedAt : datetime
    
    class Config:
        orm_mode = True

# Blog Pydantic models
class BlogBase(BaseModel):
    title : str
    description: str

class Blog(BlogBase):
    b_id: int
    approved : bool
    banner : str | None
    newsItem : News
    comments : List[Comment]
    author : User
    publishedAt : datetime
    
    class Config:
        orm_mode = True

# Admin Pydantic model
class Admin(BaseModel):
    id: int
    userID : int
    createdAt : datetime
    user : User
    approvedblogs : List[Blog]
    
    class Config:
        orm_mode = True