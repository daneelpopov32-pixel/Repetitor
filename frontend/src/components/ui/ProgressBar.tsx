"use client";

import { motion } from "framer-motion";

interface ProgressBarProps {
  value: number; // 0-100
  variant?: "default" | "success";
}

export default function ProgressBar({ value, variant = "default" }: ProgressBarProps) {
  return (
    <div className={`progress ${variant === "success" ? "progress-success" : ""}`}>
      <motion.div
        className="progress-fill"
        initial={{ width: 0 }}
        animate={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      />
    </div>
  );
}
