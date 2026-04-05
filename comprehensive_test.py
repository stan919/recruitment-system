"""
综合代码审查与功能测试报告
"""

from datetime import datetime
import random
import string
import sys

import requests

BASE_URL = "http://localhost:5000"


def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def random_suffix(length=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def test_page(url, name, expected_status=200, allow_redirects=True):
    """测试页面访问。"""
    try:
        r = requests.get(f"{BASE_URL}{url}", timeout=5, allow_redirects=allow_redirects)
        if r.status_code == expected_status:
            print(f"✅ {name}: {url} - 状态码 {r.status_code}")
            return True

        print(f"❌ {name}: {url} - 状态码 {r.status_code}（期望 {expected_status}）")
        return False
    except Exception as e:
        print(f"❌ {name}: {url} - 错误：{e}")
        return False


def test_api(url, method="GET", params=None, expected_status=200, cookies=None):
    """测试 API 接口。"""
    try:
        if method == "GET":
            r = requests.get(f"{BASE_URL}{url}", params=params, timeout=5, cookies=cookies)
        elif method == "POST":
            r = requests.post(f"{BASE_URL}{url}", json=params, timeout=5, cookies=cookies)
        elif method == "PUT":
            r = requests.put(f"{BASE_URL}{url}", json=params, timeout=5, cookies=cookies)
        else:
            raise ValueError(f"不支持的请求方法: {method}")

        if r.status_code == expected_status:
            print(f"✅ API: {method} {url} - 状态码 {r.status_code}")
            return True, r

        # 对 success 风格接口做宽松兼容
        try:
            data = r.json()
            if r.status_code == 200 and data.get("success"):
                print(f"✅ API: {method} {url} - 正常")
                return True, r
        except Exception:
            pass

        print(f"❌ API: {method} {url} - 状态码 {r.status_code}（期望 {expected_status}）")
        return False, r
    except Exception as e:
        print(f"❌ API: {method} {url} - 错误：{e}")
        return False, None


def create_temp_user(max_retry=3):
    """创建临时用户，避免依赖固定账号。"""
    password = "TestPass123"

    for _ in range(max_retry):
        username = f"ci_user_{random_suffix()}"
        payload = {
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
        }
        ok, r = test_api("/api/register", "POST", payload, expected_status=200)
        if ok and r is not None:
            data = r.json()
            if data.get("success"):
                return username, password

    return None, None


def main():
    print_section("职引未来 - 综合代码审查与功能测试")
    print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试地址：{BASE_URL}")

    total_tests = 0
    passed_tests = 0

    # 0. 健康检查
    print_section("0. 系统健康检查")
    total_tests += 1
    success, r = test_api("/health", "GET")
    if success and r is not None:
        passed_tests += 1
        health_data = r.json()
        print(f"   系统状态：{health_data.get('status', 'unknown')}")

    # 1. 页面访问测试
    print_section("1. 页面访问测试")
    public_pages = [
        ("/", "首页", 200, True),
        ("/login", "登录页", 200, True),
        ("/register", "注册页", 200, True),
        ("/insights", "数据洞察页", 200, True),
        ("/jobs/search", "职位搜索页", 200, True),
    ]

    protected_pages = [
        ("/applications", "投递记录页", 302, False),
        ("/profile", "个人中心页", 302, False),
        ("/chat/user", "用户消息页", 302, False),
    ]

    for url, name, code, allow_redirects in public_pages + protected_pages:
        total_tests += 1
        if test_page(url, name, expected_status=code, allow_redirects=allow_redirects):
            passed_tests += 1

    # 2. 公共 API
    print_section("2. 公共 API 测试")
    for api in [
        "/api/jobs/search?keyword=Python",
        "/api/jobs/search?city=bj",
        "/api/jobs/search?profession=cs",
    ]:
        total_tests += 1
        success, _ = test_api(api, "GET")
        if success:
            passed_tests += 1

    # 3. 认证流测试
    print_section("3. 认证流测试")
    username, password = create_temp_user()

    total_tests += 1
    if username:
        passed_tests += 1
        print(f"✅ 临时用户创建成功：{username}")
    else:
        print("❌ 临时用户创建失败")

    session_cookies = None
    if username:
        total_tests += 1
        success, r = test_api(
            "/api/login",
            "POST",
            {"username": username, "password": password},
            expected_status=200,
        )
        if success and r is not None and r.json().get("success"):
            passed_tests += 1
            session_cookies = r.cookies
            print("✅ 临时用户登录成功")
        else:
            print("❌ 临时用户登录失败")

    if session_cookies:
        total_tests += 1
        success, r = test_api("/api/user", "GET", expected_status=200, cookies=session_cookies)
        if success and r is not None and r.json().get("logged_in"):
            passed_tests += 1
            print("✅ 用户信息接口正常")
        else:
            print("❌ 用户信息接口异常")

        total_tests += 1
        success, _ = test_api("/api/logout", "POST", expected_status=200, cookies=session_cookies)
        if success:
            passed_tests += 1

    # 4. 结果统计
    print_section("4. 测试结果统计")
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests else 0

    print(f"测试总数：{total_tests}")
    print(f"通过数量：{passed_tests}")
    print(f"失败数量：{failed_tests}")
    print(f"通过率：{pass_rate:.1f}%")

    if failed_tests == 0:
        print("\n✅ 所有综合测试通过")
    else:
        print("\n⚠️ 存在失败项，请根据日志修复")

    return failed_tests == 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试过程中发生严重错误：{e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
