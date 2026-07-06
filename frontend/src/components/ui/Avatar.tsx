interface AvatarProps {
  name: string;
  size?: "sm" | "md" | "lg";
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export default function Avatar({ name, size = "md" }: AvatarProps) {
  return (
    <div className={`avatar ${size === "lg" ? "avatar-lg" : ""}`}>
      {getInitials(name)}
    </div>
  );
}
