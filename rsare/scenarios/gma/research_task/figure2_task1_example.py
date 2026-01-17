"""
图2.1任务完整调用流程示例

任务：东亚近海（黄海—朝鲜半岛周边海域）渔业不可见性与距离EEZ边界关系

"""

from rsare.apps.gma.tools_list import SARTools
from rsare.scenarios.gma.research_task.common_step import load_detect_tiles, load_env_tiles


def run_figure2_task1_example():
    """
    执行图2.1任务的完整流程
    
    任务：分析东亚近海渔业不可见性与距离EEZ边界的关系
    """
    
    tools = SARTools()
    
    print("=" * 80)
    print("图2.1任务：东亚近海渔业不可见性与距离EEZ边界关系")
    print("=" * 80)
    
    date_start = "2019-08-01"
    date_end = "2019-08-31"
    region = [120.0, 35.0, 130.0, 42.0]  # [lon_min, lat_min, lon_max, lat_max]

    load_detect_tiles(date_start, date_end,region=region, tools=tools)
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
    # 阶段F：空间裁剪和距离分析
    # ========================================================================
    print("\n[阶段F] 空间裁剪和距离分析")
    print("-" * 80)
    
    # 黄海—朝鲜半岛周边海域

    # result = tools.analyze_fishing_visibility_by_eez_distance(
    #     date_start=date_start,
    #     date_end=date_end,
    #     region=region,
    #     distance_bin_size_km=10.0,  # 每10km一个区间
    # )
    # print(f"✓ {result}")
    
    # ========================================================================
    # 阶段G：相关性分析
    # ========================================================================
    print("\n[阶段G] 相关性分析")
    print("-" * 80)
    
    # 从state中获取结果
    tiles_info = tools.state.tiles_info
    if tiles_info:
        key = f"eez_distance_visibility_{date_start}_{date_end}"
        if key in tiles_info:
            distance_analysis = tiles_info[key]["distance_analysis"]
            
            import numpy as np
            
            # 计算Pearson相关系数
            valid_data = distance_analysis[distance_analysis["total_fishing"] > 0]
            if len(valid_data) > 1:
                correlation = np.corrcoef(
                    valid_data["distance_bin"],
                    valid_data["dark_pct"]
                )[0, 1]
                
                print(f"✓ 分析完成")
                print(f"\n  距离区间分析结果：")
                print(f"    - 总距离区间数：{len(distance_analysis)}")
                print(f"    - 有效数据区间数：{len(valid_data)}")
                print(f"    - Pearson相关系数（距离 vs 不可见性）：{correlation:.3f}")
                
                # 显示各距离区间的统计
                print(f"\n  各距离区间不可见性统计：")
                for idx, row in valid_data.head(10).iterrows():
                    print(f"    - {row['distance_bin']:.0f}km: "
                          f"不可见性 {row['dark_pct']:.2f}%, "
                          f"总渔业活动 {row['total_fishing']:.2f}, "
                          f"检测数 {row['n_detections']}")
                
                # 识别关键距离阈值（不可见性显著变化的点）
                if len(valid_data) > 2:
                    # 计算变化率
                    valid_data = valid_data.sort_values("distance_bin")
                    valid_data["dark_pct_change"] = valid_data["dark_pct"].diff()
                    
                    # 找出变化最大的点
                    max_change_idx = valid_data["dark_pct_change"].abs().idxmax()
                    max_change_row = valid_data.loc[max_change_idx]
                    
                    print(f"\n  关键距离阈值：")
                    print(f"    - 最大变化点：{max_change_row['distance_bin']:.0f}km")
                    print(f"    - 变化幅度：{max_change_row['dark_pct_change']:.2f}%")
            else:
                print("⚠ 有效数据不足，无法进行相关性分析")
        else:
            print("⚠ 未找到距离分析结果")
    else:
        print("⚠ tiles_info为空")
    
    print("\n" + "=" * 80)
    print("任务完成总结")
    print("=" * 80)
    print(f"总检测数：{len(tools.state.vessel_detections)}")
    print(f"已完成阶段：{', '.join(sorted([s.value for s in tools.state.stages_completed]))}")
    
    return tools


if __name__ == "__main__":
    tools = run_figure2_task1_example()
