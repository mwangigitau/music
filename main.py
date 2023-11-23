from fastapi import FastAPI, HTTPException, BackgroundTasks
import uvicorn
from app.models import Message
from app.logic import publish_url, consume_url

fastapi_app = FastAPI()


@fastapi_app.post("/submit/query")
async def submit_url(params: Message, background_tasks: BackgroundTasks):
    data = publish_url(params.SongURL)
    background_tasks.add_task(consume_url)
    print(f"The data is {data}")
    if data is None:
        raise HTTPException(status_code=500, detail="Song URL not submitted")
    return {"data": data}


if __name__ == "__main__":
    uvicorn.run(app=fastapi_app, port=8080, host="0.0.0.0")
