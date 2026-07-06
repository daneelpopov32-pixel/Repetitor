export default function Spinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  return <div className={`spinner ${size === "lg" ? "spinner-lg" : ""}`} />;
}
