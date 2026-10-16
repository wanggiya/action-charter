import { useCallback, useEffect, useRef } from "react";
import type { RefObject } from "react";

/** Preview only the camera during gestures; commit React state once it settles. */
export function useCanvasZoom(ref: RefObject<HTMLDivElement | null>, size: {width:number;height:number}, zoom:number, commit:(zoom:number)=>void) {
  const current = useRef(zoom);
  const active = useRef(false);
  const frame = useRef<number | null>(null);
  const target = useRef(zoom);
  const anchor = useRef({x:0,y:0,graphX:0,graphY:0});
  const stop = useCallback(() => {
    if(frame.current!==null) cancelAnimationFrame(frame.current);
    frame.current=null; active.current=false;
    ref.current?.classList.remove("is-zooming");
    commit(current.current);
  },[commit,ref]);
  const set = useCallback((value:number) => {
    stop(); current.current=value; target.current=value; commit(value);
  },[stop,commit]);
  useEffect(()=>{if(!active.current) {current.current=zoom;target.current=zoom;}},[zoom]);
  const animate = useCallback((value:number,x:number,y:number) => {
    const element=ref.current;
    if(!element) return;
    anchor.current={x,y,graphX:(element.scrollLeft+x)/current.current,graphY:(element.scrollTop+y)/current.current};
    target.current=Math.max(.2,Math.min(1.1,value));
    if(active.current) return;
    active.current=true; element.classList.add("is-zooming");
    const canvas=element.querySelector<HTMLElement>(".canvas");
    const sizer=element.querySelector<HTMLElement>(".canvas-sizer");
    const reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let previous=performance.now();
    const tick=(now:number)=>{
      const fraction=reducedMotion?1:1-Math.exp(-Math.min(64,now-previous)/40);
      previous=now;
      current.current+=(target.current-current.current)*fraction;
      const done=Math.abs(target.current-current.current)<.0002;
      if(done) current.current=target.current;
      if(canvas) canvas.style.transform=`scale(${current.current})`;
      if(sizer) {sizer.style.width=`${size.width*current.current}px`;sizer.style.height=`${size.height*current.current}px`;}
      const a=anchor.current;
      element.scrollLeft=a.graphX*current.current-a.x;
      element.scrollTop=a.graphY*current.current-a.y;
      if(done) stop(); else frame.current=requestAnimationFrame(tick);
    };
    frame.current=requestAnimationFrame(tick);
  },[ref,size.width,size.height,stop]);
  const step=useCallback((factor:number)=>{
    const element=ref.current;
    if(element) animate(target.current*factor,element.clientWidth/2,element.clientHeight/2);
  },[animate,ref]);
  useEffect(()=>{
    const element=ref.current;
    if(!element) return;
    const wheel=(event:WheelEvent)=>{
      // Keep the node's coordinate system fixed until its pointer gesture ends.
      if(element.querySelector('.is-dragging')) {event.preventDefault();return;}
      event.preventDefault();
      const unit=event.deltaMode===1?16:event.deltaMode===2?element.clientHeight:1;
      if(event.shiftKey){stop();element.scrollLeft+=(event.deltaY||event.deltaX)*unit;return;}
      if(!event.deltaY) return;
      const bounds=element.getBoundingClientRect();
      animate(target.current*Math.exp(-Math.max(-240,Math.min(240,event.deltaY*unit))*.0015),event.clientX-bounds.left-element.clientLeft,event.clientY-bounds.top-element.clientTop);
    };
    element.addEventListener('wheel',wheel,{passive:false});
    return()=>{element.removeEventListener('wheel',wheel);stop();};
  },[animate,ref,stop]);
  return {current,active,stop,set,step};
}
