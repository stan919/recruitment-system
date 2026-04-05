"""全量功能测试脚本。"""

import random
import string

import requests

BASE_URL = "http://localhost:5000"


def random_suffix(length=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def assert_ok(resp, label):
    assert resp.status_code == 200, f"{label}失败: {resp.status_code}"


def test_all():
    print("=" * 60)
    print("开始全量功能测试")
    print("=" * 60)

    # 1. 页面访问
    print("\n1. 页面测试")
    for path in ["/", "/login", "/register", "/insights"]:
        r = requests.get(f"{BASE_URL}{path}")
        assert_ok(r, f"页面 {path} ")
        print(f"✅ {path} 正常")

    # 2. 公共 API
    print("\n2. 公共 API 测试")
    r = requests.get(f"{BASE_URL}/api/jobs/1")
    assert_ok(r, "职位详情API")
    data = r.json()
    assert data.get("success") is True
    print(f"✅ 职位详情正常: {data['job']['job_name']}")

    r = requests.get(f"{BASE_URL}/api/jobs/search", params={"keyword": "Python"})
    assert_ok(r, "职位搜索API")
    data = r.json()
    assert data.get("success") is True
    print(f"✅ 搜索正常，返回 {data.get('total', 0)} 条")

    # 3. 注册临时用户
    print("\n3. 认证流测试")
    username = f"fulltest_{random_suffix()}"
    password = "StrongPass123"
    register_payload = {
        "username": username,
        "email": f"{username}@example.com",
        "password": password,
    }
    r = requests.post(f"{BASE_URL}/api/register", json=register_payload)
    assert_ok(r, "注册API")
    assert r.json().get("success") is True
    print(f"✅ 注册成功: {username}")

    # 4. 登录并获取用户信息
    r = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": username, "password": password},
    )
    assert_ok(r, "登录API")
    data = r.json()
    assert data.get("success") is True
    session = r.cookies
    print(f"✅ 登录成功: {data['user']['username']}")

    r = requests.get(f"{BASE_URL}/api/user", cookies=session)
    assert_ok(r, "用户信息API")
    assert r.json().get("logged_in") is True
    print("✅ 用户信息正常")

    # 5. 密码校验（负例）
    print("\n4. 密码规则负例测试")
    bad_user = f"bad_{random_suffix()}"
    r = requests.post(
        f"{BASE_URL}/api/register",
        json={
            "username": bad_user,
            "email": f"{bad_user}@example.com",
            "password": "123456",
        },
    )
    assert r.status_code == 400, "短密码应被拒绝"
    print("✅ 短密码被正确拒绝")

    # 6. 登出
    r = requests.post(f"{BASE_URL}/api/logout", cookies=session)
    assert_ok(r, "登出API")
    print("✅ 登出成功")

    print("\n" + "=" * 60)
    print("✅ 全量测试通过")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_all()
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise SystemExit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback

        traceback.print_exc()
        raise SystemExit(1)
