
from fastapi_mvc_framework import api_router,api,Request,Response


@api_router( )
class TestController():
    request:Request=None
    response:Response=None
    def __init__(self):
        self.log.info(f"__init__ on TestController")

    @api.get("/" )
    def home(self): 
        c = self.session['home'] or 1
        c = c+1 
        # #setting cookies   
        # self.response.set_cookie('a',c) 
        self.session['home'] = c
        text = "Hello World! I'm in FastapiMvcFramework"
        
        return self.view()
    


    
@api_router(version="2.0",path="/{controller}/{version}")
class ABCController():
    def __init__(self):
        self.log.debug(f"__init__ on ABCController")

    @api.get("/abcd" )
    def home(self):
        v = "This is a <b><red>magical world<red></b>"
        c = self.session['home'] or 0
        if not c>0:
            return self.redirect("/")
        
        return self.view()
