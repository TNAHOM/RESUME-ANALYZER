# n8n-Driven Resume Analyzer (Secure & AI-Powered)

## Summary
A minimal backend service paired with an n8n-based automation flow to process PDF resumes. Uploaded resumes are sent through a workflow that extracts text, invokes Gemini for structured data extraction, and stores the results in Supabase. All services are orchestrated via Docker Compose for quick setup and deployment.

## Features
- Accept PDF resume uploads via HTTP API
- Send resumes to n8n for:
  - Text extraction
  - Gemini-powered information extraction (name, email, phone, skills, experience, last role)
  - Structured JSON transformation
  - Persist extracted data into Supabase

## Project Components
```
resume-analyzer/
├── .dockerignore
├── .env
├── .env.example
├── .git/
├── .gitignore
├── backend/
│   ├── auth.py
│   ├── Dockerfile
│   ├── main.py
│   ├── requirements.txt
│   ├── storage/
│   ├── upload.py
│   ├── __init__.py
│   └── __pycache__/
├── credential.json
├── docker-compose.yml
├── storage/
│   ├── final_v6(B1).pdf
│   ├── final_v6(F1) (1).pdf
│   └── final_v6(F1)p.pdf
├── venv/
└── workflows/
    └── resume_workflow.json
└── README.md               # Project documentation
```

## Prerequisites
- Docker & Docker Compose
- (Optional) Python 3.11+ for local development
- A Google Service Account JSON key
- Gemini API key 

## Configuration
Before you begin, set up Google Drive API credentials:
1. In the Google Cloud Console, enable the Google Drive API.
2. Create a service account with Drive File permissions.
3. Download the service account JSON key and save it as `credential.json` in the project root.
4. Create a Google Drive folder, set sharing to "Anyone with link can view", and note its folder ID.

1. Copy `.env.example` to `.env` at project root.
2. Populate the following variables:
   ```dotenv
   SERVICE_ACCOUNT_FILE=credential.json
   GOOGLE_DRIVE_SCOPES=https://www.googleapis.com/auth/drive.file
   GOOGLE_DRIVE_FOLDER_ID=<your-google-drive-folder-id>  # Make the folder publicly viewable ("Anyone with link can view")
   N8N_WEBHOOK_URL=<your-n8n-webhook-url>
   GEMINI_API_KEY=<your-gemini-api-key>
   ```

3. Place your Google service account JSON file as `credential.json` in the project root.

## Running with Docker Compose
In PowerShell, from project root:
```powershell
docker-compose up --build
```
This will launch the following services:
- **backend**: FastAPI server on port 8000

## Usage
Once services are up, upload a PDF resume:
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/resume.pdf" \
  -H "Content-Type: multipart/form-data"
```
On success, the response returns the original filename and a link (if configured) to the uploaded file in Google Drive.

## n8n Workflow
The `resume_workflow.json` defines an n8n flow:
1. **Trigger**: Webhook node listens for incoming requests.
2. **Text Extraction**: Extract PDF text.
3. **Gemini**: Prompt the model to parse full name, email, phone, skills, years of experience, and last job title.
4. **Data Transformation**: Format LLM response into structured JSON.
5. **Supabase**: Use Supabase node to insert the record into your Supabase database.
