"""
每日自动更新脚本

该脚本整合了累积新闻获取和RSS Feed生成，适合设置为定时任务
"""

import os
import sys
import subprocess
from datetime import datetime

def run_script(script_name, description):
    """
    执行脚本并记录结果
    """
    print(f"\n{'='*60}")
    print(f"🚀 开始执行: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print(f"✅ {description} 执行成功")
            if result.stdout:
                print("输出:")
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} 执行失败")
            if result.stderr:
                print("错误信息:")
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ 执行 {description} 时发生异常: {e}")
        return False

def main():
    """
    主函数：执行每日更新流程
    """
    start_time = datetime.now()
    print("=" * 60)
    print("🕐 每日新闻更新流程开始")
    print("=" * 60)
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    success_count = 0
    total_tasks = 2
    
    # 步骤1: 更新累积新闻
    if run_script("生成累积新闻.py", "更新累积新闻"):
        success_count += 1
    
    # 步骤2: 生成累积RSS Feed
    if run_script("生成累积RSS.py", "生成累积RSS Feed"):
        success_count += 1
    
    # 输出最终结果
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 60)
    print("📊 每日更新完成统计")
    print("=" * 60)
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {duration}")
    print(f"成功任务: {success_count}/{total_tasks}")
    
    if success_count == total_tasks:
        print("🎉 所有任务执行成功！")
        return True
    else:
        print("⚠️ 部分任务执行失败，请检查错误信息")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)