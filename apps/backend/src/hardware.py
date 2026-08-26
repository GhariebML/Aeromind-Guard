import os
import platform
import psutil
from typing import Dict, Any, Optional

def get_hardware_telemetry() -> Dict[str, Any]:
    """
    Detects local host hardware capabilities: CPU, RAM, GPU, CUDA, and VRAM.
    Gracefully handles environments without NVIDIA GPU/CUDA.
    """
    # CPU
    cpu_percent = psutil.cpu_percent(interval=None)
    cpu_count = psutil.cpu_count(logical=True) or 1
    cpu_model = platform.processor() or platform.machine() or "Host CPU"

    # RAM
    ram = psutil.virtual_memory()
    ram_total_gb = round(ram.total / (1024 ** 3), 2)
    ram_used_gb = round(ram.used / (1024 ** 3), 2)
    ram_percent = ram.percent

    # GPU / CUDA detection
    has_gpu = False
    gpu_name = None
    cuda_available = False
    cuda_version = None
    vram_total_mb = None
    vram_used_mb = None

    # Try PyTorch CUDA if available
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            has_gpu = True
            gpu_name = torch.cuda.get_device_name(0)
            cuda_version = torch.version.cuda
            vram_total_mb = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 2), 1)
            vram_used_mb = round(torch.cuda.memory_allocated(0) / (1024 ** 2), 1)
    except Exception:
        pass

    # Fallback to system query if PyTorch is absent
    if not has_gpu:
        try:
            # Check NVIDIA SMI on Windows/Linux
            import subprocess
            smi = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,memory.used", "--format=csv,noheader"],
                                 capture_output=True, text=True, timeout=1.5)
            if smi.returncode == 0 and smi.stdout.strip():
                parts = [p.strip() for p in smi.stdout.strip().split(",")]
                if len(parts) >= 1:
                    has_gpu = True
                    gpu_name = parts[0]
                    cuda_available = True
                    if len(parts) >= 3:
                        vram_total_mb = float(parts[1].replace("MiB", "").strip())
                        vram_used_mb = float(parts[2].replace("MiB", "").strip())
        except Exception:
            pass

    return {
        "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "cpu_model": cpu_model,
        "cpu_cores": cpu_count,
        "cpu_percent": cpu_percent,
        "ram_total_gb": ram_total_gb,
        "ram_used_gb": ram_used_gb,
        "ram_percent": ram_percent,
        "has_gpu": has_gpu,
        "gpu_name": gpu_name or ("NVIDIA GPU Detected" if has_gpu else "Integrated / CPU Inference"),
        "cuda_available": cuda_available,
        "cuda_version": cuda_version or ("12.x" if cuda_available else "N/A"),
        "vram_total_mb": vram_total_mb,
        "vram_used_mb": vram_used_mb
    }
