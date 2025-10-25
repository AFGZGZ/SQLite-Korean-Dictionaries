import sqlite3 from "sqlite3";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

//Change names if needed
const JSON_FILE = path.join(__dirname, "data.json");
const OUTPUT_DB = path.join(__dirname, "data.db");

function buildDatabase() {
  if (fs.existsSync(OUTPUT_DB)) {
    fs.unlinkSync(OUTPUT_DB);
    console.log("Old DB removed.");
  }

  const entries = JSON.parse(fs.readFileSync(JSON_FILE, "utf8"));
  console.log(`Loaded ${entries.length} entries from JSON.`);

  const db = new sqlite3.Database(OUTPUT_DB);

  db.serialize(() => {
    db.run("PRAGMA journal_mode=OFF;");
    db.run("PRAGMA synchronous=OFF;");

    db.run(`
      CREATE TABLE dictionary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT,
        definition TEXT
      );
    `);

    const stmt = db.prepare(
      "INSERT INTO dictionary (word, definition) VALUES (?, ?)"
    );

    db.run("BEGIN TRANSACTION;");

    for (const entry of entries) {
      stmt.run(entry.t, entry.d);
    }

    stmt.finalize();
    db.run("COMMIT;");

    db.run("CREATE INDEX idx_word ON dictionary(word);");
    db.run("VACUUM;");

    console.log(`Database built successfully at ${OUTPUT_DB}`);
  });

  db.close();
}

buildDatabase();
