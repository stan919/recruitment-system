import os
import re

templates = [
    'job_search.html', 'job_detail.html', 'insights.html', 
    'applications.html', 'user_chat.html', 'profile.html'
]

replacements = {
    # 替换页面主容器为深色变体
    r'class="job-detail-card"': 'class="job-detail-card bg-slate border-dim"',
    r'class="filters-card"': 'class="filters-card bg-slate border-dim"',
    r'class="job-card"': 'class="job-card bg-slate border-dim hover-card"',
    r'class="chart-card"': 'class="chart-card bg-slate border-dim radius-16"',
    r'class="app-item"': 'class="app-item bg-slate border-dim radius-12"',
    r'class="profile-card"': 'class="profile-card bg-slate border-dim radius-16"',
    r'class="section-block"': 'class="section-block bg-slate border-dim radius-16"',
    
    # 标题及文字高亮
    r'<h1([^>]*)>': r'<h1\1 class="text-primary">',
    r'<h2([^>]*)>': r'<h2\1 class="text-primary">',
    r'<h3([^>]*)>': r'<h3\1 class="text-primary">',
    
    # 投递和主按钮
    r'class="apply-btn"': 'class="apply-btn bronze-gradient"',
    r'class="main-search-btn"': 'class="main-search-btn bronze-gradient"',
}

for t in templates:
    path = os.path.join('templates', t)
    if not os.path.exists(path): continue
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for old, new in replacements.items():
        content = re.sub(old, new, content)
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
        
print("V2 Design System attributes injected into templates.")
