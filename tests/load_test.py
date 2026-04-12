"""
精神科AI问诊系统 - 压力测试脚本

测试目标：
1. 病例列表接口并发性能
2. 病例详情接口并发性能
3. 问诊会话创建性能
4. 问诊消息发送性能
5. 诊断提交性能
6. 记录保存性能

使用方法:
    python tests/load_test.py
"""
import sys
import json
import time
import statistics
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
from dataclasses import dataclass, field

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests

# ============================================================
# 配置
# ============================================================

BASE_URL = "http://localhost:5000"
CONCURRENT_USERS = 10  # 并发用户数
REQUESTS_PER_USER = 5  # 每个用户请求数
TIMEOUT = 30  # 请求超时时间（秒）


@dataclass
class TestResult:
    """测试结果"""
    name: str
    total_requests: int = 0
    success_count: int = 0
    fail_count: int = 0
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.success_count / self.total_requests) * 100

    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

    @property
    def p50_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return statistics.median(self.response_times)

    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    @property
    def p99_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        idx = int(len(sorted_times) * 0.99)
        return sorted_times[min(idx, len(sorted_times) - 1)]

    @property
    def min_response_time(self) -> float:
        return min(self.response_times) if self.response_times else 0.0

    @property
    def max_response_time(self) -> float:
        return max(self.response_times) if self.response_times else 0.0

    @property
    def throughput(self) -> float:
        """吞吐量 (requests/second)"""
        total_time = sum(self.response_times)
        if total_time == 0:
            return 0.0
        return self.success_count / total_time

    def summary(self) -> str:
        return f"""
  总请求数: {self.total_requests}
  成功数: {self.success_count}
  失败数: {self.fail_count}
  成功率: {self.success_rate:.2f}%
  平均响应时间: {self.avg_response_time:.3f}s
  P50 响应时间: {self.p50_response_time:.3f}s
  P95 响应时间: {self.p95_response_time:.3f}s
  P99 响应时间: {self.p99_response_time:.3f}s
  最小响应时间: {self.min_response_time:.3f}s
  最大响应时间: {self.max_response_time:.3f}s
  吞吐量: {self.throughput:.2f} req/s
"""


def make_request(method: str, url: str, **kwargs) -> tuple:
    """发送 HTTP 请求并返回 (status_code, response_time, response_data)"""
    start_time = time.time()
    try:
        response = requests.request(method, url, timeout=TIMEOUT, **kwargs)
        response_time = time.time() - start_time
        return response.status_code, response_time, response.json() if response.content else {}
    except requests.exceptions.Timeout:
        response_time = time.time() - start_time
        return 0, response_time, {"error": "timeout"}
    except requests.exceptions.ConnectionError:
        response_time = time.time() - start_time
        return 0, response_time, {"error": "connection_error"}
    except Exception as e:
        response_time = time.time() - start_time
        return 0, response_time, {"error": str(e)}


def test_get_cases(result: TestResult):
    """测试获取病例列表"""
    for _ in range(REQUESTS_PER_USER):
        result.total_requests += 1
        status_code, response_time, data = make_request("GET", f"{BASE_URL}/api/cases")
        result.response_times.append(response_time)
        if status_code == 200 and "cases" in data:
            result.success_count += 1
        else:
            result.fail_count += 1
            result.errors.append(f"status={status_code}, data={data}")


def test_get_case_info(result: TestResult, case_id: str):
    """测试获取病例详情"""
    for _ in range(REQUESTS_PER_USER):
        result.total_requests += 1
        status_code, response_time, data = make_request("GET", f"{BASE_URL}/api/case/{case_id}/info")
        result.response_times.append(response_time)
        if status_code == 200 and "id" in data:
            result.success_count += 1
        else:
            result.fail_count += 1
            result.errors.append(f"status={status_code}, data={data}")


def test_chat_start(result: TestResult, case_id: str):
    """测试创建问诊会话"""
    for _ in range(REQUESTS_PER_USER):
        result.total_requests += 1
        status_code, response_time, data = make_request(
            "POST",
            f"{BASE_URL}/api/chat/start",
            json={"case_id": case_id},
        )
        result.response_times.append(response_time)
        if status_code == 200 and "session_id" in data:
            result.success_count += 1
        else:
            result.fail_count += 1
            result.errors.append(f"status={status_code}, data={data}")


def test_chat_send(result: TestResult, session_id: str):
    """测试发送问诊消息"""
    for _ in range(REQUESTS_PER_USER):
        result.total_requests += 1
        status_code, response_time, data = make_request(
            "POST",
            f"{BASE_URL}/api/chat/send",
            json={"session_id": session_id, "message": "你好，请问你哪里不舒服？"},
        )
        result.response_times.append(response_time)
        if status_code == 200 and "response" in data:
            result.success_count += 1
        else:
            result.fail_count += 1
            result.errors.append(f"status={status_code}, data={data}")


def test_save_record(result: TestResult, case_id: str):
    """测试保存问诊记录"""
    for _ in range(REQUESTS_PER_USER):
        result.total_requests += 1
        status_code, response_time, data = make_request(
            "POST",
            f"{BASE_URL}/api/record/save",
            json={
                "case_id": case_id,
                "caseInfo": {"basicInfomation": "测试患者"},
                "conversation": [],
                "exams": [],
                "caseText": "测试病历",
                "diagnosis": None,
            },
        )
        result.response_times.append(response_time)
        if status_code == 200 and data.get("status") == "ok":
            result.success_count += 1
        else:
            result.fail_count += 1
            result.errors.append(f"status={status_code}, data={data}")


def test_get_record(result: TestResult, case_id: str):
    """测试获取问诊记录"""
    for _ in range(REQUESTS_PER_USER):
        result.total_requests += 1
        status_code, response_time, data = make_request("GET", f"{BASE_URL}/api/record/{case_id}")
        result.response_times.append(response_time)
        if status_code == 200:
            result.success_count += 1
        else:
            result.fail_count += 1
            result.errors.append(f"status={status_code}, data={data}")


def test_submit_diagnosis(result: TestResult, case_id: str):
    """测试提交诊断"""
    for _ in range(REQUESTS_PER_USER):
        result.total_requests += 1
        status_code, response_time, data = make_request(
            "POST",
            f"{BASE_URL}/api/diagnosis/submit",
            json={
                "case_id": case_id,
                "category": "心境障碍",
                "disease": "6A70 单次发作抑郁障碍",
                "reason": "测试诊断理由",
            },
        )
        result.response_times.append(response_time)
        if status_code == 200 and data.get("status") == "ok":
            result.success_count += 1
        else:
            result.fail_count += 1
            result.errors.append(f"status={status_code}, data={data}")


def run_load_test():
    """运行压力测试"""
    print("\n" + "=" * 70)
    print(" " * 20 + "精神科AI问诊系统 - 压力测试")
    print("=" * 70)
    print(f"\n配置:")
    print(f"  基础URL: {BASE_URL}")
    print(f"  并发用户数: {CONCURRENT_USERS}")
    print(f"  每用户请求数: {REQUESTS_PER_USER}")
    print(f"  超时时间: {TIMEOUT}s")

    # 先获取一个有效的 case_id
    print("\n[准备] 获取测试用例...")
    status_code, _, data = make_request("GET", f"{BASE_URL}/api/cases")
    if status_code != 200 or not data.get("cases"):
        print("  错误: 无法获取病例列表，请确保服务已启动")
        return

    test_case_id = data["cases"][0].get("id", "1009904")
    print(f"  使用病例ID: {test_case_id}")

    # 创建会话用于测试
    print("\n[准备] 创建测试会话...")
    status_code, _, session_data = make_request(
        "POST", f"{BASE_URL}/api/chat/start", json={"case_id": test_case_id}
    )
    test_session_id = session_data.get("session_id", "")
    print(f"  会话ID: {test_session_id[:16]}...")

    # ============================================================
    # 测试 1: 获取病例列表
    # ============================================================
    print("\n" + "-" * 70)
    print("测试 1: GET /api/cases (获取病例列表)")
    print("-" * 70)
    result_cases = TestResult(name="获取病例列表")
    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [executor.submit(test_get_cases, result_cases) for _ in range(CONCURRENT_USERS)]
        for f in as_completed(futures):
            f.result()
    print(result_cases.summary())

    # ============================================================
    # 测试 2: 获取病例详情
    # ============================================================
    print("\n" + "-" * 70)
    print(f"测试 2: GET /api/case/{test_case_id}/info (获取病例详情)")
    print("-" * 70)
    result_case_info = TestResult(name="获取病例详情")
    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [executor.submit(test_get_case_info, result_case_info, test_case_id) for _ in range(CONCURRENT_USERS)]
        for f in as_completed(futures):
            f.result()
    print(result_case_info.summary())

    # ============================================================
    # 测试 3: 创建问诊会话
    # ============================================================
    print("\n" + "-" * 70)
    print("测试 3: POST /api/chat/start (创建问诊会话)")
    print("-" * 70)
    result_chat_start = TestResult(name="创建问诊会话")
    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [executor.submit(test_chat_start, result_chat_start, test_case_id) for _ in range(CONCURRENT_USERS)]
        for f in as_completed(futures):
            f.result()
    print(result_chat_start.summary())

    # ============================================================
    # 测试 4: 发送问诊消息
    # ============================================================
    print("\n" + "-" * 70)
    print("测试 4: POST /api/chat/send (发送问诊消息)")
    print("-" * 70)
    result_chat_send = TestResult(name="发送问诊消息")
    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [executor.submit(test_chat_send, result_chat_send, test_session_id) for _ in range(CONCURRENT_USERS)]
        for f in as_completed(futures):
            f.result()
    print(result_chat_send.summary())

    # ============================================================
    # 测试 5: 保存问诊记录
    # ============================================================
    print("\n" + "-" * 70)
    print("测试 5: POST /api/record/save (保存问诊记录)")
    print("-" * 70)
    result_save_record = TestResult(name="保存问诊记录")
    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [executor.submit(test_save_record, result_save_record, test_case_id) for _ in range(CONCURRENT_USERS)]
        for f in as_completed(futures):
            f.result()
    print(result_save_record.summary())

    # ============================================================
    # 测试 6: 获取问诊记录
    # ============================================================
    print("\n" + "-" * 70)
    print(f"测试 6: GET /api/record/{test_case_id} (获取问诊记录)")
    print("-" * 70)
    result_get_record = TestResult(name="获取问诊记录")
    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [executor.submit(test_get_record, result_get_record, test_case_id) for _ in range(CONCURRENT_USERS)]
        for f in as_completed(futures):
            f.result()
    print(result_get_record.summary())

    # ============================================================
    # 测试 7: 提交诊断
    # ============================================================
    print("\n" + "-" * 70)
    print("测试 7: POST /api/diagnosis/submit (提交诊断)")
    print("-" * 70)
    result_submit_diagnosis = TestResult(name="提交诊断")
    with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = [executor.submit(test_submit_diagnosis, result_submit_diagnosis, test_case_id) for _ in range(CONCURRENT_USERS)]
        for f in as_completed(futures):
            f.result()
    print(result_submit_diagnosis.summary())

    # ============================================================
    # 汇总结果
    # ============================================================
    print("\n" + "=" * 70)
    print(" " * 25 + "压力测试汇总")
    print("=" * 70)

    all_results = [
        result_cases,
        result_case_info,
        result_chat_start,
        result_chat_send,
        result_save_record,
        result_get_record,
        result_submit_diagnosis,
    ]

    total_requests = sum(r.total_requests for r in all_results)
    total_success = sum(r.success_count for r in all_results)
    total_fail = sum(r.fail_count for r in all_results)
    all_response_times = []
    for r in all_results:
        all_response_times.extend(r.response_times)

    print(f"\n总请求数: {total_requests}")
    print(f"总成功数: {total_success}")
    print(f"总失败数: {total_fail}")
    print(f"总体成功率: {(total_success / total_requests * 100) if total_requests > 0 else 0:.2f}%")
    print(f"总体平均响应时间: {statistics.mean(all_response_times) if all_response_times else 0:.3f}s")
    print(f"总体 P95 响应时间: {sorted(all_response_times)[int(len(all_response_times) * 0.95)] if all_response_times else 0:.3f}s")

    # 各接口对比
    print("\n各接口性能对比:")
    print(f"{'接口':<30} {'成功率':<10} {'平均响应':<12} {'P95响应':<12} {'吞吐量':<12}")
    print("-" * 76)
    for r in all_results:
        print(f"{r.name:<30} {r.success_rate:>6.1f}%   {r.avg_response_time:>8.3f}s   {r.p95_response_time:>8.3f}s   {r.throughput:>8.2f} req/s")

    # 保存测试结果
    output_dir = Path(__file__).parent.parent / "data" / "output" / "load_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"load_test_{timestamp}.json"

    test_report = {
        "timestamp": timestamp,
        "config": {
            "base_url": BASE_URL,
            "concurrent_users": CONCURRENT_USERS,
            "requests_per_user": REQUESTS_PER_USER,
            "timeout": TIMEOUT,
        },
        "summary": {
            "total_requests": total_requests,
            "total_success": total_success,
            "total_fail": total_fail,
            "overall_success_rate": (total_success / total_requests * 100) if total_requests > 0 else 0,
            "overall_avg_response_time": statistics.mean(all_response_times) if all_response_times else 0,
            "overall_p95_response_time": sorted(all_response_times)[int(len(all_response_times) * 0.95)] if all_response_times else 0,
        },
        "results": [
            {
                "name": r.name,
                "total_requests": r.total_requests,
                "success_count": r.success_count,
                "fail_count": r.fail_count,
                "success_rate": r.success_rate,
                "avg_response_time": r.avg_response_time,
                "p50_response_time": r.p50_response_time,
                "p95_response_time": r.p95_response_time,
                "p99_response_time": r.p99_response_time,
                "min_response_time": r.min_response_time,
                "max_response_time": r.max_response_time,
                "throughput": r.throughput,
                "errors": r.errors[:5],  # 只保留前5个错误
            }
            for r in all_results
        ],
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(test_report, f, ensure_ascii=False, indent=2)

    print(f"\n测试报告已保存: {output_file}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        run_load_test()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试发生错误: {e}")
        import traceback
        traceback.print_exc()
