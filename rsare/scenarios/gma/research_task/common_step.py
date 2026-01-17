def load_env_tiles(date_start, date_end, region, tools):
    # 阶段C：AIS匹配
    result1 = tools.load_AIS_data(date1=date_start, date2=date_end, region=region)
    print(f"✓ {result1}")
    result1 = tools.sar_ais_matching(matching_score_threshold=7.4e-6)
    print(f"✓ {result1}")
    # 阶段D：捕鱼/非捕鱼分类
    print("  加载环境数据...")
    tools.load_bathymetry_data(date_start, date_end, region)
    tools.load_port_distance_data(date_start, date_end, region)
    tools.load_surface_temperature_data(date_start, date_end, region)
    tools.load_current_speed_data(date_start, date_end, region)
    tools.load_chlorophyll_data(date_start, date_end, region)
    print("  ✓ 环境数据加载完成")
    result1 = tools.generate_multiband_raster_stacks()
    print(f"✓ {result1}")
    # result1 = tools.extract_environmental_tiles(tile_width=100, tile_height=100, presence_threshold=0.7)
    # print(f"✓ {result1}")


def load_detect_tiles(date_start, date_end, region, tools):
    # ========================================================================
    # 阶段A：加载SAR场景和CFAR检测
    # ========================================================================
    print("\n[阶段A] 加载SAR场景和CFAR检测")
    print("-" * 80)
    # A.1: 加载SAR场景（从GEE获取，离线模拟从CSV读取）
    result = tools.load_SAR_scenes(
        date1=date_start,
        date2=date_end,
        region=region,  # 全球范围
        satellite="S1AB",
    )
    print(f"✓ {result}")
    # A.2: 裁剪SAR场景（去除边界噪声）
    result = tools.clip_SAR_scenes(clip_buffer=500.0)
    print(f"✓ {result}")
    # A.3: CFAR船舶检测
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
