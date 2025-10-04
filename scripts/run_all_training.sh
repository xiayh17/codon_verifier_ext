#!/bin/bash
# 一键运行所有训练方案的脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo "模型训练 - 完整流程"
echo -e "==========================================${NC}"
echo ""

# 切换到项目目录
cd "$(dirname "$0")/.."

# 检查数据文件
echo -e "${BLUE}检查数据文件...${NC}"
if [ ! -f "data/converted/merged_dataset.jsonl" ]; then
    echo -e "${RED}❌ 错误: 数据文件不存在: data/converted/merged_dataset.jsonl${NC}"
    exit 1
fi

FILE_SIZE=$(du -h data/converted/merged_dataset.jsonl | cut -f1)
LINE_COUNT=$(wc -l < data/converted/merged_dataset.jsonl)
echo -e "${GREEN}✓ 数据文件存在${NC}"
echo "  文件大小: $FILE_SIZE"
echo "  样本数量: $LINE_COUNT"
echo ""

# 询问用户要运行哪些训练
echo -e "${YELLOW}请选择要运行的训练方案:${NC}"
echo "  1) 快速测试 (1-2分钟, 1000样本)"
echo "  2) 平衡训练 (5-10分钟, 15000样本) [推荐]"
echo "  3) 主要宿主 (8-15分钟, 15000样本)"
echo "  4) 宿主特定 (10-20分钟, 每个宿主独立模型)"
echo "  5) 完整训练 (15-30分钟, 52158样本)"
echo "  6) 全部运行 (按顺序运行1-5)"
echo ""
read -p "请输入选项 (1-6): " choice

COMPOSE_FILE="docker-compose.microservices.yml"

# 函数：运行单个训练任务
run_training() {
    local config_file=$1
    local description=$2
    
    echo ""
    echo -e "${BLUE}=========================================="
    echo "$description"
    echo -e "==========================================${NC}"
    echo ""
    echo "配置文件: $config_file"
    echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    start_time=$(date +%s)
    
    if docker-compose -f "$COMPOSE_FILE" run --rm training \
        --input "/data/input/$config_file"; then
        
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        
        echo ""
        echo -e "${GREEN}✓ 训练完成${NC}"
        echo "用时: ${duration}秒"
        
        # 显示结果文件
        result_file="data/output/training/${config_file%.json}_result.json"
        if [ -f "$result_file" ]; then
            echo ""
            echo "训练指标:"
            python3 -c "
import json
try:
    with open('$result_file', 'r') as f:
        data = json.load(f)
    metrics = data.get('output', {}).get('metrics', {})
    print(f\"  样本数: {metrics.get('n_samples', 'N/A')}\"  )
    print(f\"  特征数: {metrics.get('n_features', 'N/A')}\")
    print(f\"  R²分数: {metrics.get('r2_mu', 'N/A'):.4f}\" if isinstance(metrics.get('r2_mu'), (int, float)) else f\"  R²分数: {metrics.get('r2_mu', 'N/A')}\")
    print(f\"  MAE: {metrics.get('mae_mu', 'N/A'):.4f}\" if isinstance(metrics.get('mae_mu'), (int, float)) else f\"  MAE: {metrics.get('mae_mu', 'N/A')}\")
    host_dist = metrics.get('host_distribution', {})
    if host_dist:
        print('  宿主分布:')
        for host, count in host_dist.items():
            print(f\"    {host}: {count}\")
except Exception as e:
    print(f'无法解析结果: {e}')
" || echo "  (结果文件解析失败)"
        fi
        echo ""
        return 0
    else
        echo ""
        echo -e "${RED}❌ 训练失败${NC}"
        echo ""
        return 1
    fi
}

# 根据用户选择运行训练
case $choice in
    1)
        run_training "training_real_quick.json" "方案1: 快速测试"
        ;;
    2)
        run_training "training_real_balanced.json" "方案2: 平衡训练"
        ;;
    3)
        run_training "training_real_main_hosts.json" "方案3: 主要宿主训练"
        ;;
    4)
        run_training "training_real_host_specific.json" "方案4: 宿主特定模型"
        ;;
    5)
        run_training "training_real_full.json" "方案5: 完整训练"
        ;;
    6)
        echo -e "${YELLOW}将按顺序运行所有训练方案...${NC}"
        echo ""
        
        run_training "training_real_quick.json" "方案1: 快速测试"
        run_training "training_real_balanced.json" "方案2: 平衡训练"
        run_training "training_real_main_hosts.json" "方案3: 主要宿主训练"
        run_training "training_real_host_specific.json" "方案4: 宿主特定模型"
        run_training "training_real_full.json" "方案5: 完整训练"
        ;;
    *)
        echo -e "${RED}无效的选项: $choice${NC}"
        exit 1
        ;;
esac

# 显示所有训练结果
echo ""
echo -e "${BLUE}=========================================="
echo "训练完成 - 结果汇总"
echo -e "==========================================${NC}"
echo ""

echo "训练日志:"
ls -lh data/output/training/*.json 2>/dev/null || echo "  (无日志文件)"
echo ""

echo "训练模型:"
find data/output/models -name "*.pkl" -exec ls -lh {} \; 2>/dev/null || echo "  (无模型文件)"
echo ""

echo -e "${GREEN}✅ 所有训练任务完成！${NC}"
echo ""
echo "下一步:"
echo "  1. 查看训练结果: cat data/output/training/*_result.json | python3 -m json.tool"
echo "  2. 列出训练模型: ls -lh data/output/models/"
echo "  3. 使用模型进行预测或集成到其他服务"
echo ""

