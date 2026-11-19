# config/industry_chain/_changes/

Accepted taxonomy versions (plan 28 phase 3b, D-161 updates 12–13). Each file is one version, applied in name order on top of the v0 YAML files by `ProductTaxonomy(folder, TaxonomyChangeSet.read_all(folder))`; `NodeLineageBuilder` turns them into `derived/graph/node_lineage.parquet`.

## Files
| File | Purpose | Contains |
|---|---|---|
| `v1-20261117.yaml` | Opus curation dry run of 汽车 / 电子 / 电力设备 (FY2023 → FY2025), accepted by the user 2026-11-17 except retiring SEG_AUTO_ROBOT_PARTS | 61 changes |
| `v2-20261117.yaml` | Opus curation batch 1: 基础化工, 机械设备, 计算机, 医药生物, 有色金属, 通信, 国防军工, 家用电器 (85 proposals), accepted by the user 2026-11-17; 耳机 aliased to the electronics TWS node | 162 changes |
| `v3-20261117.yaml` | Opus curation batch 2: 石油石化, 公用事业, 建筑装饰, 建筑材料, 食品饮料, 钢铁, 煤炭, 农林牧渔 (76 proposals) plus 12 context aliases (板材, 生猪 …), accepted by the user 2026-11-17 | 105 changes |
| `v4-20261117.yaml` | Opus curation batch 3: 轻工制造, 纺织服饰, 交通运输, 商贸零售, 社会服务, 传媒, 环保, 美容护理 (79 proposals), accepted by the user 2026-11-17; bare 服装 context alias left out | 113 changes |
| `v5-20261117.yaml` | Opus curation batch 4: 房地产, 银行, 非银金融, 综合 (26 proposals), accepted by the user 2026-11-17; 多元金融 hung under the new 非银金融业 root | 30 changes |
