const Database = require('better-sqlite3');
const db = new Database('backend/data/bigscreen.db');

const schema = db.prepare("SELECT sql FROM sqlite_master WHERE name='projects'").get();
console.log('projects table:', schema?.sql);

const projects = db.prepare('SELECT * FROM projects').all();
console.log('\nExisting projects:');
projects.forEach(p => console.log(`  id=${p.id}, name=${p.name}`));

db.close();