# tetraface-3dgs-utils

A collection of scripts I use and develop as part of a 3D Gaussian Splatting (3DGS) workflow.

[JP 日本語の説明](README.ja.md)

## Requirements

- [CUDA Toolkit 12.8](https://developer.nvidia.com/cuda-12-8-0-download-archive) (for GPU-enabled PyTorch workflows)
- [Python 3.x](https://www.python.org/) (confirmed with 3.11.8)
- [metashape_360_lfs.py (fork)](https://github.com/tetraface/metashape_360_lfs)

### Depended python modules

- NumPy
- OpenCV
- Pillow
- Open3D (used by `metashape_360_lfs`)
- PyTorch 2.8.0 (with CUDA 12.8)
- ultralytics
- tqdm

Install example (CUDA 12.8 PyTorch wheel + other deps):

```bash
pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
pip install numpy opencv-python Pillow open3d ultralytics tqdm
```

## Summary of scripts

### `cubemap_transforms_json.py`

Convert transforms.json produced for 360° equirectangular data (by `metashape_360_lfs`) into a cubemap-friendly format usable by common 3DGS tools.<br>
See detailed documentation: [doc/cubemap_transforms_json.md](doc/cubemap_transforms_json.md).<br>
![mask example](images/yaw45.jpg)

### `stitch_mask.py`

Generate masks that exclude angular regions outside the two fisheye lenses in a 360° image. Useful when stitch seams become visible (for example in tight indoor scenes).<br>
See details: [doc/stitch_mask.md](doc/stitch_mask.md)<br>
![mask example](images/stitch_mask.png)

### `yolo_mask.py`

Detect people in 360° images and generate mask PNGs.<br>
See details: [doc/yolo_mask.md](doc/yolo_mask.md)<br>
![mask example](images/yolo_mask.png)

