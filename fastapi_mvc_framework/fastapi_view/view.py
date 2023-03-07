import os
from fastapi import Request,Response
from fastapi.templating import Jinja2Templates
import inspect
# from . import view_request


class _View(object):
    def __init__(self,request,response=None,version="",tmpl_path:str=f"{os.path.abspath('')}/app/views"):
        self._views_directory = tmpl_path
        self._templates = Jinja2Templates(directory=self.views_directory)
        self.request = request
        self.response = response
        self.version = version
    @property
    def templates(self):
        return self._templates

    @property
    def views_directory(self):
        return self._views_directory
    
    @views_directory.setter
    def views_directory(self, views_directory: str):
        self._views_directory = views_directory
        self._templates = Jinja2Templates(directory=self.views_directory)

    def __call__(self, view_path: str="", context: dict={},local2context:bool=True):
        request = self.request
        if not request or not isinstance(request, Request):
            raise ValueError("request instance type must be fastapi.Request")
        
        caller_frame = inspect.currentframe().f_back
        # caller_file = caller_frame.f_code.co_filename
        # caller_lineno = caller_frame.f_lineno
        caller_function_name = caller_frame.f_code.co_name
        caller_locals = caller_frame.f_locals
        caller_class = caller_locals.get("self", None).__class__
        caller_classname:str = caller_class.__name__
        caller_classname = caller_classname.replace("Controller","").lower()
        #caller_file = os.path.basename(caller.filename) 
        if local2context and not context:
            del caller_locals['self']
            context = caller_locals
        if view_path=="":
            if self.version:
                version_path = f"{self.version}/"
            else:
                version_path = ""
            view_path = f"{caller_classname}/{version_path}{caller_function_name}.html" 
        

        if not view_path.endswith(".html"):
            view_path = f"{view_path}.html"

        context["request"] = request
        return self._templates.TemplateResponse(view_path, context)
         
