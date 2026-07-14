const Database = require('better-sqlite3');
const db = new Database('backend/data/bigscreen.db');

try {
  db.prepare("ALTER TABLE projects ADD COLUMN special INTEGER DEFAULT 0").run();
  console.log('Added special column successfully');
  
  const schema = db.prepare("SELECT sql FROM sqlite_master WHERE name='projects'").get();
  console.log('\nUpdated schema:', schema?.sql);
} catch (e) {
  if (e.message.includes('duplicate column')) {
    console.log('Column already exists');
  } else {
    throw e;
  }
}

db.close();