"""
图1.2任务完整调用流程示例

任务：比较2018年8月渔业活动与运输/能源两类活动"不可公开追踪活动"的占比在不同海域的差异

"""
from rsare.apps.gma.tools_list import SARTools
from rsare.scenarios.gma.research_task.common_step import load_env_tiles, load_detect_tiles


def run_figure1_task2_example():
    """
    执行图1.2任务的完整流程
    
    任务：比较2018年8月渔业活动与运输/能源两类活动"不可公开追踪活动"的占比在不同海域的差异
    """
    
    tools = SARTools()
    
    print("=" * 80)
    print("图1.2任务：比较渔业与运输/能源活动的不可见占比差异")
    print("=" * 80)
    
    date_start = "2018-08-01"
    date_end = "2018-08-31"
    region = [-180.0, -90.0, 180.0, 90.0]  # 全球范围

    load_detect_tiles(date_start, date_end, region, tools)

    # 阶段B：船舶长度和存在性预测

    result1 = tools.vessel_presence_length_estimation(tile_width=80, tile_height=80)
    print(f"✓ {result1}")

    load_env_tiles(date_start, date_end, region, tools)

    result1 = tools.fishing_nonfishing_classification(tile_width=100, tile_height=100)
    print(f"✓ {result1}")
    # 阶段E：EEZ空间关联
    # result1 = tools.load_eez_data()
    # print(f"✓ {result1}")

    # ========================================================================
    # 阶段G：按EEZ计算不可见占比
    # ========================================================================
    print("\n[阶段G] 按EEZ计算不可见占比")
    print("-" * 80)
    
    # result = tools.compute_visibility_metrics_by_eez(
    #     date_start=date_start,
    #     date_end=date_end,
    #     normalize_by_overpasses=True,
    # )
    # print(f"✓ {result}")
    #
    # ========================================================================
    # 阶段H：统计分析
    # ========================================================================
    print("\n[阶段H] 统计分析：识别差异显著的EEZ")
    print("-" * 80)
    
    # 从state中获取结果
    tiles_info = tools.state.tiles_info
    if tiles_info:
        key = f"eez_visibility_{date_start}_{date_end}"
        if key in tiles_info:
            eez_metrics = tiles_info[key]["eez_metrics"]
            
            # 按差异排序
            sorted_metrics = eez_metrics.sort_values("difference", ascending=False)
            
            # 识别渔业不可见占比显著高于非渔业的EEZ（差异>10%）
            fishing_higher = sorted_metrics[sorted_metrics["difference"] > 10.0]
            
            # 识别非渔业不可见占比显著高于渔业的EEZ（差异<-10%）
            nonfishing_higher = sorted_metrics[sorted_metrics["difference"] < -10.0]
            
            print(f"✓ 分析完成")
            print(f"\n  渔业不可见占比显著高于非渔业的EEZ（差异>10%）：{len(fishing_higher)} 个")
            if len(fishing_higher) > 0:
                print("  Top 5:")
                for idx, row in fishing_higher.head(5).iterrows():
                    print(f"    - {row['eez_iso3']}: 渔业 {row['dark_pct_fishing']:.2f}%, "
                          f"非渔业 {row['dark_pct_nonfishing']:.2f}%, "
                          f"差异 {row['difference']:.2f}%")
            
            print(f"\n  非渔业不可见占比显著高于渔业的EEZ（差异<-10%）：{len(nonfishing_higher)} 个")
            if len(nonfishing_higher) > 0:
                print("  Top 5:")
                for idx, row in nonfishing_higher.head(5).iterrows():
                    print(f"    - {row['eez_iso3']}: 渔业 {row['dark_pct_fishing']:.2f}%, "
                          f"非渔业 {row['dark_pct_nonfishing']:.2f}%, "
                          f"差异 {row['difference']:.2f}%")
            
            # 统计摘要
            print(f"\n  统计摘要：")
            print(f"    - 平均差异：{sorted_metrics['difference'].mean():.2f}%")
            print(f"    - 中位数差异：{sorted_metrics['difference'].median():.2f}%")
            print(f"    - 最大差异：{sorted_metrics['difference'].max():.2f}% ({sorted_metrics.iloc[0]['eez_iso3']})")
            print(f"    - 最小差异：{sorted_metrics['difference'].min():.2f}% ({sorted_metrics.iloc[-1]['eez_iso3']})")
        else:
            print("⚠ 未找到EEZ可见性指标结果")
    else:
        print("⚠ tiles_info为空")
    
    print("\n" + "=" * 80)
    print("任务完成总结")
    print("=" * 80)
    print(f"总检测数：{len(tools.state.vessel_detections)}")
    print(f"已完成阶段：{', '.join(sorted([s.value for s in tools.state.stages_completed]))}")
    
    return tools


if __name__ == "__main__":
    tools = run_figure1_task2_example()
