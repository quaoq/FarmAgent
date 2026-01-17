"""
图2.2任务完整调用流程示例

任务：中国沿海与邻近海域渔业不可见性与离岸距离关系
"""


from rsare.apps.gma.tools_list import SARTools
from rsare.scenarios.gma.research_task.common_step import load_detect_tiles, load_env_tiles


def run_figure2_task2_example():
    """
    执行图2.2任务的完整流程
    
    任务：分析中国沿海与邻近海域渔业不可见性与离岸距离的关系
    """
    
    tools = SARTools()
    
    print("=" * 80)
    print("图2.2任务：中国沿海与邻近海域渔业不可见性与离岸距离关系")
    print("=" * 80)
    
    date_start = "2019-08-01"
    date_end = "2019-08-31"
    # 中国EEZ及邻近海域
    region = [105.0, 15.0, 125.0, 45.0]  # [lon_min, lat_min, lon_max, lat_max]

    load_detect_tiles(date_start, date_end, region=region, tools=tools)
    # 阶段B：船舶长度和存在性预测

    result1 = tools.vessel_presence_length_estimation(tile_width=80, tile_height=80)
    print(f"✓ {result1}")

    load_env_tiles(date_end, date_start, region, tools)

    result1 = tools.fishing_nonfishing_classification(tile_weidth=100, tile_height=100)
    print(f"✓ {result1}")

    # 阶段E：EEZ空间关联
    # result1 = tools.load_eez_data()
    # print(f"✓ {result1}")
    
    # ========================================================================
    # 阶段F：按离岸距离分析
    # ========================================================================
    print("\n[阶段F] 按离岸距离分析")
    print("-" * 80)
    

    # result = tools.analyze_fishing_visibility_by_offshore_distance(
    #     date_start=date_start,
    #     date_end=date_end,
    #     region=region,
    #     eez_filter="CHN",  # 可选：只分析中国EEZ
    #     distance_bin_size_km=5.0,  # 每5km一个区间
    #     max_distance_km=200.0,  # 最大分析距离200km
    # )
    # print(f"✓ {result}")
    
    # ========================================================================
    # 阶段G：统计分析
    # ========================================================================
    print("\n[阶段G] 统计分析：不同距离段的不可见性模式")
    print("-" * 80)
    
    # 从state中获取结果
    tiles_info = tools.state.tiles_info
    if tiles_info:
        key = f"offshore_distance_visibility_{date_start}_{date_end}"
        if key in tiles_info:
            distance_analysis = tiles_info[key]["distance_analysis"]
            
            # 定义距离段
            near_shore = distance_analysis[distance_analysis["distance_bin"] <= 20]
            mid_distance = distance_analysis[
                (distance_analysis["distance_bin"] > 20) & 
                (distance_analysis["distance_bin"] <= 50)
            ]
            far_distance = distance_analysis[
                (distance_analysis["distance_bin"] > 50) & 
                (distance_analysis["distance_bin"] <= 200)
            ]
            
            print(f"✓ 分析完成")
            print(f"\n  不同距离段的不可见性统计：")
            
            if len(near_shore) > 0:
                near_shore_mean = near_shore["dark_pct"].mean()
                print(f"    - 近岸（0-20km）：平均不可见性 {near_shore_mean:.2f}%")
                print(f"      区间数：{len(near_shore)}, "
                      f"总渔业活动：{near_shore['total_fishing'].sum():.2f}")
            
            if len(mid_distance) > 0:
                mid_mean = mid_distance["dark_pct"].mean()
                print(f"    - 中距离（20-50km）：平均不可见性 {mid_mean:.2f}%")
                print(f"      区间数：{len(mid_distance)}, "
                      f"总渔业活动：{mid_distance['total_fishing'].sum():.2f}")
            
            if len(far_distance) > 0:
                far_mean = far_distance["dark_pct"].mean()
                print(f"    - 远距离（50-200km）：平均不可见性 {far_mean:.2f}%")
                print(f"      区间数：{len(far_distance)}, "
                      f"总渔业活动：{far_distance['total_fishing'].sum():.2f}")
            
            # 显示关键距离点（12海里≈22km，200海里≈370km）
            print(f"\n  关键距离点分析：")
            key_distances = [12, 22, 200]  # 12海里、22km、200海里
            for dist in key_distances:
                closest_bin = distance_analysis[
                    abs(distance_analysis["distance_bin"] - dist) == 
                    abs(distance_analysis["distance_bin"] - dist).min()
                ]
                if len(closest_bin) > 0:
                    row = closest_bin.iloc[0]
                    print(f"    - {dist}km附近：不可见性 {row['dark_pct']:.2f}%")
            
            # 显示前10个距离区间的详细数据
            print(f"\n  前10个距离区间的详细数据：")
            for idx, row in distance_analysis.head(10).iterrows():
                print(f"    - {row['distance_bin']:.0f}km: "
                      f"不可见性 {row['dark_pct']:.2f}%, "
                      f"总渔业活动 {row['total_fishing']:.2f}, "
                      f"检测数 {row['n_detections']}")
        else:
            print("⚠ 未找到离岸距离分析结果")
    else:
        print("⚠ tiles_info为空")
    
    print("\n" + "=" * 80)
    print("任务完成总结")
    print("=" * 80)
    print(f"总检测数：{len(tools.state.vessel_detections)}")
    print(f"已完成阶段：{', '.join(sorted([s.value for s in tools.state.stages_completed]))}")
    
    return tools


if __name__ == "__main__":
    tools = run_figure2_task2_example()
