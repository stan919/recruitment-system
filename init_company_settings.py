"""
初始化公司设置数据
"""
from models_company import Company, Session as CompanySession
from datetime import date

def init_company_data():
    session = CompanySession()
    try:
        # 示例公司数据
        companies_data = [
            {
                'company_name': '腾讯科技有限公司',
                'english_name': 'Tencent Technology Co., Ltd.',
                'short_name': '腾讯科技',
                'credit_code': '91440300192203821K',
                'established_date': date(1998, 11, 11),
                'industry': '互联网',
                'website': 'https://www.tencent.com',
                'phone': '0755-86013388',
                'email': 'hr@tencent.com',
                'address': '广东省深圳市南山区海天二路 33 号腾讯滨海大厦',
                'description': '腾讯成立于 1998 年，是一家总部位于中国深圳的互联网公司。我们致力于通过创新的产品和服务提升全球用户的生活品质。核心业务包括社交、游戏、广告、金融科技和企业服务等。',
                'recruitment宣言': '科技向善，连接未来。加入我们，一起用代码改变世界！',
                'logo_path': None,
                'enable_employer_brand': True,
                'culture_video_url': 'https://v.qq.com/x/cover/tencent_culture.html',
                'employee_stories': '在这里，每一位员工都能找到属于自己的舞台。从应届生到技术专家，从普通员工到团队管理者，腾讯提供多元化的发展通道和完善的培训体系，让你的职业生涯充满无限可能。',
                'resume_retention_days': 365,
                'interview_record_archive_days': 180,
                'gdpr_compliance': True,
                'consent_popup_enabled': True,
                'data_export_enabled': True,
                'data_deletion_enabled': True,
                'audit_log_enabled': True,
                'audit_log_retention_days': 90,
                'phone_mask_enabled': True,
                'email_mask_enabled': False
            },
            {
                'company_name': '阿里巴巴集团',
                'english_name': 'Alibaba Group',
                'short_name': '阿里',
                'credit_code': '91330000793361906N',
                'established_date': date(1999, 9, 10),
                'industry': '互联网',
                'website': 'https://www.alibaba.com',
                'phone': '0571-85022088',
                'email': 'recruit@alibaba-inc.com',
                'address': '浙江省杭州市余杭区文一西路 969 号阿里巴巴西溪园区',
                'description': '阿里巴巴集团成立于 1999 年，是全球领先的电子商务和科技公司。我们的使命是"让天下没有难做的生意"，业务涵盖电商、金融科技、物流、云计算等多个领域。',
                'recruitment宣言': '梦想还是要有的，万一实现了呢？阿里等你来战！',
                'logo_path': None,
                'enable_employer_brand': True,
                'culture_video_url': 'https://video.alibaba.com/culture',
                'employee_stories': '在阿里，我们相信每个人都有改变世界的力量。无论你是技术大牛还是职场新人，这里都能为你提供广阔的发展平台和成长空间。和优秀的人一起，做有挑战的事！',
                'resume_retention_days': 365,
                'interview_record_archive_days': 180,
                'gdpr_compliance': True,
                'consent_popup_enabled': True,
                'data_export_enabled': True,
                'data_deletion_enabled': True,
                'audit_log_enabled': True,
                'audit_log_retention_days': 90,
                'phone_mask_enabled': True,
                'email_mask_enabled': False
            },
            {
                'company_name': '华为技术有限公司',
                'english_name': 'Huawei Technologies Co., Ltd.',
                'short_name': '华为',
                'credit_code': '9144030027926701X2',
                'established_date': date(1987, 9, 15),
                'industry': '制造业',
                'website': 'https://www.huawei.com',
                'phone': '0755-28780808',
                'email': 'campus@huawei.com',
                'address': '广东省深圳市龙岗区坂田华为基地',
                'description': '华为创立于 1987 年，是全球领先的 ICT（信息与通信）基础设施和智能终端提供商。我们致力于把数字世界带入每个人、每个家庭、每个组织，构建万物互联的智能世界。',
                'recruitment宣言': '以奋斗者为本，长期艰苦奋斗。加入华为，成就非凡人生！',
                'logo_path': None,
                'enable_employer_brand': True,
                'culture_video_url': 'https://e.huawei.com/cn/careers/culture',
                'employee_stories': '华为为每一位奋斗者提供公平的竞争环境和广阔的发展空间。在这里，你的付出会被看见，你的成长会被支持，你的梦想会被尊重。与华为一起，共创智能世界！',
                'resume_retention_days': 365,
                'interview_record_archive_days': 180,
                'gdpr_compliance': True,
                'consent_popup_enabled': True,
                'data_export_enabled': True,
                'data_deletion_enabled': True,
                'audit_log_enabled': True,
                'audit_log_retention_days': 90,
                'phone_mask_enabled': True,
                'email_mask_enabled': False
            }
        ]
        
        for company_data in companies_data:
            # 检查是否已存在
            company = session.query(Company).filter_by(
                company_name=company_data['company_name']
            ).first()
            
            if company:
                # 更新现有记录
                for key, value in company_data.items():
                    setattr(company, key, value)
                print(f"✅ 更新公司：{company_data['company_name']}")
            else:
                # 创建新记录
                company = Company(**company_data)
                session.add(company)
                print(f"✅ 创建公司：{company_data['company_name']}")
        
        session.commit()
        print(f"\n✅ 成功初始化 {len(companies_data)} 家公司的设置数据")
        
    except Exception as e:
        session.rollback()
        print(f"❌ 初始化失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    init_company_data()
