/**
 * useAnimatedValue.ts
 * Dynamic number counter animation hook.
 * Numbers smoothly count up/down instead of jumping.
 */
import { useState, useEffect, useRef } from 'react';

export function useAnimatedValue(target: number, duration: number = 400): number {
  const [value, setValue] = useState(target);
  const animRef = useRef<number>(0);
  const startRef = useRef(value);
  const startTimeRef = useRef(0);

  useEffect(() => {
    if (Math.abs(target - value) < 0.01) {
      setValue(target);
      return;
    }
    
    startRef.current = value;
    startTimeRef.current = performance.now();

    const animate = (now: number) => {
      const elapsed = now - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = startRef.current + (target - startRef.current) * eased;
      
      setValue(current);
      
      if (progress < 1) {
        animRef.current = requestAnimationFrame(animate);
      } else {
        setValue(target);
      }
    };

    animRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animRef.current);
  }, [target, duration]);

  return value;
}

/**
 * useAnimatedInteger — same as above but returns integers (for vehicle counts etc.)
 */
export function useAnimatedInteger(target: number, duration: number = 300): number {
  return Math.round(useAnimatedValue(target, duration));
}
