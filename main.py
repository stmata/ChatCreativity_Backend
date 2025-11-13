from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.chat_router import router as chat_router
from routes.analyse_router import router as analyse_router
from routes.admin_router import router as admin_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(analyse_router)
app.include_router(admin_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
