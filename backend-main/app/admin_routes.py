from pathlib import Path
from email import message
from unicodedata import category
from . import crud, models, schemas
from fastapi_mail import FastMail, MessageSchema,ConnectionConfig
from typing import List
from pydantic import BaseModel
from sqlalchemy import insert
from fastapi.exceptions import HTTPException
from fastapi import APIRouter,status,Depends,File,UploadFile,Form,Body,Response,FastAPI, BackgroundTasks,APIRouter,status
from .database import Session,engine
from .schemas import LoginModel,AddCompanyModel,CompanyStatusDetails,CompanyDetails,StudentDetails,StudentModel,EmailSchema,BranchDetails,Placed,PlacedCategory
from .models import Company,Placed,Placed_category,Registrations,User
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt,JWTError
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Optional
from datetime import datetime, timedelta
import os
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status

load_dotenv()


security = HTTPBasic()






session=Session(bind=engine)

oauth3_scheme=OAuth2PasswordBearer(tokenUrl="admin/login",scheme_name='admin')
admin_username=os.getenv('admin_username')
admin_password=os.getenv('admin_password')
ALGORITHM="HS256"
JWT_SECRET = os.getenv("JWT_SECRET")
ACCESS_TOKEN_EXPIRE_MINUTES=1000

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


def get_current_admin(token: str=Depends(oauth3_scheme)):
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

admin_router = APIRouter(
    prefix='/admin',
    tags=['admin'],
    
    )


@admin_router.post("/login",response_model=Token,include_in_schema=True)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):
    urn=str(form_data.username)
    urn=urn.upper()
    password=str(form_data.password)
    password=password.upper()
    if ((urn==admin_username) and (password==admin_password)):
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

@admin_router.post("/add_alumni_details")
def post_alumni_details(alumni: schemas.Alumni,db: Session = Depends(get_db),current_user: bool = Depends(get_current_admin)):
    db_alumni = models.alumni(a_name=alumni.a_name, a_email=alumni.a_email, branch=alumni.branch, passout=alumni.passout, usn=alumni.usn,a_cname=alumni.a_cname)
    db.add(db_alumni)
    db.commit()
    db.refresh(db_alumni)
    return db_alumni

@admin_router.put("/update_alumni_details/{a_email}")
def update_alumni_details(a_email:str,alumnid: schemas.Alumni,db: Session = Depends(get_db),current_user: bool = Depends(get_current_admin)):
    db_alumni = db.query(models.alumni).filter(models.alumni.a_email == a_email).first()
    db_alumni.a_name = alumnid.a_name
    db_alumni.a_email = alumnid.a_email
    db_alumni.branch = alumnid.branch
    db_alumni.passout = alumnid.passout
    db_alumni.usn = alumnid.usn
    db_alumni.a_cname = alumnid.a_cname
    db.commit()
    db.refresh(db_alumni)
    return db_alumni
@admin_router.get("/get_all_alumni_details")
def get_all_alumni_details(db: Session = Depends(get_db),current_user: bool = Depends(get_current_admin)):
    return crud.get_all_alumni_details(db=db)

@admin_router.post("/admin/edit_student/{urn}",status_code=status.HTTP_201_CREATED)
def updatestudent(user:StudentModel,urn:str,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    urn=urn.upper()
    dc=session.query(User).filter(User.urn==urn).first()
    if dc is None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student doesn't exists"
        )
    dc.urn=user.urn,
    dc.full_name=user.full_name,
    dc.email=user.email,
    dc.branch=user.branch,
    dc.first_name=user.first_name, 
    dc.last_name = user.last_name,
    dc.middle_name=user.middle_name,
    dc.ssc=user.ssc
    dc.hsc=user.hsc
    dc.ug=user.ug,
    dc.pg=user.pg,
    dc.ug_percentage=user.ug_percentage
    dc.backlogs=user.backlogs,
    dc.sem1=user.sem1
    dc.sem2=user.sem2
    dc.sem3=user.sem3
    dc.sem4=user.sem4
    dc.sem5=user.sem5
    dc.sem6=user.sem6
    dc.sem7=user.sem7
    dc.sem8=user.sem8
    dc.current_backlogs=user.current_backlogs
    dc.history_backlogs=user.history_backlogs
    dc.no_of_x_grades=user.no_of_x_grades
    dc.other_grades=user.other_grades
    dc.ug_start_year=user.ug_start_year
    dc.ug_end_year=user.ug_end_year
    dc.ssc_board=user.ssc_board
    dc.hsc_board=user.hsc_board
    dc.hsc_start_year=user.hsc_start_year
    dc.hsc_end_year=user.hsc_end_year
    dc.ssc_start_year=user.ssc_start_year
    dc.ssc_end_year=user.ssc_end_year
    dc.entry_to_college=user.entry_to_college
    dc.rank=user.rank
    dc.gap_in_studies=user.gap_in_studies
    dc.dob=user.dob
    dc.gender=user.gender
    dc.category=user.category
    dc.native=user.native
    dc.parents_name=user.parents_name
    dc.present_addr=user.present_addr
    dc.permanent_addr=user.permanent_addr
    dc.phone=user.phone
    dc.secondary_phone=user.secondary_phone
    dc.verified=user.verified
       
    session.commit()
    return {"message":"Student Details Updated"}


# admin_router = APIRouter(
#     prefix='/admin',
#     tags=['admin']
#     )

# session=Session(bind=engine)
# #admin username and password here should always be kept in upper as we are validating these creds as upper case in further routes
# oauth3_scheme=OAuth2PasswordBearer(tokenUrl='/admin/login')
# admin_username="JSSISWELL"
# admin_password="JSSATE123"
# ALGORITHM="HS256"
# JWT_SECRET = "pradeepsirbcvs"
# ACCESS_TOKEN_EXPIRE_MINUTES=1000

# def get_session():
#     session = Session()
#     try:
#         yield session
#     finally:
#         session.close()

# def get_db():
#     try:
#         db = Session()
#         yield db
#     finally:
#         db.close()
    
# class Token(BaseModel):
#     access_token: str
#     token_type: str


# class TokenData(BaseModel):
#     username: Optional[str] = None

# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=15)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
#     return encoded_jwt


# def get_current_admin(token: str=Depends(oauth3_scheme)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
       
#     except JWTError:
#         raise credentials_exception
    
#     return True


# @admin_router.post("/login",response_model=Token,include_in_schema=False)
# def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),db: Session = Depends(get_db)):
#     urn=str(form_data.username)
#     urn=urn.upper()
#     password=str(form_data.password)
#     password=password.upper()
#     if ((urn==admin_username) and (password==admin_password)):
#         access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#         access_token = create_access_token(
#         data={"sub": urn}, expires_delta=access_token_expires
#     )
#     else:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect username or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     return {"access_token": access_token, "token_type": "bearer"}


# conf = ConnectionConfig(
#     MAIL_USERNAME = "placementsjssate@gmail.com",
#     MAIL_PASSWORD = "ugpfesadhglobidd",
#     MAIL_FROM = "placementsjssate@gmail.com",
#     MAIL_PORT = 587,
#     MAIL_SERVER = "smtp.gmail.com",
#     MAIL_FROM_NAME="Placement-Information JSSATE",
#     MAIL_TLS = True,
#     MAIL_SSL = False,
#     USE_CREDENTIALS = True,
#     VALIDATE_CERTS = True
# )
conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_FROM"),
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_FROM_NAME="Placement-Information",
    MAIL_TLS = True,
    MAIL_SSL = False,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

    
@admin_router.post("/home/send_feedback_reminder/{cid}",include_in_schema=True)
async def remind_feedback(remind:List[schemas.FeedbackRemindModel],db:Session=Depends(get_db),a:bool=Depends(get_current_admin)):
    a=db.query(models.Company.cname).filter(models.Company.cid == remind[0].cid).first()
    b=a.cname
    urn=db.query(models.Placed.urn).filter_by(cid=remind[0].cid).all()
    aa=[]
    for i in urn:
        aa.append(i[0])
    ba=[]
    for i in aa:
        email=db.query(models.User.email).filter_by(urn=i).all()
        ba.append(email[0][0])
    attendees = ba #['aadeevishal@gmail.com'] 
    message = MessageSchema(
            subject="Congratulations on getting selected in "+b+"!!",
            recipients=attendees,
            body="Congratulations to all of you who got selected in "+b+"."+"All of you are hereby requested to fill the feedback form on the placement portal by today without any failure.\nContact placement or the website team for any queries.\n\n"+"Regards,\nDr. M Pradeep\nTraining & Placement Officer -SJCE Mysore."
         )
            
    
    fm = FastMail(conf)
    await fm.send_message(message)
    
    return JSONResponse(status_code=200, content={"message": "Reminder details has been sent"})

@admin_router.post("/update_send_file",status_code=status.HTTP_201_CREATED)
async def update_send_file(
    file: Optional[UploadFile] = File(None),
    file1:Optional[UploadFile] = File(None),
    file2:Optional[UploadFile] = File(None),
    email: Optional[str] =Body(None) ,
    email2: Optional[str] =Body(None),
    subject: Optional[str]= Body(None),
    body: Optional[str]= Body(None),
    a:bool=Depends(get_current_admin)
    ) -> JSONResponse:
    
    list1=[]
    emails=[]

    if email2==None:
        email2="aadeevishal@gmail.com"

    if email is not None:
        emails.append(email)
    if email2 is not None:
        emails.append(email2)
        
    if (file==None and file1==None and file2==None):
        message = MessageSchema(
            recipients=emails,
            body=body,
            subject=subject
         )
    else:
        if file is not None:
            list1.append(file)
        if file1 is not None:
            list1.append(file1)
        if file2 is not None:
            list1.append(file2)
               
        message = MessageSchema(
            recipients=emails,
            attachments=list1,
            body=body,
            subject=subject
         )
            
    
    fm = FastMail(conf)
    await fm.send_message(message)
    
    return JSONResponse(status_code=200, content={"message": "Updated Company details has been sent "})


@admin_router.delete("/delete_company/{cid}",status_code=status.HTTP_201_CREATED)
def delete_company(cid:int,db:Session=Depends(get_db),a:bool=Depends(get_current_admin)):
    dc=db.query(Company).filter(Company.cid==cid).first()
    if dc is None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company doesn't exists"
        )
    db.delete(dc)
    db.commit()
    return {"message":"Company Deleted"}

@admin_router.post("/send_file",status_code=status.HTTP_201_CREATED)
async def send_file(
    file: Optional[UploadFile] = File(None),
    file1:Optional[UploadFile] = File(None),
    file2:Optional[UploadFile] = File(None),
    email: Optional[str] =Body(None) ,
    subject: Optional[str] =Body(None),
    body: Optional[str] =Body(None),
    email2: Optional[str] =Body(None),a:bool=Depends(get_current_admin)
    ) -> JSONResponse:
    
    list1=[]
    emails=[]
    if email2==None:
        email2="aadeevishal@gmail.com"

    if email is not None:
        emails.append(email)
    if email2 is not None:
        emails.append(email2)
    
    if (file==None and file1==None and file2==None):
        message = MessageSchema(
            recipients=emails,
            body=body,
            subject=subject
         )
    else:
        if file is not None:
            list1.append(file)
        if file1 is not None:
            list1.append(file1)
        if file2 is not None:
            list1.append(file2)
        
        message = MessageSchema(
            recipients=emails,
            attachments=list1,
            subject=subject,
            body=body
         )
            
    
    fm = FastMail(conf)
    await fm.send_message(message)
    
    return JSONResponse(status_code=200, content={"message": "Company details has been sent"})


@admin_router.post("/company/add_company",status_code=status.HTTP_201_CREATED)
async def add_company(
    cname    : str= Form(...),
    category  :str= Form(...),
    package   : float= Form(...),
    internship_stipend : float= Form(...),
    deadline : datetime= Form(...),
    date : datetime= Form(...),
    ssc : float= Form(...),
    hsc : float= Form(...),
    ug : float= Form(...),
    pg : float= Form(...),
    branch : str= Form(...),
    backlogs : int= Form(...),
    gender:str= Form(...),
    email: Optional[str] =Form(None),
    email2: Optional[str] =Form(None),
    body : Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    file1:Optional[UploadFile] = File(None),
    file2:Optional[UploadFile] = File(None),
    a:bool=Depends(get_current_admin)):
    new_company=Company(
        cname=cname,
        category=category,
        package=package,
        internship_stipend=internship_stipend,
        deadline=deadline,
        date=date,
        ssc = ssc,
        hsc=hsc,
        ug=ug,
        pg=pg,
        branch=branch,
        backlogs=backlogs,
        gender=gender,
        status=1
    ) 
    if backlogs==0:
        b="NO"
    else:
        b="YES"
    try:
        if body==None:
            body=" "
        list1=[]
        emails=[]
        
        if email2==None:
            email2="aadeevishal@gmail.com"
        if email is not None:
            emails.append(email)
        if email2 is not None:
            emails.append(email2)
         
        template = f"""
                <html>
                <div class="content_panel" style="clear: both;
                                                display: block;
                                                overflow: hidden;
                                                font-name: 'Roboto', sans-serif;
                                                font-style: bold;
                                                background-color: #ffff;
                                                box-sizing: border-box;
                                                -webkit-box-shadow: 0 0 12px 0 #aaa;
                                                -moz-box-shadow: 0 0 12px 0 #aaa;
                                                box-shadow: 0 0 12px 0 #aaa;
                                                border: 2px solid #FF652F;
                                                max-width:600px;
                                                margin:25px auto;">
                    <header style="background-color: #0B0C10;
                                clear: both;
                                display: block;
                                border: 2px solid #FF652F;
                                overflow: hidden;
                                color: #14A76C;">
                        <div style="margin: 0 auto;
                                    margin: 10px auto;
                                    padding: 5px;
                                    font-name: 'Roboto', sans-serif;
                                    text-align: center;">
                            <h1 class="white-font",font-name="Roboto">JSS</h1>
                            <h2 class="white-font">Academy of Technical Education</h2>
                            <hr style="width:40%;">
                            <h1 class="white-font">Training &amp; Placement Cell</h1>
                        </div>
                    </header>
                    <div style="padding:5px 25px;text-align:center;color:#0B0C10">
                        <h1>{cname}</h1>
                    </div>
                    <div style="padding: 15px 25px;">
                        <div style="text-align: center;color:#FF652F"><big><u>Details</u></big></div>
                        <table>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Company Name:</td>
                                <td>{cname}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Fulltime CTC:</td>
                                <td>{package}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Internship Stipend:</td>
                                <td>{internship_stipend}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Category:</td>
                                <td>{category}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Date:</td>
                                <td>{date}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Deadline:</td>
                                <td>{deadline}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">SSC Cutoff:</td>
                                <td>{ssc}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">HSC Cutoff:</td>
                                <td>{hsc}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">UG Cutoff:</td>
                                <td>{ug}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">PG Cutoff:</td>
                                <td>{pg}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Branches allowed:</td>
                                <td>{branch}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#F13C20">Backlogs allowed?</td>
                                <td>{b}</td>
                            </tr>
                        </table>
                    </div>
                    <div style="padding: 15px 25px;">
                        <div style="text-align: center;color:#FF652F""><big><u>More details</u></big></div>
                        {body}
                    </div>
                    <a href="https://jssatenplacements.org/" style="background-color: #0B0C10;
                            font-weight: 400;
                            padding: 15px; 
                            text-transform: uppercase;
                            text-align: center;
                            border: 2px solid #FF652F;
                            cursor: pointer;
                            display:block;
                            color:#14A76C;
                            text-decoration:none;">
                        <strong>Register Now!</strong>
                    </a>
                    <footer style="color: white;
                                    padding: 15px 0;
                                    background-color: #0b0500;
                                    text-align: center;">&copy; Jss Science & Technology University - 2022</footer>
                </div>
                
                </html>
        """
        
        if (file==None and file1==None and file2==None):
            message = MessageSchema(
            subject=str(cname)+" Registration Started",
            recipients=emails,
            html=template,
            subtype='html'
            )
        else:
            if file is not None:
                list1.append(file)
            if file1 is not None:
                list1.append(file1)
            if file2 is not None:
                list1.append(file2)
            
            message = MessageSchema(
                recipients=emails,
                attachments=list1,
                subject=str(cname)+" Registration Started",
                html=template,
                subtype='html'
            )
                        
        session.add(new_company)
        session.commit()
        
        fm = FastMail(conf)
        await fm.send_message(message)
        
        
        return {"message":"Company has been added"}
    
    except:
            session.rollback()
            raise
    finally:
            session.close()
    
    
            
@admin_router.post("/student/add_student",response_model=StudentModel,status_code=status.HTTP_201_CREATED)
def add_student(user:StudentModel,a:bool=Depends(get_current_admin)):
    
    db_cname=session.query(User).filter(User.urn==user.urn).first()

    if db_cname is not None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student already exists"
        )
        
    
    new_student=User(
        urn=user.urn,
        full_name=user.full_name,
        email=user.email,
        branch=user.branch,
        first_name=user.first_name,
        last_name=user.last_name,
        middle_name=user.middle_name,
        ssc=user.ssc,
        hsc=user.hsc,
        ug=user.ug,
        pg=user.pg,
        ug_percentage=user.ug_percentage,
        backlogs=user.backlogs,
        sem1=user.sem1,
        sem2=user.sem2,
        sem3=user.sem3,
        sem4=user.sem4,
        sem5=user.sem5,
        sem6=user.sem6,
        sem7=user.sem7,
        sem8=user.sem8,
        current_backlogs=user.current_backlogs,
        history_backlogs=user.history_backlogs,
        no_of_x_grades=user.no_of_x_grades,
        other_grades=user.other_grades,
        ug_start_year=user.ug_start_year,
        ug_end_year=user.ug_end_year,
        ssc_board=user.ssc_board,
        hsc_board=user.hsc_board,
        hsc_start_year=user.hsc_start_year,
        hsc_end_year=user.hsc_end_year,
        ssc_start_year=user.ssc_start_year,
        ssc_end_year=user.ssc_end_year,
        entry_to_college=user.entry_to_college,
        rank=user.rank,
        gap_in_studies=user.gap_in_studies,
        dob=user.dob,
        gender=user.gender,
        category=user.category,
        native=user.native,
        parents_name=user.parents_name,
        present_addr=user.present_addr,
        permanent_addr=user.permanent_addr,
        phone=user.phone,
        secondary_phone=user.secondary_phone,
        verified=user.verified,
        
    ) 

    session.add(new_student)

    session.commit()

    return message("Student added successfully")

@admin_router.get("/company/company_branch/{cid}",status_code=status.HTTP_201_CREATED)
def company_branch(cid:int,a:bool=Depends(get_current_admin)):
    dc=session.query(Company.branch).filter(Company.cid==cid).first()
    if dc is None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company doesn't exists"
        )
    list_branches=['CSE','IT','ECE','EEE','ME','MCA','CE','EE','MBA']
    cid_branches=dc[0].split(',')
    final_dict={'branches':[],'is_true':[]}
    for i in list_branches:
        if i in cid_branches:
            final_dict["branches"].append(i)
            final_dict["is_true"].append(True)
        else:
            final_dict["branches"].append(i)
            final_dict["is_true"].append(False)
    return final_dict


@admin_router.put("/company/edit_company/{cid}",status_code=status.HTTP_201_CREATED)
async def update_company(
    cid:int,
    cname    : str= Form(...),
    category  :str= Form(...),
    package   : float= Form(...),
    internship_stipend : float= Form(...),
    deadline : datetime= Form(...),
    date : datetime= Form(...),
    ssc : float= Form(...),
    hsc : float= Form(...),
    ug : float= Form(...),
    pg : float= Form(...),
    branch : str= Form(...),
    backlogs : int= Form(...),
    gender:str= Form(...),
    email: Optional[str] =Form(None),
    email2: Optional[str] =Form(None),
    body : Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    file1:Optional[UploadFile] = File(None),
    file2:Optional[UploadFile] = File(None),
    a:bool=Depends(get_current_admin)):
    dc=session.query(Company).filter(Company.cid==cid).first()
    if dc is None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company doesn't exists"
        )
    dc.cname=cname,
    dc.category=category,
    dc.package=package,
    dc.internship_stipend=internship_stipend,
    dc.deadline=deadline,
    dc.date=date,
    dc.ssc = ssc,
    dc.hsc=hsc,
    dc.ug=ug,
    dc.pg=pg,
    dc.branch=branch,
    dc.backlogs=backlogs,
    dc.gender=gender,
    dc.status=1
    
    if backlogs==0:
        b="NO"
    else:
        b="YES"
    try:
        if body==None:
            body=" "
        list1=[]
        emails=[]
        if email2==None:
            email2="aadeevishal@gmail.com"
        if email is not None:
            emails.append(email)
        if email2 is not None:
            emails.append(email2)
            
        
        template = f"""
                <html>
                <div class="content_panel" style="clear: both;
                                                display: block;
                                                overflow: hidden;
                                                font-name: 'Roboto', sans-serif;
                                                font-style: bold;
                                                background-color: #ffff;
                                                box-sizing: border-box;
                                                -webkit-box-shadow: 0 0 12px 0 #aaa;
                                                -moz-box-shadow: 0 0 12px 0 #aaa;
                                                box-shadow: 0 0 12px 0 #aaa;
                                                border: 2px solid #FF652F;
                                                max-width:600px;
                                                margin:25px auto;">
                    <header style="background-color: #0B0C10;
                                clear: both;
                                display: block;
                                border: 2px solid #FF652F;
                                overflow: hidden;
                                color: #14A76C;">
                        <div style="margin: 0 auto;
                                    margin: 10px auto;
                                    padding: 5px;
                                    font-name: 'Roboto', sans-serif;
                                    text-align: center;">
                            <h1 class="white-font",font-name="Roboto">JSS</h1>
                            <h2 class="white-font">Academy of Technical Education</h2>
                            <hr style="width:40%;">
                            <h1 class="white-font">Training &amp; Placement Cell</h1>
                        </div>
                    </header>
                    <div style="padding:5px 25px;text-align:center;color:#0B0C10">
                        <h1>{cname}</h1>
                    </div>
                    <div style="padding: 15px 25px;">
                        <div style="text-align: center;color:#FF652F"><big><u>Details</u></big></div>
                        <table>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Company Name:</td>
                                <td>{cname}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Fulltime CTC:</td>
                                <td>{package}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Internship Stipend:</td>
                                <td>{internship_stipend}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Category:</td>
                                <td>{category}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Date:</td>
                                <td>{date}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Deadline:</td>
                                <td>{deadline}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">SSC Cutoff:</td>
                                <td>{ssc}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">HSC Cutoff:</td>
                                <td>{hsc}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">UG Cutoff:</td>
                                <td>{ug}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">PG Cutoff:</td>
                                <td>{pg}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#FF652F">Branches allowed:</td>
                                <td>{branch}</td>
                            </tr>
                            <tr>
                                <td style="width: 100px;color:#F13C20">Backlogs allowed?</td>
                                <td>{b}</td>
                            </tr>
                        </table>
                    </div>
                    <div style="padding: 15px 25px;">
                        <div style="text-align: center;color:#FF652F""><big><u>More details</u></big></div>
                        {body}
                    </div>
                    <a href="https://jssatenplacements.org/" style="background-color: #0B0C10;
                            font-weight: 400;
                            padding: 15px; 
                            text-transform: uppercase;
                            text-align: center;
                            border: 2px solid #FF652F;
                            cursor: pointer;
                            display:block;
                            color:#14A76C;
                            text-decoration:none;">
                        <strong>Register Now!</strong>
                    </a>
                    <footer style="color: white;
                                    padding: 15px 0;
                                    background-color: #0b0500;
                                    text-align: center;">&copy; Jss Science & Technology University - 2022</footer>
                </div>
                
                </html>
        """
        if (file==None and file1==None and file2==None):
            message = MessageSchema(
            subject=str(cname)+" information updated",
            recipients=emails,
            html=template,
            subtype='html'
            )
        else:
            if file is not None:
                list1.append(file)
            if file1 is not None:
                list1.append(file1)
            if file2 is not None:
                list1.append(file2)
            
            message = MessageSchema(
                recipients=emails,
                attachments=list1,
                subject=str(cname)+"'s Information Updated",
                html=template,
                subtype='html'
            )
        
        session.commit()                
        fm = FastMail(conf)
        await fm.send_message(message)
        
        session.commit()
        
    
        return {"message":"Details has been updated"}
    
    except:
            session.rollback()
            raise
    finally:
            session.close()    
        
@admin_router.post("/company/extend_deadline/{cid}",status_code=status.HTTP_201_CREATED)
def extend_deadline(user:schemas.ExtendDeadlineModel,cid:int,a:bool=Depends(get_current_admin)):
    dc=session.query(Company).filter(Company.cid==cid).first()
    if dc is None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company doesn't exists"
        )
    dc.deadline=user.deadline,
    dc.date=user.date,
       
    session.commit()
    
    return {"message":"Company Deadline Updated"}


@admin_router.put("/company/registrations/StartRegistrations{cid}")
def start_registration(cid:int,a:bool=Depends(get_current_admin)):
    db_company=session.query(Company).filter(Company.cid==cid).first()

    if db_company is None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company does not exists"
        )
    
    db_company.status=1
    session.commit()

    #return db_company.cname+" started registrations"
    return {"message":"Registration started successfully"}

@admin_router.put("/company/registrations/EndRegistrations{cid}")
def end_registration(cid:int,a:bool=Depends(get_current_admin)):
    db_company=session.query(Company).filter(Company.cid==cid).first()

    if db_company is None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company does not exists"
        )

    db_company.status=2
    session.commit()

    #return db_company.cname + " ended registrations"
    return {"message":"Registration ended successfully"}

@admin_router.put("/company/registrations/EndProcess{cid}")
def end_process(cid:int,a:bool=Depends(get_current_admin)):
    db_company=session.query(Company).filter(Company.cid==cid).first()

    if db_company is None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company does not exists"
        )

    db_company.status=3
    session.commit()

    #return db_company.cname + " process ended"
    return {"message":"Process ended successfully"}

@admin_router.get("/status")
def company_records(db: Session = Depends(get_db),a:bool=Depends(get_current_admin)):
    records = db.query(models.Company).filter(Company.category!="summer_internship").order_by(Company.date.desc()).all()
    return records


@admin_router.get("/summer_status")
def company_records_summer(db: Session = Depends(get_db),a:bool=Depends(get_current_admin)):
    records = db.query(Company).filter(Company.category=="summer_internship").all()
    return records

@admin_router.get("/status_compny_count")
def company_placed_count_records(db: Session = Depends(get_db),a:bool=Depends(get_current_admin)):
    records = db.query(models.Placed).all()
    records2=db.query(models.Company).all()
    l2=len(records2)
    l=len(records)
    a=[]
    c=0
    row=1
    col=0
    f=[]
    for i in range(l):
        cid=records[i].cid
        if cid not in f:
            
            f.append(cid)
        
            c=0
            with engine.connect() as con:
            
                sql = """select * from students s 
inner join placed a on s.urn = a.urn
where a.cid ={};""".format(cid)

                rs = con.execute(sql)
        
                
                for i in rs:
                    c+=1
            a.append({"cid":cid,"count":c})        
    
    for i in range(l2):
        if records2[i].cid not in f:
            a.append({"cid":records2[i].cid,"count":0})

    return a

@admin_router.get("/status_compny_reg_count")
def company_reg_count_records(db: Session = Depends(get_db),a:bool=Depends(get_current_admin)):
    records = db.query(models.Registrations).all()
    records2=db.query(models.Company).all()
    l2=len(records2)
    
    l=len(records)
    a=[]
    c=0
    row=1
    col=0
    f=[]
    
    for i in range(l):
        cid=records[i].cid
        if cid not in f:    
            f.append(cid)
        
            c=0
            with engine.connect() as con:
            
                sql = """select * from registrations where cid ={};""".format(cid)

                rs = con.execute(sql)
        
                
                for i in rs:
                    c+=1
            
            a.append({"cid":cid,"count":c})        
    for i in range(l2):
        if records2[i].cid not in f:
            a.append({"cid":records2[i].cid,"count":0})
    return a
    
@admin_router.put("/student/edit_student/{urn}",status_code=status.HTTP_201_CREATED)
def update_student(user:StudentModel,urn:str,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    urn=urn.upper()
    dc=session.query(User).filter(User.urn==urn).first()
    if dc is None:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student doesn't exists"
        )
    dc.urn=user.urn,
    dc.full_name=user.full_name,
    dc.email=user.email,
    dc.branch=user.branch,
    dc.first_name=user.first_name, 
    dc.last_name = user.last_name,
    dc.middle_name=user.middle_name,
    dc.ssc=user.ssc
    dc.hsc=user.hsc
    dc.ug=user.ug,
    dc.pg=user.pg,
    dc.ug_percentage=user.ug_percentage
    dc.backlogs=user.backlogs,
    dc.sem1=user.sem1
    dc.sem2=user.sem2
    dc.sem3=user.sem3
    dc.sem4=user.sem4
    dc.sem5=user.sem5
    dc.sem6=user.sem6
    dc.sem7=user.sem7
    dc.sem8=user.sem8
    dc.current_backlogs=user.current_backlogs
    dc.history_backlogs=user.history_backlogs
    dc.no_of_x_grades=user.no_of_x_grades
    dc.other_grades=user.other_grades
    dc.ug_start_year=user.ug_start_year
    dc.ug_end_year=user.ug_end_year
    dc.ssc_board=user.ssc_board
    dc.hsc_board=user.hsc_board
    dc.hsc_start_year=user.hsc_start_year
    dc.hsc_end_year=user.hsc_end_year
    dc.ssc_start_year=user.ssc_start_year
    dc.ssc_end_year=user.ssc_end_year
    dc.entry_to_college=user.entry_to_college
    dc.rank=user.rank
    dc.gap_in_studies=user.gap_in_studies
    dc.dob=user.dob
    dc.gender=user.gender
    dc.category=user.category
    dc.native=user.native
    dc.parents_name=user.parents_name
    dc.present_addr=user.present_addr
    dc.permanent_addr=user.permanent_addr
    dc.phone=user.phone
    dc.secondary_phone=user.secondary_phone
    dc.verified=user.verified
       
    session.commit()
    return {"message":"Student Details Updated"}

@admin_router.post("/company/registrations/place_students/{cid}",status_code=status.HTTP_201_CREATED)
def place_students(cid:int ,student_list:str,category_placed:str,session=Depends(get_db),a:bool=Depends(get_current_admin)):
     urnlist=[]
     urnlistfinal=[]
     urnlist1=[]
     urnlist2=student_list.split(",")
     l=len(urnlist2)
     urnlist3=[]
     db_company=session.query(Company).filter(Company.cid==cid).first()
     a=db_company.cname
     b=a.lower()
     for i in range(0,l):
         urnlist2[i]=urnlist2[i].upper()
         urnlist.append(urnlist2[i])
         urnlistfinal.append(urnlist2[i])
         urnlist.append(cid)
         urnlist.append(category_placed)
     urnlist3 = [urnlist[i:i + 3] for i in range(0,len(urnlist), 3)] 
     final_list=[]
     for a in urnlistfinal:
        i=0
        db_company=session.query(User).filter(User.urn==a).all()
        urn_list=db_company[i].urn
        i=i+1
        final_list.append(urn_list) 
    
     for i in final_list:
        name=session.query(User.full_name).filter(User.urn==i).first()   
        urn= session.query(User.urn).filter(User.urn==i).first()
        branch= session.query(User.branch).filter(User.urn==i).first()
        gender= session.query(User.gender).filter(User.urn==i).first()
        
        if gender[0]=="male" or gender[0]=="Male":
            gender="M"
        elif gender[0]=="female" or gender[0]=="Female":
            gender="F"
    
        email= session.query(User.email).filter(User.urn==i).first()
        phone= session.query(User.phone).filter(User.urn==i).first()
        
        if session.query(Placed).filter(Placed.urn==i).filter(Placed.cid==cid).first() is not None:
            return False
        
        
        if category_placed=="tier1":
            tier1=True
        else:
            tier1=False
        
        if category_placed=="tier2":
            tier2=True
        else:
            tier2=False
            
        if category_placed=="dream":
            dream=True
        else:
            dream=False
        
        if category_placed=="internship":
            internship=True
        else:
            internship=False
        
        if category_placed=="summer_internship":
            summer_internship=True
        else:
            summer_internship=False
            
        
        placed=Placed_category(name=name[0],urn=urn[0],branch=branch[0],gender=gender[0],email=email[0],phone=phone[0],tier2=tier2,tier1=tier1,dream=dream,internship=internship,summer_internship=summer_internship,cid=cid)
        feedback=True
        placed2=Placed(urn=urn[0],cid=cid,category_placed=category_placed,feedback=feedback)
        session.add(placed)
        session.add(placed2)
        
        session.commit()
     return {"message":"Students Placed"}    

@admin_router.post("/company/registrations/place_summer_interns/{cid}",status_code=status.HTTP_201_CREATED)
def place_students(cid:int ,name :str,urn:str,branch:str,gender:str,email:str,phone:str,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    urn=urn.upper()
    gender=gender.upper()
    branch=branch
    category_placed="summer_internship"
    summer_internship=True    
    placed=Placed_category(name=name,urn=urn,branch=branch,gender=gender,email=email,phone=phone,tier2=False,tier1=False,dream=False,internship=False,summer_internship=summer_internship,cid=cid)
    feedback=True
    placed2=Placed(urn=urn,cid=cid,category_placed=category_placed,feedback=feedback)
    session.add(placed)
    session.add(placed2)
        
    session.commit()
    return {"message":"Summer Intern Students Placed"}    

@admin_router.delete("/company/registrations/unplace{urn}/{cid}",status_code=status.HTTP_201_CREATED)
def unplace_students(urn:str,cid:int,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    urn=urn.upper()
    session.query(Placed).filter_by(urn=urn).filter_by(cid=cid).delete()
    session.query(Placed_category).filter_by(urn=urn).filter_by(cid=cid).delete()
    session.commit()
    return {"message":"Student Unplaced"}

@admin_router.delete("/company/registrations/unregister{urn}/{cid}",status_code=status.HTTP_201_CREATED)
def un_register_students(urn:str,cid:int,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    urn=urn.upper()
    session.query(Registrations).filter_by(urn=urn).filter_by(cid=cid).delete()
    session.commit()
    return {"message":"Student un-registered"}

    
@admin_router.get("/company/registrations/convert/{cid}",status_code=status.HTTP_201_CREATED)
def convert_summerinterns(urn:str,cid:int,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    urn=urn.upper()
         
    db_student=session.query(Placed).filter(Placed.urn==urn).filter(Placed.cid==cid)
        #at last we will look upto to placed table to check the final status of the student
    db_student.update({"category_placed":"tier2"})
    db_student1=session.query(Placed_category).filter(Placed_category.urn==urn).filter(Placed_category.cid==cid)
        #at last we will look upto to placed table to check the final status of the student
    db_student1.update({"tier2":True})
    
    session.commit()
    return {"message":"TIER UPDATED"}

@admin_router.get("/company/registrations/details{cid}",status_code=status.HTTP_201_CREATED)
def get_company_details(cid:int,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    db_company=session.query(Company).filter(Company.cid==cid).first()
    return db_company
    
@admin_router.get("/company/place_summer_interns/details{cid}",status_code=status.HTTP_201_CREATED)
def get_summerintern_details(cid:int,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    db_company=session.query(Placed.urn).filter_by(cid=cid).all()
    l=[]
    for i in db_company:
        db_user=session.query(User).filter(User.urn==i[0]).first()
        l.append(db_user)
    return l

@admin_router.get("/company/registrations/place_students/Select_students{cid}",status_code=status.HTTP_201_CREATED)
def select_registered_students(cid:int,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    urn= crud.get_registered_students(session,cid)
    urn_list=[]
    for i in urn:
        urn_list.append(i[0])
    record_list=[]
    for i in urn_list:
        records=session.query(User).filter(User.urn==i).all()
        record_list.append(records)
    final_record=[]
    j=0
    for i in record_list:
         final_record.append(record_list[j][0])
         j=j+1   
    return final_record

@admin_router.get("/company/registrations/place_students/placed_students_info{cid}",status_code=status.HTTP_201_CREATED)
def select_placed_students(cid:int,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    urn= crud.get_placed_students(session,cid)
    urn_list=[]
    for i in urn:
        urn_list.append(i[0])
    record_list=[]
    for i in urn_list:
        records=session.query(Placed_category).filter(Placed_category.urn==i).all()
        record_list.append(records)
       
    final_record=[]
    j=0
    for i in record_list:
         final_record.append(record_list[j][0])
         j=j+1   
    return final_record

@admin_router.get("/company/registrations/place_students/placed_students_info/status{cid}",status_code=status.HTTP_201_CREATED)
def status_placed_students(cid:int,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    urn= crud.get_placed_students(session,cid)
    urn_list=[]
    for i in urn:
        urn_list.append(i[0])
    cate_list=[]
    for i in urn_list:
        records2=session.query(Placed.category_placed).filter(Placed.urn==i).all()
        record_list=[]
        for j in records2:
            record_list.append(j[0])
        cate_list.append(record_list)
    final_record=[]
    j=0
    for i in cate_list:
        final_record.append(cate_list[j])
        j=j+1   
    return final_record
#commit
@admin_router.get("/company/registrations/place_students/placed_students_info/cname{cid}",status_code=status.HTTP_201_CREATED)
def companyname_placed_students(cid:int,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    urn= crud.get_placed_students(session,cid)
    urn_list=[]
    for i in urn:
        urn_list.append(i[0])
    cate_list=[]
    n=[]
    for i in urn_list:
        records11=session.query(Placed.cid).filter(Placed.urn==i).all()
        n.append(records11)
    new_list=[]
    jj=0
    for i in n:
        h=0
        record_list=[]
        for j in i:
            records2=session.query(Company.cname).filter(Company.cid==n[jj][h][0]).all()
            record_list.append(records2[0][0])
            h+=1
        new_list.append(record_list)
        jj+=1
    return new_list

@admin_router.get("/company/registrations/place_students/placed_students_info/cid_name{cid}",status_code=status.HTTP_201_CREATED)
def companyid_placed_students(cid:int,session=Depends(get_db),a:bool=Depends(get_current_admin)):
    urn= crud.get_placed_students(session,cid)
    urn_list=[]
    for i in urn:
        urn_list.append(i[0])
    cate_list=[]
    n=[]
    for i in urn_list:
        records11=session.query(Placed.cid).filter(Placed.urn==i).all()
        n.append(records11)
    new_list=[]
    jj=0
    for i in n:
        h=0
        record_list=[]
        for j in i:
            records2=session.query(Company.cid).filter(Company.cid==n[jj][h][0]).all()
            record_list.append(records2[0][0])
            h+=1
        new_list.append(record_list)
        jj+=1
    return new_list
