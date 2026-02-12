import express from "express";
import path from "path";
import crypto from "crypto";
import Database from "better-sqlite3";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
app.use(express.json());

// ✅ Serve ALL flat files (index.html, app.js, styles.css) from the same folder
app.use(express.static(__dirname));

// ---------------- DB ----------------
const db = new Database("hangout.db");
db.exec(`
CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  title TEXT,
  start_date TEXT,
  end_date TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS responses (
  event_id TEXT,
  name TEXT,
  unavailable_json TEXT,
  updated_at TEXT,
  PRIMARY KEY (event_id, name)
);
`);

function now() {
  return new Date().toISOString();
}

// -------- Multi-word ID --------
const WORDS = [
  "ember","falcon","plum","violet","orbit","river","thunder","cinder","puzzle","lumen",
  "hazel","comet","atlas","raven","mango","cedar","opal","breeze","quantum","saffron",
  "zenith","pickle","marble","anchor","lantern","kestrel","glacier","squid","pepper",
  "nectar","spruce","jigsaw","cobalt","fjord","tulip","aurora","socket","crystal",
  "mosaic","pirate","canyon","whisper","rocket","basil","matrix","copper","plasma",
  "fable","cashew","goblin","vortex","sugar","radar","cactus","magnet","tiger","kiwi",
  "octane","sphinx","dragon","sailor","waffle","ripple","velvet","banjo","scooter"
];

function randWord() {
  return WORDS[crypto.randomInt(0, WORDS.length)];
}

function makeId() {
  const token = crypto.randomBytes(5).toString("base64url").toUpperCase();
  return `${randWord()}-${randWord()}-${randWord()}-${token}`;
}

// ---------------- API ----------------

app.post("/api/events", (req, res) => {
  const { title, startDate, endDate } = req.body || {};
  if (!title || !startDate || !endDate) {
    return res.status(400).json({ error: "Missing fields: title, startDate, endDate" });
  }

  const id = makeId();

  db.prepare(`
    INSERT INTO events (id, title, start_date, end_date, created_at)
    VALUES (?, ?, ?, ?, ?)
  `).run(id, title, startDate, endDate, now());

  res.json({ id });
});

app.get("/api/events/:id", (req, res) => {
  const event = db.prepare("SELECT * FROM events WHERE id = ?").get(req.params.id);
  if (!event) return res.status(404).json({ error: "Not found" });

  const responses = db.prepare(
    "SELECT name, unavailable_json FROM responses WHERE event_id = ?"
  ).all(req.params.id);

  res.json({
    event,
    responses: responses.map(r => ({
      name: r.name,
      unavailable: JSON.parse(r.unavailable_json)
    }))
  });
});

app.post("/api/events/:id/submit", (req, res) => {
  const { name, unavailableDates } = req.body || {};
  if (!name) return res.status(400).json({ error: "Name required" });

  db.prepare(`
    INSERT INTO responses (event_id, name, unavailable_json, updated_at)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(event_id, name) DO UPDATE SET
      unavailable_json = excluded.unavailable_json,
      updated_at = excluded.updated_at
  `).run(
    req.params.id,
    name,
    JSON.stringify(unavailableDates || []),
    now()
  );

  res.json({ ok: true });
});

// ---------------- Start ----------------
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Running on http://localhost:${PORT}`);
});
