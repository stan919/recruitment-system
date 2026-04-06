"""
数据可视化模块 - 生成 6 个核心图表
"""
from pyecharts import options as opts
from pyecharts.charts import Map, Bar, Pie, WordCloud
from pyecharts.globals import ThemeType
import os


class JobVisualizer:
    """职位数据可视化"""
    
    def __init__(self, analyzer, output_dir='static/charts'):
        self.analyzer = analyzer
        self.output_dir = output_dir
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    def create_city_map(self):
        """1. 全国岗位分布地图（改为柱状图）"""
        print("生成图表：全国岗位分布柱状图")
        
        city_data = self.analyzer.get_city_distribution(20)
        
        # 城市到省份的映射（完整版）
        city_to_province = {
            '北京': '北京',
            '上海': '上海',
            '天津': '天津',
            '重庆': '重庆',
            '广州': '广东',
            '深圳': '广东',
            '佛山': '广东',
            '东莞': '广东',
            '成都': '四川',
            '绵阳': '四川',
            '南京': '江苏',
            '苏州': '江苏',
            '无锡': '江苏',
            '杭州': '浙江',
            '宁波': '浙江',
            '武汉': '湖北',
            '西安': '陕西',
            '长沙': '湖南',
            '郑州': '河南',
            '济南': '山东',
            '青岛': '山东',
            '合肥': '安徽',
            '福州': '福建',
            '厦门': '福建',
            '南昌': '江西',
            '昆明': '云南',
            '贵阳': '贵州',
            '南宁': '广西',
            '海口': '海南',
            '沈阳': '辽宁',
            '大连': '辽宁',
            '长春': '吉林',
            '哈尔滨': '黑龙江',
            '石家庄': '河北',
            '太原': '山西',
            '呼和浩特': '内蒙古',
            '兰州': '甘肃',
            '西宁': '青海',
            '银川': '宁夏',
            '乌鲁木齐': '新疆',
            '拉萨': '西藏',
        }
        
        # 转换为省份数据并聚合
        province_data = {}
        for city, count in zip(city_data.index, city_data.values):
            province = city_to_province.get(str(city), str(city))
            if province and len(province) > 0:
                province_data[province] = province_data.get(province, 0) + int(count)
        
        # 按数量排序
        sorted_provinces = sorted(province_data.items(), key=lambda x: x[1], reverse=True)
        
        print(f"省份数据：{province_data}")
        
        # 柱状图
        bar_chart = (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="500px"))
            .add_xaxis([p[0] for p in sorted_provinces])
            .add_yaxis(
                series_name="岗位数量",
                y_axis=[p[1] for p in sorted_provinces],
                label_opts=opts.LabelOpts(is_show=True, position="top"),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="各省份岗位数量分布"),
                yaxis_opts=opts.AxisOpts(name="岗位数量"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30)),
            )
        )
        
        filename = f"{self.output_dir}/city_map.html"
        bar_chart.render(filename)
        print(f"✓ 柱状图已保存：{filename}")
        return filename
    
    def create_salary_bar(self):
        """2. 薪资水平分析（柱状图）"""
        print("生成图表：薪资水平分析")
        
        city_data = self.analyzer.get_city_distribution(15)
        salary_by_city = {}
        
        for city in city_data.index[:15]:
            city_df = self.analyzer.df[self.analyzer.df['city'] == city]
            if len(city_df) > 0:
                avg_sal = city_df['avg_salary'].mean()
                salary_by_city[city] = avg_sal
        
        bar_chart = (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="500px"))
            .add_xaxis(list(salary_by_city.keys()))
            .add_yaxis(
                series_name="平均薪资（元/月）",
                y_axis=[round(v, 2) for v in salary_by_city.values()],
                label_opts=opts.LabelOpts(is_show=True, position="top"),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="各城市平均薪资对比"),
                yaxis_opts=opts.AxisOpts(name="薪资（元）"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30)),
            )
        )
        
        filename = f"{self.output_dir}/salary_bar.html"
        bar_chart.render(filename)
        print(f"✓ 柱状图已保存：{filename}")
        return filename

    def create_salary_boxplot(self):
        """3. 城市薪资分位图（P25/P50/P75）"""
        print("生成图表：城市薪资分位图")

        city_data = self.analyzer.get_city_distribution(12)
        city_labels = []
        p25_values = []
        p50_values = []
        p75_values = []

        for city in city_data.index:
            city_df = self.analyzer.df[self.analyzer.df['city'] == city]
            values = city_df['avg_salary'].dropna().astype(float)
            if len(values) < 8:
                continue
            city_labels.append(str(city))
            p25_values.append(round(float(values.quantile(0.25)), 2))
            p50_values.append(round(float(values.quantile(0.50)), 2))
            p75_values.append(round(float(values.quantile(0.75)), 2))

        if not city_labels:
            city_labels = ['样本不足']
            p25_values = [0]
            p50_values = [0]
            p75_values = [0]

        chart = (
            Bar(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="500px"))
            .add_xaxis(city_labels)
            .add_yaxis("P25", p25_values, category_gap="42%")
            .add_yaxis("P50(中位)", p50_values, category_gap="42%")
            .add_yaxis("P75", p75_values, category_gap="42%")
            .set_global_opts(
                title_opts=opts.TitleOpts(is_show=False),
                tooltip_opts=opts.TooltipOpts(trigger="axis"),
                legend_opts=opts.LegendOpts(pos_top="3%"),
                xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=25)),
                yaxis_opts=opts.AxisOpts(name="薪资（元/月）"),
            )
        )

        filename = f"{self.output_dir}/salary_boxplot.html"
        chart.render(filename)
        print(f"✓ 分位对比图已保存：{filename}")
        return filename
    
    def create_education_pie(self):
        """4. 学历要求分布（环形图）"""
        print("生成图表：学历要求分布")
        
        edu_data = self.analyzer.get_education_distribution()
        
        # 转换为 Python 原生类型
        data_pair = [[str(edu), int(count)] for edu, count in zip(edu_data.index, edu_data.values)]
        
        pie_chart = (
            Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="500px"))
            .add(
                series_name="学历分布",
                data_pair=data_pair,
                radius=["50%", "75%"],
                center=["50%", "50%"],
                label_opts=opts.LabelOpts(is_show=True, formatter="{b}: {c} ({d}%)", position="outside"),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="学历要求分布", pos_top="20", pos_left="center"),
                legend_opts=opts.LegendOpts(pos_top="15%", orient="horizontal"),
            )
        )
        
        filename = f"{self.output_dir}/education_pie.html"
        pie_chart.render(filename)
        print(f"✓ 环形图已保存：{filename}")
        return filename
    
    def create_experience_pie(self):
        """5. 经验要求分布（环形图）"""
        print("生成图表：经验要求分布")
        
        exp_data = self.analyzer.get_experience_distribution()
        
        # 转换为 Python 原生类型
        data_pair = [[str(exp), int(count)] for exp, count in zip(exp_data.index, exp_data.values)]
        
        pie_chart = (
            Pie(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="500px"))
            .add(
                series_name="经验要求",
                data_pair=data_pair,
                radius=["50%", "75%"],
                center=["50%", "50%"],
                label_opts=opts.LabelOpts(is_show=True, formatter="{b}: {c} ({d}%)", position="outside"),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="经验要求分布", pos_top="20", pos_left="center"),
                legend_opts=opts.LegendOpts(pos_top="15%", orient="horizontal"),
            )
        )
        
        filename = f"{self.output_dir}/experience_pie.html"
        pie_chart.render(filename)
        print(f"✓ 环形图已保存：{filename}")
        return filename
    
    def create_skill_wordcloud(self):
        """6. 技能关键词词云"""
        print("生成图表：技能关键词词云")
        
        skill_data = self.analyzer.get_skill_cloud(100)
        
        wordcloud = (
            WordCloud(init_opts=opts.InitOpts(theme=ThemeType.LIGHT, width="100%", height="500px"))
            .add(
                series_name="技能关键词",
                data_pair=skill_data,
                word_size_range=[10, 100],
                shape="cardioid",
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(title="技能需求词云"),
            )
        )
        
        filename = f"{self.output_dir}/skill_wordcloud.html"
        wordcloud.render(filename)
        print(f"✓ 词云已保存：{filename}")
        return filename
    
    def generate_all_charts(self):
        """生成所有图表"""
        print("\n" + "="*60)
        print("开始生成可视化图表...")
        print("="*60 + "\n")
        
        charts = []
        
        # 生成 6 个核心图表
        charts.append(self.create_city_map())
        charts.append(self.create_salary_bar())
        charts.append(self.create_salary_boxplot())
        charts.append(self.create_education_pie())
        charts.append(self.create_experience_pie())
        charts.append(self.create_skill_wordcloud())
        
        print("\n" + "="*60)
        print(f"✓ 所有图表生成完成，共{len(charts)}个")
        print("="*60 + "\n")
        
        return charts


def main():
    """主函数"""
    from data_cleaner import DataCleaner, DataAnalyzer
    
    # 清洗和分析数据
    cleaner = DataCleaner()
    df = cleaner.run_cleaning()
    
    analyzer = DataAnalyzer(df)
    
    # 生成图表
    visualizer = JobVisualizer(analyzer)
    visualizer.generate_all_charts()


def load_cleaned_data():
    """加载清洗后的数据"""
    from data_cleaner import DataAnalyzer
    import pandas as pd
    from sqlalchemy import create_engine
    import config
    
    db_url = f"mysql+pymysql://{config.DATABASE_CONFIG['user']}:{config.DATABASE_CONFIG['password']}@{config.DATABASE_CONFIG['host']}:{config.DATABASE_CONFIG['port']}/{config.DATABASE_CONFIG['database']}?charset=utf8mb4"
    engine = create_engine(db_url)
    
    # 直接从清洗后的表加载数据
    df = pd.read_sql("SELECT * FROM job_positions_clean", engine)
    print(f"加载清洗后的数据：{len(df)}条")
    
    analyzer = DataAnalyzer(df)
    return analyzer


if __name__ == '__main__':
    main()
