from fastapi import FastAPI

app = FastAPI(swagger_ui_parameters={})

@app.get("/")
def read_root():
    return 'Hello World'