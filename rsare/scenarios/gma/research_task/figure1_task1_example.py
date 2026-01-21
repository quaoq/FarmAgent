"""
图1.1任务完整调用流程示例

任务：识别2018年8月全球海域中"公开可追踪船舶活动"最密集的区域与最稀疏的区域

"""

from rsare.apps.gma.tools_list import SARTools
from rsare.scenarios.gma.research_task.common_step import load_env_tiles, load_detect_tiles


def run_figure1_task1_example():
    """
    执行图1.1任务的完整流程
    
    工作流阶段：
    A. 原始SAR检测（CFAR）
    B. 船舶长度和存在性预测
    C. AIS匹配
    D. 捕鱼/非捕鱼分类
    E. EEZ空间关联
    F. 网格聚合和密度计算
    G. 识别最密集和最稀疏区域
    """
    
    # 初始化工具系统
    tools = SARTools()

    print("=" * 80)
    print("图1.1任务：识别2018年8月公开可追踪船舶活动最密集/稀疏区域")
    print("=" * 80)
    date_start = "2018-08-01"
    date_end = "2018-08-31"
    region = [-180.0, -90.0, 180.0, 90.0]  # 全球范围
    load_detect_tiles(date_start, date_end, region, tools)

    # ========================================================================
    # 阶段B：船舶长度和存在性预测
    # ========================================================================
    print("\n[阶段B] 船舶长度和存在性预测")
    print("-" * 80)
    
    # B.2: 模型推理（ResNet预测presence和length）
    result = tools.vessel_presence_length_estimation(
        tile_width=80,
        tile_height=80,
    )
    print(f"✓ {result}")
    
    # ========================================================================
    # 阶段C：AIS匹配
    # ========================================================================
    print("\n[阶段C] AIS匹配")
    print("-" * 80)

    load_env_tiles(date_start, date_end,region, tools)
    # D.10: 捕鱼/非捕鱼分类（ConvNeXt模型）
    result = tools.fishing_nonfishing_classification(
        tile_width=100,
        tile_height=100,
    )
    print(f"✓ {result}")
    
    # ========================================================================
    # 阶段E：EEZ空间关联
    # ========================================================================
    print("\n[阶段E] EEZ空间关联")
    print("-" * 80)
    
    # # E.1: 加载EEZ数据
    # result = tools.load_eez_data()
    # print(f"✓ {result}")
    
    # 注意：在离线模拟中，EEZ关联可能已经在CSV数据中完成
    # 在真实实现中，这里会执行ST_CONTAINS空间连接
    
    # ========================================================================
    # 阶段F：网格聚合和密度计算
    # ========================================================================
    print("\n[阶段F] 网格聚合和密度计算")
    print("-" * 80)
    
    # F.1: 按网格聚合公开可追踪活动（tracked = matched vessels）
    result = tools.aggregate_detections_by_grid(
        date_start="2018-08-01",
        date_end="2018-08-31",
        scale_deg=0.1,  # 论文Methods中使用的0.1度网格
        activity_type="tracked",  # 只统计匹配的船舶（公开可追踪）
        normalize_by_overpasses=True,  # 按过境次数归一化
    )
    print(f"✓ {result}")
    
    # ========================================================================
    # 阶段G：识别最密集和最稀疏区域
    # ========================================================================
    print("\n[阶段G] 识别最密集和最稀疏区域")
    print("-" * 80)
    
    # 从state中获取网格聚合结果
    tiles_info = tools.state.tiles_info
    if tiles_info:
        key = "grid_tracked_2018-08-01_2018-08-31"
        if key in tiles_info:
            grid_data = tiles_info[key]["grid"]
            
            # 排序找出最密集和最稀疏
            sorted_grid = grid_data.sort_values("density_km2", ascending=False)
            
            # Top 10% 最密集
            top_10_pct = int(len(sorted_grid) * 0.1)
            top_dense = sorted_grid.head(max(1, top_10_pct))
            
            # Bottom 10% 最稀疏（排除零值）
            non_zero = sorted_grid[sorted_grid["density_km2"] > 0]
            bottom_10_pct = int(len(non_zero) * 0.1)
            bottom_sparse = non_zero.tail(max(1, bottom_10_pct))
            
            print(f"✓ 最密集区域（Top 10%）：{len(top_dense)} 个网格单元")
            print(f"  最高密度：{top_dense['density_km2'].max():.6f} 活动/km²")
            print(f"  位置示例：")
            for idx, row in top_dense.head(3).iterrows():
                print(f"    - 纬度 {row['lat_center']:.2f}°, 经度 {row['lon_idx']*0.1:.2f}°, "
                      f"密度 {row['density_km2']:.6f} 活动/km²")
            
            print(f"\n✓ 最稀疏区域（Bottom 10%，非零）：{len(bottom_sparse)} 个网格单元")
            print(f"  最低密度：{bottom_sparse['density_km2'].min():.6f} 活动/km²")
            print(f"  位置示例：")
            for idx, row in bottom_sparse.head(3).iterrows():
                print(f"    - 纬度 {row['lat_center']:.2f}°, 经度 {row['lon_idx']*0.1:.2f}°, "
                      f"密度 {row['density_km2']:.6f} 活动/km²")
        else:
            print("⚠ 未找到网格聚合结果，请检查aggregate_detections_by_grid是否成功执行")
    else:
        print("⚠ tiles_info为空，请检查前面的步骤是否成功执行")
    
    # ========================================================================
    # 总结
    # ========================================================================
    print("\n" + "=" * 80)
    print("任务完成总结")
    print("=" * 80)
    print(f"总检测数：{len(tools.state.vessel_detections)}")
    print(f"已处理场景数：{len(tools.state.scenes)}")
    print(f"已完成阶段：{', '.join(sorted([s.value for s in tools.state.stages_completed]))}")
    
    return tools


if __name__ == "__main__":
    # 运行示例
    tools = run_figure1_task1_example()
    
    # 可选：保存结果到文件
    # import pickle
    # with open("figure1_task1_results.pkl", "wb") as f:
    #     pickle.dump(tools.state, f)
    # print("\n结果已保存到 figure1_task1_results.pkl")
