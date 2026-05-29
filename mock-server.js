const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 8000;
const FRONTEND_DIR = path.join(__dirname, 'frontend/dist');

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

// Mock data with multiple goals to test "latest month with score" logic
const mockProjects = [
  {
    id: 1,
    name: "SWGT MTPF",
    owner: "张三",
    department: "研发部",
    target_date: "2026-12-31",
    status: "healthy",
    progress: 85.5,
    score: 90.0,
    achievement_rate: 90.0,
    goals: [
      {
        id: 1,
        name: "MTPF目标1（5月有评分90）",
        latest_score: 90,
        latest_year: 2026,
        latest_month: 5,
        latest_monthly_value: "100",
        latest_monthly_actual: "90",
        latest_monthly_rate: 90,
        yearly_target: "1000",
        latest_yearly_value: "450",
        latest_yearly_rate: 45
      },
      {
        id: 2,
        name: "MTPF目标2（3月有评分80）",
        latest_score: 80,
        latest_year: 2026,
        latest_month: 3,
        latest_monthly_value: "50",
        latest_monthly_actual: "40",
        latest_monthly_rate: 80,
        yearly_target: "500",
        latest_yearly_value: "200",
        latest_yearly_rate: 40
      },
      {
        id: 3,
        name: "MTPF目标3（无评分数据）",
        latest_score: null,
        latest_year: null,
        latest_month: null,
        latest_monthly_value: null,
        latest_monthly_actual: null,
        latest_monthly_rate: null,
        yearly_target: "200",
        latest_yearly_value: null,
        latest_yearly_rate: null
      }
    ],
    sub_teams: [
      {
        id: 1,
        name: "子团队A",
        leader: "李四",
        ratings: [
          { year: 2026, month: 5, rating: "达成" }
        ],
        members: [
          { id: 1, name: "王五", role: "开发" },
          { id: 2, name: "赵六", role: "测试" }
        ]
      },
      {
        id: 2,
        name: "子团队B",
        leader: "孙七",
        ratings: [],
        members: [
          { id: 3, name: "周八", role: "产品" }
        ]
      },
      {
        id: 3,
        name: "子团队C（无ratings字段测试）",
        leader: "吴九",
        members: []
      }
    ],
    milestones: [],
    reports: []
  }
];

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

  if (url === '/api/projects') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(mockProjects));
    return;
  }

  if (url.startsWith('/api/projects/')) {
    const parts = url.split('/');
    const id = parseInt(parts[3]);
    const project = mockProjects.find(p => p.id === id);
    if (project) {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(project));
    } else {
      res.writeHead(404);
      res.end(JSON.stringify({ error: 'Not found' }));
    }
    return;
  }

  if (url.startsWith('/api/member-performance')) {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      rows: [
        {
          member_id: 1,
          member_name: "王五",
          sub_team_id: 1,
          sub_team_name: "子团队A",
          scores: [
            { label: "2026-05", score: 4.5 }
          ]
        },
        {
          member_id: 2,
          member_name: "赵六",
          sub_team_id: 1,
          sub_team_name: "子团队A",
          scores: [
            { label: "2026-05", score: 4.0 }
          ]
        }
      ]
    }));
    return;
  }

  // Static files
  let filePath = path.join(FRONTEND_DIR, url === '/' ? 'index.html' : url);
  
  if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
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
  console.log(`Mock server running at http://localhost:${PORT}`);
  console.log(`Frontend served from: ${FRONTEND_DIR}`);
  console.log(`Mock projects: ${mockProjects.length}`);
  console.log(`Mock goals: ${mockProjects[0].goals.length}`);
});
