from typing import Any,Dict
import uvicorn
from fastapi import FastAPI,UploadFile,File,Header, Depends,HTTPException,Request,Response
from fastapi.security import OAuth2PasswordBearer
from fastapi_mvc_framework import create_controller,controller as api,   register_controllers_to_app,Session, FileStorage,MemoryStorage
from pydantic import BaseModel 
from fastapi_controller.controller_utils import  TEMPLATE_PATH_KEY, VER_KEY
import time,os,inspect
from fastapi import FastAPI, Cookie,Request
 
from .fastapi_controller import SessionManager,_SESSION_STORAGES
import datetime  
from starlette.responses import FileResponse
from fastapi_mvc_framework.fastapi_view import _View
from hashlib import md5
from fastapi_mvc_framework.config import YamlConfig
from fastapi.staticfiles import StaticFiles

ROOT_PATH = os.path.realpath(os.curdir)


__app = FastAPI() 
__app_views_dirs = {}

__all_controller__ = []
config = YamlConfig(os.path.join(ROOT_PATH,"configs") )
__session_config = config.get('session')

_sessionManager = SessionManager(storage=_SESSION_STORAGES[__session_config['type']](__session_config['dir'],__session_config['secretkey']))
 

def api_router(path:str="", version:str=""):  
    '''
    path :special path format ,
    '''
    caller_frame = inspect.currentframe().f_back
    caller_file = caller_frame.f_code.co_filename
    relative_path = caller_file.replace(ROOT_PATH,"")
    if relative_path.count(os.sep)>2:
        app_dir = os.path.dirname(os.path.dirname(relative_path)).replace(os.sep,"")
    else:
        app_dir = "app"
    app_dir = os.path.join(ROOT_PATH,app_dir)

    def format_path(p,v):
        if p and  '{controller}' not in p :
            p += '/{controller}' 
            p += '/{version}' if v else ''
        if v and not path:
            p = "/{controller}/{version}"
        return p
    path = format_path(path,version) 
    _controllerBase = create_controller(path,version)  
        
    __all_controller__.append(_controllerBase)
    
    def _wapper(targetController):  
        # 定义一个傀儡类，继承自目标类  
        class puppetController( targetController ,_controllerBase ): 
            
            def __init__(self,**kwags) -> None:
                print(f"__init__ on puppetController")
                super().__init__()
             
            @property
            def view(self): 
                def url_for(url:str="",type:str="static",**kws):
                    url_path :str = self.__view_url__ 
                    url = url.strip()
                    if type!='static' or kws: #url route
                        if kws:
                            url_path = ""
                            pairs = []
                            if 'app' in kws and kws['app'].strip():
                                pairs.append(kws['app'].strip())
                            if 'controller' in kws  and kws['controller'].strip():
                                pairs.append(kws['controller'].strip())
                            if 'version' in kws  and kws['version'].strip():
                                pairs.append(kws['version'].strip())
                            if 'action' in kws  and kws['action'].strip():
                                pairs.append(kws['action'].strip())
                            elif url :
                                pairs.append(url)
                            url_path = "/"+"/".join(pairs)
                            return url_path
                            pass
                        else:
                             
                            url_path = self.__template_path__.replace('{controller}',self.__controller_name__).replace("{version}",self.__version__)
                            return url_path + "/" + url.strip()
                    else:
                        url_path += '/' + self.__controller_name__
                        if self.__version__:
                            url_path += '/' + self.__version__
                        return url_path + "/"  + url.strip()
                    
                template_path = os.path.join(self.__appdir__,"views")
                viewobj = _View(self.request,self.response,self.__version__,tmpl_path=template_path) 
                viewobj._templates.env.globals["url_for"] = url_for 
                return viewobj
            
            async def getUploadFile(self,file:File):  
                if config.get("upload"):
                    updir = config.get("upload")['dir'] or "uploads"
                else:
                    updir = 'uploads'
                _save_dir = os.path.join(ROOT_PATH,updir) 
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
                self.session = await  _sessionManager.initSession(request,response )

            async def _deconstructor(self,new_response:Response):
                await _sessionManager.process(session =  self.session,response = new_response,request=self.request)
                pass
                 
        setattr(puppetController,"__name__",targetController.__name__)  
        setattr(puppetController,"__controller_name__",targetController.__name__.lower().replace("controller",""))  
        
        setattr(puppetController,"__version__",version)  
        setattr(puppetController,"__location__",relative_path)  
        setattr(puppetController,"__appdir__",app_dir)  

        setattr(puppetController,"__controler_url__",targetController.__name__.lower().replace("controller",""))  
        #for generate url_for function
        _view_url_path:str = "/" + os.path.basename(app_dir) + '_views'  
         
        setattr(puppetController,"__view_url__",_view_url_path) 

        #add app dir sub views to StaticFiles
        if not app_dir in __app_views_dirs:
            __app_views_dirs[app_dir] = os.path.join(app_dir,"views")
            #path match static files
            _static_path = _view_url_path              
            __app.mount(_static_path,  StaticFiles(directory=__app_views_dirs[app_dir]), name=os.path.basename(app_dir))
 
        return puppetController 
    return _wapper #: @puppetController 





@__app.middleware("http")
async def preprocess_request(request: Request, call_next):
    print(f"dispatch on preprocess_request")
    # def is_static_file(filename: str) -> bool:
    #     if filename.find(".")<0:return False
    #     static_extensions = ['.css', '.js', '.png', '.jpg']
    #     file_extension = os.path.splitext(filename)[1].lower()
    #     return file_extension in static_extensions
    # if is_static_file(request.url.path): 
    #     curpath = os.path.realpath(os.curdir+"/app/views")
    #     abspath = os.path.realpath(curpath+request.url.path )
    #     response = FileResponse(path=abspath,filename=os.path.basename(abspath))
    #     return response 
   
    if __is_debug:
        start_time = time.time() 
    #pre call to controller method
    response:Response = await call_next(request)

    if __is_debug:
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)  
    return response 

__is_debug=False
def run(*args,**kwargs): 
    ip =  "host" in kwargs  and kwargs["host"]  or '127.0.0.1' 
    port = "port" in kwargs  and kwargs["port"] or 8000  
    isDebug = "debug" in kwargs and kwargs["debug"]  
    global __is_debug
    __is_debug = isDebug 
    
    if not len(__all_controller__)>0:
        raise "must use @api_route to define a controller class"
    all_routers = []
    for ctrl in __all_controller__:
        all_routers.append(register_controllers_to_app(__app, ctrl))
    if isDebug:
        print("all router:\n")
        for router in all_routers:
            for r in router.routes:
                funcname = str(r.endpoint).split('<function ')[1].split(" at ")[0]
                print(f"*****   \033[1;43m  http:{ip}:{port}{r.path} \033[0m ->({funcname})" )
    
    uvicorn.run(__app, host=ip, port=port,debug=isDebug)