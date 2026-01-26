# cubemap_transforms_json.py : 全球(360°パノラマ)画像用transforms.jsonのキューブマップ変換

このスクリプトは [metashape_360_lfs](https://github.com/gradeeterna/metashape_360_lfs) が変換した ** 360度画像用 ** `transforms.json` ファイルをさらにキューブマップ用に変換します。

つまり、以下の変換が可能です:

Metashape (Standard/Professional) > xml/pointcloud > transforms.json > キューブマップ > 3DGSソフト ([Jawset Postshot](https://www.jawset.com/), [Brush](https://github.com/ArthurBrussee/brush), [LichtFeld Studio](https://github.com/MrNeRF/LichtFeld-Studio)など)


## 要件

- Python 3.x (3.11.8で確認)
- NumPy
- OpenCV
- Pillow
- Open3D (metashape_360_lfs内で使用)
- [metashape_360_lfs.py](https://github.com/gradeeterna/metashape_360_lfs) 

```
pip install numpy opencv-python Pillow open3d
```

## ディレクトリ構造

### 入力ディレクトリの例

```
(入力ディレクトリ)/
├─ metashape.xml
├─ metashape.ply
├─ transforms.json
├─ pointcloud.ply (オプション)
├─ images/
│ ├─ image_000.jpg (または .png)
│ └─ image_001.jpg
│ └─ ...
└─ masks/ # (オプション)
  ├─ image_000.png (または .jpg.png, .png.png)
  └─ image_001.png
  └─ ...
```

| ファイル | 説明 |
|------|-------------|
|metashape.ply| Metashape [ファイル > エクスポート > ポイントクラウドをエクスポート] で出力|
|metashape.xml| Metashape [ファイル > エクスポート > カメラをエクスポート] で出力|
|transforms.json| metashape_360_lfsで変換|
|pointcloud.ply| metashape_360_lfsで変換 (オプション)|

### 出力ディレクトリ例

```
(出力ディレクトリ)/
├─ transforms.json
├─ images/
│ ├─ image_000_nx.jpg (または .png)
│ ├─ image_000_ny.jpg
│ ├─ image_000_nz.jpg
│ ├─ image_000_px.jpg
│ ├─ image_000_py.jpg
│ ├─ image_000_pz.jpg
│ ├─ image_001_nx.jpg
│ └─ ...
└─ masks/
  ├─ image_000_nx.png
│ └─ ...
```


## 使用例

### 基本的な使用法

カレントディレクトリにある transforms.json とimagesディレクトリ内の画像を変換: (masksディレクトリがあればそれも変換)
```
python metashape_360_lfs.py --images images --xml metashape.xml --output .
python cubemap_transforms_json.py .
```

### 詳細

出力ディレクトリを指定:
```
python cubemap_transforms_json.py . ./cubic
```

各オプション:

```
python cubemap_transforms_json.py . ./cubic \
  --yaw 45 \
  --stitch 2.5 \
  --fov 90
```

 `--yaw 45 --stitch DEGREE` を指定することで、2つの魚眼画像間の縫い目部分がキューブマップ画像の中心を横切るのを防ぎます。これらのオプションは、カメラの傾きやステッチングなどの補正なしで出力されたInsta360やOSMO 360の画像に効果的です。

### LichtFeld Studio向け

デフォルトでは、Postshot/Brush に適した座標軸変換が行われます。LichtFeld Studioの場合、 `--no_transform` を指定してください。

```
python metashape_360_lfs.py --images images --xml metashape.xml \
  --ply metashape.ply --output .
python cubemap_transforms_json.py . ./cubic --no_tranform
```

### オプション一覧

|オプション|説明|
|------|-----------|
|--yaw|水平方向の角度をシフトします (default=45.0 degrees)|
|--stitch|スティッチング領域を除外するための角度 (default=0.0 degrees)|
|--fov|各キューブマップ面の画像のFOV (default=90.0 degrees)|
|--no_image|画像の変換を行わず、transforms.json の変換のみ行います|
|--no_transform|座標軸変換を行いません|

## 3DGSソフトウェアへのインポート

各ソフトウェアで以下のファイルをインポートしてください:

### Postshot / Brush

- metashape.ply (`Metashape`で出力)
- transforms.json (出力ディレクトリ内)
- images (出力ディレクトリ内)
- masks (出力ディレクトリ内: オプション)

### LichtFeld Studio

- pointcloud.ply (`metashape_360_lfs`で変換)
- transforms.json (出力ディレクトリ内)
- images (出力ディレクトリ内)
- masks (出力ディレクトリ内: オプション)
