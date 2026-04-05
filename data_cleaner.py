"""
数据清洗与处理模块
"""
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import config
import jieba
from collections import Counter


class DataCleaner:
    """数据清洗类"""
    
    def __init__(self):
        # 数据库连接
        self.db_url = f"mysql+pymysql://{config.DATABASE_CONFIG['user']}:{config.DATABASE_CONFIG['password']}@{config.DATABASE_CONFIG['host']}:{config.DATABASE_CONFIG['port']}/{config.DATABASE_CONFIG['database']}?charset=utf8mb4"
        self.engine = create_engine(self.db_url)
    
    def load_data(self, sql="SELECT * FROM job_positions"):
        """从数据库加载数据"""
        df = pd.read_sql(sql, self.engine)
        print(f"加载数据：{len(df)}条")
        return df
    
    def clean_salary(self, df):
        """清洗薪资数据"""
        # 填充缺失值
        df['min_salary'] = df['min_salary'].fillna(df['min_salary'].median())
        df['max_salary'] = df['max_salary'].fillna(df['max_salary'].median())
        
        # 计算平均薪资
        df['avg_salary'] = (df['min_salary'] + df['max_salary']) / 2
        
        # 去除异常值（超过 3 个标准差）
        mean_sal = df['avg_salary'].mean()
        std_sal = df['avg_salary'].std()
        df = df[(df['avg_salary'] > mean_sal - 3*std_sal) & 
                (df['avg_salary'] < mean_sal + 3*std_sal)]
        
        return df
    
    def clean_city(self, df):
        """清洗城市数据"""
        # 统一城市名称
        df['city'] = df['city'].map(config.CLEAN_CITY_MAPPING).fillna(df['city'])
        return df
    
    def clean_education(self, df):
        """清洗学历数据"""
        # 统一学历名称
        df['education'] = df['education'].map(config.CLEAN_EDUCATION_MAPPING).fillna('不限')
        return df
    
    def clean_experience(self, df):
        """清洗经验要求"""
        # 统一经验要求
        df['experience'] = df['experience'].map(config.CLEAN_EXPERIENCE_MAPPING).fillna('不限')
        return df
    
    def extract_skills(self, description):
        """从职位描述中提取技能关键词"""
        if pd.isna(description):
            return []
        
        # 分词
        words = jieba.lcut(str(description))
        
        # 筛选技能相关词汇
        skills = [w for w in words if w not in config.STOP_WORDS and len(w) > 1]
        
        return skills
    
    def run_cleaning(self):
        """执行完整清洗流程"""
        print("开始数据清洗...")
        
        # 加载数据
        df = self.load_data()
        
        # 清洗各字段
        df = self.clean_salary(df)
        df = self.clean_city(df)
        df = self.clean_education(df)
        df = self.clean_experience(df)
        
        # 保存清洗后的数据
        df.to_sql('job_positions_clean', con=self.engine, if_exists='replace', index=False)
        print(f"清洗完成，保存{len(df)}条数据")
        
        return df


class DataAnalyzer:
    """数据分析类"""
    
    def __init__(self, df):
        self.df = df
    
    def get_city_distribution(self, top_n=20):
        """获取城市分布"""
        city_counts = self.df['city'].value_counts().head(top_n)
        return city_counts
    
    def get_salary_stats(self):
        """获取薪资统计"""
        return {
            'mean': self.df['avg_salary'].mean(),
            'median': self.df['avg_salary'].median(),
            'min': self.df['avg_salary'].min(),
            'max': self.df['avg_salary'].max(),
            'std': self.df['avg_salary'].std()
        }
    
    def get_education_distribution(self):
        """获取学历分布"""
        return self.df['education'].value_counts()
    
    def get_experience_distribution(self):
        """获取经验要求分布"""
        return self.df['experience'].value_counts()
    
    def get_skill_cloud(self, top_n=100):
        """获取技能词云数据"""
        all_skills = []
        for desc in self.df['description']:
            skills = jieba.lcut(str(desc))
            all_skills.extend(skills)
        
        # 过滤停用词
        skills_filtered = [s for s in all_skills if s not in config.STOP_WORDS and len(s) > 1]
        
        # 统计词频
        skill_counts = Counter(skills_filtered)
        return skill_counts.most_common(top_n)


def main():
    """主函数"""
    # 清洗数据
    cleaner = DataCleaner()
    df = cleaner.run_cleaning()
    
    # 分析数据
    analyzer = DataAnalyzer(df)
    
    print("\n=== 城市分布 TOP10 ===")
    print(analyzer.get_city_distribution(10))
    
    print("\n=== 薪资统计 ===")
    stats = analyzer.get_salary_stats()
    for k, v in stats.items():
        print(f"{k}: {v:.2f}")
    
    print("\n=== 学历分布 ===")
    print(analyzer.get_education_distribution())
    
    print("\n=== 经验要求分布 ===")
    print(analyzer.get_experience_distribution())


if __name__ == '__main__':
    main()
