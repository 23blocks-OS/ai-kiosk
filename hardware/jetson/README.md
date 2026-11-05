# Jetson Orin Nano Super — setup

Pilot hardware for the AI Kiosk: **NVIDIA Jetson Orin Nano Super
Developer Kit, 8 GB** (kit P/N 945-13766-0000-000).

## What is in the box

- The board (8 GB soldered LPDDR5, shared CPU + GPU — **RAM cannot be
  added**), heatsink + fan, preinstalled Wi-Fi module.
- **19 V / 45 W power supply included** — do not buy a separate one.
- No storage, no case, no screen, no keyboard/mouse.

## Storage

- **WD Blue SN5100 1 TB NVMe** (M.2 2280, PCIe Gen4 drive running at
  Gen3 speed in the Jetson's Gen3 x4 slot). Installs in the 2280 slot
  on the underside of the carrier board, held by one screw.
- A microSD card works for first boot, but NVMe is the real home for
  the OS and the models.

## OS install (first boot)

The Jetson arrives with **no OS and no storage**, so the OS is installed
from a USB stick:

1. On a Mac/PC, download the **Jetson ISO — JetPack 7.2.1**
   (file `jetsoninstaller-r39.2.1.iso`, **~4.7 GB**). Free NVIDIA
   Developer account required for the download.
2. Write the ISO to a USB stick with **Balena Etcher** (Intel build for
   the Intel Mac mini). NVIDIA's spec says a **16 GB or larger** stick;
   the ISO is 4.7 GB, so an **8 GB stick also works** — flash it ahead
   of time and let Etcher verify.
3. Install the SSD, plug in the screen, a wired keyboard/mouse, and the
   USB installer. Power on, boot the installer, install to NVMe.
4. First-boot Ubuntu setup: username/password, timezone, Wi-Fi, updates.
5. Set **25 W Super power mode**, then install the AI runtime
   (llama.cpp CUDA build or Ollama) and download Qwen3-VL 4B.

Firmware caveat: JetPack 7.2+ needs JetPack 6.x-generation UEFI/QSPI
firmware. If the installer boots to a black screen or a UEFI shell,
do the JetPack 6.x firmware update first — do not force it.

Fallback only: SDK Manager needs an x86 Ubuntu host PC and Force
Recovery Mode (short pins 9–10 of the J14 header). Not the first route.

## Video — DisplayPort only

The board has **DisplayPort 1.2 only**. No HDMI, and USB-C is not a
video output. The pilot screen is a 15.6" UPERFECT touchscreen
(1920×1080, Mini HDMI + USB-C ports), connected with a single
**DisplayPort-to-Mini HDMI cable** (full-size DP at the Jetson end,
Mini HDMI at the screen end — not Mini DisplayPort). Touch travels on
a separate **USB-A to USB-C** cable. Test touch on first boot; the
screen's bundled Bluetooth keyboard/touchpad is the fallback.

## Power

Jetson 7–25 W on its included 45 W adapter. The screen needs its own
USB-C power for all-day use (its battery lasts ~4.5 h). Plan on two
wall outlets / a power strip: Jetson + screen. Do not power the screen
off the Jetson's USB ports.

## Camera

- **First: any standard USB (UVC) webcam** in one of the 4× USB 3.2
  Type-A ports — plug-and-play on Ubuntu. Use the spare webcam on hand.
- **Second: Raspberry Pi Camera Module v2** via the board's MIPI CSI
  connectors (2×, 22-pin, 0.5 mm pitch) with a **15-pin to 22-pin
  conversion cable**. Better quality, more setup — try it after the
  USB webcam works.
- The UPERFECT screen has **no built-in camera**.

Point the camera at the document on the desk, not at a person's face.
It reads papers; it does not need to record people.

## Model ceiling (8 GB unified memory)

- 1–3 B quantized: fast, voice/text work.
- **7–8 B Q4_K_M: the sweet spot** (~4.6 GB weights, ~4K context).
- 9 B Q4: tight. 13 B: only Q3 with reduced context, not recommended.
- 14 B+, 8 B FP16/Q8: will not fit.
- Vision + LLM run together must share the same 8 GB — size them
  together. That is why the kiosk uses **one VLM (Qwen3-VL 4B)** as
  its single brain, not a chat LLM plus a separate vision model.

## Case

Not required to boot (heatsink + fan are included). For a kiosk, use
an Orin Nano-specific **ventilated** aluminum case that keeps the stock
fan and air path. A sealed box overheats. Case purchase is deferred.
