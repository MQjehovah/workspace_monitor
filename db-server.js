const http = require('http');
const fs = require('fs');
const path = require('path');
const Database = require('better-sqlite3');

const PORT = 8000;
const FRONTEND_DIR = path.join(__dirname, 'frontend/dist');
const DB_PATH = path.join(__dirname, 'backend/data/bigscreen.db');

const db = new Database(DB_PATH, { readonly: true });

const mimeTypes = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

function sendJSON(res, data) {
  res.setHeader('Content-Type', 'application/json');
  res.writeHead(200);
  res.end(JSON.stringify(data));
}

function sendError(res, status, msg) {
  res.setHeader('Content-Type', 'application/json');
  res.writeHead(status);
  res.end(JSON.stringify({ detail: msg }));
}

// ===== Database helpers =====
function getProjects() {
  return db.prepare('SELECT * FROM projects WHERE special = 0').all();
}

function getSpecialProjects() {
  return db.prepare('SELECT * FROM projects WHERE special = 1').all();
}

function getProjectById(id) {
  return db.prepare('SELECT * FROM projects WHERE id = ?').get(id);
}

function getGoalsByProjectId(projectId) {
  return db.prepare('SELECT * FROM goals WHERE project_id = ?').all(projectId);
}

function getScoresByGoalId(goalId) {
  return db.prepare('SELECT * FROM goal_scores WHERE goal_id = ? ORDER BY year DESC, month DESC').all(goalId);
}

function getMilestonesByProjectId(projectId) {
  return db.prepare('SELECT * FROM milestones WHERE project_id = ? ORDER BY due_date').all(projectId);
}

function getReportsByProjectId(projectId) {
  return db.prepare('SELECT * FROM monthly_reports WHERE project_id = ? ORDER BY year DESC, month DESC').all(projectId);
}

function getSubTeamsByProjectId(projectId) {
  return db.prepare('SELECT * FROM sub_teams WHERE project_id = ?').all(projectId);
}

function getMembersBySubTeamId(subTeamId) {
  return db.prepare('SELECT * FROM sub_team_members WHERE sub_team_id = ?').all(subTeamId);
}

function getRatingsBySubTeamId(subTeamId) {
  return db.prepare('SELECT * FROM sub_team_ratings WHERE sub_team_id = ? ORDER BY year DESC, month DESC').all(subTeamId);
}

function getMemberScores(memberId) {
  return db.prepare('SELECT * FROM member_monthly_scores WHERE sub_team_member_id = ? ORDER BY year DESC, month DESC').all(memberId);
}

function buildGoalWithLatest(goal) {
  const scores = db.prepare('SELECT * FROM goal_scores WHERE goal_id = ? ORDER BY year DESC, month DESC').all(goal.id);
  const validScores = scores.filter(s => s.score !== null && s.score > 0);

  let latestScore = null;
  let latestYear = null;
  let latestMonth = null;
  let latestComment = null;
  let latestMonthlyValue = null;
  let latestMonthlyActual = null;
  let latestMonthlyRate = null;
  let latestYearlyValue = null;
  let latestYearlyRate = null;

  if (validScores.length > 0) {
    const s = validScores[0];
    latestScore = s.score;
    latestYear = s.year;
    latestMonth = s.month;
    latestComment = s.comment;
    latestMonthlyValue = s.monthly_value;
    latestMonthlyActual = s.actual_value;
    latestMonthlyRate = s.monthly_rate;
  } else if (scores.length > 0) {
    const s = scores[0];
    latestScore = s.score;
    latestYear = s.year;
    latestMonth = s.month;
    latestComment = s.comment;
    latestMonthlyValue = s.monthly_value;
    latestMonthlyActual = s.actual_value;
    latestMonthlyRate = s.monthly_rate;
  }

  // Find yearly data
  const yearlyRecord = validScores.find(s => s.yearly_value !== null || s.yearly_rate !== null)
    || scores.find(s => s.yearly_value !== null || s.yearly_rate !== null);
  if (yearlyRecord) {
    latestYearlyValue = yearlyRecord.yearly_value;
    latestYearlyRate = yearlyRecord.yearly_rate;
  }

  return {
    id: goal.id,
    name: goal.name,
    description: goal.description,
    latest_score: latestScore,
    latest_year: latestYear,
    latest_month: latestMonth,
    latest_comment: latestComment,
    monthly_target: goal.monthly_target,
    yearly_target: goal.yearly_target,
    unit: goal.unit || '',
    latest_monthly_value: latestMonthlyValue,
    latest_monthly_actual: latestMonthlyActual,
    latest_monthly_rate: latestMonthlyRate,
    latest_yearly_value: latestYearlyValue,
    latest_yearly_rate: latestYearlyRate,
  };
}

function buildProjectWithGoals(project) {
  const goals = getGoalsByProjectId(project.id);
  const goalsData = goals.map(g => buildGoalWithLatest(g));
  const milestones = getMilestonesByProjectId(project.id);
  const reports = getReportsByProjectId(project.id);
  const subTeams = getSubTeamsByProjectId(project.id);
  const subTeamsData = subTeams.map(st => {
    const members = getMembersBySubTeamId(st.id);
    const ratings = getRatingsBySubTeamId(st.id);
    return {
      id: st.id,
      project_id: st.project_id,
      name: st.name,
      leader: st.leader,
      members: members.map(m => ({ id: m.id, sub_team_id: m.sub_team_id, name: m.name, role: m.role })),
      ratings: ratings.map(r => ({ id: r.id, sub_team_id: r.sub_team_id, year: r.year, month: r.month, rating: r.rating, comment: r.comment })),
    };
  });

  return {
    id: project.id,
    name: project.name,
    owner: project.owner,
    department: project.department,
    progress: project.progress,
    achievement_rate: project.achievement_rate,
    score: project.score,
    status: project.status,
    target_date: project.target_date,
    goals: goalsData,
    milestones: milestones.map(m => ({
      id: m.id, project_id: m.project_id,
      group_name: m.group_name, due_date: m.due_date,
      event: m.event, achieved: m.achieved, note: m.note,
    })),
    reports: reports.map(r => ({
      id: r.id, project_id: r.project_id,
      year: r.year, month: r.month, content: r.content,
      pdf_path: r.pdf_path,
    })),
    sub_teams: subTeamsData,
  };
}

const server = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  const url = req.url;
  console.log(`${req.method} ${url}`);

  // ===== API Routes =====
  if (url === '/api/projects') {
    const projects = getProjects();
    sendJSON(res, projects);
    return;
  }

  if (url === '/api/special-projects') {
    const projects = getSpecialProjects();
    sendJSON(res, projects);
    return;
  }

  if (url.startsWith('/api/projects/') && !url.includes('/goals') && !url.includes('/milestones') && !url.includes('/reports') && !url.includes('/subteams')) {
    const parts = url.split('/');
    const id = parseInt(parts[3]);
    const project = getProjectById(id);
    if (project) {
      sendJSON(res, buildProjectWithGoals(project));
    } else {
      sendError(res, 404, 'Project not found');
    }
    return;
  }

  if (url === '/api/stats') {
    const projects = getProjects();
    if (!projects.length) {
      sendJSON(res, { total_projects: 0, avg_progress: 0, avg_achievement: 0, avg_score: 0, risk_count: 0, achieved_teams: 0, total_teams: 0 });
      return;
    }
    const riskCount = projects.filter(p => p.status === 'risk').length;
    const allRatings = db.prepare('SELECT * FROM sub_team_ratings').all();
    const totalTeams = db.prepare('SELECT COUNT(*) as c FROM sub_teams').get().c;
    let achievedTeams = 0;
    if (allRatings.length > 0) {
      const latest = allRatings.reduce((a, b) => (a.year > b.year || (a.year === b.year && a.month > b.month)) ? a : b);
      achievedTeams = allRatings.filter(r => r.year === latest.year && r.month === latest.month && r.rating === '达成').length;
    }
    sendJSON(res, {
      total_projects: projects.length,
      avg_progress: +(projects.reduce((s, p) => s + p.progress, 0) / projects.length).toFixed(1),
      avg_achievement: +(projects.reduce((s, p) => s + p.achievement_rate, 0) / projects.length).toFixed(1),
      avg_score: +(projects.reduce((s, p) => s + p.score, 0) / projects.length).toFixed(1),
      risk_count: riskCount,
      achieved_teams: achievedTeams,
      total_teams: totalTeams,
    });
    return;
  }

  if (url.match(/^\/api\/projects\/\d+\/goals$/)) {
    const id = parseInt(url.split('/')[3]);
    const goals = getGoalsByProjectId(id);
    sendJSON(res, goals);
    return;
  }

  if (url.match(/^\/api\/projects\/\d+\/milestones$/)) {
    const id = parseInt(url.split('/')[3]);
    const milestones = getMilestonesByProjectId(id);
    sendJSON(res, milestones);
    return;
  }

  if (url.match(/^\/api\/projects\/\d+\/reports$/)) {
    const id = parseInt(url.split('/')[3]);
    const reports = getReportsByProjectId(id);
    sendJSON(res, reports);
    return;
  }

  if (url.match(/^\/api\/projects\/\d+\/subteams$/)) {
    const id = parseInt(url.split('/')[3]);
    const subTeams = getSubTeamsByProjectId(id);
    const result = subTeams.map(st => {
      const members = getMembersBySubTeamId(st.id);
      const ratings = getRatingsBySubTeamId(st.id);
      return {
        id: st.id, project_id: st.project_id, name: st.name, leader: st.leader,
        members: members.map(m => ({ id: m.id, sub_team_id: m.sub_team_id, name: m.name, role: m.role })),
        ratings: ratings.map(r => ({ id: r.id, sub_team_id: r.sub_team_id, year: r.year, month: r.month, rating: r.rating, comment: r.comment })),
      };
    });
    sendJSON(res, result);
    return;
  }

  if (url.match(/^\/api\/goals\/\d+\/scores$/)) {
    const id = parseInt(url.split('/')[3]);
    const scores = getScoresByGoalId(id);
    sendJSON(res, scores);
    return;
  }

  if (url === '/api/member-performance' || url.startsWith('/api/member-performance?')) {
    const members = db.prepare(`
      SELECT stm.* FROM sub_team_members stm
      JOIN sub_teams st ON stm.sub_team_id = st.id
      JOIN projects p ON st.project_id = p.id
      WHERE p.special = 0
    `).all();
    const monthsList = [];
    for (let m = 4; m <= 12; m++) monthsList.push({ year: 2026, month: m, label: `2026-${String(m).padStart(2, '0')}` });

    // 收集所有子团队的最新评级（year, month）— 仅供详情页用，前端绩效页不再使用
    const subTeams = db.prepare('SELECT * FROM sub_teams').all();
    const teamLatestRating = {};
    subTeams.forEach(st => {
      const r = db.prepare('SELECT * FROM sub_team_ratings WHERE sub_team_id = ? ORDER BY year DESC, month DESC LIMIT 1').get(st.id);
      if (r) {
        teamLatestRating[st.id] = { year: r.year, month: r.month };
      }
    });

    const rows = members.map(member => {
      const subTeam = db.prepare('SELECT * FROM sub_teams WHERE id = ?').get(member.sub_team_id);
      let projectName = '';
      let subTeamName = '';
      let latestRatingMonth = null;
      if (subTeam) {
        subTeamName = subTeam.name;
        const project = db.prepare('SELECT * FROM projects WHERE id = ?').get(subTeam.project_id);
        if (project) projectName = project.name;
        const lr = teamLatestRating[subTeam.id];
        if (lr) latestRatingMonth = { year: lr.year, month: lr.month };
      }
      const scoreRecords = getMemberScores(member.id);
      const scoresDict = {};
      scoreRecords.forEach(sr => { scoresDict[`${sr.year}-${String(sr.month).padStart(2, '0')}`] = { score: sr.score, id: sr.id, comment: sr.comment }; });

      // 展示所有月份的得分（不再过滤）
      const rowScores = monthsList.map(ml => {
        const key = `${ml.year}-${String(ml.month).padStart(2, '0')}`;
        if (scoresDict[key]) {
          return { year: ml.year, month: ml.month, label: ml.label, score: scoresDict[key].score, id: scoresDict[key].id, comment: scoresDict[key].comment };
        }
        return { year: ml.year, month: ml.month, label: ml.label, score: null, id: null, comment: '' };
      });

      return {
        member_id: member.id,
        member_name: member.name,
        role: member.role || '',
        project_id: subTeam ? subTeam.project_id : 0,
        project_name: projectName,
        sub_team_name: subTeamName,
        specialty_name: subTeam ? (subTeam.specialty_name || '') : '',
        latest_rating_month: latestRatingMonth,
        scores: rowScores,
      };
    });

    rows.sort((a, b) => (a.project_id - b.project_id) || a.sub_team_name.localeCompare(b.sub_team_name));

    sendJSON(res, { months: monthsList, rows, total: rows.length });
    return;
  }

  if (url === '/api/score-rules') {
    sendJSON(res, {
      score_levels: [
        { score: 1, label: '1分（差）', range: '<40', color: '#e74c3c', desc: '远未达成目标，存在明显短板' },
        { score: 2, label: '2分（合格）', range: '40-55', color: '#e67e22', desc: '基本完成工作，但距离目标有较大差距' },
        { score: 3, label: '3分（良）', range: '55-70', color: '#f39c12', desc: '较好完成工作，大部分目标达成' },
        { score: 4, label: '4分（优秀）', range: '70-85', color: '#27ae60', desc: '出色完成工作，超额达成部分目标' },
        { score: 5, label: '5分（卓越）', range: '≥85', color: '#2980b9', desc: '卓越表现，全面超额完成目标，可作为标杆' },
      ],
      team_distribution: {
        excellent: { condition: '团队得分 >80分', ratio: [0, 10, 30, 40, 20] },
        good: { condition: '团队得分 60-80分', ratio: [10, 20, 30, 30, 10] },
        fair: { condition: '团队得分 <60分', ratio: [20, 30, 30, 20, 0] },
      },
      leader_rule: {
        title: '专项负责人赋分规则',
        rules: [
          '1. 专项负责人/子团队负责人不参与上述比例强制分配',
          '2. 负责人得分由上级根据专项整体达成情况+个人贡献度综合评定（1-5分）',
          '3. 负责人得分可高于团队成员最高分，以体现管理责任与贡献',
          '4. 当专项整体未达成目标（<60分）时，负责人得分原则上不超过3分',
          '5. 当专项超额达成目标（≥85分）时，负责人可直接评为5分（卓越）',
          '6. 负责人得分需在成员评分完成后，由部门负责人或PMO确认后生效',
        ],
      },
    });
    return;
  }

  if (url === '/api/goal-dashboard' || url.startsWith('/api/goal-dashboard?')) {
    const goals = db.prepare(`
      SELECT g.* FROM goals g
      JOIN projects p ON g.project_id = p.id
      WHERE p.special = 0
    `).all();
    const projectsMap = {};
    db.prepare('SELECT * FROM projects WHERE special = 0').all().forEach(p => projectsMap[p.id] = p.name);
    const displayMonths = [4, 5, 6, 7, 8, 9, 10, 11, 12];
    const year = 2026;

    const rows = goals.map(g => {
      const scoresList = db.prepare('SELECT * FROM goal_scores WHERE goal_id = ? AND year = ? ORDER BY month').all(g.id, year);
      const scoreMap = {};
      scoresList.forEach(s => { scoreMap[s.month] = s; });

      const monthsData = displayMonths.map(m => {
        const sc = scoreMap[m];
        return {
          month: m,
          monthly_target: sc ? sc.monthly_value : null,
          actual_value: sc ? sc.actual_value : null,
          completion_rate: sc ? sc.monthly_rate : null,
          comment: sc ? sc.comment : null,
        };
      });

      let latestSc = null;
      for (let i = displayMonths.length - 1; i >= 0; i--) {
        if (scoreMap[displayMonths[i]]) { latestSc = scoreMap[displayMonths[i]]; break; }
      }

      return {
        id: g.id,
        project_id: g.project_id,
        project_name: projectsMap[g.project_id] || '',
        goal_name: g.name,
        description: g.description,
        unit: g.unit || '',
        yearly_target: g.yearly_target,
        yearly_value: latestSc ? latestSc.yearly_value : null,
        yearly_rate: latestSc ? latestSc.yearly_rate : null,
        months: monthsData,
      };
    });

    sendJSON(res, { months: displayMonths, rows });
    return;
  }

  if (url === '/api/goal-management' || url.startsWith('/api/goal-management?')) {
    const goals = db.prepare(`
      SELECT g.* FROM goals g
      JOIN projects p ON g.project_id = p.id
      WHERE p.special = 0
    `).all();
    const projectGoals = {};
    goals.forEach(g => {
      if (!projectGoals[g.project_id]) projectGoals[g.project_id] = [];
      projectGoals[g.project_id].push(buildGoalWithLatest(g));
    });

    const projectsList = [];
    for (const pid of Object.keys(projectGoals)) {
      const project = getProjectById(parseInt(pid));
      projectsList.push({
        project_id: parseInt(pid),
        project_name: project ? project.name : '',
        goals: projectGoals[pid],
      });
    }
    sendJSON(res, { projects: projectsList });
    return;
  }

  if (url === '/api/seed') {
    sendJSON(res, { message: 'Data already seeded (using real database)' });
    return;
  }

  if (url === '/health') {
    sendJSON(res, { status: 'healthy' });
    return;
  }

  // ===== Static files =====
  // 支持 base=/project 路径
  let cleanUrl = url;
  if (cleanUrl.startsWith('/project')) {
    cleanUrl = cleanUrl.substring('/project'.length) || '/';
  }
  // 去除 query string
  const queryIdx = cleanUrl.indexOf('?');
  if (queryIdx >= 0) cleanUrl = cleanUrl.substring(0, queryIdx);

  // SPA fallback: 非 /api/ 开头的 GET 请求，如果文件不存在就返回 index.html
  const isAsset = /\.[a-zA-Z0-9]+$/.test(cleanUrl);
  let filePath = path.join(FRONTEND_DIR, cleanUrl === '/' ? 'index.html' : cleanUrl);

  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
    if (isAsset) {
      res.writeHead(404);
      res.end('Not found');
      return;
    }
    filePath = path.join(FRONTEND_DIR, 'index.html');
  }

  const ext = path.extname(filePath).toLowerCase();
  const contentType = mimeTypes[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        res.writeHead(404);
        res.end('Not found');
      } else {
        res.writeHead(500);
        res.end('Server error');
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content);
    }
  });
});

server.listen(PORT, () => {
  console.log(`DB Server running at http://localhost:${PORT}`);
  console.log(`Frontend served from: ${FRONTEND_DIR}`);
  console.log(`Database: ${DB_PATH}`);
});
