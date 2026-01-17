"""
图4.1任务完整调用流程示例

任务：油气平台与海上风电结构数量规模的长期主导者与增长最快者

本示例展示如何使用tools_list.py中的工具方法完成完整工作流。
"""

from rsare.apps.gma.tools_list import SARTools


def run_figure4_task1_example():
    """
    执行图4.1任务的完整流程
    
    任务：分析基础设施增长，识别主导者和增长最快者
    """
    
    tools = SARTools()
    
    print("=" * 80)
    print("图4.1任务：基础设施增长分析")
    print("=" * 80)
    
    # ========================================================================
    # 阶段A-C：基础设施检测和分类
    # ========================================================================
    print("\n[阶段A-C] 基础设施检测和分类")
    print("-" * 80)
    
    # 启用基础设施检测加载
    tools.state.load_infra = True
    
    result = tools.load_SAR_scenes(
        date1="2017-01-01",
        date2="2021-12-31",  # 长期分析需要多年数据
        region=[-180.0, -90.0, 180.0, 90.0],
        satellite="S1AB",
    )
    print(f"✓ {result}")

    result = tools.load_optical_scenes(
        date1="2017-01-01",
        date2="2021-12-31",
        region=[-180.0, -90.0, 180.0, 90.0],
    )
    print(f"✓ {result}")
    
    # 生成中位数合成
    result = tools.generate_median_scene_composites(
        region=[-180.0, -90.0, 180.0, 90.0],
        start_date="2017-01-01",
        time_window_duration="6 months",
    )
    print(f"✓ {result}")
    
    # CFAR基础设施检测
    result = tools.infrastructure_CFAR_detection(
        inner_window_width=140,
        inner_window_height=140,
        outer_window_width=200,
        outer_window_height=200,
    )
    print(f"✓ {result}")
    
    # 生成多波段合成
    result = tools.generate_multiband_median_scene_composites(
        time_window_duration="6 months",
        multiband_image_bands=["VH", "VV", "R", "G", "B", "NIR"],
    )
    print(f"✓ {result}")
    
    # 基础设施分类
    result = tools.infrastructure_classification(
        tile_width=100,
        tile_height=100,
        time_window_duration="6 months",
        multiband_image_bands=["VH", "VV", "R", "G", "B", "NIR"],
    )
    print(f"✓ {result}")
    
    # ========================================================================
    # 阶段D：分析基础设施增长
    # ========================================================================
    print("\n[阶段D] 分析基础设施增长")
    print("-" * 80)
    
    # # 分析所有类型
    # result_all = tools.analyze_infrastructure_growth(
    #     date_start="2017-01-01",
    #     date_end="2021-12-31",
    #     infrastructure_type=None,  # 所有类型
    # )
    # print(f"✓ {result_all}")
    #
    # # 分别分析油气和风电
    # result_oil = tools.analyze_infrastructure_growth(
    #     date_start="2017-01-01",
    #     date_end="2021-12-31",
    #     infrastructure_type="oil",
    # )
    # print(f"✓ 油气平台：{result_oil}")
    #
    # result_wind = tools.analyze_infrastructure_growth(
    #     date_start="2017-01-01",
    #     date_end="2021-12-31",
    #     infrastructure_type="wind",
    # )
    # print(f"✓ 海上风电：{result_wind}")

    # ========================================================================
    # 阶段E：识别主导者和增长最快者
    # ========================================================================
    print("\n[阶段E] 识别主导者和增长最快者")
    print("-" * 80)
    
    # 从state中获取结果
    tiles_info = tools.state.tiles_info
    if tiles_info:
        key = "infrastructure_growth_2017-01-01_2021-12-31"
        if key in tiles_info:
            growth_analysis = tiles_info[key]["growth_analysis"]
            yearly_counts = tiles_info[key]["yearly_counts"]
            
            print(f"✓ 分析完成")
            print(f"\n  基础设施增长分析：")
            
            # 识别主导者（最后一年数量最多）
            if len(growth_analysis) > 0:
                dominant = growth_analysis.iloc[0]  # 已按last_count排序
                print(f"\n    长期主导者：{dominant['infra_type']}")
                print(f"      - 最后一年数量：{dominant['last_count']} ({dominant['last_year']})")
                print(f"      - 第一年数量：{dominant['first_count']} ({dominant['first_year']})")
                print(f"      - 总增长：{dominant['total_growth']}")
                print(f"      - 增长率：{dominant['growth_rate_pct']:.2f}%")
            
            # 识别增长最快者（增长率最高）
            if len(growth_analysis) > 0:
                fastest_growing = growth_analysis.nlargest(1, "growth_rate_pct").iloc[0]
                print(f"\n    增长最快者：{fastest_growing['infra_type']}")
                print(f"      - 增长率：{fastest_growing['growth_rate_pct']:.2f}%")
                print(f"      - 总增长：{fastest_growing['total_growth']}")
                print(f"      - 从 {fastest_growing['first_count']} ({fastest_growing['first_year']}) "
                      f"增长到 {fastest_growing['last_count']} ({fastest_growing['last_year']})")
            
            # 显示各类型详细统计
            print(f"\n    各类型详细统计：")
            for idx, row in growth_analysis.iterrows():
                print(f"      {row['infra_type']}:")
                print(f"        - 最后一年数量：{row['last_count']} ({row['last_year']})")
                print(f"        - 增长率：{row['growth_rate_pct']:.2f}%")
                print(f"        - 总增长：{row['total_growth']}")
            
            # 显示年度趋势
            print(f"\n    年度趋势（按类型）：")
            for infra_type in yearly_counts["infra_type"].unique():
                type_data = yearly_counts[yearly_counts["infra_type"] == infra_type].sort_values("year")
                print(f"      {infra_type}:")
                for _, row in type_data.iterrows():
                    print(f"        - {row['year']}: {row['count']} 个结构")
        else:
            print("⚠ 未找到基础设施增长分析结果")
    else:
        print("⚠ tiles_info为空")
    
    print("\n" + "=" * 80)
    print("任务完成总结")
    print("=" * 80)
    print(f"总基础设施检测数：{len(tools.state.infrastructure_detections)}")
    print(f"已完成阶段：{', '.join(sorted([s.value for s in tools.state.stages_completed]))}")
    
    return tools


if __name__ == "__main__":
    tools = run_figure4_task1_example()
