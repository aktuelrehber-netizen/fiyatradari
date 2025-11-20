import Image from 'next/image'

interface LogoProps {
  className?: string
  showText?: boolean
  textColor?: string
}

export function Logo({ className = "", showText = true, textColor = "text-white" }: LogoProps) {
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      {/* Logo Image */}
      <div className="relative w-32 h-8">
        <Image
          src="/logo.webp"
          alt="FiyatRadarı"
          fill
          sizes="128px"
          className="object-contain"
          priority
        />
      </div>
    </div>
  )
}
