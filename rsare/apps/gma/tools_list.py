from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Set, Tuple, cast, Any

import numpy as np
import pandas as pd

from rsare.agents.agent.toolset_builder import agent_tool
from rsare.apps.gma.constant import VESSEL_DETECTIONS_DIR, INFRASTRUCTURE_DETECTIONS_DIR


class _DetectIdMixin:
    @staticmethod
    def make_detect_id(scene_id: str, lon: float, lat: float) -> str:
        return f"{scene_id};{lon:.6f};{lat:.6f}"

    @staticmethod
    def parse_detect_id(detect_id: str) -> Tuple[str, float, float]:
        parts = detect_id.split(";")
        if len(parts) != 3:
            return '', 0.0, 0.0
        return parts[0], float(parts[1]), float(parts[2])


class ProcessingStage(str, Enum):
    """Processing stage identifiers  """
    SCENES_LOADED = "scenes_loaded"
    PREPROCESSED = "preprocessed"
    CFAR_VESSEL_DONE = "cfar_vessel_done"
    TILES_EXTRACTED = "tiles_extracted"
    PRESENCE_LENGTH_PREDICTED = "presence_length_predicted"
    FISHING_PREDICTED = "fishing_predicted"
    AIS_MATCHED = "ais_matched"
    AIS_DATA_LOADED = "ais_data_loaded"
    CFAR_INFRA_DONE = "cfar_infra_done"
    INFRA_TILES_EXTRACTED = "infra_tiles_extracted"
    INFRA_CLASSIFIED = "infra_classified"
    RESULTS_AGGREGATED = "results_aggregated"
    OPTICAL_SCENES_LOADED = "optical_scenes_loaded"
    MEDIAN_COMPOSITES_GENERATED = "median_composites_generated"
    MULTIBAND_COMPOSITES_GENERATED = "multiband_composites_generated"
    RASTER_STACKS_GENERATED = "raster_stacks_generated"
    CLUSTERED_DETECTIONS_FILTERED = "clustered_detections_filtered"


@dataclass
class Scene:
    """Sentinel-1 SAR scene"""
    scene_id: str
    timestamp: Optional[datetime] = None
    bbox: Optional[tuple[float, float, float, float]] = None
    satellite: Optional[str] = None  # "S1A" or "S1B"

    # Processing flags
    vessel_preprocessed: bool = False
    infra_preprocessed: bool = False

    clipped: bool = False
    clip_buffer_m: float = 500.0


@dataclass
class VesselDetection:
    """Vessel detection - 所有数据从 CSV 读取，但存储在 state 中"""
    detect_id: str  # "scene_id;lon;lat"
    scene_id: str
    detect_lon: float
    detect_lat: float
    detect_timestamp: Optional[datetime] = None

    # 从 CSV 读取的原始数据
    presence_score: Optional[float] = None  # 来自 CSV 的 presence_score
    length_m: Optional[float] = None  # 来自 CSV 的 length_m
    mmsi: Optional[int] = None  # 来自 CSV 的 mmsi
    matching_score: Optional[float] = None  # 来自 CSV 的 matching_score
    fishing_score: Optional[float] = None  # 来自 CSV 的 fishing_score
    matched_category: Optional[str] = None  # 来自 CSV 的 matched_category

    cfar_inner_window: Optional[Tuple[int, int]] = None
    cfar_outer_window: Optional[Tuple[int, int]] = None
    cfar_threshold: Optional[float] = None

    # 处理状态标志
    # predict_vessel_presence_and_length
    presence_prob: Optional[float] = None  # 赋值：presence_score
    presence_binary: Optional[bool] = None  # presence_prob > 0.5

    # extract_environmental_tiles (只处理 presence_prob > 0.7)
    env_tiles_extracted: bool = False
    env_tiles_path: Optional[str] = None

    # infer_fishing_nonfishing (需要 env_tiles_extracted=True)
    fishing_prob: Optional[float] = None  # 赋值：fishing_score 或从 CSV 读取
    fishing_binary: Optional[bool] = None  # fishing_prob > 0.5

    # match_ais_to_detections
    ssvid: Optional[int] = None  # 赋值：mmsi 或从 CSV 读取
    match_score: Optional[float] = None  # 赋值：matching_score 或从 CSV 读取
    is_high_confidence: bool = False  # match_score > 7.4e-6
    is_bright_vessel: bool = False  # ssvid is not None
    is_dark_vessel: bool = True  # ssvid is None

    # extract_vessel_detection_tiles
    detection_tiles_extracted: bool = False
    tiles_info: Optional[dict] = None


@dataclass
class InfrastructureDetection:
    """Infrastructure detection - 数据从 CSV 读取"""
    detection_id: str
    scene_id: str
    detect_lon: float
    detect_lat: float
    detection_date: Optional[date] = None

    # 从 CSV 读取的原始数据
    structure_id: Optional[int] = None
    structure_start_date: Optional[date] = None
    structure_end_date: Optional[date] = None
    label: Optional[str] = None  # "wind", "oil", "other", "noise"
    label_confidence: Optional[str] = None

    # CFAR detection parameters
    cfar_inner_window: Optional[Tuple[int, int]] = None  # (140, 140)
    cfar_outer_window: Optional[Tuple[int, int]] = None  # (200, 200)
    # 处理状态标志
    infra_tiles_extracted: bool = False
    sar_tiles_path: Optional[str] = None
    optical_tiles_path: Optional[str] = None

    # classify_infrastructure
    predicted_class: Optional[str] = None  # label
    confidence: Optional[str] = None  # label_confidence


@dataclass
class EnvironmentData:
    """Environment data descriptor"""
    resolution_deg: float = 0.01
    loaded: bool = False

    # Environmental feature raster paths (used for fishing-nonfishing classification)
    bathymetry_path: Optional[str] = None
    port_distance_path: Optional[str] = None
    sst_path: Optional[str] = None  # Sea surface temperature
    current_speed_path: Optional[str] = None
    chlorophyll_path: Optional[str] = None
    shoreline_path: Optional[str] = None  # For filter_shoreline_regions_sar_scenes
    roads_path: Optional[str] = None  # For filter_road_regions_sar_scenes


@dataclass
class Composite:
    """Median composite for infrastructure detection"""
    composite_id: str
    time_window_duration: str
    center_date: date
    start_date: date
    end_date: date
    bands: List[str] = field(default_factory=list)
    composite_path: Optional[str] = None
    generated: bool = False


@dataclass
class SARARESystem:
    region: tuple[float, float, float, float]  # [lon_min, lon_max, lat_min, lat_max]
    date_start: date
    date_end: Optional[date] = None
    # need several minutes to load intra csv while the region is large(add a flag to control this
    # or move load infra csv to median_composites_generated??)TODO
    load_infra = False
    # Scenes ( get_SAR_scenes - 从 GEE 获取)
    scenes: List[Scene] = field(default_factory=list)
    scene_ids: List[str] = field(default_factory=list)  # 方便查询

    # Vessel detections ( run_cfar_detection_vessel - 从 CSV 读取)
    # Key: detect_id
    vessel_detections: Dict[str, VesselDetection] = field(default_factory=dict)

    # Infrastructure detections ( run_cfar_detection_infra - 从 CSV 读取)
    # Key: detection_id
    infrastructure_detections: Dict[str, InfrastructureDetection] = field(default_factory=dict)

    # Environment data ( load_environment_data)
    env_data: Optional[EnvironmentData] = None

    # AIS data (  load_ais_data)
    ais_data: List[dict] = field(default_factory=list)

    # Processing state flags
    stages_completed: Set[ProcessingStage] = field(default_factory=set)

    # Tiles info ( extract_detection_tiles)
    tiles_info: Optional[dict] = None

    # Raster stacks
    multiband_raster_stacks: Dict[str, dict] = field(default_factory=dict)

    # Cross-validation labels for infrastructure classification
    # (used during model training/evaluation phase)
    cv_labels: Optional[Dict[str, Any]] = None

    created_at: datetime = field(default_factory=datetime.now)
    output_dir: str = "output"

    def has_stage(self, stage: ProcessingStage) -> bool:
        """检查处理阶段是否完成"""
        return stage in self.stages_completed

    def mark_stage(self, stage: ProcessingStage):
        """标记处理阶段完成"""
        self.stages_completed.add(stage)

    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """根据 scene_id 获取场景"""
        for scene in self.scenes:
            if scene.scene_id == scene_id:
                return scene
        return None

    def get_high_confidence_detections(self, threshold: float = 0.7) -> List[VesselDetection]:
        return [
            det for det in self.vessel_detections.values()
            if det.presence_prob is not None and det.presence_prob > threshold
        ]


class SARTools:
    def __init__(self):
        self.state = SARARESystem(
            region=(0.0, 0.0, 0.0, 0.0),
            date_start=date.today(),
            env_data=EnvironmentData()
        )

    def _load_vessel_detections_from_csv(self, csv_file: Path):
        """Internal method to load vessel detections from CSV"""
        try:
            df = pd.read_csv(csv_file)

            if self.state.scene_ids:
                df = df[df["scene_id"].isin(self.state.scene_ids)].copy()

            for _, row in df.iterrows():
                detect_id = _DetectIdMixin.make_detect_id(
                    row["scene_id"], row["lon"], row["lat"]
                )

                if detect_id in self.state.vessel_detections:
                    continue

                detection = VesselDetection(
                    detect_id=detect_id,
                    scene_id=row["scene_id"],
                    detect_lon=float(row["lon"]),
                    detect_lat=float(row["lat"]),
                    presence_score=float(row["presence_score"]) if pd.notna(row.get("presence_score")) else None,
                    length_m=float(row["length_m"]) if pd.notna(row.get("length_m")) else None,
                    mmsi=int(row["mmsi"]) if pd.notna(row.get("mmsi")) else None,
                    matching_score=float(row["matching_score"]) if pd.notna(row.get("matching_score")) else None,
                    fishing_score=float(row["fishing_score"]) if pd.notna(row.get("fishing_score")) else None,
                    matched_category=str(row["matched_category"]) if pd.notna(row.get("matched_category")) else None,
                )

                if "timestamp" in row and pd.notna(row.get("timestamp")):
                    try:
                        detection.detect_timestamp = pd.to_datetime(row["timestamp"])
                    except:
                        pass

                self.state.vessel_detections[detect_id] = detection
        except Exception as e:
            print(f"Error loading {csv_file}: {e}")

    def _load_infrastructure_detections(
            self,
            date1: Optional[str] = None,
            date2: Optional[str] = None,
            region: Optional[List[float]] = None,
    ):
        """
        Load infrastructure detections from CSV, filtering by date and region.

        Args:
            date1: Start date for filtering (YYYY-MM-DD format). If None, uses self.state.date_start
            date2: End date for filtering (YYYY-MM-DD format). If None, uses self.state.date_end or no upper limit
            region: Bounding box [lon_min, lat_min, lon_max, lat_max]. If None, uses self.state.region
        """

        csv_file = INFRASTRUCTURE_DETECTIONS_DIR / "sar_fixed_infrastructure_202410.csv"
        if not csv_file.exists():
            print(f"Warning: Infrastructure CSV not found: {csv_file}")
            return

        try:
            df = pd.read_csv(csv_file)

            # 确定过滤参数
            if region is None:
                region = self.state.region
            if date1 is None:
                date1_obj = self.state.date_start
            else:
                date1_obj = pd.to_datetime(date1).date() if date1 else None
            if date2 is None:
                date2_obj = self.state.date_end
            else:
                date2_obj = pd.to_datetime(date2).date() if date2 else None

            # 空间过滤
            if region and region != (0.0, 0.0, 0.0, 0.0):
                lon_min, lat_min, lon_max, lat_max = region
                df = df[
                    (df["lon"] >= lon_min) & (df["lon"] <= lon_max) &
                    (df["lat"] >= lat_min) & (df["lat"] <= lat_max)
                    ].copy()

            # 时间过滤
            if "detection_date" in df.columns and date1_obj is not None:
                df["detection_date"] = pd.to_datetime(df["detection_date"], errors="coerce")
                df = df[df["detection_date"].notna()].copy()  # 移除无效日期

                # 下界过滤
                if date1_obj:
                    df = df[df["detection_date"] >= pd.Timestamp(date1_obj)].copy()

                # 上界过滤
                if date2_obj:
                    df = df[df["detection_date"] <= pd.Timestamp(date2_obj)].copy()

            # 加载检测数据
            for _, row in df.iterrows():
                detection_id_str = str(row.get("detection_id", f"infra_{row.name}"))

                # 解析 detection_id（可能包含场景ID和坐标）
                scene_id_from_id, lon_from_id, lat_from_id = _DetectIdMixin.parse_detect_id(
                    detection_id_str)

                # 优先使用 CSV 中的 lon/lat 列，如果没有则使用 detection_id 中解析的
                if "lon" in df.columns and pd.notna(row.get("lon")):
                    detect_lon = float(row["lon"])
                elif lon_from_id is not None:
                    detect_lon = lon_from_id
                else:
                    continue  # 跳过没有坐标的记录

                if "lat" in df.columns and pd.notna(row.get("lat")):
                    detect_lat = float(row["lat"])
                elif lat_from_id is not None:
                    detect_lat = lat_from_id
                else:
                    continue  # 跳过没有坐标的记录

                detection = InfrastructureDetection(
                    detection_id=detection_id_str,
                    detect_lon=detect_lon,
                    detect_lat=detect_lat,
                    scene_id=scene_id_from_id,  # 如果 detection_id 包含场景ID，则设置
                    detection_date=pd.to_datetime(row.get("detection_date")).date() if pd.notna(
                        row.get("detection_date")) else None,
                    structure_id=int(row["structure_id"]) if pd.notna(row.get("structure_id")) else None,
                    structure_start_date=pd.to_datetime(row.get("structure_start_date")).date() if pd.notna(
                        row.get("structure_start_date")) else None,
                    structure_end_date=pd.to_datetime(row.get("structure_end_date")).date() if pd.notna(
                        row.get("structure_end_date")) else None,
                    label=str(row.get("label", "")) if pd.notna(row.get("label")) else None,
                    label_confidence=str(row.get("label_confidence", "")) if pd.notna(
                        row.get("label_confidence")) else None,
                )

                self.state.infrastructure_detections[detection_id_str] = detection

            print(f"Loaded {len(self.state.infrastructure_detections)} infrastructure detections")
        except Exception as e:
            print(f"Error loading infrastructure detections: {e}")

    def _get_matching_csv_files(self, date_start: date, date_end: date) -> List[Path]:
        """
        根据日期范围找到匹配的 CSV 文件。

        文件名格式: sar_vessel_detections_pipev20231026_YYYYMM.csv
        例如: sar_vessel_detections_pipev20231026_201808.csv 表示 2018年8月

        Args:
            date_start: 开始日期
            date_end: 结束日期

        Returns:
            匹配的 CSV 文件路径列表
        """
        matching_files = []
        csv_files = list(VESSEL_DETECTIONS_DIR.glob("sar_vessel_detections_*.csv"))

        for csv_file in csv_files:
            # 从文件名提取年月: sar_vessel_detections_pipev20231026_YYYYMM.csv
            filename = csv_file.stem  # 不含扩展名
            parts = filename.split("_")
            if len(parts) >= 4:
                year_month_str = parts[-1]  # 最后一部分，例如 "201808"

                if len(year_month_str) == 6 and year_month_str.isdigit():
                    year = int(year_month_str[:4])
                    month = int(year_month_str[4:6])

                    # 构建日期范围（该月的第一天和最后一天）
                    try:
                        file_start = date(year, month, 1)
                        if month == 12:
                            file_end = date(year + 1, 1, 1) - timedelta(days=1)
                        else:
                            file_end = date(year, month + 1, 1) - timedelta(days=1)

                        # 检查文件日期范围是否与查询范围重叠
                        if file_start <= date_end and file_end >= date_start:
                            matching_files.append(csv_file)
                    except ValueError:
                        continue

        return matching_files

    @agent_tool
    def load_SAR_scenes(
            self,
            date1:str,
            date2:Optional[str] ,
            region: List[float] = None,
            satellite:str="S1AB",  # choice is S1A, S1B, or "S1AB"
            collection:str="COPERNICUS/S1_GRD",
    ):
        """Get Sentinel-1 SAR scenes over ocean areas within a specified date range.

        This function queries Google Earth Engine for Sentinel-1 GRD (Ground Range
        Detected) imagery that overlaps with specified ocean and region boundaries.
        The results are filtered to include only IW (Interferometric Wide) mode images
        with both VV and VH polarizations at high resolution.

        Args:
            date1 (str): Start date of the query range in "YYYY-MM-DD" format.
            date2 (str or None): End date of the query range in "YYYY-MM-DD" format.
                If None, defaults to date1 + 1 day.
            region: List of four floats defining the bounding box
                [lon_min, lat_min, lon_max, lat_max].
            satellite (str): Satellite identifier prefix to filter scenes
                by (e.g., "S1A" "S1B" "S1AB").Defaults to "S1AB".
            collection (str): Earth Engine image collection ID. Defaults
                to "COPERNICUS/S1_GRD".

        Returns:
            reply [str]: Message with the number of matching scenes, if any found.
        """
        if region:
            if len(region) != 4:
                return f"region must have 4 values, got {len(region)}: {region}"

            try:
                region4 = tuple(float(v) for v in region)
            except (TypeError, ValueError) as e:
                return f"region values must be convertible to float: {region!r}"

            print(region)
            print(self)

            self.state.region = cast(tuple[float, float, float, float], region4)

        if self.state.load_infra:
            self._load_infrastructure_detections(date1, date2, region)

        self.load_vessel_detects(date1, date2, satellite, region)

        self.state.mark_stage(ProcessingStage.SCENES_LOADED)

        return f"Loaded SAR scenes"

    def load_vessel_detects(self, date1, date2, satellite, region):
        date_start = pd.to_datetime(date1).date()
        date_end = pd.to_datetime(date2).date() if date2 else date_start + timedelta(days=1)
        self.state.date_start = date_start
        self.state.date_end = date_end
        lon_min, lat_min, lon_max, lat_max = region
        # 根据日期范围找到匹配的 CSV 文件
        matching_csv_files = self._get_matching_csv_files(date_start, date_end)
        if not matching_csv_files:
            print(f"No matching CSV files found for date range {date1} to {date_end}")
            return
        scene_ids_set = set()
        # 遍历所有匹配的 CSV 文件，完整加载数据
        for csv_file in matching_csv_files:

            try:
                # 完整读取 CSV 文件（不使用 nrows 限制）
                df = pd.read_csv(csv_file)

                # 时间过滤：如果 CSV 中有 timestamp 列，进行时间过滤
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                    df = df[
                        (df["timestamp"] >= pd.Timestamp(date_start, tz="UTC")) &
                        (df["timestamp"] <= pd.Timestamp(date_end, tz="UTC"))
                        ].copy()

                # 空间过滤：根据 region 过滤
                df = df[
                    (df["lon"] >= lon_min) & (df["lon"] <= lon_max) &
                    (df["lat"] >= lat_min) & (df["lat"] <= lat_max)
                    ].copy()

                # 提取 scene_ids
                if "scene_id" in df.columns:
                    scene_ids_set.update(df["scene_id"].unique())

                # 加载所有符合条件的 detections 到 state
                for _, row in df.iterrows():
                    detect_id = _DetectIdMixin.make_detect_id(
                        row["scene_id"], row["lon"], row["lat"]
                    )

                    if detect_id in self.state.vessel_detections:
                        continue

                    detection = VesselDetection(
                        detect_id=detect_id,
                        scene_id=row["scene_id"],
                        detect_lon=float(row["lon"]),
                        detect_lat=float(row["lat"]),
                        presence_score=float(row["presence_score"]) if pd.notna(row.get("presence_score")) else None,
                        length_m=float(row["length_m"]) if pd.notna(row.get("length_m")) else None,
                        mmsi=int(row["mmsi"]) if pd.notna(row.get("mmsi")) else None,
                        matching_score=float(row["matching_score"]) if pd.notna(row.get("matching_score")) else None,
                        fishing_score=float(row["fishing_score"]) if pd.notna(row.get("fishing_score")) else None,
                        matched_category=str(row["matched_category"]) if pd.notna(
                            row.get("matched_category")) else None,
                    )

                    if "timestamp" in row and pd.notna(row.get("timestamp")):
                        try:
                            detection.detect_timestamp = pd.to_datetime(row["timestamp"])
                        except:
                            pass

                    self.state.vessel_detections[detect_id] = detection

            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
        # Filter by satellite if specified
        if satellite in ["S1A", "S1B"]:
            scene_ids_set = {sid for sid in scene_ids_set if sid.startswith(satellite)}
            # 同时过滤 detections 的 scene_id
            self.state.vessel_detections = {
                k: v for k, v in self.state.vessel_detections.items()
                if v.scene_id in scene_ids_set
            }
        # Add scenes to state
        for scene_id in scene_ids_set:
            if scene_id not in self.state.scene_ids:
                scene = Scene(
                    scene_id=scene_id,
                    satellite=scene_id[:3] if len(scene_id) >= 3 else None
                )
                self.state.scenes.append(scene)
                self.state.scene_ids.append(scene_id)

    @agent_tool
    def load_optical_scenes(
            self,
            date1: str,
            date2: Optional[str] = None,
            region: List[float] = None,
            satellite: str = "S2AB",
            collection: str = "COPERNICUS/S2",
    ) -> str:
        """
            Load Sentinel-2 optical scenes (RGB+NIR).

            Args:
                date1: Start date "YYYY-MM-DD"
                date2: End date "YYYY-MM-DD"
                region: [lon_min, lat_min, lon_max, lat_max]
                satellite: "S2A", "S2B", or "S2AB"
                collection: GEE collection ID

            Returns:
                Message with scenes loaded
        """
        # TODO should i add bandslist parameter?
        self.state.mark_stage(ProcessingStage.OPTICAL_SCENES_LOADED)
        return f"Loaded optical scenes"

    @agent_tool
    def clip_SAR_scenes(self, clip_buffer: float = 500.0) -> str:
        """
            Clip SAR scenes off the borders (in meters) to eliminate potential noise artefacts.

            Args:
                clip_buffer: Buffer distance in meters (default: 500m)

            Returns:
                Message indicating completion
        """
        if not self.state.has_stage(ProcessingStage.SCENES_LOADED):
            return f"No scenes loaded,please load scenes first"

        for scene in self.state.scenes:
            scene.clipped = True
            scene.clip_buffer_m = clip_buffer

        return f"Clipped {len(self.state.scenes)} scenes with {clip_buffer}m buffer"

    @agent_tool
    def vessel_CFAR_detection(
            self,
            inner_window_width: int = 200,
            inner_window_height: int = 200,
            outer_window_width: int = 600,
            outer_window_height: int = 600,
            s1A_background_pixel_threshold: float = 18.0,
            s1B_background_pixel_threshold: float = 18.0,
    ) -> str:
        """
            Run CFAR vessel detection.

            Args:
                inner_window_width:width of inner window
                inner_window_height:height of inner window
                outer_window_width:width of outer window
                outer_window_height:height of outer window
                s1A_background_pixel_threshold: Threshold for S1A (14-24)
                s1B_background_pixel_threshold: Threshold for S1B (14-24)

            Returns:
                Message with detection count
        """
        if not self.state.has_stage(ProcessingStage.SCENES_LOADED):
            return f"No scenes loaded,please load scenes first"
        inner_window_size = (inner_window_width, inner_window_height)
        outer_window_size = (outer_window_width, outer_window_height)
        for detection in self.state.vessel_detections.values():
            scene = self.state.get_scene(detection.scene_id)
            if scene:
                detection.cfar_inner_window = inner_window_size
                detection.cfar_outer_window = outer_window_size
                if scene.satellite == "S1A":
                    detection.cfar_threshold = s1A_background_pixel_threshold
                elif scene.satellite == "S1B":
                    detection.cfar_threshold = s1B_background_pixel_threshold

        self.state.mark_stage(ProcessingStage.CFAR_VESSEL_DONE)
        return f"CFAR detection parameters set for {len(self.state.vessel_detections)} detections"

    @agent_tool
    def vessel_CFAR_detection_hyperparameters(
            self,
            inner_window_width: int = 200,
            inner_window_height: int = 200,
            outer_window_width: int = 600,
            outer_window_height: int = 600,
            s1A_background_pixel_threshold: float = 18.0,
            s1B_background_pixel_threshold: float = 18.0,
    ) -> dict:
        """
            Evaluate hyperparameters for CFAR vessel detection.

            Args:
                inner_window_width:width of inner window
                inner_window_height:height of inner window
                outer_window_width:width of outer window
                outer_window_height:height of outer window
                s1A_background_pixel_threshold: Threshold for S1A (14-24)
                s1B_background_pixel_threshold: Threshold for S1B (14-24)

            Returns:
                scores [dict]: Hyperparameter evaluation scores
        """
        if not self.state.has_stage(ProcessingStage.SCENES_LOADED):
            return {"warning": f"No scenes loaded,please load scenes first"}

        # Empirical defaults described in the paper/text:
        # inner ring: 200x200, outer ring: 600x600
        expected_inner = (200, 200)
        expected_outer = (600, 600)
        inner_window_size = (inner_window_width, inner_window_height)
        outer_window_size = (outer_window_width, outer_window_height)
        # Time-dependent thresholds (S1A, S1B) described in the paper/text.
        # We choose the most recent matching interval when ranges overlap.
        # Note: the first interval reports S1B as "none"; we treat that as "not enforced".
        thresholds_by_interval = [
            # (start_date, end_date, s1a_thr, s1b_thr)
            (date(2020, 1, 1), date(2021, 12, 31), 22.0, 24.0),
            (date(2018, 3, 1), date(2020, 1, 31), 16.0, 19.0),
            (date(2017, 1, 1), date(2018, 3, 31), 14.0, 17.0),
            (date(2016, 9, 1), date(2017, 1, 31), 14.0, 18.0),
            (date(2016, 1, 1), date(2016, 10, 31), 14.0, None),
        ]

        query_date = self.state.date_start
        expected_s1a_thr: float = 18.0
        expected_s1b_thr: Optional[float] = 18.0

        for start_d, end_d, s1a_thr, s1b_thr in thresholds_by_interval:
            if start_d <= query_date <= end_d:
                expected_s1a_thr = float(s1a_thr)
                expected_s1b_thr = float(s1b_thr) if s1b_thr is not None else None
                break

        # Define "optimal" as matching the empirical defaults for the current interval.
        is_optimal = (
                inner_window_size == expected_inner
                and outer_window_size == expected_outer
                and abs(s1A_background_pixel_threshold - expected_s1a_thr) < 1e-6
                and (expected_s1b_thr is None or abs(s1B_background_pixel_threshold - expected_s1b_thr) < 1e-6)
        )

        if is_optimal:
            score = 1.0
        else:
            # If parameters are not optimal, return a purely random lower score.
            score = 0.6 + 0.3 * float(np.random.random())  # 0.6..0.9

        scores = {
            "inner_window": inner_window_size,
            "outer_window": outer_window_size,
            "s1A_threshold": float(s1A_background_pixel_threshold),
            "s1B_threshold": float(s1B_background_pixel_threshold),
            "is_optimal": is_optimal,  # TODO need is_optimal？
            "score": 0.6 * float(score),
        }

        return scores

    @agent_tool
    def vessel_presence_length_estimation(self, tile_width: int = 80, tile_height: int = 80) -> str:
        """Estimate vessel presence probability and vessel length.

        Args:
            tile_width:width of tile in pixels
            tile_height:height of tile in pixels
        Returns:
            string indicating how many detections were processed.
        """
        if not self.state.has_stage(ProcessingStage.CFAR_VESSEL_DONE):
            return "CFAR vessel detection must be completed first"

        for detection in self.state.vessel_detections.values():
            detection.presence_prob = detection.presence_score if detection.presence_score is not None else 0.9
            detection.presence_binary = detection.presence_prob > 0.5

        self.state.mark_stage(ProcessingStage.PRESENCE_LENGTH_PREDICTED)
        return f"Predicted presence/length for {len(self.state.vessel_detections)} detections"

    @agent_tool
    def vessel_presence_length_estimation_hyperparameters(
            self,
            tile_width: int = 80,
            tile_height: int = 80
    ) -> dict:
        """Evaluate hyperparameters for vessel presence/length estimation.

        Args:
            tile_width:width in pixels used for the model input tile.
            tile_height:height in pixels used for the model input tile.

        Returns:
            A dict of evaluation metrics, including:
                - `presence_accuracy`
                - `presence_f1`
                - `length_r2`
        """
        tile_size = (tile_width, tile_height)
        expected_tile_size = (80, 80)
        is_optimal = tile_size == expected_tile_size

        if is_optimal:
            # Best model (paper-like targets): F1 ~0.97, accuracy ~97.5%, R^2 ~0.84, RMSE ~21.9 m.
            presence_accuracy = 0.975
            presence_f1 = 0.97
            length_r2 = 0.84
        else:
            # If parameters are not optimal, return randomly degraded metrics.
            # Keep them strictly worse than the optimal case.
            presence_accuracy = 0.70 + 0.20 * float(np.random.random())  # 0.70..0.90
            presence_f1 = 0.70 + 0.20 * float(np.random.random())  # 0.70..0.90
            length_r2 = 0.60 + 0.20 * float(np.random.random())  # 0.60..0.80
        scores = {
            "tile_size": tile_size,
            "expected_tile_size": expected_tile_size,
            "presence_accuracy": float(presence_accuracy),
            "presence_f1": float(presence_f1),
            "length_r2": float(length_r2),
            "is_optimal": bool(is_optimal)
        }
        return scores

    @agent_tool
    def generate_median_scene_composites(
            self,
            region: List[float],
            start_date:str,
            tile_dx:float = 1,
            tile_dy:float = 1,
            time_window_duration: str = "6 months",
            satellite: str = "",  # "S1A", "S1B", "S1AB"
    ) -> str:
        """
            Generate median scene composites for infrastructure detection.

            Args:
                region: Bounding box [lon_min, lat_min, lon_max, lat_max]
                start_date: Start date for composite generation
                tile_dx: Tile X resolution in degrees
                tile_dy: Tile Y resolution in degrees
                time_window_duration: Temporal aggregation window (default: "6 months")
                satellite: Satellite identifier ("S1A", "S1B", "S1AB", or "")

            Returns:
                A status message indicating how many unique composites were found/processed.
            """

        if not self.state.has_stage(ProcessingStage.SCENES_LOADED):
            return f"please load SAR scenes first"
        composite_ids = set()

        for detection in self.state.infrastructure_detections.values():
            if detection.scene_id:
                composite_ids.add(detection.scene_id)

        self.state.mark_stage(ProcessingStage.MEDIAN_COMPOSITES_GENERATED)

        return f"Generated median composites: found {len(composite_ids)}  composites"

    @agent_tool
    def infrastructure_CFAR_detection(
            self,
            inner_window_width: int = 140,
            inner_window_height: int = 140,
            outer_window_width: int = 200,
            outer_window_height: int = 200,
    ) -> str:
        """
            Run CFAR infrastructure detection.

            Args:
                inner_window_width: width in pixels
                inner_window_height: height in pixels
                outer_window_width: width in pixels
                outer_window_height: height in pixels

            Returns:
                Message with detection count
        """
        if not self.state.has_stage(ProcessingStage.MEDIAN_COMPOSITES_GENERATED):
            return f"please generate median scene composites first"

        inner_window_size = (inner_window_width, inner_window_height)
        outer_window_size = (outer_window_width, outer_window_height)
        for detection in self.state.infrastructure_detections.values():
            detection.cfar_inner_window = inner_window_size
            detection.cfar_outer_window = outer_window_size

        self.state.mark_stage(ProcessingStage.CFAR_INFRA_DONE)
        return f"CFAR detection parameters set for {len(self.state.infrastructure_detections)} infrastructure detections"

    @agent_tool
    def infrastructure_CFAR_detection_hyperparameters(
            self,
            inner_window_width: int = 140,
            inner_window_height: int = 140,
            outer_window_width: int = 200,
            outer_window_height: int = 200,
    ) -> dict:
        """Evaluate hyperparameters for CFAR-based offshore infrastructure detection.

            Args:
                inner_window_width: width in pixels for the inner CFAR ring.
                inner_window_height: height in pixels for the inner CFAR ring.
                outer_window_width: width in pixels for the outer CFAR ring.
                outer_window_height: height in pixels for the outer CFAR ring.

            Returns:
                A dict containing:
                    - `inner_window`
                    - `outer_window`
                    - `is_optimal`
                    - `score`
        """
        if not self.state.has_stage(ProcessingStage.MEDIAN_COMPOSITES_GENERATED):
            return {"warning": f"please generate median scene composites first"}
        inner_window_size = (inner_window_width, inner_window_height)
        outer_window_size = (outer_window_width, outer_window_height)
        expected_inner = (140, 140)
        expected_outer = (200, 200)

        is_optimal = (inner_window_size == expected_inner and outer_window_size == expected_outer)

        if is_optimal:
            score = 1.0
        else:
            # If parameters are not optimal, return a purely random lower score.
            score = 0.60 + 0.30 * float(np.random.random())  # 0.60..0.90

        scores = {
            "inner_window": inner_window_size,
            "outer_window": outer_window_size,
            "is_optimal": bool(is_optimal),
            "score": float(score)}

        return scores

    @agent_tool
    def generate_multiband_median_scene_composites(
            self,
            time_window_duration: str = "6 months",
            multiband_image_bands: List[str] = None,
    ) -> str:
        """Generate multiband median composites for infrastructure classification.

        Args:
            time_window_duration: the temporal aggregation window (default: "6 months").
            multiband_image_bands: List of band/source identifiers to concatenate.
                Typical options include: ["VH", "VV", "R","G","B","NIR"].

        Returns:
            generate result
        """
        if not self.state.has_stage(ProcessingStage.CFAR_INFRA_DONE):
            return "please do infrastructure CFAR detect first"
        if not self.state.has_stage(ProcessingStage.OPTICAL_SCENES_LOADED):
            return "please load optical scenes first"

        self.state.mark_stage(ProcessingStage.MULTIBAND_COMPOSITES_GENERATED)
        return f"Generated multiband median scene composites"

    @agent_tool
    def infrastructure_classification(
            self,
            tile_width: int = 100,
            tile_height: int = 100,
            time_window_duration: str = "6 months",
            multiband_image_bands: List[str] = None,
    ) -> str:
        """Classify offshore infrastructure detections using multiband composites.

        Args:
            tile_width:width in pixels for extracted tiles used by the classifier (eg: 100).
            tile_height:height in pixels for extracted tiles used by the classifier (eg: 100)
            time_window_duration: Temporal window descriptor for the composites
                (eg: "6 months").
            multiband_image_bands: list of availabe bands to concat ("VH", "VV", "R","G","B","NIR").(e.g., ["VH", "VV", "R","G","B","NIR"])

        Returns:
            A string indicating how many detections were classified.
        """
        if not self.state.has_stage(ProcessingStage.MULTIBAND_COMPOSITES_GENERATED):
            return f"please generate multiband median scene composites first"

        for detection in self.state.infrastructure_detections.values():
            detection.predicted_class = detection.label
            detection.confidence = detection.label_confidence

        self.state.mark_stage(ProcessingStage.INFRA_CLASSIFIED)
        return f"Classified {len(self.state.infrastructure_detections)} infrastructure detections"

    @agent_tool
    def infrastructure_classification_hyperparameters(
            self,
            tile_width: int = 100,
            tile_height: int = 100,
            multiband_image_bands: List[str] = None
    ) -> dict:
        """Evaluate hyperparameters for infrastructure classification.

        Args:
            tile_width:width in pixels used for the model input tile.
            tile_height:height in pixels used for the model input tile.
            multiband_image_bands: list of availabe bands to concat ("VH", "VV", "R","G","B","NIR") (e.g., ["VH", "VV", "R","G","B","NIR"])

        Returns:
            A dict of evaluation metrics for the given hyperparameters.
        """
        if not self.state.has_stage(ProcessingStage.MULTIBAND_COMPOSITES_GENERATED):
            return {"warning": "please generate multiband median scene composites first"}

        expected_tile_size = (100, 100)
        expected_bands = ["VH", "VV", "R", "G", "B", "NIR"]
        tile_size = (tile_width, tile_height)
        is_optimal = (tile_size == expected_tile_size and multiband_image_bands == expected_bands)

        if is_optimal:
            # Paper-like best model metrics.
            accuracy = 0.989
            weighted_f1 = 0.99
        else:
            # Randomly degraded metrics (strictly worse than optimal).
            accuracy = 0.85 + 0.12 * float(np.random.random())  # 0.85..0.97
            weighted_f1 = 0.85 + 0.13 * float(np.random.random())  # 0.85..0.98

        scores = {
            "tile_size": tile_size,
            "multiband_bands": multiband_image_bands,
            "accuracy": float(accuracy),
            "weighted_f1": float(weighted_f1),
            "is_optimal": bool(is_optimal)
        }

        return scores

    @agent_tool
    def filter_infrastructure_clustered_detections(self, cluster_radius: float = 50.0) -> str:
        """Post-process infrastructure detections by spatial clustering.

        Args:
            cluster_radius: Radius threshold (meters) for grouping detections
                into clusters (default: 50m).

        Returns:
            A human-readable status string with the number of clusters produced.
        """
        if not self.state.has_stage(ProcessingStage.INFRA_CLASSIFIED):
            return f"please classify infrastructure detections first"
        # TODO
        self.state.mark_stage(ProcessingStage.CLUSTERED_DETECTIONS_FILTERED)
        return f"Clustered {len(self.state.infrastructure_detections)} infrastructure detections into clusters"

    @agent_tool
    def load_cv_infrastructure_classification_labels(self, training_split: float = 0.8) -> str:
        """
        Load cross-validation labels for infrastructure classification.

        Args:
            training_split: Fraction of data to use for training (default: 0.8 = 80%).
                           The remaining (1 - training_split) is used for validation/testing.

        Returns:
            A string message indicating the number of train and validation samples loaded.
        """
        # TODO Do we need check if load_crossvalidation_infrastructure_classification_labels has been called before call infrastructure_classification?
        if not self.state.has_stage(ProcessingStage.CFAR_INFRA_DONE):
            return f"please do infrastructure CFAR detect first"

        total = len(self.state.infrastructure_detections)
        train_size = int(total * training_split)

        detection_ids = list(self.state.infrastructure_detections.keys())
        train_ids = detection_ids[:train_size]
        val_ids = detection_ids[train_size:]

        self.state.cv_labels = {
            "train": train_ids,
            "val": val_ids,
            "training_split": training_split,
            "train_size": train_size,
            "val_size": len(val_ids),
        }

        return f"Loaded cross-validation labels: {train_size} train, {len(val_ids)} validation"

    @agent_tool
    def load_bathymetry_data(self, date1: str, date2: str, region: List[float]) -> str:
        """
        Load bathymetry (seafloor depth/elevation) data.

        **Used as input for fishing-nonfishing classification!**

        Args:
            date1: Start date for the data query window (YYYY-MM-DD format).
            date2: End date for the data query window (YYYY-MM-DD format).
            region: Bounding box as [lon_min, lat_min, lon_max, lat_max].

        Returns:
            A status message indicating that bathymetry data was loaded.
        """
        if self.state.env_data:
            self.state.env_data.bathymetry_path = f"bathymetry_{date1}_{date2}.tif"
        return "Bathymetry data loaded"

    @agent_tool
    def load_port_distance_data(self, date1: str, date2: str, region: List[float]) -> str:
        """
        Load distance from nearest port data.

        **Used as input for fishing-nonfishing classification!**
        Args:
            date1: Start date for the data query window (YYYY-MM-DD format).
            date2: End date for the data query window (YYYY-MM-DD format).
            region: Bounding box as [lon_min, lat_min, lon_max, lat_max].

        Returns:
            A status message indicating that port distance data was loaded.
        """
        if self.state.env_data:
            self.state.env_data.port_distance_path = f"port_distance_{date1}_{date2}.tif"
        return "Port distance data loaded"

    @agent_tool
    def load_surface_temperature_data(self, date1: str, date2: str, region: List[float]) -> str:
        """
        Load sea surface temperature (SST) data.

        **Used as input for fishing-nonfishing classification!**

        Args:
            date1: Start date for the data query window (YYYY-MM-DD format).
                   Temperature data is aggregated over this time period.
            date2: End date for the data query window (YYYY-MM-DD format).
            region: Bounding box as [lon_min, lat_min, lon_max, lat_max].

        Returns:
            A status message indicating that sea surface temperature data was loaded.
        """
        if self.state.env_data:
            self.state.env_data.sst_path = f"sst_{date1}_{date2}.tif"
        return "SST data loaded"

    @agent_tool
    def load_current_speed_data(self, date1: str, date2: str, region: List[float]) -> str:
        """
        Load ocean current speed data.

        **Used as input for fishing-nonfishing classification!**

        Args:
            date1: Start date for the data query window (YYYY-MM-DD format).
                   Current data is aggregated over this time period.
            date2: End date for the data query window (YYYY-MM-DD format).
            region: Bounding box as [lon_min, lat_min, lon_max, lat_max].

        Returns:
            A status message indicating that current speed data was loaded.
        """
        if self.state.env_data:
            self.state.env_data.current_speed_path = f"current_speed_{date1}_{date2}.tif"
        return "Current speed data loaded"

    @agent_tool
    def load_chlorophyll_data(self, date1: str, date2: str, region: List[float]) -> str:
        """
        Load ocean current speed data.

        **Used as input for fishing-nonfishing classification!**

        Args:
            date1: Start date for the data query window (YYYY-MM-DD format).
                   Current data is aggregated over this time period.
            date2: End date for the data query window (YYYY-MM-DD format).
            region: Bounding box as [lon_min, lat_min, lon_max, lat_max].

        Returns:
            A status message indicating that current speed data was loaded.
        """
        if self.state.env_data:
            self.state.env_data.current_speed_path = f"current_speed_{date1}_{date2}.tif"
        return "Current speed data loaded"

    @agent_tool
    def load_chlorophyll_data(self, date1: str, date2: str, region: List[float]) -> str:
        """
        Load chlorophyll concentration data.

        **Used as input for fishing-nonfishing classification!**

        Args:
            date1: Start date for the data query window (YYYY-MM-DD format).
                   Chlorophyll data is aggregated over this time period (typically
                   annual or seasonal averages).
            date2: End date for the data query window (YYYY-MM-DD format).
            region: Bounding box as [lon_min, lat_min, lon_max, lat_max].

        Returns:
            A status message indicating that chlorophyll data was loaded.
        """
        if self.state.env_data:
            self.state.env_data.chlorophyll_path = f"chlorophyll_{date1}_{date2}.tif"
        return "Chlorophyll data loaded"

    @agent_tool
    def load_global_shoreline_data(self, date1: str, date2: str, region: List[float]) -> str:
        """
        Load global shoreline data for filtering SAR detections.

        **Used to filter out parts of SAR imagery near shorelines!**

        Args:
            date1: Start date (YYYY-MM-DD) - kept for API consistency, not used
            date2: End date (YYYY-MM-DD) - kept for API consistency, not used
            region: Bounding box [lon_min, lat_min, lon_max, lat_max] - kept for
                   API consistency, not used (shoreline data is global)

        Returns:
            Status message indicating shoreline data has been loaded
        """
        if self.state.env_data:
            self.state.env_data.shoreline_path = "global_shoreline.shp"
        return "Shoreline data loaded"

    @agent_tool
    def load_global_roads_data(self, date1: str, date2: str, region: List[float]) -> str:
        """
        Load global roads data for filtering road vehicle detections in SAR imagery.

        **Used to filter out parts of SAR imagery affected by road vehicles!**

        Args:
            date1: Start date (YYYY-MM-DD) - kept for API consistency, not used
            date2: End date (YYYY-MM-DD) - kept for API consistency, not used
            region: Bounding box [lon_min, lat_min, lon_max, lat_max] - kept for
                   API consistency, not used (roads data is global)

        Returns:
            Status message indicating roads data has been loaded
        """
        if self.state.env_data:
            self.state.env_data.roads_path = "global_roads.shp"
        return "Roads data loaded"

    @agent_tool
    def filter_shoreline_regions_sar_scenes(self, shore_distance: float = 1000.0) -> str:
        """
        Apply a shoreline-based spatial mask to SAR scenes to restrict analysis to valid offshore areas.

        Args:
            shore_distance: Buffer distance in meters from shoreline (default: 1000.0m = 1km).

        Returns:
            A status message indicating the filtering operation was completed.

        """
        if not self.state.env_data or not self.state.env_data.shoreline_path:
            return "Warning: Shoreline data not loaded. Please  load global shoreline data first"

        return f"Filtered scenes by {shore_distance}m from shoreline "

    @agent_tool
    def filter_road_regions_sar_scenes(self, road_distance: float = 3000.0) -> str:
        """
        Filter SAR scenes by excluding detections in areas affected by road vehicle Doppler shift.

        **Used to filter out false detections from road vehicles appearing in SAR imagery!**

        Args:
            road_distance: Distance threshold in meters for identifying roads near SAR scenes
                          (default: 3000.0m).

        Returns:
            A status message indicating the filtering operation was completed.
        """
        if not self.state.env_data or not self.state.env_data.roads_path:
            return "Warning: Roads data not loaded. Please call load_global_roads_data() first"

        return f"Filtered scenes by {road_distance}m from roads"

    @agent_tool
    def generate_multiband_raster_stacks(
            self,
            multiband_rasters: List[str] = None,
    ) -> str:
        """
        Generate multiband raster stacks for fishing-nonfishing classification.

        Args:
            multiband_rasters: List of raster band identifiers to include in the stack.
                             If None, defaults to all available bands:
                             ["sar_cfar", "sar_vessel_length", "bathymetry",
                              "distance_from_port", "AIS_vessel_activity",
                              "surface_temperature", "current_speed", "chlorophyll"]
            tile_size: (width, height) in pixels for extracted tiles used by the
                classifier (eg: (100, 100)).

        Returns:
            A status message indicating the raster stack was generated.
            If required processing stages are not completed or required
                       raster data is not loaded.

        """
        if multiband_rasters is None:
            multiband_rasters = [
                "sar_cfar", "sar_vessel_length", "bathymetry",
                "distance_from_port", "AIS_vessel_activity",
                "surface_temperature", "current_speed", "chlorophyll"
            ]

        missing_stages = []
        if not self.state.has_stage(ProcessingStage.CFAR_VESSEL_DONE):
            missing_stages.append("CFAR_VESSEL_DONE (for sar_cfar)")
        if not self.state.has_stage(
                ProcessingStage.PRESENCE_LENGTH_PREDICTED):
            missing_stages.append("PRESENCE_LENGTH_PREDICTED (for sar_vessel_length)")

        # Check if required environmental data is loaded
        missing_rasters = []
        if not self.state.env_data:
            missing_rasters.append("Environment data not initialized (call load_environment_data first)")
        else:
            if "bathymetry" in multiband_rasters and not self.state.env_data.bathymetry_path:
                missing_rasters.append("bathymetry (call load_bathymetry_data)")
            if "distance_from_port" in multiband_rasters and not self.state.env_data.port_distance_path:
                missing_rasters.append("distance_from_port (call load_port_distance_data)")
            if "surface_temperature" in multiband_rasters and not self.state.env_data.sst_path:
                missing_rasters.append("surface_temperature (call load_surface_temperature_data)")
            if "current_speed" in multiband_rasters and not self.state.env_data.current_speed_path:
                missing_rasters.append("current_speed (call load_current_speed_data)")
            if "chlorophyll" in multiband_rasters and not self.state.env_data.chlorophyll_path:
                missing_rasters.append("chlorophyll (call load_chlorophyll_data)")

        # Report missing dependencies
        if missing_stages or missing_rasters:
            error_msg = "Cannot generate raster stack. Missing dependencies:\n"
            if missing_stages:
                error_msg += f"  - Processing stages: {', '.join(missing_stages)}\n"
            if missing_rasters:
                error_msg += f"  - Raster data: {', '.join(missing_rasters)}"
            return error_msg

        self.state.mark_stage(ProcessingStage.RASTER_STACKS_GENERATED)
        return f"Generated multiband raster stacks  with {len(multiband_rasters)} bands: {', '.join(multiband_rasters)}"

    # ========================================================================
    # Fishing Classification Methods
    # ========================================================================

    @agent_tool
    def fishing_nonfishing_classification(
            self,
            tile_weidth: int = 100,
            tile_height: int = 100,
            multiband_rasters: List[str] = None,
    ) -> str:
        """
        Classify vessels as fishing vs non-fishing using environmental rasters.


        Args:
            tile_weidth: width in pixels for the environmental tiles (default: 100).
            tile_height: height in pixels for the environmental tiles (default: 100).
            multiband_rasters: List of raster bands used (kept for API consistency).
                              Should match the bands in generate_multiband_raster_stacks.

        Returns:
            A string indicating how many detections were classified.
        """
        if not self.state.has_stage(ProcessingStage.PRESENCE_LENGTH_PREDICTED):
            return "Vessel presence/length prediction must be completed first"
        if not self.state.has_stage(ProcessingStage.RASTER_STACKS_GENERATED):
            return "Multiband raster stacks must be generated first"

        # Only process high-confidence detections (presence_prob > 0.7)
        high_confidence_detections = self.state.get_high_confidence_detections(threshold=0.7)

        for detection in high_confidence_detections:
            # Use fishing_score from CSV if available, otherwise default to 0.5
            detection.fishing_prob = detection.fishing_score if detection.fishing_score is not None else 0.5
            detection.fishing_binary = detection.fishing_prob > 0.5

        self.state.mark_stage(ProcessingStage.FISHING_PREDICTED)
        return f"Classified fishing/non-fishing for {len(high_confidence_detections)} high-confidence detections"

    @agent_tool
    def fishing_nonfishing_classification_hyperparameters(
            self,
            tile_weidth: int = 100,
            tile_height: int = 100,
            multiband_rasters: List[str] = None,
    ) -> dict:
        """
        Evaluate hyperparameters for fishing/non-fishing classification.

        Args:
            tile_weidth: width in pixels for the environmental tiles.
            tile_height: height in pixels for the environmental tiles.
            multiband_rasters: List of raster band identifiers to include.
                             If None, defaults to all standard bands.

        Returns:
            A dict of evaluation metrics, including:
                - `tile_size`
                - `multiband_rasters`
                - `accuracy`
                - `precision`
                - `recall`
                - `f1_score`
                - `is_optimal`
        """
        tile_size = (tile_weidth, tile_height)
        if multiband_rasters is None:
            multiband_rasters = [
                "sar_cfar", "sar_vessel_length", "bathymetry",
                "distance_from_port", "AIS_vessel_activity",
                "surface_temperature", "current_speed", "chlorophyll"
            ]

        expected_tile_size = (100, 100)
        expected_rasters = [
            "sar_cfar", "sar_vessel_length", "bathymetry",
            "distance_from_port", "AIS_vessel_activity",
            "surface_temperature", "current_speed", "chlorophyll"
        ]

        is_optimal = (
                tile_size == expected_tile_size and
                multiband_rasters == expected_rasters
        )

        if is_optimal:
            # Best model ensemble (paper-like targets): F1 ~0.91, accuracy ~90.5%
            accuracy = 0.905
            precision = 0.90
            recall = 0.92
            f1_score = 0.91
        else:
            # If parameters are not optimal, return randomly degraded metrics.
            # Keep them strictly worse than the optimal case.
            accuracy = 0.75 + 0.12 * float(np.random.random())  # 0.75..0.87
            precision = 0.75 + 0.12 * float(np.random.random())  # 0.75..0.87
            recall = 0.75 + 0.12 * float(np.random.random())  # 0.75..0.87
            f1_score = 0.75 + 0.12 * float(np.random.random())  # 0.75..0.87

        scores = {
            "tile_size": tile_size,
            "multiband_rasters": multiband_rasters,
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1_score),
            "is_optimal": bool(is_optimal)
        }

        return scores

    @agent_tool
    def load_AIS_data(self, date1: str, date2: str, region: List[float]) -> str:
        """
        Load AIS (Automatic Identification System) vessel tracking data.

        AIS data provides real-time vessel positions, identities, and metadata
        that are used for matching to SAR detections and vessel classification.

        Args:
            date1: Start date for the data query window (YYYY-MM-DD format).
            date2: End date for the data query window (YYYY-MM-DD format).
            region: Bounding box as [lon_min, lat_min, lon_max, lat_max].

        Returns:
            A status message indicating that AIS data was loaded.
        """
        # In actual implementation, this would load AIS messages from BigQuery or local files
        # For simulation, store empty list (data comes from CSV detections)
        self.state.ais_data = []
        self.state.mark_stage(ProcessingStage.AIS_DATA_LOADED)
        return f"Loaded {len(self.state.ais_data)} AIS records"

    @agent_tool
    def sar_ais_matching(self, matching_score_threshold: float = 7.4e-6) -> str:
        """
        Match AIS identities to SAR detections.


        Args:
            matching_score_threshold: Minimum matching score for high-confidence matches
                                     (default: 7.4e-6). Matches above this threshold
                                     are considered high-confidence.

        Returns:
            A string indicating the number of bright and dark vessels matched.
        """
        if not self.state.has_stage(ProcessingStage.CFAR_VESSEL_DONE):
            return f"CFAR vessel detection must be completed first"
        if not self.state.has_stage(ProcessingStage.AIS_DATA_LOADED):
            return f"AIS data must be loaded first (call load_AIS_data)"

        for detection in self.state.vessel_detections.values():
            # Use mmsi from CSV if available (pre-matched data)
            detection.ssvid = detection.mmsi
            detection.match_score = detection.matching_score
            detection.is_high_confidence = (
                    detection.match_score is not None and
                    detection.match_score > matching_score_threshold
            )
            detection.is_bright_vessel = detection.ssvid is not None
            detection.is_dark_vessel = detection.ssvid is None

        self.state.mark_stage(ProcessingStage.AIS_MATCHED)
        bright_count = sum(1 for d in self.state.vessel_detections.values() if d.is_bright_vessel)
        dark_count = sum(1 for d in self.state.vessel_detections.values() if d.is_dark_vessel)
        return f"Matched AIS: {bright_count} bright vessels, {dark_count} dark vessels"

    @agent_tool
    def sar_ais_matching_hyperparameter(
            self,
            number_vessel_classes: int = 6,
            number_vessel_speed_intervals: int = 6,
            number_time_intervals: int = 36,
    ) -> dict:
        """
        Evaluate hyperparameters for SAR-AIS matching algorithm.


        Args:
            number_vessel_classes: Number of vessel class categories used in the
                                  probabilistic raster (default: 6). Common classes include:
                                  trawlers, purse_seines, cargo_or_tanker, tug,
                                  drifting_longlines, fishing, other.
            number_vessel_speed_intervals: Number of speed bins for vessel movement
                                          modeling (default: 6). Speed intervals typically
                                          range from 0 to 10+ knots.
            number_time_intervals: Number of temporal bins for position extrapolation
                                  (default: 36). Time intervals are measured in minutes
                                  relative to the SAR scene acquisition time.

        Returns:
            A dict of evaluation metrics, including:
                - `number_vessel_classes`
                - `number_vessel_speed_intervals`
                - `number_time_intervals`
                - `matching_precision`: Precision of the matching algorithm
                - `matching_recall`: Recall of the matching algorithm
                - `optimal_threshold`: Optimal matching score threshold (default: 7.4e-6)
                - `is_optimal`: Whether the parameters match the expected optimal values
        """
        expected_vessel_classes = 6
        expected_speed_intervals = 6
        expected_time_intervals = 36

        is_optimal = (
                number_vessel_classes == expected_vessel_classes and
                number_vessel_speed_intervals == expected_speed_intervals and
                number_time_intervals == expected_time_intervals
        )

        if is_optimal:
            # Optimal parameters (paper-like targets): precision ~0.82, recall ~0.78
            # Threshold optimized at 7.4e-6 for high-confidence matches
            matching_precision = 0.82
            matching_recall = 0.78
            optimal_threshold = 7.4e-6
        else:
            # If parameters are not optimal, return randomly degraded metrics.
            # Keep them strictly worse than the optimal case.
            matching_precision = 0.70 + 0.10 * float(np.random.random())  # 0.70..0.80
            matching_recall = 0.65 + 0.10 * float(np.random.random())  # 0.65..0.75
            optimal_threshold = 7.4e-6 + np.random.random() * 1e-6  # Slightly varied

        scores = {
            "number_vessel_classes": number_vessel_classes,
            "number_vessel_speed_intervals": number_vessel_speed_intervals,
            "number_time_intervals": number_time_intervals,
            "matching_precision": float(matching_precision),
            "matching_recall": float(matching_recall),
            "optimal_threshold": float(optimal_threshold),
            "is_optimal": bool(is_optimal)
        }

        return scores
