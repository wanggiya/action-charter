export type Point = { x: number; y: number };
export function canonicalDragPosition(origin: Point, delta: Point, zoom: number, horizontal: boolean): Point {
  const dx = delta.x / zoom, dy = delta.y / zoom;
  return { x: Math.min(16000, Math.max(0, origin.x + (horizontal ? dx : dy / .72))), y: Math.min(16000, Math.max(0, origin.y + (horizontal ? dy : dx / 1.25))) };
}
export function displayDragPosition(origin: Point, displayed: Point, current: Point, horizontal: boolean): Point {
  return { x: displayed.x + (horizontal ? current.x - origin.x : (current.y - origin.y) * 1.25), y: displayed.y + (horizontal ? current.y - origin.y : (current.x - origin.x) * .72) };
}
export function bezierGeometry(start: Point, end: Point, horizontal: boolean) {
  if(horizontal && end.x < start.x+36) {
    const lane=Math.max(start.y,end.y)+72;
    return {path:`M ${start.x} ${start.y} C ${start.x+40} ${start.y}, ${start.x+40} ${lane}, ${start.x+40} ${lane} L ${end.x-40} ${lane} C ${end.x-40} ${lane}, ${end.x-40} ${end.y}, ${end.x} ${end.y}`,labelX:(start.x+end.x)/2,labelY:lane-7};
  }
  if(!horizontal && end.y < start.y+36) {
    const lane=Math.max(start.x,end.x)+72;
    return {path:`M ${start.x} ${start.y} C ${start.x} ${start.y+40}, ${lane} ${start.y+40}, ${lane} ${start.y+40} L ${lane} ${end.y-40} C ${lane} ${end.y-40}, ${end.x} ${end.y-40}, ${end.x} ${end.y}`,labelX:lane+7,labelY:(start.y+end.y)/2};
  }
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
