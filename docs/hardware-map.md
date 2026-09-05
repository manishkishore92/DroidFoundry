# Hardware Map

The hardware map combines proprietary blob classification and VINTF HAL declarations.

```bash
droidfoundry hardware ./firmware-dump --output hardware-map.md --json-out hardware-map.json
```

Detected areas include camera, audio, Bluetooth, Wi-Fi, GPS, sensors, fingerprint, NFC, DRM, graphics, radio and power.

The map is a hint for Android bring-up. It does not prove that hardware works, but it helps maintainers identify missing or visible subsystems before first boot testing.
