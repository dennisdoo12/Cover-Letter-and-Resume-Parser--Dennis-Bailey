// Import libraries
const express = require("express");
const cors = require("cors");
const multer = require("multer");
const sqlite3 = require("sqlite3").verbose();
const fs = require("fs");
const crypto = require("crypto");

// Create backend app
const app = express();
const PORT = 5050;

// Middleware
app.use(cors());
app.use(express.json());

// Simple logging for debugging
app.use((req, res, next) => {
  const startTime = Date.now();

  res.on("finish", () => {
    const timeTaken = Date.now() - startTime;
    console.log(`${req.method} ${req.originalUrl} - ${res.statusCode} - ${timeTaken}ms`);
  });

  next();
});

// Make sure uploads folder exists
fs.mkdirSync("uploads", { recursive: true });

// Connect to SQLite database
const db = new sqlite3.Database("./resumerank.db", (err) => {
  if (err) {
    console.error("Database connection failed:", err.message);
  } else {
    console.log("Connected to ResumeRank SQLite database.");
  }
});

// Creating tables based on Rae's updated database schema
db.serialize(() => {
  db.run("PRAGMA foreign_keys = ON");

  db.run(`
    CREATE TABLE IF NOT EXISTS User (
      user_id INTEGER NOT NULL PRIMARY KEY,
      user_username TEXT(30) NOT NULL,
      user_password TEXT(30) NOT NULL,
      user_firstname TEXT,
      user_lastname TEXT
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS JobListing (
      job_id INTEGER NOT NULL PRIMARY KEY,
      job_title TEXT NOT NULL,
      job_desc TEXT,
      user_id INTEGER NOT NULL,
      FOREIGN KEY (user_id) REFERENCES User(user_id)
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS Candidate (
      cand_id INTEGER NOT NULL PRIMARY KEY,
      cand_name TEXT,
      cand_phone TEXT,
      cand_email TEXT,
      user_id INTEGER NOT NULL,
      FOREIGN KEY (user_id) REFERENCES User(user_id)
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS Resume (
      res_id INTEGER NOT NULL PRIMARY KEY,
      res_filename TEXT,
      res_parsedtext TEXT,
      cand_id INTEGER NOT NULL,
      FOREIGN KEY (cand_id) REFERENCES Candidate(cand_id)
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS CoverLetter (
      cover_id INTEGER NOT NULL PRIMARY KEY,
      cover_filename TEXT,
      cover_parsedtext TEXT,
      cand_id INTEGER NOT NULL,
      FOREIGN KEY (cand_id) REFERENCES Candidate(cand_id)
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS Skill (
      cand_id INTEGER NOT NULL,
      skill_name TEXT,
      FOREIGN KEY (cand_id) REFERENCES Candidate(cand_id)
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS Score (
      cand_id INTEGER NOT NULL,
      job_id INTEGER NOT NULL,
      score_number REAL,
      FOREIGN KEY (cand_id) REFERENCES Candidate(cand_id),
      FOREIGN KEY (job_id) REFERENCES JobListing(job_id)
    )
  `);

  // Sample user for demo login
  db.run(`
    INSERT OR IGNORE INTO User 
    (user_id, user_username, user_password, user_firstname, user_lastname)
    VALUES
    (1, 'dummyUser', 'SecretPassWord1223', 'Tony', 'Stark')
  `);

  // Sample job for demo ranking
  db.run(`
    INSERT OR IGNORE INTO JobListing
    (job_id, job_title, job_desc, user_id)
    VALUES
    (1, 'Backend Developer Intern', 'Looking for Python, SQL, Docker, AWS, and backend development skills.', 1)
  `);
});

// Simple in-memory session storage
const sessions = new Map();
const SESSION_TIME = 30 * 60 * 1000;

// Create session token after login
function createSession(user) {
  const token = crypto.randomBytes(24).toString("hex");

  sessions.set(token, {
    userId: user.user_id,
    username: user.user_username,
    expiresAt: Date.now() + SESSION_TIME
  });

  return token;
}

// Check if user is logged in
function requireSession(req, res, next) {
  const authHeader = req.headers.authorization || "";
  const token = authHeader.startsWith("Bearer ") ? authHeader.slice(7) : null;

  if (!token || !sessions.has(token)) {
    return res.status(401).json({ error: "Please log in first." });
  }

  const session = sessions.get(token);

  if (Date.now() > session.expiresAt) {
    sessions.delete(token);
    return res.status(401).json({ error: "Session expired. Please log in again." });
  }

  session.expiresAt = Date.now() + SESSION_TIME;
  req.user = session;

  next();
}

// Convert skills into a clean array
function normalizeSkills(skills) {
  if (!skills) {
    return [];
  }

  if (Array.isArray(skills)) {
    return skills.map(String).map((skill) => skill.trim()).filter(Boolean);
  }

  if (typeof skills === "string") {
    return skills.split(",").map((skill) => skill.trim()).filter(Boolean);
  }

  return [];
}

// Save skills into Skill table
function saveSkills(candidateId, skills, callback) {
  const cleanSkills = [...new Set(normalizeSkills(skills))];

  if (cleanSkills.length === 0) {
    return callback(null);
  }

  let completed = 0;
  let hasError = false;

  cleanSkills.forEach((skill) => {
    db.run(
      "INSERT INTO Skill (cand_id, skill_name) VALUES (?, ?)",
      [candidateId, skill],
      (err) => {
        if (hasError) {
          return;
        }

        if (err) {
          hasError = true;
          return callback(err);
        }

        completed++;

        if (completed === cleanSkills.length) {
          callback(null);
        }
      }
    );
  });
}

// File upload setup
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, "uploads/");
  },

  filename: function (req, file, cb) {
    const uniqueName = Date.now() + "-" + file.originalname;
    cb(null, uniqueName);
  }
});

// Allow only resume/cover letter file types
const fileFilter = (req, file, cb) => {
  const allowedTypes = [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain"
  ];

  if (allowedTypes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error("Only PDF, Word, or text files are allowed."));
  }
};

const upload = multer({
  storage: storage,
  fileFilter: fileFilter,
  limits: {
    fileSize: 5 * 1024 * 1024
  }
});

// Route 1: Health check
app.get("/api/health", (req, res) => {
  res.json({ message: "ResumeRank backend is running." });
});

// Route 2: Login
app.post("/api/auth/login", (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({ error: "Username and password are required." });
  }

  db.get(
    "SELECT * FROM User WHERE user_username = ? AND user_password = ?",
    [username, password],
    (err, user) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      if (!user) {
        return res.status(401).json({ error: "Invalid username or password." });
      }

      const token = createSession(user);

      res.json({
        message: "Login successful.",
        token: token,
        user: {
          id: user.user_id,
          username: user.user_username,
          firstName: user.user_firstname,
          lastName: user.user_lastname
        }
      });
    }
  );
});

// Route 3: Check session
app.get("/api/auth/session", requireSession, (req, res) => {
  res.json({
    message: "Session is active.",
    user: req.user
  });
});

// Route 4: Get job listings
app.get("/api/jobs", (req, res) => {
  db.all(
    `
    SELECT 
      JobListing.job_id,
      JobListing.job_title,
      JobListing.job_desc,
      User.user_username
    FROM JobListing
    LEFT JOIN User ON JobListing.user_id = User.user_id
    ORDER BY JobListing.job_id
    `,
    [],
    (err, rows) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      res.json(rows);
    }
  );
});

// Route 5: Create candidate
app.post("/api/candidates", requireSession, (req, res) => {
  const { name, phone, email } = req.body;

  if (!name) {
    return res.status(400).json({ error: "Candidate name is required." });
  }

  db.run(
    "INSERT INTO Candidate (cand_name, cand_phone, cand_email, user_id) VALUES (?, ?, ?, ?)",
    [name, phone, email, req.user.userId],
    function (err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      res.status(201).json({
        message: "Candidate created.",
        candidateId: this.lastID
      });
    }
  );
});

// Route 6: Upload resume file
app.post("/api/resumes/upload", requireSession, upload.single("resume"), (req, res) => {
  const { candidateId, parsedText, skills } = req.body;

  if (!candidateId) {
    return res.status(400).json({ error: "Candidate ID is required." });
  }

  if (!req.file) {
    return res.status(400).json({ error: "Resume file is required." });
  }

  db.run(
    "INSERT INTO Resume (res_filename, res_parsedtext, cand_id) VALUES (?, ?, ?)",
    [req.file.filename, parsedText || "", candidateId],
    function (err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      saveSkills(candidateId, skills, (skillErr) => {
        if (skillErr) {
          return res.status(500).json({ error: skillErr.message });
        }

        res.status(201).json({
          message: "Resume uploaded successfully.",
          resumeId: this.lastID,
          fileName: req.file.filename
        });
      });
    }
  );
});

// Route 7: Upload cover letter file
app.post("/api/cover-letters/upload", requireSession, upload.single("coverLetter"), (req, res) => {
  const { candidateId, parsedText } = req.body;

  if (!candidateId) {
    return res.status(400).json({ error: "Candidate ID is required." });
  }

  if (!req.file) {
    return res.status(400).json({ error: "Cover letter file is required." });
  }

  db.run(
    "INSERT INTO CoverLetter (cover_filename, cover_parsedtext, cand_id) VALUES (?, ?, ?)",
    [req.file.filename, parsedText || "", candidateId],
    function (err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      res.status(201).json({
        message: "Cover letter uploaded successfully.",
        coverLetterId: this.lastID,
        fileName: req.file.filename
      });
    }
  );
});

// Route 8: Save score manually
app.post("/api/scores", requireSession, (req, res) => {
  const { candidateId, jobId, score } = req.body;

  if (!candidateId || !jobId || score === undefined) {
    return res.status(400).json({ error: "Candidate ID, job ID, and score are required." });
  }

  db.run(
    "INSERT INTO Score (cand_id, job_id, score_number) VALUES (?, ?, ?)",
    [candidateId, jobId, score],
    function (err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      res.status(201).json({ message: "Score saved." });
    }
  );
});

// Route 9: Receive Alex's parser and matcher result
app.post("/api/parser-results", requireSession, (req, res) => {
  const {
    parsed,
    scored,
    reason,
    file,
    name,
    email,
    phone,
    skills,
    matched_skills,
    jobId,
    match_score
  } = req.body;

  if (parsed === false || scored === false) {
    return res.status(422).json({
      message: "Parser could not process this file.",
      reason: reason || "No reason provided.",
      file: file || null
    });
  }

  if (!name || !jobId || match_score === undefined) {
    return res.status(400).json({
      error: "Name, job ID, and match score are required."
    });
  }

  const parsedText = JSON.stringify(req.body, null, 2);
  const allSkills = [...normalizeSkills(skills), ...normalizeSkills(matched_skills)];

  db.run(
    "INSERT INTO Candidate (cand_name, cand_phone, cand_email, user_id) VALUES (?, ?, ?, ?)",
    [name, phone, email, req.user.userId],
    function (err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      const newCandidateId = this.lastID;

      db.run(
        "INSERT INTO Resume (res_filename, res_parsedtext, cand_id) VALUES (?, ?, ?)",
        [file || "parser-output", parsedText, newCandidateId],
        function (err) {
          if (err) {
            return res.status(500).json({ error: err.message });
          }

          saveSkills(newCandidateId, allSkills, (skillErr) => {
            if (skillErr) {
              return res.status(500).json({ error: skillErr.message });
            }

            db.run(
              "INSERT INTO Score (cand_id, job_id, score_number) VALUES (?, ?, ?)",
              [newCandidateId, jobId, match_score],
              function (err) {
                if (err) {
                  return res.status(500).json({ error: err.message });
                }

                res.status(201).json({
                  message: "Alex parser result saved.",
                  candidateId: newCandidateId,
                  jobId: jobId,
                  score: match_score
                });
              }
            );
          });
        }
      );
    }
  );
});

// Route 10: Receive Dennis's cover letter quality result
app.post("/api/cover-letter-results", requireSession, (req, res) => {
  const {
    candidateId,
    name,
    email,
    phone,
    skills,
    file
  } = req.body;

  const parsedText = JSON.stringify(req.body, null, 2);

  function saveCoverLetter(finalCandidateId) {
    db.run(
      "INSERT INTO CoverLetter (cover_filename, cover_parsedtext, cand_id) VALUES (?, ?, ?)",
      [file || "cover-letter-parser-output", parsedText, finalCandidateId],
      function (err) {
        if (err) {
          return res.status(500).json({ error: err.message });
        }

        saveSkills(finalCandidateId, skills, (skillErr) => {
          if (skillErr) {
            return res.status(500).json({ error: skillErr.message });
          }

          res.status(201).json({
            message: "Dennis parser result saved.",
            candidateId: finalCandidateId,
            coverLetterId: this.lastID
          });
        });
      }
    );
  }

  if (candidateId) {
    return saveCoverLetter(candidateId);
  }

  if (!name) {
    return res.status(400).json({
      error: "Candidate ID or candidate name is required."
    });
  }

  db.run(
    "INSERT INTO Candidate (cand_name, cand_phone, cand_email, user_id) VALUES (?, ?, ?, ?)",
    [name, phone, email, req.user.userId],
    function (err) {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      saveCoverLetter(this.lastID);
    }
  );
});

// Route 11: Get all candidates
app.get("/api/candidates", (req, res) => {
  db.all(
    `
    SELECT 
      Candidate.cand_id,
      Candidate.cand_name,
      Candidate.cand_phone,
      Candidate.cand_email,
      GROUP_CONCAT(Skill.skill_name, ', ') AS skills
    FROM Candidate
    LEFT JOIN Skill ON Candidate.cand_id = Skill.cand_id
    GROUP BY Candidate.cand_id
    ORDER BY Candidate.cand_id
    `,
    [],
    (err, rows) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      res.json(rows);
    }
  );
});

// Route 12: Get ranked candidates for a job
app.get("/api/rankings/:jobId", (req, res) => {
  const { jobId } = req.params;

  db.all(
    `
    SELECT 
      Candidate.cand_id,
      Candidate.cand_name,
      Candidate.cand_phone,
      Candidate.cand_email,
      JobListing.job_id,
      JobListing.job_title,
      Score.score_number,
      Resume.res_filename,
      CoverLetter.cover_filename,
      GROUP_CONCAT(Skill.skill_name, ', ') AS skills
    FROM Score
    JOIN Candidate ON Score.cand_id = Candidate.cand_id
    JOIN JobListing ON Score.job_id = JobListing.job_id
    LEFT JOIN Resume ON Candidate.cand_id = Resume.cand_id
    LEFT JOIN CoverLetter ON Candidate.cand_id = CoverLetter.cand_id
    LEFT JOIN Skill ON Candidate.cand_id = Skill.cand_id
    WHERE Score.job_id = ?
    GROUP BY Candidate.cand_id, JobListing.job_id, Score.score_number
    ORDER BY Score.score_number DESC
    `,
    [jobId],
    (err, rows) => {
      if (err) {
        return res.status(500).json({ error: err.message });
      }

      res.json(rows);
    }
  );
});

// Route 13: Database status for demo
app.get("/api/database-status", (req, res) => {
  const tables = ["User", "JobListing", "Candidate", "Resume", "CoverLetter", "Skill", "Score"];
  const result = {};
  let completed = 0;

  tables.forEach((table) => {
    db.get(`SELECT COUNT(*) AS count FROM ${table}`, [], (err, row) => {
      if (err) {
        result[table] = "error";
      } else {
        result[table] = row.count;
      }

      completed++;

      if (completed === tables.length) {
        res.json(result);
      }
    });
  });
});


// Backend demo dashboard
app.get("/demo", (req, res) => {
  res.send(`
<!DOCTYPE html>
<html>
<head>
  <title>ResumeRank Backend Demo</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #111827;
      color: #f9fafb;
      padding: 30px;
    }

    h1 {
      color: #93c5fd;
    }

    h2 {
      color: #bfdbfe;
      margin-top: 25px;
    }

    .card {
      background: #1f2937;
      border: 1px solid #374151;
      border-radius: 12px;
      padding: 18px;
      margin-bottom: 18px;
    }

    button {
      background: #2563eb;
      color: white;
      border: none;
      border-radius: 8px;
      padding: 10px 14px;
      cursor: pointer;
      margin-right: 8px;
    }

    button:hover {
      background: #1d4ed8;
    }

    pre {
      background: #030712;
      color: #d1d5db;
      padding: 14px;
      border-radius: 8px;
      overflow-x: auto;
      white-space: pre-wrap;
    }

    a {
      color: #93c5fd;
    }
  </style>
</head>
<body>
  <h1>ResumeRank Backend Demo</h1>

  <div class="card">
    <p>This page shows Bayram's backend API working with the SQLite database.</p>
    <p>After uploading a resume through the Flask UI, refresh the database status and rankings below.</p>
  </div>

  <div class="card">
    <h2>Useful Routes</h2>
    <p><a href="/api/health" target="_blank">/api/health</a></p>
    <p><a href="/api/jobs" target="_blank">/api/jobs</a></p>
    <p><a href="/api/database-status" target="_blank">/api/database-status</a></p>
    <p><a href="/api/rankings/1" target="_blank">/api/rankings/1</a></p>
  </div>

  <div class="card">
    <h2>Database Status</h2>
    <button onclick="loadDatabaseStatus()">Refresh Database Status</button>
    <pre id="databaseStatus">Loading...</pre>
  </div>

  <div class="card">
    <h2>Ranked Candidates for Job ID 1</h2>
    <button onclick="loadRankings()">Refresh Rankings</button>
    <pre id="rankings">Loading...</pre>
  </div>

  <script>
    async function loadDatabaseStatus() {
      const box = document.getElementById("databaseStatus");

      try {
        const response = await fetch("/api/database-status");
        const data = await response.json();
        box.textContent = JSON.stringify(data, null, 2);
      } catch (error) {
        box.textContent = "Could not load database status: " + error.message;
      }
    }

    async function loadRankings() {
      const box = document.getElementById("rankings");

      try {
        const response = await fetch("/api/rankings/1");
        const data = await response.json();
        box.textContent = JSON.stringify(data, null, 2);
      } catch (error) {
        box.textContent = "Could not load rankings: " + error.message;
      }
    }

    loadDatabaseStatus();
    loadRankings();
  </script>
</body>
</html>
  `);
});


// Error handler
app.use((err, req, res, next) => {
  res.status(400).json({ error: err.message });
});

// Start server
app.listen(PORT, () => {
  console.log(`Backend server running on http://localhost:${PORT}`);
});