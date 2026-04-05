"""
生成模拟招聘数据 - 30000 条
"""
import pandas as pd
import random
from datetime import datetime, timedelta
import csv


def generate_jobs(count=30000):
    """生成模拟职位数据"""
    
    # 职位类型（按专业分类）
    job_categories = {
        '计算机': [
            '软件工程师', '前端开发工程师', '后端开发工程师', '全栈工程师',
            'Java 开发工程师', 'Python 开发工程师', 'C++开发工程师',
            'Go 开发工程师', 'PHP 开发工程师', '.NET 开发工程师'
        ],
        '软件': [
            '软件开发工程师', '软件架构师', '软件测试工程师',
            '软件实施工程师', '软件技术支持', '需求分析师'
        ],
        '人工智能': [
            '算法工程师', '机器学习工程师', '深度学习工程师',
            'NLP 算法工程师', '计算机视觉工程师', 'AI 应用工程师',
            '数据科学家', '大数据工程师'
        ],
        '电子': [
            '硬件工程师', '嵌入式软件工程师', 'FPGA 工程师',
            '电路设计工程师', 'PCB 工程师', '单片机工程师',
            '电子工程师', '射频工程师'
        ],
        '工商管理': [
            '管理培训生', '业务分析师', '项目管理专员',
            '运营专员', '人力资源专员', '行政专员',
            '总经理助理', '管培生'
        ],
        '金融': [
            '金融分析师', '投资顾问', '风险管理专员',
            '量化分析师', '财务分析师', '审计专员',
            '银行柜员', '证券分析师'
        ],
        '设计': [
            'UI 设计师', 'UX 设计师', '平面设计师',
            '交互设计师', '视觉设计师', '产品设计师',
            '网页设计师', '多媒体设计师'
        ],
        '市场': [
            '市场营销专员', '品牌推广专员', '新媒体运营',
            '内容运营', '用户运营', '市场策划',
            '数字营销专员', 'SEO 专员'
        ]
    }
    
    # 公司前缀和后缀
    company_prefixes = [
        '华为', '腾讯', '阿里巴巴', '百度', '字节跳动', '美团',
        '京东', '网易', '小米', 'OPPO', 'VIVO', '滴滴',
        '拼多多', '快手', '哔哩哔哩', '小红书', '知乎',
        '携程', '去哪儿', '58 同城', '新浪', '搜狐', '360'
    ]
    
    company_suffixes = [
        '科技有限公司', '网络技术有限公司', '信息技术有限公司',
        '数据服务有限公司', '智能科技有限公司', '系统有限公司',
        '软件有限公司', '科技股份有限公司'
    ]
    
    # 城市及薪资水平
    city_salary = {
        '北京': (12, 45), '上海': (12, 42), '广州': (9, 35),
        '深圳': (13, 48), '杭州': (11, 40), '成都': (8, 30),
        '南京': (9, 32), '武汉': (8, 28), '西安': (7, 26),
        '苏州': (9, 33), '天津': (8, 30), '重庆': (7, 28)
    }
    
    # 学历要求
    educations = ['大专', '本科', '硕士', '博士']
    education_weights = [0.15, 0.65, 0.18, 0.02]
    
    # 经验要求
    experiences = [
        '应届生', '无经验', '1 年以下', '1-3 年',
        '3-5 年', '5-10 年', '经验不限'
    ]
    experience_weights = [0.25, 0.15, 0.10, 0.25, 0.15, 0.05, 0.05]
    
    # 技能关键词（按专业）
    skill_keywords_map = {
        '计算机': [
            'Java', 'Python', 'C++', 'JavaScript', 'HTML', 'CSS',
            'MySQL', 'Linux', 'Git', '数据结构', '算法', '计算机网络',
            '操作系统', '数据库', 'Spring', 'Vue', 'React', 'Docker'
        ],
        '软件': [
            '软件工程', '敏捷开发', 'Scrum', '测试用例', '需求分析',
            '系统设计', '代码审查', '版本控制', 'CI/CD', 'DevOps'
        ],
        '人工智能': [
            '机器学习', '深度学习', 'TensorFlow', 'PyTorch',
            'NLP', '计算机视觉', '数据挖掘', '统计分析',
            '神经网络', 'CNN', 'RNN', 'Transformer'
        ],
        '电子': [
            '电路设计', '嵌入式系统', 'FPGA', 'ARM', '单片机',
            'PCB 设计', 'Altium Designer', 'Cadence', 'Verilog',
            '模拟电路', '数字电路', '信号处理'
        ],
        '工商管理': [
            '项目管理', '团队协作', '沟通协调', '数据分析',
            '商业分析', '市场调研', 'PPT', 'Excel', '思维导图'
        ],
        '金融': [
            '金融分析', '财务报表', '风险评估', '投资分析',
            '量化交易', 'Wind', 'Bloomberg', 'CFA', 'FRM'
        ],
        '设计': [
            'Photoshop', 'Illustrator', 'Sketch', 'Figma',
            'UI 设计', '交互设计', '原型设计', 'Axure',
            '平面设计', '色彩搭配', '排版设计'
        ],
        '市场': [
            '市场营销', '品牌推广', '新媒体运营', '内容创作',
            '活动策划', '社交媒体', 'Google Analytics',
            'SEO', 'SEM', '信息流广告'
        ]
    }
    
    # 行业
    industries = [
        '互联网/电子商务', '计算机软件', '计算机硬件',
        '人工智能/大数据', '电子技术/半导体', '通信/电信',
        '金融/银行', '专业服务/咨询', '贸易/零售',
        '教育/培训', '医疗/健康', '文化/传媒'
    ]
    
    # 公司规模
    company_sizes = [
        '少于 20 人', '20-99 人', '100-499 人',
        '500-999 人', '1000-4999 人', '5000 人以上'
    ]
    size_weights = [0.10, 0.20, 0.30, 0.20, 0.15, 0.05]
    
    jobs_data = []
    
    for i in range(count):
        # 随机选择专业方向
        profession = random.choice(list(job_categories.keys()))
        
        # 随机选择职位
        job_name = random.choice(job_categories[profession])
        
        # 随机生成公司
        company = f'{random.choice(company_prefixes)}{random.choice(company_suffixes)}'
        
        # 随机选择城市
        city = random.choice(list(city_salary.keys()))
        salary_range = city_salary[city]
        
        # 生成薪资（单位：元/月）
        min_salary = random.randint(salary_range[0], salary_range[1]) * 1000
        max_salary = min_salary + random.randint(5000, 20000)
        
        # 确保最大薪资不超过合理范围
        if max_salary > 80000:
            max_salary = random.randint(50000, 80000)
        
        # 学历和经验
        education = random.choices(educations, weights=education_weights)[0]
        experience = random.choices(experiences, weights=experience_weights)[0]
        
        # 如果是应届生岗位，调整经验要求
        if '应届' in job_name or '管培生' in job_name or '实习生' in job_name:
            experience = '应届生'
        
        # 技能标签（随机选择 3-8 个）
        skills = random.sample(skill_keywords_map[profession], k=random.randint(3, 8))
        skill_tags = ','.join(skills)
        
        # 职位描述模板
        descriptions = [
            f'负责{job_name}相关工作，参与产品设计与开发',
            f'主导{job_name}项目，解决技术难题，推动团队技术进步',
            f'参与需求分析、系统设计、编码实现和单元测试',
            f'负责核心模块的开发和优化，提升系统性能和稳定性',
            f'与产品、测试团队合作，确保项目高质量交付',
            f'跟踪前沿技术，持续优化现有技术架构'
        ]
        
        description = random.choice(descriptions)
        
        # 生成发布日期（最近 3 个月内）
        days_ago = random.randint(0, 90)
        publish_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        
        # 是否校招岗位
        is_campus = (experience == '应届生' or 
                    any(kw in job_name for kw in ['应届', '实习', '管培生']) or
                    random.random() < 0.3)  # 30% 概率是校招
        
        job = {
            'job_name': job_name,
            'company_name': company,
            'salary': f'{min_salary//1000}-{max_salary//1000}K',
            'city': city,
            'district': random.choice(['朝阳区', '海淀区', '浦东新区', '天河区', '南山区', '高新区', '']),
            'experience': experience,
            'education': education,
            'skill_tags': skill_tags,
            'description': description,
            'industry': random.choice(industries),
            'company_size': random.choices(company_sizes, weights=size_weights)[0],
            'source': 'generated',
            'is_campus': is_campus,
            'publish_date': publish_date,
            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'min_salary': min_salary,
            'max_salary': max_salary
        }
        
        jobs_data.append(job)
    
    return jobs_data


def save_to_csv(data, filename='jobs_data_30k.csv'):
    """保存数据到 CSV"""
    if not data:
        print("没有数据可保存")
        return
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"✓ 数据已保存到 {filename}")
    print(f"✓ 共{len(data)}条数据")
    
    # 显示前几行
    print(f"\n前 5 条数据预览:")
    print(df[['job_name', 'company_name', 'city', 'min_salary', 'max_salary']].head())


if __name__ == '__main__':
    print("="*60)
    print("开始生成模拟招聘数据")
    print("="*60)
    
    jobs = generate_jobs(count=30000)
    save_to_csv(jobs, 'jobs_data_30k.csv')
    
    print("\n" + "="*60)
    print("数据生成完成！")
    print("="*60)
