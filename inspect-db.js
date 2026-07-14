const Database = require('better-sqlite3');
const db = new Database('backend/data/bigscreen.db');
const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all();
console.log('Tables:', tables.map(t => t.name).join(', '));
tables.forEach(t => {
  const cols = db.prepare(`PRAGMA table_info(${t.name})`).all();
  console.log('\nTable: ' + t.name);
  cols.forEach(c => console.log('  ' + c.name + ' (' + c.type + ')'));
});
db.close();
