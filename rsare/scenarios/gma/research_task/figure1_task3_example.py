"""
图1.3任务完整调用流程示例

任务：衡量不可公开追踪活动是否由少数海域主导

"""
from rsare.apps.gma.tools_list import SARTools
from rsare.scenarios.gma.research_task.common_step import load_env_tiles, load_detect_tiles


def run_figure1_task3_example():
    """
    执行图1.3任务的完整流程
    
    任务：衡量不可公开追踪活动是否由少数海域主导
    """
    
    tools = SARTools()
    
    print("=" * 80)
    print("图1.3任务：衡量不可公开追踪活动是否由少数海域主导")
    print("=" * 80)
    
    date_start = "2018-08-01"
    date_end = "2018-08-31"
    region = [-180.0, -90.0, 180.0, 90.0]  # 全球范围
    load_detect_tiles(date_start=date_start, date_end=date_end, region=region, tools=tools)
    # 阶段B：船舶长度和存在性预测

    result1 = tools.vessel_presence_length_estimation(tile_width=80, tile_height=80)
    print(f"✓ {result1}")

    load_env_tiles(date_end, date_start, region,tools)

    result1 = tools.fishing_nonfishing_classification(tile_weidth=100, tile_height=100)
    print(f"✓ {result1}")
    # 阶段E：EEZ空间关联
    # result1 = tools.load_eez_data()
    # print(f"✓ {result1}")

    # ========================================================================
    # 阶段G：按EEZ汇总不可见活动
    # ========================================================================
    print("\n[阶段G] 按EEZ汇总不可见活动")
    print("-" * 80)
    
    # result = tools.aggregate_detections_by_eez(
    #     date_start=date_start,
    #     date_end=date_end,
    #     activity_type="dark",  # 只统计不可见（未匹配）活动
    #     normalize_by_overpasses=True,
    # )
    # print(f"✓ {result}")
    
    # ========================================================================
    # 阶段H：识别Top 5并计算贡献比例
    # ========================================================================
    print("\n[阶段H] 识别Top 5 EEZ并计算贡献比例")
    print("-" * 80)
    
    # 从state中获取结果
    tiles_info = tools.state.tiles_info
    if tiles_info:
        key = f"eez_dark_{date_start}_{date_end}"
        if key in tiles_info:
            eez_activity = tiles_info[key]["eez_activity"]
            
            # 计算总活动量
            total_activity = eez_activity["activity"].sum()
            
            # 计算占比
            eez_activity["share"] = eez_activity["activity"] / total_activity * 100
            
            # 排序并取Top 5
            top5 = eez_activity.nlargest(5, "activity").copy()
            
            # 计算累积占比
            top5["cumulative_share"] = top5["share"].cumsum()
            top5_total_share = top5["share"].sum()
            
            print(f"✓ 分析完成")
            print(f"\n  Top 5 EEZ（按不可见活动量）：")
            for idx, row in top5.iterrows():
                print(f"    {len(top5) - len(top5[top5.index <= idx]) + 1}. {row['eez_iso3']}: "
                      f"{row['activity']:.2f} 活动 ({row['share']:.2f}%), "
                      f"累积 {row['cumulative_share']:.2f}%")
            
            print(f"\n  Top 5 总贡献：{top5_total_share:.2f}%")
            print(f"  全球总不可见活动：{total_activity:.2f}")
            print(f"  总EEZ数量：{len(eez_activity)}")
            
            # 判断是否由少数海域主导（Top 5占比>50%）
            if top5_total_share > 50.0:
                print(f"\n  ✓ 结论：不可公开追踪活动主要由少数海域主导（Top 5占比 {top5_total_share:.2f}%）")
            else:
                print(f"\n  ⚠ 结论：不可公开追踪活动分布相对分散（Top 5占比 {top5_total_share:.2f}%）")
            
            # 计算Top 10占比（进一步分析）
            top10 = eez_activity.nlargest(10, "activity")
            top10_total_share = top10["share"].sum()
            print(f"\n  Top 10 总贡献：{top10_total_share:.2f}%")
            
        else:
            print("⚠ 未找到EEZ聚合结果")
    else:
        print("⚠ tiles_info为空")
    
    print("\n" + "=" * 80)
    print("任务完成总结")
    print("=" * 80)
    print(f"总检测数：{len(tools.state.vessel_detections)}")
    print(f"已完成阶段：{', '.join(sorted([s.value for s in tools.state.stages_completed]))}")
    
    return tools


if __name__ == "__main__":
    tools = run_figure1_task3_example()
