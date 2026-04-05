"""
数据导入脚本 - 将 CSV 数据导入 MySQL
"""
import pandas as pd
from sqlalchemy import create_engine
import config
from models_job import JobPosition
from sqlalchemy.orm import sessionmaker
from datetime import datetime


def import_jobs_data(csv_file='jobs_data_30k.csv'):
    """将 CSV 数据导入 MySQL"""
    print(f"开始导入数据：{csv_file}")
    
    # 读取 CSV
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    print(f"读取到 {len(df)} 条数据")
    
    # 数据库连接
    db_url = f"mysql+pymysql://{config.DATABASE_CONFIG['user']}:{config.DATABASE_CONFIG['password']}@{config.DATABASE_CONFIG['host']}:{config.DATABASE_CONFIG['port']}/{config.DATABASE_CONFIG['database']}?charset=utf8mb4"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 批量插入数据
        for index, row in df.iterrows():
            job = JobPosition(
                job_name=str(row.get('job_name', '')),
                company_name=str(row.get('company_name', '')),
                min_salary=int(row.get('min_salary', 0)),
                max_salary=int(row.get('max_salary', 0)),
                salary_text=str(row.get('salary', '')),
                city=str(row.get('city', '')),
                district=str(row.get('district', '')) if pd.notna(row.get('district')) else '',
                experience=str(row.get('experience', '')),
                education=str(row.get('education', '')),
                skill_tags=str(row.get('skill_tags', '')),
                description=str(row.get('description', '')),
                industry=str(row.get('industry', '')),
                company_size=str(row.get('company_size', '')),
                source=str(row.get('source', 'generated')),
                is_campus=1 if row.get('is_campus', False) else 0,
                publish_date=str(row.get('publish_date', '')),
                crawl_time=datetime.now()
            )
            session.add(job)
            
            # 每 1000 条提交一次
            if (index + 1) % 1000 == 0:
                session.commit()
                print(f"已导入 {index + 1} 条...")
        
        # 提交剩余数据
        session.commit()
        print(f"✓ 数据导入成功！共{len(df)}条")
        
    except Exception as e:
        session.rollback()
        print(f"✗ 数据导入失败：{e}")
    finally:
        session.close()
        engine.dispose()


if __name__ == '__main__':
    import_jobs_data()
