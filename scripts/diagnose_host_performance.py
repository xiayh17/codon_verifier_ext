#!/usr/bin/env python3
"""
分宿主性能诊断脚本
用于分析训练好的模型在各个宿主上的表现
"""

import argparse
import json
import sys
import numpy as np
from pathlib import Path
from collections import defaultdict
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from codon_verifier.surrogate import SurrogateModel, build_feature_vector
from codon_verifier.hosts.tables import HOST_TABLES
from codon_verifier.data_loader import DataLoader, DataConfig


def diagnose_model(model_path: str, data_path: str, output_path: str = None):
    """
    诊断模型在各宿主上的性能
    """
    print(f"加载模型: {model_path}")
    model = SurrogateModel.load(model_path)
    
    print(f"加载数据: {data_path}")
    loader = DataLoader(DataConfig())
    records = loader.load_and_mix([data_path], target_hosts=None, total_samples=None)
    
    print(f"总样本数: {len(records)}")
    
    # 按宿主分组
    host_records = defaultdict(list)
    for r in records:
        host = r.get('host', 'unknown')
        host_records[host].append(r)
    
    print(f"\n宿主分布:")
    for host, recs in sorted(host_records.items(), key=lambda x: -len(x[1])):
        print(f"  {host:20s}: {len(recs):6d} 样本")
    
    # 分宿主评估
    results = {}
    print(f"\n{'='*70}")
    print("分宿主性能评估")
    print(f"{'='*70}")
    
    for host in sorted(host_records.keys()):
        recs = host_records[host]
        if len(recs) < 10:
            print(f"\n{host}: 样本太少 ({len(recs)}), 跳过")
            continue
        
        print(f"\n{host} ({len(recs)} 样本)")
        print("-" * 70)
        
        # 获取宿主表
        if host not in HOST_TABLES:
            print(f"  ⚠️  无宿主表，跳过")
            continue
        
        usage, trna_w = HOST_TABLES[host]
        
        # 构建特征和目标
        X = []
        y_true = []
        for r in recs:
            try:
                dna = r['sequence']
                extra = r.get('extra_features')
                vec, _ = build_feature_vector(dna, usage, trna_w=trna_w, extra_features=extra)
                X.append(vec)
                
                expr = r.get('expression', {})
                y_val = float(expr.get('value', 0) if isinstance(expr, dict) else expr)
                y_true.append(y_val)
            except Exception as e:
                continue
        
        if len(y_true) < 10:
            print(f"  ⚠️  有效样本太少 ({len(y_true)}), 跳过")
            continue
        
        X = np.vstack(X)
        y_true = np.array(y_true)
        
        # 预测
        mu_pred, sigma_pred = model.predict_mu_sigma(X)
        
        # 计算指标
        r2 = r2_score(y_true, mu_pred)
        mae = mean_absolute_error(y_true, mu_pred)
        rmse = np.sqrt(mean_squared_error(y_true, mu_pred))
        
        # 统计信息
        y_mean = np.mean(y_true)
        y_std = np.std(y_true)
        pred_mean = np.mean(mu_pred)
        pred_std = np.std(mu_pred)
        
        print(f"  R² 分数:     {r2:8.4f}")
        print(f"  MAE:         {mae:8.2f}")
        print(f"  RMSE:        {rmse:8.2f}")
        print(f"  真实值均值:  {y_mean:8.2f} ± {y_std:.2f}")
        print(f"  预测值均值:  {pred_mean:8.2f} ± {pred_std:.2f}")
        print(f"  Sigma均值:   {np.mean(sigma_pred):8.2f}")
        
        results[host] = {
            'n_samples': len(y_true),
            'r2': float(r2),
            'mae': float(mae),
            'rmse': float(rmse),
            'y_mean': float(y_mean),
            'y_std': float(y_std),
            'pred_mean': float(pred_mean),
            'pred_std': float(pred_std),
            'sigma_mean': float(np.mean(sigma_pred))
        }
    
    # 总结
    print(f"\n{'='*70}")
    print("性能总结")
    print(f"{'='*70}")
    print(f"{'宿主':<20s} {'样本数':>8s} {'R²':>8s} {'MAE':>8s} {'RMSE':>8s}")
    print("-" * 70)
    
    for host in sorted(results.keys()):
        r = results[host]
        print(f"{host:<20s} {r['n_samples']:>8d} {r['r2']:>8.4f} {r['mae']:>8.2f} {r['rmse']:>8.2f}")
    
    # 保存结果
    if output_path:
        output_data = {
            'model_path': model_path,
            'data_path': data_path,
            'host_results': results,
            'summary': {
                'avg_r2': float(np.mean([r['r2'] for r in results.values()])),
                'avg_mae': float(np.mean([r['mae'] for r in results.values()])),
                'avg_rmse': float(np.mean([r['rmse'] for r in results.values()])),
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n结果已保存到: {output_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description='分宿主性能诊断')
    parser.add_argument('--model', required=True, help='训练好的模型路径 (.pkl)')
    parser.add_argument('--data', required=True, help='数据文件路径 (.jsonl)')
    parser.add_argument('--output', help='输出结果JSON路径（可选）')
    
    args = parser.parse_args()
    
    try:
        diagnose_model(args.model, args.data, args.output)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

