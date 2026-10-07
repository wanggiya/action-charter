export type Point = { x: number; y: number };
export function canonicalDragPosition(origin: Point, delta: Point, zoom: number, horizontal: boolean): Point {
  const dx = delta.x / zoom, dy = delta.y / zoom;
  return { x: Math.min(4000, Math.max(0, origin.x + (horizontal ? dx : dy / .72))), y: Math.min(4000, Math.max(0, origin.y + (horizontal ? dy : dx / 1.25))) };
}
export function displayDragPosition(origin: Point, displayed: Point, current: Point, horizontal: boolean): Point {
  return { x: displayed.x + (horizontal ? current.x - origin.x : (current.y - origin.y) * 1.25), y: displayed.y + (horizontal ? current.y - origin.y : (current.x - origin.x) * .72) };
}
export function bezierGeometry(start: Point, end: Point, horizontal: boolean) {
  const bend = horizontal ? (start.x + end.x) / 2 : (start.y + end.y) / 2;
  return { path: horizontal ? `M ${start.x} ${start.y} C ${bend} ${start.y}, ${bend} ${end.y}, ${end.x} ${end.y}` : `M ${start.x} ${start.y} C ${start.x} ${bend}, ${end.x} ${bend}, ${end.x} ${end.y}`, labelX: horizontal ? bend : (start.x + end.x) / 2, labelY: horizontal ? (start.y + end.y) / 2 - 7 : bend - 7 };
}

type Wire = { path: SVGPathElement; label: SVGTextElement | null; geometry: (position: Point) => ReturnType<typeof bezierGeometry> };
export function createNodeDragPreview(element: HTMLElement, origin: Point, wires: Wire[]) {
  const originalTransform = element.style.transform;
  const previous = wires.map((wire) => ({ path: wire.path.getAttribute("d"), x: wire.label?.getAttribute("x"), y: wire.label?.getAttribute("y") }));
  const canvas = element.closest?.(".canvas");
  canvas?.classList.add("node-drag-active");
  element.classList.add("is-dragging");
  return {
    move(position: Point) {
      element.style.transform = `translate3d(${position.x - origin.x}px, ${position.y - origin.y}px, 0)`;
      for (const wire of wires) {
        const geometry = wire.geometry(position);
        wire.path.setAttribute("d", geometry.path);
        wire.label?.setAttribute("x", String(geometry.labelX));
        wire.label?.setAttribute("y", String(geometry.labelY));
      }
    },
    finish(cancelled = false) {
      element.style.transform = originalTransform;
      element.classList.remove("is-dragging");
      canvas?.classList.remove("node-drag-active");
      if (cancelled) wires.forEach((wire, index) => {
        const old = previous[index];
        if (old.path != null) wire.path.setAttribute("d", old.path);
        if (old.x != null) wire.label?.setAttribute("x", old.x);
        if (old.y != null) wire.label?.setAttribute("y", old.y);
      });
    },
  };
}
