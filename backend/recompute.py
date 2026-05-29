import sys
sys.path.insert(0, 'D:/workspace/workspace_monitor-master/backend')

from app.database import SessionLocal
from app.main import recompute_project_score

db = SessionLocal()
try:
    recompute_project_score(db, 1)
    print("Recomputed project 1 score")
    
    # 验证结果
    from app.models import Project
    project = db.query(Project).filter(Project.id == 1).first()
    print(f"Project score: {project.score}, status: {project.status}")
finally:
    db.close()
