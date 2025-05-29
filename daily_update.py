"""
每日自动更新脚本

该脚本整合了累积新闻获取和RSS Feed生成，适合设置为定时任务
支持GitHub Actions环境
"""

import os
import sys
import subprocess
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('daily_update.log', encoding='utf-8')
    ]
)

def run_script(script_name, description):
    """
    执行脚本并记录结果
    """
    print(f"\n{'='*60}")
    print(f"🚀 开始执行: {description}")
    print(f"{'='*60}")
    
    try:
        # 在GitHub Actions环境中确保使用正确的Python路径
        python_cmd = sys.executable
        result = subprocess.run([python_cmd, script_name], 
                              capture_output=True, text=True, encoding='utf-8',
                              timeout=1800)  # 30分钟超时
        
        if result.returncode == 0:
            print(f"✅ {description} 执行成功")
            if result.stdout:
                print("输出:")
                print(result.stdout)
            logging.info(f"{description} 执行成功")
            return True
        else:
            print(f"❌ {description} 执行失败")
            if result.stderr:
                print("错误信息:")
                print(result.stderr)
            logging.error(f"{description} 执行失败: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ {description} 执行超时")
        logging.error(f"{description} 执行超时")
        return False
    except Exception as e:
        print(f"❌ 执行 {description} 时发生异常: {e}")
        logging.error(f"执行 {description} 时发生异常: {e}")
        return False

def check_environment():
    """
    检查运行环境
    """
    print("🔍 检查运行环境...")
    
    # 检查是否在GitHub Actions中运行
    is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
    if is_github_actions:
        print("📍 运行环境: GitHub Actions")
        print(f"📂 工作目录: {os.getcwd()}")
        print(f"🐍 Python版本: {sys.version}")
    else:
        print("📍 运行环境: 本地")
    
    # 检查必要文件
    required_files = [
        "生成累积新闻.py",
        "生成累积RSS.py",
        "RSS feed URL/rss_feed_url.json",
        "src/rss_read.py",
        "src/load_rss_url.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 缺少必要文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    print("✅ 环境检查通过")
    return True

def create_github_pages_structure():
    """
    创建GitHub Pages需要的目录结构
    """
    print("📁 创建GitHub Pages目录结构...")
    
    # 确保feed目录存在
    if not os.path.exists('feed'):
        os.makedirs('feed')
        print("   ✅ 创建feed目录")
    
    # 确保cumulative_news目录存在
    if not os.path.exists('cumulative_news'):
        os.makedirs('cumulative_news')
        print("   ✅ 创建cumulative_news目录")
    
    # 创建简单的index.html
    index_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Free News Agent - RSS订阅源</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .rss-link { display: block; margin: 10px 0; padding: 10px; background: #f0f0f0; border-radius: 5px; text-decoration: none; color: #333; }
        .rss-link:hover { background: #e0e0e0; }
        .last-update { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>🔄 Free News Agent RSS订阅源</h1>
    <p class="last-update">最后更新: LAST_UPDATE_TIME</p>
    
    <h2>📡 RSS订阅地址</h2>
    <div id="rss-links">
        <!-- RSS链接将在这里动态生成 -->
    </div>
    
    <h2>📚 说明</h2>
    <ul>
        <li>RSS源每天自动更新</li>
        <li>包含累积的历史新闻</li>
        <li>支持各大RSS阅读器</li>
    </ul>
</body>
</html>"""
    
    # 替换更新时间
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    index_content = index_content.replace('LAST_UPDATE_TIME', current_time)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print("   ✅ 创建index.html")

def main():
    """
    主函数：执行每日更新流程
    """
    start_time = datetime.now()
    print("=" * 60)
    print("🕐 每日新闻更新流程开始")
    print("=" * 60)
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查环境
    if not check_environment():
        print("❌ 环境检查失败，终止执行")
        return False
    
    # 创建GitHub Pages结构
    create_github_pages_structure()
    
    success_count = 0
    total_tasks = 2
    
    # 步骤1: 更新累积新闻
    print(f"\n📝 步骤1/{total_tasks}: 更新累积新闻")
    if run_script("生成累积新闻.py", "更新累积新闻"):
        success_count += 1
    
    # 步骤2: 生成累积RSS Feed
    print(f"\n📡 步骤2/{total_tasks}: 生成累积RSS Feed")
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
        
        # 检查生成的RSS文件
        if os.path.exists('feed'):
            rss_files = [f for f in os.listdir('feed') if f.endswith('.xml')]
            print(f"\n📡 生成的RSS文件 ({len(rss_files)}个):")
            for rss_file in rss_files:
                file_size = os.path.getsize(os.path.join('feed', rss_file))
                print(f"   - {rss_file} ({file_size:,} bytes)")
        
        # GitHub Actions环境提示
        if os.getenv('GITHUB_ACTIONS') == 'true':
            repo_name = os.getenv('GITHUB_REPOSITORY', 'your-username/News-Agent')
            base_url = f"https://{repo_name.split('/')[0]}.github.io/{repo_name.split('/')[1]}"
            print(f"\n🌐 GitHub Pages URL: {base_url}")
            print(f"📡 RSS订阅基础地址: {base_url}/feed/")
        
        logging.info("每日更新任务完成")
        return True
    else:
        print("⚠️ 部分任务执行失败，请检查错误信息")
        logging.error("每日更新任务失败")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ 用户中断执行")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行过程中发生未预期的错误: {e}")
        logging.error(f"执行过程中发生未预期的错误: {e}")
        sys.exit(1)
        