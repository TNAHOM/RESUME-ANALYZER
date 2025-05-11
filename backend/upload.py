from fastapi import APIRouter, File, UploadFile, HTTPException, status
import os
from pathlib import Path
import httpx
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io
from dotenv import load_dotenv

load_dotenv()

# Read configuration from environment
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE')
SCOPES = os.getenv('GOOGLE_DRIVE_SCOPES', '').split(',')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')

router = APIRouter()

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

async def upload_to_google_drive(file_content: bytes, filename: str) -> str:
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': filename,
        }
        media = MediaIoBaseUpload(io.BytesIO(file_content),
                                  mimetype='application/pdf',
                                  resumable=True)
        
        uploaded_file = service.files().create(body=file_metadata,
                                               media_body=media,
                                               fields='id,webViewLink').execute()

        return uploaded_file.get('webViewLink')

    except Exception as e:
        print(f"Google Drive Upload Error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Failed to upload to Google Drive: {str(e)}")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf") or file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF uploads are allowed."
        )
    # Prevent directory traversal
    filename = os.path.basename(file.filename)
    save_path = STORAGE_DIR / filename
    
    content = await file.read()
    
    # Save file to local diRectory
    with open(save_path, "wb") as f:
        f.write(content)
    
    # Upload to Google Drive
    try:
        google_drive_url = await upload_to_google_drive(content, filename)
        if not google_drive_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get Google Drive URL after upload."
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during Google Drive upload call: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during Google Drive upload: {str(e)}"
        )

    # Send the Google Drive URL to the n8n webhook
    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, read=60.0)) as client:
        n8n_payload = {"pdfUrl": google_drive_url, "originalFilename": filename}
        try:
            resp = await client.post(
                N8N_WEBHOOK_URL,
                json=n8n_payload 
            )
            print(f"N8N Response status: {resp.status_code}")
            print(f"N8N Response content: {resp.text}")
            
            resp.raise_for_status()

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send URL to n8n: {e.response.status_code} - {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Request to n8n failed: {str(e)}"
            )
    
    return {"filename": filename, "googleDriveUrl": google_drive_url}