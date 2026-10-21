#!/usr/bin/env python3
"""The customer path on an INSTALLED Crisp.app: start its engine, GET /health, one free export, one ncnn upscale.

    python3 scripts/ci_customer_path.py --app /Applications/Crisp.app --out DIR [--port 8841] [--expect-build 1.0.N]
    python3 scripts/ci_customer_path.py --dev-repo . --out DIR      # the same checks on a source engine (proves the driver)

Run by .github/workflows/macos14-customer-path.yml on GitHub's macos-14 and macos-15 runners (Apple Silicon), after
the public release DMG is downloaded, mounted and copied to /Applications. That is the one place the macOS floor can be
PROVEN: this box runs macOS 26, and a machine cannot detect a floor it is standing on. Stdlib only, so it runs on any
python3 the runner has. Exit 0 only when every check passed; DIR/summary.json says which did what.

  1. the engine starts and answers /health with the build the app's Info.plist names (a binary that needs a newer
     macOS dies in dyld before it can answer, and its log says so: classified as "floor");
  2. a FREE export, the way a buyer's first one goes: trim 4 s to 2 s, then compress the trim; both come out, with
     the duration they should have;
  3. an upscale on the ncnn binary (CRISP_NO_COREML=1; runner VMs have no Core ML GPU worth timing): 160x90 in,
     320x180 out, with upscayl-bin seen running under the engine.

⚠️ A RUNNER IS A VM, AND TWO THINGS A REAL MAC HAS MAY BE MISSING THERE. They are classified, never passed silently:
  - no Vulkan/Metal device for ncnn: the upscale fails with "gpu" and the run fails, saying the upscale was NOT PROVEN
    on this runner (not that Crisp is broken on macOS 14);
  - no VideoToolbox encoder: the free export and the upscale are retried once with av1 (SVT-AV1 in software: a codec
    the engine's API accepts, unlike a raw libx264, which it answers 400 'unsupported codec'),
    and the summary says the default encoder was unavailable, so a pass never hides which encoder made it.
A fresh HOME makes it a new free copy and keeps the runner's (or this Mac's) real profile out of it.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

H = {"Origin": "tauri://localhost", "Content-Type": "application/json"}
_FLOOR = re.compile(r"Symbol not found|Library not loaded|built for macOS [\d.]+ which is newer than running OS|"
                    r"incompatible (?:platform|OS)|dyld\[\d+\]", re.I)
_GPU = re.compile(r"vkCreateInstance|vkEnumeratePhysicalDevices|invalid gpu device|no vulkan|failed to create gpu|"
                  r"VK_ERROR", re.I)
_VT = re.compile(r"videotoolbox|compression session|Error while opening encoder|Could not open encoder|"
                 r"kVTVideoEncoder|-12908|-12902", re.I)


def classify(text: str) -> str:
    """Why something failed, from its error text and the engine log: floor | gpu | encoder | other."""
    if _FLOOR.search(text):
        return "floor"
    if _GPU.search(text):
        return "gpu"
    if _VT.search(text):
        return "encoder"
    return "other"


def trim_body(src: str, out: str, codec: str | None = None) -> dict:
    b = {"task": "trim", "input": src, "output": out, "trim_start": 1.0, "trim_end": 3.0}
    return {**b, "codec": codec} if codec else b


def compress_body(src: str, out: str, codec: str | None = None) -> dict:
    b = {"task": "compress", "input": src, "output": out, "compress_level": "medium"}
    return {**b, "codec": codec} if codec else b


def upscale_body(src: str, out: str, codec: str | None = None) -> dict:
    b = {"task": "upscale", "input": src, "output": out, "preset": "enhance", "scale": 2}
    return {**b, "codec": codec} if codec else b


#: The software encoder to retry with on a runner whose VM has no VideoToolbox (GitHub's macos-14 image, 2026-10-21):
#: one of the engine API's own codec names (ffmpeg_io.VIDEO_CODECS), so the retry reaches ffmpeg instead of a 400.
SOFTWARE_CODEC = "av1"
#: The upscale's retry uses software ProRes instead: an AV1 UPSCALE fails on every Crisp up to 1.0.1580, because the
#: upscale encodes into .mov intermediates and ffmpeg refuses AV1 in MOV ("av1 only supported in MP4 and AVIF"). That
#: is a pre-existing engine bug (queued to fix), not a macOS-floor result; ProRes needs no VideoToolbox and lives in MOV.
SOFTWARE_UPSCALE_CODEC = "prores_lt"


def same_build(got, want) -> bool:
    """/health reports the build NUMBER (1580); the plist and the manifest say 1.0.1580. Compare the number."""
    return str(got).split(".")[-1] == str(want).split(".")[-1]


def near(got: float | None, want: float, tol: float = 0.35) -> bool:
    return got is not None and abs(got - want) <= tol


class Engine:
    def __init__(self, cmd: list[str], cwd: Path, port: int, home: Path, log: Path):
        self.port, self.log_path = port, log
        env = {**os.environ, "HOME": str(home), "CRISP_NO_COREML": "1", "CRISP_NO_AUTOTUNE": "1"}
        self.log = open(log, "w")
        self.proc = subprocess.Popen([*cmd, "serve", "--port", str(port)], cwd=str(cwd), env=env,
                                     stdout=self.log, stderr=subprocess.STDOUT)

    def call(self, path: str, body: dict | None = None) -> tuple[int, dict]:
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", headers=H,
                                   data=None if body is None else json.dumps(body).encode())
        try:
            resp = urllib.request.urlopen(r, timeout=60)
            return resp.status, json.load(resp)
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.load(e)
            except Exception:  # noqa: BLE001
                return e.code, {}

    def log_text(self) -> str:
        self.log.flush()
        return self.log_path.read_text(encoding="utf-8", errors="replace")

    def children(self) -> set[str]:
        out = subprocess.run(["ps", "-Ao", "pid=,ppid=,comm="], capture_output=True, text=True).stdout.splitlines()
        kids: dict[int, list[tuple[int, str]]] = {}
        for line in out:
            parts = line.split(None, 2)
            if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
                kids.setdefault(int(parts[1]), []).append((int(parts[0]), os.path.basename(parts[2].strip())))
        names, todo = set(), [self.proc.pid]
        while todo:
            for cpid, name in kids.get(todo.pop(), []):
                names.add(name)
                todo.append(cpid)
        return names

    def wait_health(self, budget_s: float) -> dict | None:
        t0 = time.monotonic()
        while time.monotonic() - t0 < budget_s:
            if self.proc.poll() is not None:
                return None
            try:
                code, h = self.call("/health")
                if code == 200 and h.get("build"):
                    return h
            except Exception:  # noqa: BLE001
                pass
            time.sleep(1.0)
        return None

    def job(self, body: dict, budget_s: float = 900, poll_s: float = 0.25) -> tuple[dict, set[str]]:
        code, j = self.call("/jobs", body)
        jid = j.get("id") or (j.get("job") or {}).get("id")
        if code != 200 or not jid:
            return {"status": f"http {code}", "error": json.dumps(j)[:400]}, set()
        seen: set[str] = set()
        t0 = time.monotonic()
        while time.monotonic() - t0 < budget_s:
            seen |= self.children()
            _, st = self.call(f"/jobs/{jid}")
            if st.get("status") in ("done", "failed", "cancelled", "error"):
                return st, seen
            time.sleep(poll_s)
        return {"status": "timeout", "error": f"no result in {budget_s:.0f} s"}, seen

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(20)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        self.log.close()


def probe(ffprobe: Path, path: str) -> dict:
    out = subprocess.run([str(ffprobe), "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,codec_name,nb_frames:format=duration", "-of", "json", path],
                         capture_output=True, text=True, timeout=60).stdout
    try:
        d = json.loads(out or "{}")
    except ValueError:
        return {}
    s = (d.get("streams") or [{}])[0]
    dur = (d.get("format") or {}).get("duration")
    return {"width": s.get("width"), "height": s.get("height"), "codec": s.get("codec_name"),
            "frames": s.get("nb_frames"), "duration": float(dur) if dur else None}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--app", type=Path, default=Path("/Applications/Crisp.app"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--port", type=int, default=8841)
    ap.add_argument("--expect-build", default=None, help="the build the live manifest names (default: the plist's)")
    ap.add_argument("--health-budget", type=float, default=240.0)
    ap.add_argument("--dev-repo", type=Path, default=None,
                    help="run <repo>/backend/cli.py on <repo>/.venv's python instead of the app (a driver check, "
                         "never a floor proof: the source engine is not the shipped one)")
    a = ap.parse_args(argv)
    if a.port in (8766, 8799):
        print("✗ 8799 is the installed app's own port and 8766 another product's; pick another", file=sys.stderr)
        return 2
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if a.dev_repo:
        repo = a.dev_repo.resolve()
        py = repo / ".venv" / "bin" / "python"
        cmd, cwd = [str(py if py.exists() else sys.executable), str(repo / "backend" / "cli.py")], repo
        ffmpeg, ffprobe = repo / "vendor" / "ffmpeg" / "ffmpeg", repo / "vendor" / "ffmpeg" / "ffprobe"
        info = {"CFBundleVersion": None, "LSMinimumSystemVersion": None}
    else:
        res = a.app / "Contents" / "Resources" / "crisp"
        cmd, cwd = [str(res / "crisp")], res
        ffmpeg, ffprobe = res / "ffmpeg", res / "ffprobe"
        info = plistlib.loads((a.app / "Contents" / "Info.plist").read_bytes())
    summary: dict = {"macos": platform.mac_ver()[0], "machine": platform.machine(),
                     "engine": "source (--dev-repo: NOT the shipped engine)" if a.dev_repo else str(a.app),
                     "app_build": info.get("CFBundleVersion"), "app_min_macos": info.get("LSMinimumSystemVersion"),
                     "checks": []}

    def check(name: str, ok: bool, detail: str = "", why: str = "") -> bool:
        summary["checks"].append({"name": name, "ok": ok, "detail": detail, "why": "" if ok else why})
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else "")
              + ("" if ok or not why else f"  [classified: {why}]"), flush=True)
        return ok

    print(f"macOS {summary['macos']} {summary['machine']} · Crisp {summary['app_build']} · "
          f"LSMinimumSystemVersion {summary['app_min_macos']}", flush=True)
    home = Path(tempfile.mkdtemp(prefix="crisp-ci-home-"))
    work = out / "work"
    work.mkdir(exist_ok=True)
    eng = Engine(cmd, cwd, a.port, home, out / "engine.log")
    try:
        h = eng.wait_health(a.health_budget)
        want = a.expect_build or summary["app_build"]
        if not h:
            text = eng.log_text()
            check("the engine starts and answers /health", False,
                  f"exit {eng.proc.poll()}; log tail: {text[-600:]!r}", classify(text))
            return finish(out, summary)
        (out / "health.json").write_text(json.dumps(h, indent=2))
        got = (h.get("build") or {}).get("number")
        check("the engine starts and answers /health", True, f"build {got}, coreml {h.get('coreml')}")
        if want:
            check("…and it is the build the app names", same_build(got, want), f"/health {got}, expected {want}", "other")

        # the clips, made by the APP'S ffmpeg: loading it at all is part of the floor proof
        clip, tiny = work / "clip.mp4", work / "tiny.mp4"
        mk = subprocess.run([str(ffmpeg), "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=10",
                             "-f", "lavfi", "-i", "sine=frequency=440", "-t", "4", "-c:v", "libx264", "-pix_fmt",
                             "yuv420p", "-c:a", "aac", "-shortest", str(clip)], capture_output=True, text=True)
        mk2 = subprocess.run([str(ffmpeg), "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=10",
                              "-t", "3", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(tiny)],
                             capture_output=True, text=True)
        if not check("the bundled ffmpeg runs and makes the test clips", mk.returncode == 0 and mk2.returncode == 0,
                     (mk.stderr + mk2.stderr)[-400:], classify(mk.stderr + mk2.stderr)):
            return finish(out, summary)

        # FREE EXPORT: trim, then compress the trim
        def export(make, src, name, want_dur):
            st, _ = eng.job(make(str(src), str(work / name)))
            enc = "default"
            # retry ONLY on the job's own error text: the log names the encoder on every healthy render too
            if st.get("status") != "done" and classify(str(st.get("error") or "")) == "encoder":
                st, _ = eng.job(make(str(src), str(work / name), SOFTWARE_CODEC))
                enc = f"{SOFTWARE_CODEC} (software; the default VideoToolbox encoder is unavailable on this runner)"
            outp = (st.get("result") or {}).get("output") or str(work / name)
            meta = probe(ffprobe, outp) if os.path.exists(outp) else {}
            ok = st.get("status") == "done" and near(meta.get("duration"), want_dur)
            why = classify(f"{st.get('error')} {eng.log_text()[-3000:]}")
            check(f"free export: {name}", ok, f"{st.get('status')} · {meta} · encoder {enc} · "
                                               f"{str(st.get('error') or '')[:200]}", why)
            return outp if ok else None

        trimmed = export(trim_body, clip, "trimmed.mp4", 2.0)
        if trimmed:
            export(compress_body, trimmed, "compressed.mp4", 2.0)

        # NCNN UPSCALE
        # polled every 50 ms: 30 frames this small can finish on a fast GPU before a slower poll ever sees the binary
        st, seen = eng.job(upscale_body(str(tiny), str(work / "upscaled.mp4")), poll_s=0.05)
        up_enc = "default"
        if st.get("status") != "done" and classify(f"{st.get('error')} {eng.log_text()[-4000:]}") == "encoder":
            st, seen2 = eng.job(upscale_body(str(tiny), str(work / "upscaled.mov"), SOFTWARE_UPSCALE_CODEC), poll_s=0.05)
            seen = seen | seen2
            up_enc = f"{SOFTWARE_UPSCALE_CODEC} (software; no VideoToolbox on this runner)"
        outp = (st.get("result") or {}).get("output") or str(work / ("upscaled.mov" if up_enc != "default" else "upscaled.mp4"))
        meta = probe(ffprobe, outp) if os.path.exists(outp) else {}
        text = eng.log_text()
        ok = st.get("status") == "done" and (meta.get("width"), meta.get("height")) == (320, 180)
        why = classify(f"{st.get('error')} {text[-4000:]}")
        detail = (f"{st.get('status')} · {meta} · encoder {up_enc} · "
                  f"upscaler processes seen: {sorted(seen & {'upscayl-bin', 'crisp-vision'})}"
                  + (f" · job error: {str(st.get('error'))[:900]}" if st.get("error") else ""))
        (out / "upscale-job.json").write_text(json.dumps(st, indent=2, default=str))
        if not ok and why == "gpu":
            detail += " · NOT PROVEN on this runner: ncnn found no GPU device (a VM limit, not a macOS-floor result)"
        check("ncnn upscale 160x90 -> 320x180", ok, detail, why)
        check("…on the ncnn binary, not Core ML", "upscayl-bin" in seen and "on Core ML" not in text,
              f"seen {sorted(seen)}", "other")
        return finish(out, summary)
    finally:
        eng.stop()
        shutil.rmtree(home, ignore_errors=True)


def finish(out: Path, summary: dict) -> int:
    summary["passed"] = bool(summary["checks"]) and all(c["ok"] for c in summary["checks"])
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\n{'CUSTOMER PATH OK' if summary['passed'] else 'CUSTOMER PATH FAILED'} on macOS {summary['macos']} "
          f"({sum(c['ok'] for c in summary['checks'])}/{len(summary['checks'])} checks)", flush=True)
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
