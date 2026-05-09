"""
run_all.py — Jalankan semua 7 bot sekaligus
Usage: python run_all.py
"""
import subprocess, sys, time

bots = [
    ("Orchestrator", "bot1_orchestrator/main.py"),
    ("Worker      ", "bot2_worker/main.py"),
    ("Critic      ", "bot3_critic/main.py"),
    ("Refiner     ", "bot4_refiner/main.py"),
    ("FactChecker ", "bot5_factchecker/main.py"),
    ("Reminder    ", "bot6_reminder/main.py"),
    ("Market BTC  ", "bot7_btc/main.py"),
]

processes = []
print("Menjalankan semua 7 bot...\n")

for name, path in bots:
    print(f"  Starting {name}...")
    p = subprocess.Popen(
        [sys.executable, path],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    processes.append((name, p))
    time.sleep(1.5)

print("\nSemua bot berjalan! Tekan Ctrl+C untuk stop semua.\n")

try:
    while True:
        for name, p in processes:
            line = p.stdout.readline()
            if line:
                print(f"[{name}] {line.strip()}")
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nMenghentikan semua bot...")
    for name, p in processes:
        p.terminate()
        print(f"  Stopped: {name}")
    print("Semua bot dihentikan.")