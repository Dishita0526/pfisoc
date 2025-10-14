# main.py
from fastapi import FastAPI, UploadFile
from extract import extract_text_from_pdf

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Compliance API running"}

@app.post("/upload/")
async def upload_pdf(file: UploadFile):
    file_location = f"temp/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    
    text = extract_text_from_pdf(file_location)
    return {"filename": file.filename, "text": text}
