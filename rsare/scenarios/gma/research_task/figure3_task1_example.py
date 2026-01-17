"""
图3.1任务完整调用流程示例

任务：2020年较2018–2019年渔业与运输/能源活动变化幅度比较

"""

from rsare.apps.gma.tools_list import SARTools
from rsare.scenarios.gma.research_task.common_step import load_detect_tiles, load_env_tiles

def run_figure3_task1_example():
    """
    执行图3.1任务的完整流程
    
    任务：比较2020年较2018–2019年渔业与运输/能源活动变化幅度
    """
    
    tools = SARTools()
    
    print("=" * 80)
    print("图3.1任务：2020年较2018–2019年活动变化幅度比较")
    print("=" * 80)

    # 运行共同阶段（A-E）- 需要加载2018-2020年的数据
    print("\n[加载数据] 加载2018-2020年的数据")
    print("-" * 80)
    
    # 加载2018-2020年的SAR场景
    date_start = "2018-01-01"
    date_end = "2020-12-31"
    region = [-180.0, -90.0, 180.0, 90.0]
    load_detect_tiles(date_start=date_start, date_end=date_end, region=region, tools=tools)
    
    result = tools.vessel_presence_length_estimation(tile_width=80, tile_height=80)
    print(f"✓ {result}")
    
    load_env_tiles(date_start=date_start, date_end=date_end, region=region, tools=tools)
    
    result = tools.fishing_nonfishing_classification(tile_weidth=100, tile_height=100)
    print(f"✓ {result}")
    
    # result = tools.load_eez_data()
    # print(f"✓ {result}")
    
    # ========================================================================
    # 阶段G：计算变化幅度
    # ========================================================================
    print("\n[阶段G] 计算活动变化幅度")
    print("-" * 80)
    
    # # 计算渔业活动变化
    # result_fishing = tools.compute_activity_change_over_time(
    #     baseline_start=date_start,
    #     baseline_end="2019-12-31",
    #     comparison_start="2020-01-01",
    #     comparison_end=date_end,
    #     activity_type="fishing",
    # )
    # print(f"✓ 渔业活动：{result_fishing}")
    
    # # 计算非渔业活动变化
    # result_nonfishing = tools.compute_activity_change_over_time(
    #     baseline_start=date_start,
    #     baseline_end="2019-12-31",
    #     comparison_start="2020-01-01",
    #     comparison_end=date_end,
    #     activity_type="nonfishing",
    # )
    # print(f"✓ 非渔业活动：{result_nonfishing}")
    
    # ========================================================================
    # 阶段H：比较变化幅度
    # ========================================================================
    print("\n[阶段H] 比较变化幅度")
    print("-" * 80)
    
    # 从state中获取结果
    tiles_info = tools.state.tiles_info
    if tiles_info:
        fishing_key = "activity_change_fishing_2018-01-01_2020-01-01"
        nonfishing_key = "activity_change_nonfishing_2018-01-01_2020-01-01"
        
        fishing_data = tiles_info.get(fishing_key)
        nonfishing_data = tiles_info.get(nonfishing_key)
        
        if fishing_data and nonfishing_data:
            print(f"✓ 比较完成")
            print(f"\n  变化幅度对比：")
            print(f"    渔业活动：")
            print(f"      - 基准期均值：{fishing_data['baseline_mean']:.2f}")
            print(f"      - 2020年均值：{fishing_data['comparison_mean']:.2f}")
            print(f"      - 变化百分比：{fishing_data['change_pct']:.2f}%")
            print(f"      - 绝对变化：{fishing_data['abs_change_pct']:.2f}%")
            
            print(f"\n    非渔业活动：")
            print(f"      - 基准期均值：{nonfishing_data['baseline_mean']:.2f}")
            print(f"      - 2020年均值：{nonfishing_data['comparison_mean']:.2f}")
            print(f"      - 变化百分比：{nonfishing_data['change_pct']:.2f}%")
            print(f"      - 绝对变化：{nonfishing_data['abs_change_pct']:.2f}%")
            
            # 比较哪个变化更大
            if fishing_data['abs_change_pct'] > nonfishing_data['abs_change_pct']:
                print(f"\n  ✓ 结论：渔业活动变化幅度更大（{fishing_data['abs_change_pct']:.2f}% vs {nonfishing_data['abs_change_pct']:.2f}%）")
            else:
                print(f"\n  ✓ 结论：非渔业活动变化幅度更大（{nonfishing_data['abs_change_pct']:.2f}% vs {fishing_data['abs_change_pct']:.2f}%）")
            
            # 计算变化比例
            change_ratio = fishing_data['abs_change_pct'] / nonfishing_data['abs_change_pct'] if nonfishing_data['abs_change_pct'] > 0 else 0
            print(f"    变化比例：{change_ratio:.2f}x")
        else:
            print("⚠ 未找到变化分析结果")
    else:
        print("⚠ tiles_info为空")
    
    print("\n" + "=" * 80)
    print("任务完成总结")
    print("=" * 80)
    print(f"总检测数：{len(tools.state.vessel_detections)}")
    print(f"已完成阶段：{', '.join(sorted([s.value for s in tools.state.stages_completed]))}")
    
    return tools


if __name__ == "__main__":
    tools = run_figure3_task1_example()
