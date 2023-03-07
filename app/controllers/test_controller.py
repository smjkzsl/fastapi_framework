
from fastapi_mvc_framework import api_router,api,Request,Response


@api_router( )
class TestController():
    request:Request=None
    response:Response=None
    def __init__(self):
        print(f"__init__ on TestController")

    @api.get("/" )
    def home(self): 
        c = self.session['a'] or 1
        c = c+1 
        #从 cookies 字典中写出cookies 
        self.response.set_cookie('a',c) 
        self.session['a'] = c
        text = "你好，世界！"
        return self.view()
    


    
@api_router(version="2.0",path="/{version}/{controller}")
class ABCController():
    def __init__(self):
        print(f"__init__ on ABCController")

    @api.get("/abcd" )
    def home(self):
        v = "这是个神奇的世界"
        
        
        return self.view()
