from email import message
from pydantic import EmailStr, BaseModel
from unicodedata import category
from pydantic import BaseModel
import jwt
from jose import JWTError,jwt
from fastapi.encoders import jsonable_encoder
from datetime import datetime, timedelta
from sqlalchemy import select
from fastapi import UploadFile, File,APIRouter, Depends,status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from werkzeug.security import generate_password_hash , check_password_hash
from fastapi_jwt_auth import AuthJWT
from fastapi.exceptions import HTTPException
import pytz
import boto3
from botocore.exceptions import ClientError
import ast
from datetime import datetime, timezone
from starlette.responses import JSONResponse
import json
from typing import List, Optional
import databases
from sqlalchemy.orm import Session 
from .models import User,Feedback,Credentials,Company
from . import crud, models
from .database import Session, engine
from .schemas import CompanyDetails,StudentDetails,StudentModel
from . import crud, models, schemas
from dotenv import load_dotenv
import os
load_dotenv()

def generate_password():
    import random
    import array

    MAX_LEN = 6

    
    DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] 
    LOCASE_CHARACTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
                        'i', 'j', 'k', 'm', 'n', 'o', 'p', 'q',
                        'r', 's', 't', 'u', 'v', 'w', 'x', 'y',
                        'z']

    UPCASE_CHARACTERS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                        'I', 'J', 'K', 'M', 'N', 'O', 'P', 'Q',
                        'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y',
                        'Z']
    SYMBOLS = ['@','(', ')', '<']

    COMBINED_LIST = DIGITS + UPCASE_CHARACTERS + LOCASE_CHARACTERS + SYMBOLS
    rand_digit = random.choice(DIGITS)
    rand_upper = random.choice(UPCASE_CHARACTERS)
    rand_lower = random.choice(LOCASE_CHARACTERS)
    rand_symbol = random.choice(SYMBOLS)

    temp_pass = rand_digit + rand_upper + rand_lower + rand_symbol

    for x in range(MAX_LEN - 4):
        temp_pass = temp_pass + random.choice(COMBINED_LIST)
    temp_pass_list = array.array('u', temp_pass)
    random.shuffle(temp_pass_list)

    password = ""
    for x in temp_pass_list:
        password = password + x
    return password

from fastapi_mail import FastMail, MessageSchema,ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME = "placementsjssate@gmail.com",
    MAIL_PASSWORD = "ugpfesadhglobidd",
    MAIL_FROM = "placementsjssate@gmail.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_FROM_NAME="Placement-Information-JSSATE",
    MAIL_TLS = True,
    MAIL_SSL = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)
def get_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()

def get_db():
    try:
        db = Session()
        yield db
    finally:
        db.close()


oauth2_scheme=OAuth2PasswordBearer(tokenUrl="student/login",scheme_name="student")

ALGORITHM="HS256"
JWT_SECRET = os.getenv("JWT_SECRET")
ACCESS_TOKEN_EXPIRE_MINUTES=1000


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_student(token: str=Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
       
    except JWTError:
        raise credentials_exception
    
    return True
session=Session(bind=engine)

itemrouter = APIRouter(    
    prefix='/student',
    tags=['student']
    
)


#@itemrouter.post("/login", response_model=Token,include_in_schema=True)
@itemrouter.post("/login",response_model=Token,include_in_schema=True)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):
    urn=str(form_data.username)
    urn=urn.upper()
    password=str(form_data.password)
   
    urn=urn.strip()
    db_user=session.query(Credentials).filter(urn==Credentials.urn).first()
   
    if db_user and check_password_hash(db_user.password,password):
    
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
        data={"sub": urn}, expires_delta=access_token_expires
    )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": access_token, "token_type": "bearer"}

@itemrouter.post("/home/register",status_code=status.HTTP_201_CREATED)
async def register(urn:str,email: EmailStr,db: session = Depends(get_db)) -> JSONResponse:
     urn=urn.upper()
     urn=urn.strip()
     email=email.strip()
     
     db_email=session.query(User).filter(User.email==email).first() 
     db_urn=session.query(User).filter(User.urn==urn).first()
     db_cred=session.query(Credentials).filter(Credentials.urn==urn).first()
     
     if db_urn and (db_urn.email==email) and db_cred==None:
        a=generate_password()
        message = MessageSchema(
            subject="Password Set Link",
            recipients=[email],  # List of recipients, as many as you can pass 
            body="your password is "+a,
        
            )
        a=generate_password_hash(a)
        credentials=Credentials(urn=urn,password=a,activated=True)
        session.add(credentials)
        session.commit()
        fm = FastMail(conf)
        await fm.send_message(message)
        return JSONResponse(status_code=200, content={"message": "email has been sent"})
     elif db_urn and (db_urn.email==email) and (db_cred.activated==True):
        return JSONResponse(status_code=200, content={"message": "Account Already Activated"})
     else:
        return JSONResponse(status_code=200, content={"message": "Check if your data exists in database (in correct format)"})
        
@itemrouter.post("/home/forgot_password",status_code=status.HTTP_201_CREATED)
async def forgot_pass(urn:str,email: EmailStr,db: session = Depends(get_db)) -> JSONResponse:
     urn=urn.upper()
     urn=urn.strip()
     db_email=session.query(User).filter(User.email==email).first()
     db_urn=session.query(User).filter(User.urn==urn).first()
     db_cred=session.query(Credentials).filter(Credentials.urn==urn).first()
     if db_urn and (db_urn.email==email) and db_cred!=None:
        db_user= crud.get_item_by_credentials(db,urn)
        a=generate_password()
        message = MessageSchema(
            subject="Password Set Link",
            recipients=[email],  # List of recipients, as many as you can pass 
            body="your password is "+a,
        
            )
        a=generate_password_hash(a)
        db_user[0].password=a
        db.commit()
        fm = FastMail(conf)
        await fm.send_message(message)
        return JSONResponse(status_code=200, content={"message": "email has been sent"})
     elif db_urn and (db_urn.email==email) and (db_cred==None):
        return JSONResponse(status_code=200, content={"message": "Account yet not activated"})
     else:
         return JSONResponse(status_code=200, content={"message": "invalid response"})     

@itemrouter.post("/home/changepassword/{urn}")
def change_password_student(urn:str,oldpass:str,newpass:str,db:Session=Depends(get_db),b: bool =Depends(get_current_student)):
    urn=urn.upper()
    urn=urn.strip()
    db_user= crud.get_item_by_credentials(db,urn)
    if db_user and check_password_hash(db_user[0].password,oldpass):
        newpass=generate_password_hash(newpass)
        db_user[0].password=newpass
        db.commit()
        return {"message":"Password changed successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
        detail="Wrong Password")
@itemrouter.get("/home/all_companies", response_model=List[CompanyDetails],include_in_schema=True)
def show_records(db: Session = Depends(get_db),b: bool =Depends(get_current_student)):
    records = db.query(models.Company).all()
    return records


@itemrouter.get("/home/thirdyear/all_companies", response_model=List[CompanyDetails],include_in_schema=True)
def show_records_jnr(db: Session = Depends(get_db),b: bool =Depends(get_current_student)):
    records = db.query(models.Company).filter_by(category="summer_internship").all()
    return records

@itemrouter.get("/home/total_company_count",include_in_schema=True)
def show_count(db: Session = Depends(get_db),b: bool =Depends(get_current_student)):
    records = db.query(models.Company.cid).all()
    records = str(records) 
    data = json.dumps(ast.literal_eval(records)) 
    data=json.loads(data)
    return len(data)
    
@itemrouter.get("/home/upcoming_companies", response_model=List[CompanyDetails],include_in_schema=True)
def upcoming_companies(db: Session = Depends(get_db),b: bool =Depends(get_current_student)):
    IST = pytz.timezone('Asia/Kolkata')
    datetime_ist = datetime.now(IST)
    cur_date_time= datetime_ist.strftime('%Y-%m-%d %H:%M:%S')
    cur_date_time=datetime.strptime(cur_date_time,'%Y-%m-%d %H:%M:%S')
    records = db.query(models.Company).filter(Company.date>=cur_date_time).filter(Company.status!=3).order_by(Company.date.asc()).all()
    return records

@itemrouter.put("/update_marks/",status_code=status.HTTP_201_CREATED)
def update_marks(user:schemas.UpdateMarks,session = Depends(get_db),b: bool =Depends(get_current_student)):
    dc=session.query(User).filter(User.urn==user.urn.upper()).first()
    if dc is None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student doesn't exists"
        )
    
    dc.urn=user.urn,
    dc.sem5=user.sem5,
    dc.sem6=user.sem6,
    dc.sem7=user.sem7,
    dc.sem8=user.sem8
    
    session.commit()
    
    return {"message":"Student Marks Updated"}

@itemrouter.get("/feedbacks/details",include_in_schema=True)
def feedbacks(db: Session = Depends(get_db),b: bool =Depends(get_current_student)):
    return db.query(Feedback).distinct(Feedback.urn).all()
    
@itemrouter.post("/home/eligible/register/{user_id}",include_in_schema=True)
def record_placed(user_id:str,db: Session = Depends(get_db),b: bool =Depends(get_current_student)):
    user_id=user_id.upper()
    records = crud.placed_item(db,urn=user_id)
    records = str(records) 
    data = json.dumps(ast.literal_eval(records)) 
    data=json.loads(data)
    
    categoryCount=len(data)
    categories=[]
    for i in range(0,categoryCount):
        categories.append(data[i][0])
    
    records2 = db.query(models.Company.cid).all()
    records2 = str(records2) 
    data2 = json.dumps(ast.literal_eval(records2)) 
    data2=json.loads(data2)
    array_eligible_cid={"company_details":[],"eligible":[],"is_registered":[]}
    # for i in data2:
    #     return i[0]
    student_variable=crud.get_item_by_urn(db, urn=user_id)
    
    
    s_verified=student_variable.verified
    s_ssc=student_variable.ssc
    s_hsc=student_variable.hsc
    s_ug= student_variable.ug
    s_pg=student_variable.pg
    s_backlogs=student_variable.current_backlogs
    s_branch=student_variable.branch
    s_gender=student_variable.gender
    if s_gender=="male" or s_gender=="Male" or s_gender=="MALE" :
        s_gender="M"
    elif s_gender=="female" or s_gender=="Female" or s_gender=="FEMALE" :
        s_gender="F"
    
    company_variables=crud.item_of_company(db)
    for i in range(len(data2)):
        c_cid=company_variables[i].cid
        c_hsc=company_variables[i].hsc
        c_ssc=company_variables[i].ssc
        c_ug= company_variables[i].ug
        c_pg=company_variables[i].pg
        c_backlogs=company_variables[i].backlogs
        c_branch=company_variables[i].branch
        c_category=company_variables[i].category
        c_package=company_variables[i].package
        c_deadline=company_variables[i].deadline
        c_status=company_variables[i].status
        c_gender=company_variables[i].gender
    
        nonCircuitBranches=['MECH','EE','EEE','CE']
        category_condition=''
        #logic-> a student can take 2 offers from tier1,tier2,tier3,dream
        #tier 1-> upto 7 lpa , tier2->7-15 lpa, tier3->15-20 lpa, dream->20+ lpa
        #a student can take one offer from internship/core so total 3 offers
        IST = pytz.timezone('Asia/Kolkata')
        datetime_ist = datetime.now(IST)
        cur_date_time= datetime_ist.strftime('%Y-%m-%d %H:%M:%S')
        cur_date_time=datetime.strptime(cur_date_time,'%Y-%m-%d %H:%M:%S')
        eligible=True
        if c_status==2:
            eligible=False
        else:    
            if (c_deadline>cur_date_time):
                eligible=True               
            elif (((c_deadline<cur_date_time)==True) and (c_status==1)):
                eligible=False
                company_variables[i].status=2
                db.commit()           
            if  c_status != 1 or (s_gender not in c_gender) or (s_branch not in c_branch) or (c_deadline < cur_date_time) or s_hsc < c_hsc or s_ssc<c_ssc or ((s_ug < c_ug and s_pg == -1) or (s_pg != -1 and s_pg<c_pg)) or (c_backlogs == 0 and s_backlogs != '0') or s_verified != 1 or (c_category in categories):
                eligible=False
            elif categoryCount == 2:
                if (("internship" or "core") in categories) or (not(c_category in ["internship","core"])): 
                    eligible=False
            elif categoryCount == 3:
                eligible=False           
            elif categoryCount == 1:
                if ("tier1" in categories):
                    if (c_category == "tier1"):
                        eligible = False
                elif ("tier2" in categories):
                    if ((c_category == "tier1") or (c_category == "tier2")):
                        eligible = False
                elif ("tier3" in categories):
                    if ((c_category == "tier1") or (c_category == "tier2") or (c_category == "tier3")):
                        eligible = False
                elif ("dream" in categories):
                    if ((c_category == "tier1") or (c_category == "tier2") or (c_category == "tier3") or (c_category == "dream")):
                        eligible = False      
                elif ("core" in categories):
                    if((c_category == "core") or (c_category == "internship")):
                        eligible = False
                elif ("internship" in categories):
                    if((c_category == "internship") or (c_category == "core")):
                        eligible = False
            else:
                eligible=True
       
        exist=db.query(models.Registrations.urn).filter_by(cid=c_cid).all()
        records = str(exist) 
        data = json.dumps(ast.literal_eval(records)) 
        exist=json.loads(data)
        is_registered=False
        for j in exist:
            if user_id == j[0]:
                eligible=False
                is_registered=True    
        company_variables=crud.item_of_company(db)
        array_eligible_cid["company_details"].append(company_variables[i])      
        array_eligible_cid["eligible"].append(eligible)
        array_eligible_cid["is_registered"].append(is_registered)
                  
    return array_eligible_cid

@itemrouter.post("/home/file/show_resume/{urn}",include_in_schema=True)
def show(urn:str,b: bool =Depends(get_current_student)):
    urn=urn.upper()
    urn=urn +".pdf"
    try:
        client.head_object(Bucket='resumesnoida', Key=urn)
    except ClientError:
        return False
    
    url = client.generate_presigned_url(
    ClientMethod='get_object',
    Params={
        'Bucket': 'resumesnoida',
        'Key': urn,
    },
    ExpiresIn=600
)
    
    return url
@itemrouter.post("/home/eligible/debug_register/{user_id}",include_in_schema=True)
def testing_debugging(user_id:str,db: Session = Depends(get_db),b: bool =Depends(get_current_student)):
    user_id=user_id.upper()
    records = crud.placed_item(db,urn=user_id)
    records = str(records) 
    data = json.dumps(ast.literal_eval(records)) 
    data=json.loads(data)
    
    categoryCount=len(data)
    categories=[]
    for i in range(0,categoryCount):
        categories.append(data[i][0])
    
    records2 = db.query(models.Company.cid).all()
    records2 = str(records2) 
    data2 = json.dumps(ast.literal_eval(records2)) 
    data2=json.loads(data2)
    array_eligible_cid={"company_details":[],"eligible":[],"is_registered":[]}
    # for i in data2:
    #     return i[0]
    student_variable=crud.get_item_by_urn(db, urn=user_id)
    
    
    s_verified=student_variable.verified
    s_ssc=student_variable.ssc
    s_hsc=student_variable.hsc
    s_ug= student_variable.ug
    s_pg=student_variable.pg
    s_backlogs=student_variable.current_backlogs
    s_branch=student_variable.branch
    s_gender=student_variable.gender
    if s_gender=="male" or s_gender=="Male" or s_gender=="MALE" :
        s_gender="M"
    elif s_gender=="female" or s_gender=="Female" or s_gender=="FEMALE" :
        s_gender="F"
    
    company_variables=crud.item_of_company(db)
    for i in range(len(data2)):
        c_cid=company_variables[i].cid
        c_hsc=company_variables[i].hsc
        c_ssc=company_variables[i].ssc
        c_ug= company_variables[i].ug
        c_pg=company_variables[i].pg
        c_backlogs=company_variables[i].backlogs
        c_branch=company_variables[i].branch
        c_category=company_variables[i].category
        c_package=company_variables[i].package
        c_deadline=company_variables[i].deadline
        c_status=company_variables[i].status
        c_gender=company_variables[i].gender
    
        nonCircuitBranches=['MECH','CE','EE','EEE']
        category_condition=''
    
        IST = pytz.timezone('Asia/Kolkata')
        datetime_ist = datetime.now(IST)
        cur_date_time= datetime_ist.strftime('%Y-%m-%d %H:%M:%S')
        cur_date_time=datetime.strptime(cur_date_time,'%Y-%m-%d %H:%M:%S')
        eligible=True
        if c_status==2:
            eligible=1
        else:    
            if c_category=="other" and (c_deadline>cur_date_time):
                eligible=True               
            elif (((c_deadline<cur_date_time)==True) and (c_status==1)):
                eligible=2
                company_variables[i].status=2
                db.commit()           
            elif c_category=="summer_internship":
                eligible=3
            #or (s_gender not in c_gender)or (c_backlogs == 0 and s_backlogs != '0')or (c_deadline < cur_date_time) or  or (s_branch not in c_branch)  or s_hsc < c_hsc or s_ssc<c_ssc or ((s_ug < c_ug and s_pg == -1) or (s_pg != -1 and s_pg<c_pg)) 
            elif  c_status != 1 or s_verified != 1 or (c_category in categories):
                eligible=4
            elif ("dream" in categories):
                eligible = False
            elif categoryCount >= 2 and (not(c_category in ["dream","special"])): 
                eligible=False           
            elif categoryCount == 1:
                if ("tier1" in categories):
                    if (s_branch in nonCircuitBranches):
                        if (not(c_category in ["core","tier2","internship","dream","special"])):
                            eligible = 5
                    else:
                        if (not(c_category in ["tier2","internship","dream","special"])):
                            eligible = 6
                elif ("core" in categories):
                    if(not(c_category in ["tier2","internship","dream","special"])):
                        eligible = 7
                elif ("tier2" in categories):
                    if(not(c_category in ["dream","special"])):
                        eligible = 8
                elif ("internship" in categories):
                    if (s_branch in  nonCircuitBranches) and c_category=='core':
                        eligible= True   
                     #assuming internship and summer internship sirf tier 2 me hota hai
                    elif (not(c_category in ["tier1","dream","special"])):
                        eligible=False
            else:
                eligible=True
       
        exist=db.query(models.Registrations.urn).filter_by(cid=c_cid).all()
        records = str(exist) 
        data = json.dumps(ast.literal_eval(records)) 
        exist=json.loads(data)
        is_registered=False
        for j in exist:
            if user_id == j[0]:
                eligible=11
                is_registered=True    
        company_variables=crud.item_of_company(db)
        array_eligible_cid["company_details"].append(company_variables[i])      
        array_eligible_cid["eligible"].append(eligible)
        array_eligible_cid["is_registered"].append(is_registered)
                  
    return array_eligible_cid

@itemrouter.post("/home/eligible/cid/register_to_company/{user_id}/{cid}",include_in_schema=True)
def register_into_company(user_id:str,cid:int,db:Session=Depends(get_db),b: bool =Depends(get_current_student)):
    user_id=user_id.upper()
    #exist=db.query(models.Registrations.urn).filter_by(cid=cid,urn=user_id).all()
    # records = str(exist) 
    # data = json.dumps(ast.literal_eval(records)) 
    # exist=json.loads(data)
    #for i in exist:
    #print(exist)
    
    statement=select(models.Registrations.urn).where(models.Registrations.cid==cid, models.Registrations.urn==user_id)
    
    exist=db.execute(statement).scalar_one_or_none()
#registration.cid based on urns
   # return exist
    if exist is not None:
        return False
    reg=models.Registrations(urn=user_id,cid=cid)
    db.add(reg)
    db.commit()
    return True

@itemrouter.get("/home/eligible/details/{cid}",include_in_schema=True)
def get_company_details_students(cid:int,session=Depends(get_db),b: bool =Depends(get_current_student)):
    return crud.get_item_by_company(session,cid=cid)

@itemrouter.get("/home/status_category{urn}",include_in_schema=True)
def get_student_status(urn:str,session=Depends(get_db),b: bool =Depends(get_current_student)):
    urn=urn.upper()
    return crud.get_placedcategory_students(session,urn=urn)

@itemrouter.get("/home/status_stipend{urn}",include_in_schema=True)
def get_stipend_status(urn:str,session=Depends(get_db),b: bool =Depends(get_current_student)):
    urn=urn.upper()
    return crud.get_stipend_students(session,urn=urn)

@itemrouter.get("/home/status_cname{urn}",include_in_schema=True)
def get_student_cname_status(urn:str,session=Depends(get_db),b: bool =Depends(get_current_student)):
    urn=urn.upper()
    return crud.get_cname_students(session,urn=urn)
@itemrouter.get("/home/status_package{urn}",include_in_schema=True)
def get_student_package_status(urn:str,session=Depends(get_db),b: bool =Depends(get_current_student)):
    urn=urn.upper()
    return crud.get_package_students(session,urn=urn)

@itemrouter.get("/home/status_tier{urn}",include_in_schema=True)
def get_student_tier_status(urn:str,session=Depends(get_db),b: bool =Depends(get_current_student)):
    urn=urn.upper()
    return crud.placed_category(session,urn=urn)

@itemrouter.get("/home/myprofile{urn}", response_model=schemas.StudentModel,include_in_schema=True)
def my_profile(urn: str, db:Session = Depends(get_db),b: bool =Depends(get_current_student)):
    item = crud.get_item_by_urn(db, urn=urn)
    if item is None:
        raise HTTPException(status_code=404, detail="user not found")
    return item
client = boto3.client(
    's3',
    aws_access_key_id = os.getenv("aws_access_key_id"),
    aws_secret_access_key = os.getenv("aws_secret_access_key"),
    region_name = 'ap-south-1'
)
    
# Creating the high level object oriented interface
resource = boto3.resource(
    's3',
     aws_access_key_id = os.getenv("aws_access_key_id"),
    aws_secret_access_key = os.getenv("aws_secret_access_key"),
    region_name = 'ap-south-1'
)

@itemrouter.post("/home/file/upload/{urn}",include_in_schema=True)
async def upload_resume(urn:str,file: UploadFile = File(...) ,b: bool =Depends(get_current_student)):
    if file.content_type != "application/pdf":
        raise HTTPException(400, detail="Invalid document type")
    contents = await file.read()
    urn=urn.upper()
    urn=urn +".pdf"
    file.filename=urn
    import io
    temp_file = io.BytesIO()
    temp_file.write(contents)
    temp_file.seek(0)
    client.upload_fileobj(temp_file, 'resumesnoida',file.filename)
    temp_file.close()
    return {"message": "Resume uploaded successfully"}


@itemrouter.post("/home/feedback/{urn}",include_in_schema=True)
def write_feedback(urn:str,cname:str,feedback:schemas.Feedback,db:Session=Depends(get_db),b: bool =Depends(get_current_student)):
    #,feedback:schemas.Feedback
    try:
        urn=urn.upper()
        exist=db.query(models.Feedback).filter_by(urn=urn).all()
        if exist !=[]:
            return {"message":"Feedback already exist"}
        cn=crud.get_placed_students_cname(db,urn=urn)
        sn=db.query(models.User.full_name).filter_by(urn=urn).first()
        #return cn[0][0]
        cname=cname.upper()
        j=0
        f=1
        
        if f==1:
            feedback_obj=models.Feedback(urn=urn,
                                    cname=cname,
                                    sname=sn[0],
                                    branch=feedback.branch,
                                    role=feedback.role,
                                    ctc= feedback.ctc,
                                    base=feedback.base,
                                    technical_round=feedback.technical_round,
                                    hr_round=feedback.hr_round,
                                    tips=feedback.tips,
                                    topics_covered=feedback.topics_covered,
                                    codinground_difficulty=feedback.codinground_difficulty,
                                    interview_difficulty=feedback.interview_difficulty,
                                    overall_experience=feedback.overall_experience,
                                    passing_year=feedback.passing_year,
                                    #need to check ful, time/summer intern issue from frontend
                                    full_time=True,
                                    summer_internship=False,
                                    stipend=feedback.stipend,
                                    location=feedback.location,
                                    mode=feedback.mode)
            db.add(feedback_obj)
            db.commit()
            return {"message":"Successfully submitted feedback"}
        return {"message":"Incorrect Details"}
    except:
            db.rollback()
            raise HTTPException(status_code=400,detail="Error in submitting feedback")
    finally:
            db.close()
    
@itemrouter.get("/home/registered_email/{cid}",include_in_schema=True)
def get_registered_email(cid:int,db:Session=Depends(get_db),b: bool =Depends(get_current_student)):
    urn=db.query(models.Registrations.urn).filter_by(cid=cid).all()
    a=[]
    for i in urn:
        a.append(i[0])
    b=[]
    for i in a:
        email=db.query(models.User.email).filter_by(urn=i).all()
        b.append(email[0][0])
    return b    
           
@itemrouter.get("/home/feedback/eligible{urn}",include_in_schema=True)
def eligible_feedback(urn:str,db:Session=Depends(get_db),b: bool =Depends(get_current_student)):
    urn=urn.upper()
    item=db.query(models.Placed_category).filter_by(urn=urn).all()
    items= item.__len__()
    if items==0:
        return False
    else:
        return True
    
# @itemrouter.post('/home/file/download_resume/{urn}')
# def download_resume(urn_list:str):
#     urnlist=urn_list.split(",")
#     a=[]
#     for i in urnlist:
#         j=i.upper()+".pdf"
#         a.append(j)
#     b=[]
#     #bucket = client.list_objects(Bucket='test-resumes14')
#     f=0
#     for i in a:
#         str=r"C:/Users/HP/Downloads/Placement-website-resume/resume"+"/"+i
#         client.download_file('test-resumes14',i,str)
#         f=f+1
        
#     return {"message":"Successfully downloaded %d resumes"%f}
    
        
    

# @itemrouter.get("/home/list_buckets")
# async def list_buckets():
#     clientResponse = client.list_buckets()
#     a=[]
# # Print the bucket names one by one
#     print('Printing bucket names...')
#     for bucket in clientResponse['Buckets']:
#         a=bucket['Name']
#     return a
