# Firmware comparison

DroidFoundry can compare two extracted firmware dumps.

```bash
droidfoundry compare ./old-firmware ./new-firmware --output firmware-compare.md
```

The comparison report includes:

- Metadata changes
- Added proprietary blobs
- Removed proprietary blobs
- Changed common blobs
- Added or removed image files
- Added or removed VINTF files
- Added or removed init files

This is useful when updating device blobs from a newer stock release.

## Recommended workflow

1. Extract the older stock firmware.
2. Extract the newer stock firmware.
3. Run `droidfoundry compare`.
4. Review added and removed blobs.
5. Update `proprietary-files.txt` carefully.
6. Rebuild the ROM and test on device.

Large files are compared by size to avoid slow hashing of complete firmware images. Smaller common files are hashed to detect content changes.
