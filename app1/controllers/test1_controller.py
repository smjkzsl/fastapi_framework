from fastapi_mvc_framework import controller,api_router,api

@api_router(version="v1.0",path="")
class Test1Controller:
    @api.get('/home')
    def home(self):
        return self.view()
    