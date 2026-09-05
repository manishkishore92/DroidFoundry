# Firmware dumps

DroidFoundry expects an extracted Android firmware dump, not a single untouched ZIP.

A useful dump may contain folders and files such as:

```text
system/build.prop
vendor/build.prop
product/build.prop
odm/build.prop
system_ext/build.prop
vendor/etc/vintf/
vendor/etc/init/
vendor/etc/permissions/
vendor/lib/
vendor/lib64/
vendor/bin/
vendor/firmware/
boot.img
vendor_boot.img
dtbo.img
vbmeta.img
super.img
```

## Partial dumps

Partial dumps are supported. DroidFoundry will scan whatever exists and warn about missing items.

## Property files

Property files are important because they help detect:

- Brand
- Manufacturer
- Device codename
- Model
- Android version
- SDK level
- Security patch
- Build fingerprint
- Platform
- Shipping API level

## Vendor files

Vendor files are useful for proprietary blob lists, VINTF analysis, init service review and fstab review.

## Image files

Image files such as `boot.img`, `vendor_boot.img`, `dtbo.img`, `vbmeta.img` and `super.img` help identify boot, recovery, dynamic partition and verified boot layouts.

## Before generating files

Run:

```bash
droidfoundry doctor ./firmware-dump
```

Fix missing extraction pieces when possible, then generate the workspace.
