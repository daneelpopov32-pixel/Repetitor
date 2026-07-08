/** Reusable framer-motion presets — calm, purposeful animations. */

export const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  transition: { duration: 0.3 },
};

export const slideUp = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.35, ease: "easeOut" as const },
};

export const scaleIn = {
  initial: { opacity: 0, scale: 0.97 },
  animate: { opacity: 1, scale: 1 },
  transition: { duration: 0.25, ease: "easeOut" as const },
};

export const stagger = {
  animate: { transition: { staggerChildren: 0.05 } },
};

export const expand = {
  initial: { height: 0, opacity: 0 },
  animate: { height: "auto" as const, opacity: 1 },
  exit: { height: 0, opacity: 0 },
  transition: { duration: 0.25, ease: "easeInOut" as const },
};

export const hoverScale = {
  whileHover: { scale: 1.01 },
  whileTap: { scale: 0.99 },
};
