"""
运行10轮评估，记录共情度和专业度打分详情

重点关注：
1. 共情度等级和证据
2. 专业度总分、各题分数和证据
3. 证据验证结果
"""

import sys
import json
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.evaluate.interview_phase1_eval import evaluate_phase1


def run_10_rounds_evaluation():
    """运行10轮评估并记录详细结果"""
    
    results = []
    
    print("=" * 80)
    print("开始运行10轮评估测试")
    print("=" * 80)
    
    for i in range(1, 11):
        print(f"\n{'='*80}")
        print(f"第 {i}/10 轮评估")
        print(f"{'='*80}")
        
        try:
            result = evaluate_phase1(
                model_name="qwen-flash",
                case_id="1009904",
                enable_empathy_eval=True,
                enable_profession_eval=True,
                parallel_eval=True
            )
            
            # 提取关键信息
            round_data = {
                "round": i,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": result.get("status", "unknown"),
                "empathy": None,
                "profession": None
            }
            
            # 共情度评估
            if result.get("empathy_evaluation"):
                empathy = result["empathy_evaluation"]
                round_data["empathy"] = {
                    "level": empathy.get("empathy_level"),
                    "evidence": empathy.get("evidence", "")[:500],  # 截取前500字符
                    "why_this_level": empathy.get("why_this_level", "")[:300]
                }
                print(f"\n  【共情度评估】")
                print(f"    等级: {empathy.get('empathy_level')}")
                print(f"    证据: {empathy.get('evidence', '')[:200]}...")
            
            # 专业度评估
            if result.get("profession_evaluation"):
                profession = result["profession_evaluation"]
                round_data["profession"] = {
                    "total_score": profession.get("total_score"),
                    "average_score": profession.get("average_score"),
                    "evidence_verification": profession.get("evidence_verification", {})
                }
                print(f"\n  【专业度评估】")
                print(f"    总分: {profession.get('total_score')}")
                print(f"    平均分: {profession.get('average_score'):.2f}")
                
                # 证据验证
                ev = profession.get("evidence_verification", {})
                if ev:
                    print(f"    证据验证: {'通过' if ev.get('is_valid') else '失败'} (置信度: {ev.get('confidence', 0):.2f})")
                    if ev.get("warning"):
                        print(f"    警告: {ev.get('warning')[:200]}")
            
            results.append(round_data)
            print(f"\n  ✓ 第 {i} 轮完成")
            
        except Exception as e:
            print(f"\n  ✗ 第 {i} 轮失败: {e}")
            results.append({
                "round": i,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status": "error",
                "error": str(e)
            })
    
    # 保存结果
    output_file = project_root / "data" / "evaluation_10_rounds_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 打印汇总统计
    print(f"\n{'='*80}")
    print("10轮评估汇总统计")
    print(f"{'='*80}")
    
    empathy_levels = [r["empathy"]["level"] for r in results if r.get("empathy") and r["empathy"].get("level")]
    profession_scores = [r["profession"]["total_score"] for r in results if r.get("profession") and r["profession"].get("total_score") is not None]
    
    if empathy_levels:
        print(f"\n共情度等级统计:")
        print(f"  平均值: {sum(empathy_levels)/len(empathy_levels):.2f}")
        print(f"  最高: {max(empathy_levels)}")
        print(f"  最低: {min(empathy_levels)}")
        print(f"  各轮分数: {empathy_levels}")
    
    if profession_scores:
        print(f"\n专业度总分统计:")
        print(f"  平均值: {sum(profession_scores)/len(profession_scores):.2f}")
        print(f"  最高: {max(profession_scores)}")
        print(f"  最低: {min(profession_scores)}")
        print(f"  各轮分数: {profession_scores}")
    
    print(f"\n详细结果已保存至: {output_file}")
    
    return results


if __name__ == "__main__":
    run_10_rounds_evaluation()
