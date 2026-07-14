const Database = require('better-sqlite3');
const db = new Database('backend/data/bigscreen.db', { readonly: true });

// 找到 MTPF 项目
const proj = db.prepare("SELECT * FROM projects WHERE name LIKE '%MTPF%'").get();
console.log('项目:', proj);

const subTeams = db.prepare("SELECT * FROM sub_teams WHERE project_id = ?").all(proj.id);
console.log('\n子团队:');
subTeams.forEach(st => {
  console.log('  id=' + st.id, '|', st.name, '| 负责人:', st.leader);
  const ratings = db.prepare("SELECT * FROM sub_team_ratings WHERE sub_team_id = ? ORDER BY year DESC, month DESC").all(st.id);
  console.log('    评级:', JSON.stringify(ratings));
  const members = db.prepare("SELECT * FROM sub_team_members WHERE sub_team_id = ?").all(st.id);
  console.log('    成员数:', members.length);
  members.forEach(m => {
    const scores = db.prepare("SELECT * FROM member_monthly_scores WHERE sub_team_member_id = ?").all(m.id);
    console.log('    -', m.name, '| 月度得分:', JSON.stringify(scores.map(s => `${s.year}-${String(s.month).padStart(2,'0')}=${s.score}`)));
  });
});

db.close();
