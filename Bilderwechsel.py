#!/usr/bin/env python3
"""
Raspberry Pi Folder Kiosk – Fullscreen Slideshow/Player (mit PDF-Unterstützung)

Neu: PDFs werden seitenweise im Vollbild angezeigt (PyMuPDF).

Features
- Bilder (jpg, jpeg, png, gif, bmp, webp) im Vollbild.
- Videos (mp4, mov, mkv, avi, m4v) im Vollbild (cvlc/mpv/omxplayer – was vorhanden ist).
- **PDFs**: Jede Seite als eigene Folie; Anzeigedauer separat einstellbar.
- Live-Ordnerüberwachung (watchdog); automatische Aktualisierung der Playlist.
- Tastatur:  
  ESC/q = Beenden · →/n = Nächstes · ←/p = Vorheriges · Space = Pause (Bilder/PDF) · r = neu einlesen · f = Vollbild
- Optional: zufällige Reihenfolge, rekursives Einlesen, Sortierung nach Name/Änderungsdatum.

Abhängigkeiten installieren (Raspberry Pi OS):
    sudo apt-get update && sudo apt-get install -y python3-pip vlc
    pip3 install pygame watchdog pymupdf

Startbeispiele:
    python3 kiosk_viewer.py --dir /home/pi/kiosk --delay 8 --shuffle
    # mit PDF-spezifischer Zeit und Render-Qualität
    python3 kiosk_viewer.py --dir /home/pi/kiosk --delay 8 --pdf-delay 10 --pdf-zoom 2.0

Hinweis: Für Videos wird bevorzugt "cvlc" (VLC) genutzt; fallback: mpv, omxplayer.

Autor: ChatGPT (GPT-5 Thinking) · Lizenz: MIT
"""
import argparse
import os
import sys
import time
import random
import subprocess
from pathlib import Path

import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE, K_q, K_RIGHT, K_LEFT, K_SPACE, K_n, K_p, K_r, K_f

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

try:
    import fitz  # PyMuPDF
    HAVE_PYMUPDF = True
except Exception:
    HAVE_PYMUPDF = False

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".m4v"}
PDF_EXTS   = {".pdf"}

class DirChangeHandler(FileSystemEventHandler):
    def __init__(self, on_change):
        super().__init__()
        self.on_change = on_change
    def on_any_event(self, event):
        self.on_change()

class KioskViewer:
    def __init__(self, directory: Path, delay: float, recursive: bool, shuffle: bool, sort: str,
                 pdf_delay: float, pdf_zoom: float, bg_color=(0,0,0)):
        self.directory = directory
        self.delay = delay
        self.recursive = recursive
        self.shuffle = shuffle
        self.sort = sort
        self.bg_color = bg_color
        self.pdf_delay = pdf_delay
        self.pdf_zoom = pdf_zoom

        # Playlist-Items sind Tupel (type, payload)
        # type ∈ {"image","video","pdf_page"}
        # payload: Path oder (Path, page_index)
        self.items = []
        self.index = 0
        self.paused = False
        self.fullscreen = True
        self.changed_flag = False

        pygame.init()
        pygame.display.set_caption("Raspberry Pi Kiosk Viewer")
        self._set_display(self.fullscreen)
        pygame.mouse.set_visible(False)
        self.clock = pygame.time.Clock()

        self.scan_files()
        self._setup_watchdog()

    def _set_display(self, fullscreen: bool):
        flags = pygame.FULLSCREEN if fullscreen else 0
        info = pygame.display.Info()
        self.screen_w, self.screen_h = info.current_w, info.current_h
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), flags)

    def _setup_watchdog(self):
        handler = DirChangeHandler(self._mark_changed)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.directory), recursive=self.recursive)
        self.observer.start()

    def _mark_changed(self):
        self.changed_flag = True

    def shutdown(self):
        try:
            self.observer.stop(); self.observer.join(timeout=2)
        except Exception:
            pass
        pygame.quit()

    def scan_files(self):
        files = []
        it = self.directory.rglob("*") if self.recursive else self.directory.glob("*")
        for p in it:
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            if ext in IMAGE_EXTS or ext in VIDEO_EXTS or ext in PDF_EXTS:
                files.append(p)
        if self.sort == "mtime":
            files.sort(key=lambda p: p.stat().st_mtime)
        else:
            files.sort(key=lambda p: str(p).lower())
        if self.shuffle:
            random.shuffle(files)

        # Playlist bauen (PDF -> einzelne Seiten)
        items = []
        for p in files:
            ext = p.suffix.lower()
            if ext in IMAGE_EXTS:
                items.append(("image", p))
            elif ext in VIDEO_EXTS:
                items.append(("video", p))
            elif ext in PDF_EXTS:
                if not HAVE_PYMUPDF:
                    items.append(("image", p))  # Fallback: später Text-Hinweis
                    continue
                try:
                    with fitz.open(str(p)) as doc:
                        for page_index in range(len(doc)):
                            items.append(("pdf_page", (p, page_index)))
                except Exception:
                    items.append(("image", p))  # Fallback mit Hinweis

        prev_item = self.current_item() if self.items else None
        self.items = items
        if prev_item and prev_item in self.items:
            self.index = self.items.index(prev_item)
        else:
            self.index = 0

    def current_item(self):
        if not self.items:
            return None
        return self.items[self.index]

    def next(self):
        if not self.items:
            return
        self.index = (self.index + 1) % len(self.items)

    def prev(self):
        if not self.items:
            return
        self.index = (self.index - 1) % len(self.items)

    def toggle_pause(self):
        self.paused = not self.paused

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self._set_display(self.fullscreen)

    def _scale_to_fit(self, surf):
        iw, ih = surf.get_width(), surf.get_height()
        sw, sh = self.screen_w, self.screen_h
        scale = min(sw / iw, sh / ih)
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        return pygame.transform.smoothscale(surf, (nw, nh))

    def _play_video_subprocess(self, path: Path):
        cmd = None
        if shutil_which("cvlc"):
            cmd = ["cvlc", "--quiet", "--no-video-title-show", "--fullscreen", "--play-and-exit", str(path)]
        elif shutil_which("mpv"):
            cmd = ["mpv", "--fs", "--quiet", "--no-osd-bar", "--ontop=no", "--keep-open=no", str(path)]
        elif shutil_which("omxplayer"):
            cmd = ["omxplayer", "-o", "hdmi", "--no-osd", str(path)]
        if cmd is None:
            self._show_text_center("Kein Videoplayer gefunden (cvlc/mpv/omxplayer)")
            self._flip(); time.sleep(3); return
        try:
            self.screen.fill(self.bg_color); self._flip()
            subprocess.run(cmd)
        except Exception as e:
            self._show_text_center(f"Video-Fehler: {e}")
            self._flip(); time.sleep(3)

    def _render_pdf_page_surface(self, pdf_path: Path, page_index: int):
        if not HAVE_PYMUPDF:
            return self._render_text_as_surface("PyMuPDF nicht installiert – 'pip3 install pymupdf'\n" + pdf_path.name)
        try:
            doc = fitz.open(str(pdf_path))
            page = doc.load_page(page_index)
            mat = fitz.Matrix(self.pdf_zoom, self.pdf_zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            mode = "RGB" if pix.n < 4 else "RGBA"
            img_bytes = pix.tobytes("png")
            import io
            surf = pygame.image.load(io.BytesIO(img_bytes), "png")
            doc.close()
            return surf
        except Exception as e:
            return self._render_text_as_surface(f"PDF-Fehler: {pdf_path.name}\n{e}")

    def _render_text_as_surface(self, text: str, size: int = 32):
        self.screen.fill(self.bg_color)
        try:
            font = pygame.font.SysFont(None, size)
        except Exception:
            pygame.font.init(); font = pygame.font.SysFont(None, size)
        # einfache Textfläche mit Umbruch
        lines = text.split("\n")
        max_w, total_h = 0, 0
        surfaces = []
        for line in lines:
            s = font.render(line, True, (200,200,200)); surfaces.append(s)
            max_w = max(max_w, s.get_width()); total_h += s.get_height() + 6
        surf = pygame.Surface((max_w+20, total_h+20))
        surf.fill(self.bg_color)
        y = 10
        for s in surfaces:
            surf.blit(s, (10, y)); y += s.get_height() + 6
        return surf

    def _show_text_center(self, text: str):
        surf = self._render_text_as_surface(text)
        surf = self._scale_to_fit(surf)
        rect = surf.get_rect(center=(self.screen_w//2, self.screen_h//2))
        self.screen.fill(self.bg_color)
        self.screen.blit(surf, rect)

    def _flip(self):
        pygame.display.flip()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                return False
            if event.type == KEYDOWN:
                if event.key in (K_ESCAPE, K_q):
                    return False
                elif event.key in (K_RIGHT, K_n):
                    self.next(); self.paused = False
                elif event.key in (K_LEFT, K_p):
                    self.prev(); self.paused = False
                elif event.key == K_SPACE:
                    self.toggle_pause()
                elif event.key == K_r:
                    self.scan_files()
                elif event.key == K_f:
                    self.toggle_fullscreen()
        return True

    def run(self):
        try:
            last_switch = time.monotonic()
            while True:
                if not self._handle_events():
                    break
                if self.changed_flag:
                    time.sleep(0.2); self.scan_files(); self.changed_flag = False

                current = self.current_item()
                if not current:
                    self._show_text_center("Keine Medien im Ordner gefunden"); self._flip(); self.clock.tick(30); continue

                kind, payload = current
                if kind == "image":
                    p = payload if isinstance(payload, Path) else Path(payload)
                    try:
                        img = pygame.image.load(str(p))
                        img = self._scale_to_fit(img)
                        self.screen.fill(self.bg_color)
                        rect = img.get_rect(center=(self.screen_w//2, self.screen_h//2))
                        self.screen.blit(img, rect)
                        self._flip()
                    except Exception as e:
                        self._show_text_center(f"Bild-Fehler: {Path(p).name}\n{e}"); self._flip(); time.sleep(2)
                        self.next(); last_switch = time.monotonic(); continue
                    if not self.paused and (time.monotonic() - last_switch) >= self.delay:
                        self.next(); last_switch = time.monotonic()

                elif kind == "video":
                    p = payload
                    self._play_video_subprocess(p)
                    self.next(); last_switch = time.monotonic()

                elif kind == "pdf_page":
                    pdf_path, page_idx = payload
                    surf = self._render_pdf_page_surface(pdf_path, page_idx)
                    surf = self._scale_to_fit(surf)
                    self.screen.fill(self.bg_color)
                    rect = surf.get_rect(center=(self.screen_w//2, self.screen_h//2))
                    self.screen.blit(surf, rect)
                    self._flip()
                    if not self.paused and (time.monotonic() - last_switch) >= self.pdf_delay:
                        self.next(); last_switch = time.monotonic()

                self.clock.tick(30)
        finally:
            self.shutdown()


def shutil_which(cmd):
    from shutil import which
    return which(cmd) is not None


def main():
    parser = argparse.ArgumentParser(description="Raspberry Pi Folder Kiosk – Fullscreen Slideshow/Player (mit PDF)")
    parser.add_argument("--dir", "-d", type=str, required=True, help="Quellordner mit Medien")
    parser.add_argument("--delay", "-t", type=float, default=6.0, help="Anzeigedauer für Bilder in Sekunden")
    parser.add_argument("--recursive", "-r", action="store_true", help="Unterordner rekursiv einlesen")
    parser.add_argument("--shuffle", "-s", action="store_true", help="Zufällige Reihenfolge")
    parser.add_argument("--sort", choices=["name", "mtime"], default="name", help="Sortierung (name|mtime)")
    parser.add_argument("--pdf-delay", type=float, default=8.0, help="Anzeigedauer pro PDF-Seite in Sekunden")
    parser.add_argument("--pdf-zoom", type=float, default=2.0, help="Render-Zoom für PDF (Qualität vs. Geschwindigkeit)")
    args = parser.parse_args()

    directory = Path(args.dir).expanduser().resolve()
    if not directory.exists() or not directory.is_dir():
        print(f"Ordner nicht gefunden: {directory}", file=sys.stderr)
        sys.exit(1)

    viewer = KioskViewer(directory, delay=args.delay, recursive=args.recursive, shuffle=args.shuffle, sort=args.sort,
                         pdf_delay=args.pdf_delay, pdf_zoom=args.pdf_zoom)
    viewer.run()


if __name__ == "__main__":
    main()
