from typing import Any,Dict
import uvicorn
from fastapi import FastAPI,UploadFile,File,Header, Depends,HTTPException,Request,Response
from fastapi.security import OAuth2PasswordBearer
from fastapi_framework import create_controller,controller as api,   register_controllers_to_app,Session, FileStorage,MemoryStorage
from pydantic import BaseModel 
from fastapi_controller.controller_utils import  TEMPLATE_PATH_KEY, VER_KEY
import time,os,inspect
from fastapi import FastAPI, Cookie,Request
 
from .fastapi_controller import SessionManager
import datetime  
from starlette.responses import FileResponse
from fastapi_framework.fastapi_view import _View
from hashlib import md5

__app = FastAPI() 
 
__all_controller__ = []

_sessionManager = SessionManager(storage=FileStorage("sessions",key="123456"))
 

def api_router(path:str="", version:str=""):  
    if  version:
        if path:
            _controllerBase = create_controller(path,version )
        else:
            _controllerBase = create_controller("/{controller}/v{version}",version )  
    else:
        _controllerBase = create_controller( ) 
    
     
    __all_controller__.append(_controllerBase)
    
    def _wapper(targetController):  
        # 定义一个傀儡类，继承自目标类 
         
        class puppetController( targetController ,_controllerBase ): 
             
            def __init__(self,**kwags) -> None:
                print(f"__init__ on puppetController")
                super().__init__()
             
            @property
            def view(self): 
                return _View(self.request,self.response)
            
            async def getUploadFile(self,file:File):
                
                _save_dir = os.path.realpath(os.path.dirname(__file__))
                _save_dir = os.path.join(_save_dir, "uploads") 
                if not os.path.exists(_save_dir):
                    os.mkdir(_save_dir) 
                data = await file.read()
                ext = file.filename.split(".")[-1]
                md5_name = md5(data).hexdigest()
                if ext:
                    md5_name+="."+ext
                save_file = os.path.join(_save_dir, md5_name) 
                if not os.path.exists(save_file): 
                    f = open(save_file, 'wb') 
                    f.write(data)
                    f.close()
                return save_file
            async def _constructor(self,request = Request,response=Response):
                # self.request = request
                # self.response = response
                self.session = await  _sessionManager.initSession(request,response )
            async def _deconstructor(self,new_response:Response):
                await _sessionManager.process(self.session,new_response)
                pass
                 
        setattr(puppetController,"__name__",targetController.__name__)  

        return puppetController 
    return _wapper #: @puppetController

 


@__app.middleware("http")
async def preprocess_request(request: Request, call_next):
    print(f"dispatch on preprocess_request")
    def is_static_file(filename: str) -> bool:
        if filename.find(".")<0:return False
        static_extensions = ['.css', '.js', '.png', '.jpg']
        file_extension = os.path.splitext(filename)[1].lower()
        return file_extension in static_extensions
    if is_static_file(request.url.path): 
        curpath = os.path.realpath(os.curdir+"/app/views")
        abspath = os.path.realpath(curpath+request.url.path )
        response = FileResponse(path= (abspath),filename=os.path.basename(abspath))
        return response 
   
    if __is_debug:start_time = time.time() 
    response:Response = await call_next(request)
    if __is_debug:
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time) 
    
     
    # response.request = request
    return response

 


__is_debug=False
def run(*args,**kwargs): 
    ip =  "host" in kwargs  and kwargs["host"]  or '127.0.0.1' 
    port = "port" in kwargs  and kwargs["port"] or 8000  
    isDebug = "debug" in kwargs and kwargs["debug"]  
     
    if not len(__all_controller__)>0:
        raise "must use @api_route to define a controller class"
     
    for ctrl in __all_controller__:
        register_controllers_to_app(__app, ctrl) 
    global __is_debug
    __is_debug = isDebug
    uvicorn.run(__app, host=ip, port=port,debug=isDebug)