### Definitions

- **Metrics**: Derived information based on indicators used to make statements or evaluate certain conditions (e.g., completeness, freshness, etc.). These allow for high-level assessments.
- **Indicators**: Actual count or raw data used in calculations to produce metrics (e.g., building counts, road lengths, highway lengths, etc.).

### Calculated Metrics

1. **osm_building_completeness_percentage**:
   - **Definition**: Percentage of buildings in the OSM dataset compared to an AI-estimated building count.
   - **Formula**: 
     ```python
     combined_data["osm_building_completeness_percentage"] = (
         100
         if combined_data["osmBuildingsCount"] == 0
         and combined_data["aiBuildingsCountEstimation"] == 0
         else (
             combined_data["osmBuildingsCount"]
             / combined_data["aiBuildingsCountEstimation"]
         ) * 100
     )
     ```
   - **Indicators**: `osmBuildingsCount`, `aiBuildingsCountEstimation`

2. **osm_roads_completeness_percentage**:
   - **Definition**: Percentage of highways in the OSM dataset compared to AI-estimated highway length.
   - **Formula**:
     ```python
     combined_data["osm_roads_completeness_percentage"] = (
         100
         if combined_data["highway_length"] == 0
         and combined_data["aiRoadCountEstimation"] == 0
         else (
             combined_data["highway_length"]
             / combined_data["aiRoadCountEstimation"]
         ) * 100
     )
     ```
   - **Indicators**: `highway_length`, `aiRoadCountEstimation`

3. **osm_building_recency_percentage (last 6 months)**:
   - **Definition**: Percentage of buildings in OSM that have been modified or created in the last 6 months.
   - **Formula**:
     ```python
     osm_building_recency_percentage = (
         osm_building_count_6_months / osm_building_count
     ) * 100
     ```
   - **Indicators**: `osm_building_count_6_months`, `osm_building_count`

4. **osm_road_recency_percentage (last 6 months)**:
   - **Definition**: Percentage of highways in OSM that have been modified or created in the last 6 months.
   - **Formula**:
     ```python
     osm_road_recency_percentage = round(
         (osm_highway_length_6_months / osm_highway_length) * 100
     )
     ```
   - **Indicators**: `osm_highway_length_6_months`, `osm_highway_length`

