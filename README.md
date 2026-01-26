# cubemap_transforms_json.py : transforms.json converter from equirectangular to cubemap

This script converts `transforms.json` for **360° equirectangular image** by [metashape_360_lfs](https://github.com/gradeeterna/metashape_360_lfs) into **cubemap-based images**.

That is, the following conversions are possible:

Metashape (Standard/Professional) > xml/pointcloud > transforms.json > cubemap > 3DGS software ([Jawset Postshot](https://www.jawset.com/), [Brush](https://github.com/ArthurBrussee/brush), [LichtFeld Studio](https://github.com/MrNeRF/LichtFeld-Studio), etc...)

[JP 日本語の説明](README.ja.md)

## Requirements

- Python 3.x (3.11.8 confirmed)
- NumPy
- OpenCV
- Pillow
- Open3D (used in metashape_360_lfs)
- [metashape_360_lfs.py](https://github.com/gradeeterna/metashape_360_lfs) 

```
pip install numpy opencv-python Pillow open3d
```

## Directory structure

### Input directory example

```
input_dir/
├─ metashape.xml
├─ metashape.ply
├─ transforms.json
├─ pointcloud.ply (optional)
├─ images/
│ ├─ image_000.jpg (or .png)
│ └─ image_001.jpg
│ └─ ...
└─ masks/ # (optional)
  ├─ image_000.png (or .jpg.png, .png.png)
  └─ image_001.png
  └─ ...
```

| File | Description |
|------|-------------|
|metashape.ply|Expoted in Metashape [File > Export > Export Point Cloud]|
|metashape.xml|Expoted in Metashape [File > Export > Export Cameras]|
|transforms.json|Converted by metashape_360_lfs|
|pointcloud.ply|Converted by metashape_360_lfs (optional)|

### Output directory example

```
output_dir/
├─ transforms.json
├─ images/
│ ├─ image_000_nx.jpg (or .png)
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


## Usage

### Basic usage

Convert transforms.json and images in the current directory: (also convert if masks directory exists)
```
python metashape_360_lfs.py --images images --xml metashape.xml --output .
python cubemap_transforms_json.py .
```

### Detailed

With specifying output directory:
```
python cubemap_transforms_json.py . ./cubic
```

With options:

```
python cubemap_transforms_json.py . ./cubic \
  --yaw 45 \
  --stitch 2.5 \
  --fov 90
```

Specifying `--yaw 45 --stitch DEGREE` will prevent the stitching area between two fisheye images from crossing the center of the cubemap image. These options are effective for Insta360 and OSMO 360 images without any image correction like camera tilt and stitching.

### For LichtFeld Studio

By default, coordinate axis transformation suitable for Postshot/Brush is performed. For LichtFeld Studio, specify `--no_transform`.

```
python metashape_360_lfs.py --images images --xml metashape.xml \
  --ply metashape.ply --output .
python cubemap_transforms_json.py . ./cubic --no_tranform
```

### Options

|Option|Description|
|------|-----------|
|--yaw|Shift the horizontal angle (default=45.0 degrees)|
|--stitch|Angle to avoid stitching areas (default=0.0 degrees)|
|--fov|Field of view for cubemap faces (default=90.0 degrees)|
|--no_image|Disable image conversion. Only transforms.json will be converted.|
|--no_transform|Disable coordinate axis conversion.|

## Import into 3DGS software

Import the following files in each software:

### Postshot / Brush

- metashape.ply (exported in `Metashape`)
- transforms.json (in the output directory)
- images (in the output directory)
- masks (in the output directory: optional)

### LichtFeld Studio

- pointcloud.ply (converted by `metashape_360_lfs`)
- transforms.json (in the output directory)
- images (in the output directory)
- masks (in the output directory: optional)
