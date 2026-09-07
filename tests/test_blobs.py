from pathlib import Path

from droidfoundry.blobs import BlobGenerator


def test_blob_generator_collects_vendor_files(tmp_path: Path):
    target = tmp_path / "vendor" / "lib64" / "libcamera.so"
    target.parent.mkdir(parents=True)
    target.write_text("blob")
    assert BlobGenerator(tmp_path).collect() == ["vendor/lib64/libcamera.so"]
