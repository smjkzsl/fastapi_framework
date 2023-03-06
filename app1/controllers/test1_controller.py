from fastapi_framework import controller,api_router,api

@api_router(version="1.0",path="")
class Test1Controller:
    @api.get('/home')
    def home(self):
        return self.view()
    