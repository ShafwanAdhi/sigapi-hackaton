import {
  ArrowRight,
  CalendarDays,
  CircleCheck,
  CircleX,
  Image,
  ImagePlus,
  Info,
  LoaderCircle,
  LocateFixed,
  LockKeyhole,
  Map,
  MapPin,
  ShieldCheck,
  TriangleAlert,
  X,
} from 'lucide-react';

const icons = {
  pin: MapPin,
  calendar: CalendarDays,
  map: Map,
  checkCircle: CircleCheck,
  crossCircle: CircleX,
  cross: X,
  shield: ShieldCheck,
  warning: TriangleAlert,
  info: Info,
  locate: LocateFixed,
  image: Image,
  imagePlus: ImagePlus,
  lock: LockKeyhole,
  arrow: ArrowRight,
  loader: LoaderCircle,
} as const;

export function Icon({ name, size = 20, className }: { name: keyof typeof icons; size?: number; className?: string }) {
  const LucideIcon = icons[name];
  return <LucideIcon aria-hidden="true" focusable="false" size={size} strokeWidth={1.8} className={className} />;
}
