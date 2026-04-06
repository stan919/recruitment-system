"""综合功能测试脚本。"""

from datetime import datetime
import random
import string
import sys

import requests

BASE_URL = "http://localhost:5000"


def random_suffix(length=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def test_page(url, name, expected_status=200, allow_redirects=True):
    try:
        response = requests.get(
            f"{BASE_URL}{url}",
            timeout=5,
            allow_redirects=allow_redirects,
        )
        passed = response.status_code == expected_status
        return passed, f"页面 {name} {url} -> {response.status_code}"
    except Exception as e:
        return False, f"页面 {name} {url} -> 错误: {e}"


def test_api(url, method="GET", params=None, expected_status=200, cookies=None):
    try:
        if method == "GET":
            response = requests.get(
                f"{BASE_URL}{url}", params=params, timeout=5, cookies=cookies
            )
        elif method == "POST":
            response = requests.post(
                f"{BASE_URL}{url}", json=params, timeout=5, cookies=cookies
            )
        elif method == "PUT":
            response = requests.put(
                f"{BASE_URL}{url}", json=params, timeout=5, cookies=cookies
            )
        else:
            return False, None, f"API {method} {url} -> 不支持的方法"

        if response.status_code == expected_status:
            return True, response, f"API {method} {url} -> {response.status_code}"

        try:
            data = response.json()
            if response.status_code == 200 and data.get("success"):
                return True, response, f"API {method} {url} -> 200(success=true)"
        except Exception:
            pass

        return (
            False,
            response,
            f"API {method} {url} -> {response.status_code} (期望 {expected_status})",
        )
    except Exception as e:
        return False, None, f"API {method} {url} -> 错误: {e}"


def create_temp_user(max_retry=3):
    password = "TestPass123"
    for _ in range(max_retry):
        username = f"ci_user_{random_suffix()}"
        payload = {
            "username": username,
            "email": f"{username}@example.com",
            "password": password,
        }
        success, response, _ = test_api("/api/register", "POST", payload, expected_status=200)
        if success and response is not None:
            data = response.json()
            if data.get("success"):
                return username, password
    return None, None


def main():
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    results = []

    success, response, message = test_api("/health", "GET")
    results.append((success, message))
    health_status = response.json().get("status", "unknown") if (success and response is not None) else "unknown"

    page_cases = [
        ("/", "首页", 200, True),
        ("/login", "登录页", 200, True),
        ("/register", "注册页", 200, True),
        ("/insights", "数据洞察页", 200, True),
        ("/jobs/search", "职位搜索页", 200, True),
        ("/applications", "投递记录页", 302, False),
        ("/profile", "个人中心页", 302, False),
        ("/chat/user", "用户消息页", 302, False),
    ]
    for url, name, expected_status, allow_redirects in page_cases:
        success, message = test_page(url, name, expected_status, allow_redirects)
        results.append((success, message))

    api_cases = [
        "/api/jobs/search?keyword=Python",
        "/api/jobs/search?city=bj",
        "/api/jobs/search?profession=cs",
    ]
    for api in api_cases:
        success, _, message = test_api(api, "GET")
        results.append((success, message))

    username, password = create_temp_user()
    results.append((bool(username), "临时用户注册"))

    session_cookies = None
    if username:
        success, response, _ = test_api(
            "/api/login",
            "POST",
            {"username": username, "password": password},
            expected_status=200,
        )
        login_ok = bool(success and response is not None and response.json().get("success"))
        results.append((login_ok, "临时用户登录"))
        if login_ok:
            session_cookies = response.cookies

    if session_cookies:
        success, response, _ = test_api(
            "/api/user",
            "GET",
            expected_status=200,
            cookies=session_cookies,
        )
        user_ok = bool(success and response is not None and response.json().get("logged_in"))
        results.append((user_ok, "用户信息接口"))

        success, _, _ = test_api(
            "/api/logout",
            "POST",
            expected_status=200,
            cookies=session_cookies,
        )
        results.append((success, "用户登出接口"))

    total_tests = len(results)
    passed_tests = sum(1 for passed, _ in results if passed)
    failed_tests = total_tests - passed_tests
    pass_rate = (passed_tests / total_tests * 100) if total_tests else 0
    failed_items = [item for passed, item in results if not passed]

    print("=" * 70)
    print("职引未来 综合测试总览")
    print("=" * 70)
    print(f"测试时间: {started_at}")
    print(f"测试地址: {BASE_URL}")
    print(f"健康状态: {health_status}")
    print(f"总用例: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {failed_tests}")
    print(f"通过率: {pass_rate:.1f}%")
    if failed_items:
        print(f"失败项: {'; '.join(failed_items)}")
    else:
        print("失败项: 无")
    print("=" * 70)

    return failed_tests == 0


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"测试过程中发生严重错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
