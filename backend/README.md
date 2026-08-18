# ResumeRank Backend

This is Bayram Charyyev's backend API for the ResumeRank capstone project.

## Tech Stack

- Node.js
- Express
- SQLite
- Multer
- CORS

## What This Backend Does

- Creates and connects to the SQLite database
- Creates the main tables: User, JobListing, Candidate, Resume, CoverLetter, Skill, and Score
- Provides authentication/session routes
- Receives resume parser/matcher results
- Receives cover letter parser results
- Saves candidate, resume, cover letter, skill, and score data
- Returns ranked candidates by job ID
- Provides a backend demo dashboard

## Run Locally

Install dependencies:

npm install

Start backend:

npm start

Backend runs on:

http://localhost:5050

Backend demo page:

http://localhost:5050/demo

Useful API routes:

- GET /api/health
- GET /api/jobs
- POST /api/auth/login
- GET /api/auth/session
- POST /api/parser-results
- POST /api/cover-letter-results
- GET /api/database-status
- GET /api/rankings/1

## Demo Login

username: dummyUser  
password: SecretPassWord1223

## Integration

The Flask UI/parser app runs from:

cover-letter-parser-capstone/

The Flask app runs on:

http://127.0.0.1:5000

The Flask app sends parsed resume and cover letter results to this backend on:

http://localhost:5050
