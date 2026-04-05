"""
全功能测试脚本
测试所有 API 端点和功能
"""
import requests
import json

BASE_URL = 'http://localhost:5000'

def test_health():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    response = requests.get(f'{BASE_URL}/health')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    print("✅ 健康检查通过")
    return True

def test_login_page():
    """测试登录页面"""
    print("\n=== 测试登录页面 ===")
    response = requests.get(f'{BASE_URL}/login')
    assert response.status_code == 200
    print("✅ 登录页面加载成功")
    return True

def test_register_page():
    """测试注册页面"""
    print("\n=== 测试注册页面 ===")
    response = requests.get(f'{BASE_URL}/register')
    assert response.status_code == 200
    print("✅ 注册页面加载成功")
    return True

def test_home_page():
    """测试主页"""
    print("\n=== 测试主页 ===")
    response = requests.get(f'{BASE_URL}/')
    assert response.status_code == 200
    print("✅ 主页加载成功")
    return True

def test_api_login_fail():
    """测试登录失败场景"""
    print("\n=== 测试登录失败 ===")
    response = requests.post(f'{BASE_URL}/api/login', json={})
    assert response.status_code == 400
    print("✅ 空参数登录失败测试通过")
    
    response = requests.post(f'{BASE_URL}/api/login', json={'username': 'test', 'password': ''})
    assert response.status_code == 400
    print("✅ 空密码登录失败测试通过")
    return True

def test_api_register_validation():
    """测试注册验证"""
    print("\n=== 测试注册验证 ===")
    # 测试空参数
    response = requests.post(f'{BASE_URL}/api/register', json={})
    assert response.status_code == 400
    print("✅ 空参数注册验证通过")
    
    # 测试短密码
    response = requests.post(f'{BASE_URL}/api/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': '123'
    })
    assert response.status_code == 400
    print("✅ 短密码验证通过（至少 8 位）")
    return True

def test_jobs_search():
    """测试职位搜索"""
    print("\n=== 测试职位搜索 API ===")
    response = requests.get(f'{BASE_URL}/api/jobs/search')
    assert response.status_code == 200
    data = response.json()
    assert data['success'] == True
    print(f"✅ 职位搜索 API 正常，返回 {data.get('total', 0)} 个职位")
    return True

def test_insights_page():
    """测试数据洞察页面"""
    print("\n=== 测试数据洞察页面 ===")
    response = requests.get(f'{BASE_URL}/insights')
    assert response.status_code == 200
    print("✅ 数据洞察页面加载成功")
    return True

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始全功能测试")
    print("=" * 60)
    
    tests = [
        ("健康检查", test_health),
        ("登录页面", test_login_page),
        ("注册页面", test_register_page),
        ("主页", test_home_page),
        ("登录失败验证", test_api_login_fail),
        ("注册验证", test_api_register_validation),
        ("职位搜索", test_jobs_search),
        ("数据洞察", test_insights_page),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {name} 失败：{str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"测试完成：{passed} 通过，{failed} 失败")
    print("=" * 60)
    
    return failed == 0

if __name__ == '__main__':
    import time
    print("等待服务启动...")
    time.sleep(2)
    
    success = run_all_tests()
    exit(0 if success else 1)
