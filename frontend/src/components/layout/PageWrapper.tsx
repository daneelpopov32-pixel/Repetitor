"use client";

import { ReactNode } from "react";
import { motion } from "framer-motion";
import { slideUp } from "@/lib/motion";

interface PageWrapperProps {
  children: ReactNode;
  title?: string;
  actions?: ReactNode;
}

export default function PageWrapper({ children, title, actions }: PageWrapperProps) {
  return (
    <motion.div className="layout-content" {...slideUp}>
      {(title || actions) && (
        <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
          {title && <h1 style={{ fontSize: "var(--text-3xl)", fontWeight: 700 }}>{title}</h1>}
          {actions && <div style={{ display: "flex", gap: "0.5rem" }}>{actions}</div>}
        </div>
      )}
      {children}
    </motion.div>
  );
}
