"""
测试 Phase 1 评估功能

测试共情度和专业度评估
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.evaluate.interview_phase1_eval import evaluate_phase1


def test_phase1_evaluation():
    """测试 Phase 1 评估"""
    print("=" * 60)
    print("测试：Phase 1 评估功能（包含共情度和专业度评估）")
    print("=" * 60)
    
    try:
        result = evaluate_phase1(
            model_name="qwen-flash",
            case_id="1009904",
            enable_empathy_eval=True,
            enable_profession_eval=True,
            parallel_eval=True
        )
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
        print("\n评估结果摘要:")
        print(f"  模型: {result['model_name']}")
        print(f"  病例: {result['case_id']}")
        print(f"  状态: {result['status']}")
        print(f"  输出文件: {result['output_file']}")
        
        if result.get('empathy_evaluation'):
            print(f"\n  共情度评估:")
            print(f"    总分: {result['empathy_evaluation']['total_score']}")
            print(f"    平均分: {result['empathy_evaluation']['average_score']:.2f}")
            print(f"    方差: {result['empathy_evaluation']['score_variance']:.4f}")
        
        if result.get('profession_evaluation'):
            print(f"\n  专业度评估:")
            print(f"    总分: {result['profession_evaluation']['total_score']}")
            print(f"    平均分: {result['profession_evaluation']['average_score']:.2f}")
        
        return result
        
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_phase1_evaluation()
