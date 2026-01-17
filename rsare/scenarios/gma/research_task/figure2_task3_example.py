"""
图2.3任务完整调用流程示例

任务：北非/南亚/东南亚沿岸不可见活动强度更高海域

"""

from rsare.apps.gma.tools_list import SARTools
from rsare.scenarios.gma.research_task.common_step import load_detect_tiles, load_env_tiles


def run_figure2_task3_example():
    """
    执行图2.3任务的完整流程
    
    任务：识别北非/南亚/东南亚沿岸不可见活动强度更高的海域
    """
    
    tools = SARTools()
    
    print("=" * 80)
    print("图2.3任务：北非/南亚/东南亚沿岸不可见活动强度更高海域")
    print("=" * 80)
    
    date_start = "2019-08-01"
    date_end = "2019-08-31"
    regions = {
        "north_africa": [-10.0, 20.0, 35.0, 37.0],  # [lon_min, lat_min, lon_max, lat_max]
        "south_asia": [60.0, 5.0, 100.0, 30.0],
        "southeast_asia": [95.0, -10.0, 145.0, 25.0],
    }
    for region in regions:
        # 运行共同阶段（A-E）
        load_detect_tiles(date_start, date_end, region=region, tools=tools)
    # 阶段B：船舶长度和存在性预测

    result1 = tools.vessel_presence_length_estimation(tile_width=80, tile_height=80)
    print(f"✓ {result1}")

    for region in regions:
        load_env_tiles(date_end, date_start, region, tools)

    result1 = tools.fishing_nonfishing_classification(tile_weidth=100, tile_height=100)
    print(f"✓ {result1}")

    # 阶段E：EEZ空间关联
    # result1 = tools.load_eez_data()
    # print(f"✓ {result1}")
    # ========================================================================
    # 阶段F：区域空间裁剪和网格化
    # ========================================================================
    print("\n[阶段F] 区域空间裁剪和网格化")
    print("-" * 80)

    #
    # result = tools.identify_regional_dark_activity_hotspots(
    #     date_start=date_start,
    #     date_end=date_end,
    #     regions=regions,
    #     scale_deg=0.1,  # 0.1度网格
    #     top_percentile=10.0,  # Top 10%作为热点
    # )
    # print(f"✓ {result}")
    
    # ========================================================================
    # 阶段G：识别热点
    # ========================================================================
    print("\n[阶段G] 识别热点区域")
    print("-" * 80)
    
    # 从state中获取结果
    tiles_info = tools.state.tiles_info
    if tiles_info:
        key = f"regional_hotspots_{date_start}_{date_end}"
        if key in tiles_info:
            regions_data = tiles_info[key]["regions"]
            
            print(f"✓ 分析完成")
            print(f"\n  各区域热点统计：")
            
            for region_name, region_data in regions_data.items():
                hotspots = region_data["hotspots"]
                grid = region_data["grid"]
                
                print(f"\n  {region_name.upper()}：")
                print(f"    - 总网格数：{len(grid)}")
                print(f"    - 热点数量：{len(hotspots)}")
                print(f"    - 热点阈值：{region_data['threshold']:.6f} 活动/km²")
                
                if len(hotspots) > 0:
                    print(f"    - 最高密度：{hotspots['density_km2'].max():.6f} 活动/km²")
                    print(f"    - 平均密度：{hotspots['density_km2'].mean():.6f} 活动/km²")
                    
                    # 显示Top 5热点
                    top5 = hotspots.nlargest(5, "density_km2")
                    print(f"\n    Top 5 热点位置：")
                    for idx, row in top5.iterrows():
                        lon_center = (row["lon_idx"] + 0.5) * 0.1
                        lat_center = row["lat_center"]
                        print(f"      - 纬度 {lat_center:.2f}°, 经度 {lon_center:.2f}°: "
                              f"密度 {row['density_km2']:.6f} 活动/km², "
                              f"活动量 {row['dark_activity']:.2f}")
            
            # 跨区域比较
            print(f"\n  跨区域比较：")
            all_hotspots = []
            for region_name, region_data in regions_data.items():
                hotspots = region_data["hotspots"].copy()
                hotspots["region"] = region_name
                all_hotspots.append(hotspots)
            
            if all_hotspots:
                import pandas as pd
                combined = pd.concat(all_hotspots, ignore_index=True)
                top_global = combined.nlargest(10, "density_km2")
                
                print(f"    全球Top 10 热点：")
                for idx, row in top_global.iterrows():
                    lon_center = (row["lon_idx"] + 0.5) * 0.1
                    lat_center = row["lat_center"]
                    print(f"      {idx+1}. {row['region']}: "
                          f"纬度 {lat_center:.2f}°, 经度 {lon_center:.2f}°, "
                          f"密度 {row['density_km2']:.6f} 活动/km²")
        else:
            print("⚠ 未找到区域热点分析结果")
    else:
        print("⚠ tiles_info为空")
    
    print("\n" + "=" * 80)
    print("任务完成总结")
    print("=" * 80)
    print(f"总检测数：{len(tools.state.vessel_detections)}")
    print(f"已完成阶段：{', '.join(sorted([s.value for s in tools.state.stages_completed]))}")
    
    return tools


if __name__ == "__main__":
    tools = run_figure2_task3_example()
