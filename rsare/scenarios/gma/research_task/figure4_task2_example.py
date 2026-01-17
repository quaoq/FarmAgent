"""
图4.2任务完整调用流程示例

任务：哪类基础设施带来更高的近场船舶停留

"""

from rsare.apps.gma.tools_list import SARTools
from rsare.scenarios.gma.research_task.common_step import load_detect_tiles, load_env_tiles



def run_figure4_task2_example():
    """
    执行图4.2任务的完整流程
    
    任务：分析哪类基础设施带来更高的近场船舶停留
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

    
    print("\n" + "=" * 80)
    print("图4.2任务：基础设施附近船舶活动分析")
    print("=" * 80)
    

    print("\n[加载船舶数据] 加载船舶检测数据")
    print("-" * 80)

    result = tools.vessel_CFAR_detection(
        inner_window_width=200,
        inner_window_height=200,
        outer_window_width=600,
        outer_window_height=600,
        s1A_background_pixel_threshold=16.0,  # 2018-2020区间阈值
        s1B_background_pixel_threshold=19.0,
    )
    print(f"✓ {result}")
    # result = tools.extract_vessel_detection_tiles(tile_width=80, tile_height=80, tile_scale_m=20.0)
    # print(f"✓ {result}")
    result = tools.vessel_presence_length_estimation(tile_width=80, tile_height=80)
    print(f"✓ {result}")
    # ========================================================================
    # 阶段D：分析各类基础设施附近的船舶活动
    # ========================================================================
    print("\n[阶段D] 分析各类基础设施附近的船舶活动")
    print("-" * 80)
    
    # # 分析油气平台附近
    # result_oil = tools.analyze_vessel_activity_near_infrastructure(
    #     date_start="2019-01-01",
    #     date_end="2019-12-31",
    #     infrastructure_type="oil",
    #     near_field_radius_km=5.0,
    # )
    # print(f"✓ 油气平台：{result_oil}")
    #
    # # 分析海上风电附近
    # result_wind = tools.analyze_vessel_activity_near_infrastructure(
    #     date_start="2019-01-01",
    #     date_end="2019-12-31",
    #     infrastructure_type="wind",
    #     near_field_radius_km=5.0,
    # )
    # print(f"✓ 海上风电：{result_wind}")
    #
    # # 分析其他类型基础设施附近
    # result_other = tools.analyze_vessel_activity_near_infrastructure(
    #     date_start="2019-01-01",
    #     date_end="2019-12-31",
    #     infrastructure_type="other",
    #     near_field_radius_km=5.0,
    # )
    # print(f"✓ 其他类型：{result_other}")
    #
    # ========================================================================
    # 阶段E：比较分析
    # ========================================================================
    print("\n[阶段E] 比较分析：哪类基础设施带来更高的近场船舶停留")
    print("-" * 80)
    
    # 从state中获取结果
    tiles_info = tools.state.tiles_info
    if tiles_info:
        oil_key = "vessel_activity_near_oil_2019-01-01_2019-12-31"
        wind_key = "vessel_activity_near_wind_2019-01-01_2019-12-31"
        other_key = "vessel_activity_near_other_2019-01-01_2019-12-31"
        
        oil_data = tiles_info.get(oil_key)
        wind_data = tiles_info.get(wind_key)
        other_data = tiles_info.get(other_key)
        
        results = []
        if oil_data:
            results.append(("油气平台", oil_data))
        if wind_data:
            results.append(("海上风电", wind_data))
        if other_data:
            results.append(("其他类型", other_data))
        
        if results:
            print(f"✓ 比较完成")
            print(f"\n  各类基础设施附近的船舶活动统计：")
            
            for name, data in results:
                print(f"\n    {name}：")
                print(f"      - 近场活动量：{data['near_field_activity']:.2f}")
                print(f"      - 远场活动量：{data['far_field_activity']:.2f}")
                print(f"      - 总活动量：{data['total_activity']:.2f}")
                print(f"      - 近场占比：{data['near_field_pct']:.2f}%")
                print(f"      - 近场半径：{data['near_field_radius_km']}km")
                print(f"      - 船舶数量：{data['n_vessels']}")
                print(f"      - 基础设施数量：{data['n_infrastructure']}")
            
            # 找出近场占比最高的
            if len(results) > 0:
                max_near_field = max(results, key=lambda x: x[1]['near_field_pct'])
                print(f"\n  ✓ 结论：{max_near_field[0]}带来最高的近场船舶停留")
                print(f"    近场占比：{max_near_field[1]['near_field_pct']:.2f}%")
                
                # 比较近场活动密度（活动量/基础设施数量）
                print(f"\n    近场活动密度（活动量/基础设施数量）：")
                for name, data in results:
                    if data['n_infrastructure'] > 0:
                        density = data['near_field_activity'] / data['n_infrastructure']
                        print(f"      - {name}：{density:.2f} 活动/基础设施")
        else:
            print("⚠ 未找到船舶活动分析结果")
    else:
        print("⚠ tiles_info为空")
    
    print("\n" + "=" * 80)
    print("任务完成总结")
    print("=" * 80)
    print(f"总基础设施检测数：{len(tools.state.infrastructure_detections)}")
    print(f"总船舶检测数：{len(tools.state.vessel_detections)}")
    print(f"已完成阶段：{', '.join(sorted([s.value for s in tools.state.stages_completed]))}")
    
    return tools


if __name__ == "__main__":
    tools = run_figure4_task2_example()
