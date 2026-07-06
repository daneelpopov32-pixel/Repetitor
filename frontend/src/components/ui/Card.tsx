"use client";

import { CSSProperties, ReactNode } from "react";
import { motion } from "framer-motion";

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  onClick?: () => void;
  style?: CSSProperties;
}

export default function Card({ children, className = "", hover = false, onClick, style }: CardProps) {
  const classes = `card ${hover ? "card-hover card-clickable" : ""} ${className}`;
  if (hover || onClick) {
    return (
      <motion.div
        className={classes}
        onClick={onClick}
        whileHover={{ y: -1 }}
        transition={{ duration: 0.15 }}
        style={style}
      >
        {children}
      </motion.div>
    );
  }
  return <div className={classes} style={style}>{children}</div>;
}
