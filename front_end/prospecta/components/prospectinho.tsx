"use client"

import { useState } from "react"

interface ProspectinhoProps {
  message?: string
  size?: "sm" | "md" | "lg"
  mood?: "happy" | "excited" | "thinking" | "waving"
  className?: string
  onClick?: () => void
}

export function Prospectinho({ message, size = "md", mood = "happy", className = "", onClick }: ProspectinhoProps) {
  const [isHovered, setIsHovered] = useState(false)

  const sizeClasses = {
    sm: "w-16 h-16",
    md: "w-24 h-24",
    lg: "w-32 h-32",
  }

  const getMouthPath = () => {
    switch (mood) {
      case "excited":
        return "M 30 42 Q 40 55 50 42" // Big smile
      case "thinking":
        return "M 32 45 L 48 45" // Neutral line
      case "waving":
        return "M 30 42 Q 40 52 50 42" // Medium smile
      default:
        return "M 32 42 Q 40 50 48 42" // Normal smile
    }
  }

  return (
    <div
      className={`relative inline-flex flex-col items-center ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
    >
      {/* Speech bubble */}
      {message && (
        <div
          className={`
          absolute -top-16 left-1/2 -translate-x-1/2 
          bg-card text-card-foreground px-4 py-2 rounded-2xl 
          shadow-lg border-2 border-primary/20
          text-sm font-medium whitespace-nowrap
          transition-all duration-300
          ${isHovered ? "opacity-100 scale-100" : "opacity-0 scale-95"}
        `}
        >
          {message}
          <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-card border-b-2 border-r-2 border-primary/20 rotate-45" />
        </div>
      )}

      {/* Mascot SVG */}
      <svg
        viewBox="0 0 80 90"
        className={`${sizeClasses[size]} ${mood === "waving" ? "animate-bounce-gentle" : ""} cursor-pointer transition-transform hover:scale-110`}
      >
        {/* Body */}
        <ellipse cx="40" cy="55" rx="28" ry="30" fill="#58CC02" />

        {/* Body highlight */}
        <ellipse cx="35" cy="50" rx="18" ry="20" fill="#6BD907" opacity="0.5" />

        {/* Face */}
        <circle cx="40" cy="35" r="25" fill="#58CC02" />

        {/* Face highlight */}
        <ellipse cx="35" cy="30" rx="15" ry="12" fill="#6BD907" opacity="0.6" />

        {/* Left eye */}
        <ellipse cx="32" cy="32" rx="6" ry="7" fill="white" />
        <circle cx="33" cy="32" r="3" fill="#1B1B1B" />
        <circle cx="34" cy="31" r="1" fill="white" />

        {/* Right eye */}
        <ellipse cx="48" cy="32" rx="6" ry="7" fill="white" />
        <circle cx="49" cy="32" r="3" fill="#1B1B1B" />
        <circle cx="50" cy="31" r="1" fill="white" />

        {/* Eyebrows */}
        <path
          d={mood === "excited" ? "M 26 24 Q 32 20 38 24" : "M 26 26 Q 32 24 38 26"}
          stroke="#3D8200"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d={mood === "excited" ? "M 42 24 Q 48 20 54 24" : "M 42 26 Q 48 24 54 26"}
          stroke="#3D8200"
          strokeWidth="2"
          fill="none"
          strokeLinecap="round"
        />

        {/* Mouth */}
        <path d={getMouthPath()} stroke="#3D8200" strokeWidth="3" fill="none" strokeLinecap="round" />

        {/* Cheeks */}
        <circle cx="22" cy="38" r="4" fill="#FFB84D" opacity="0.5" />
        <circle cx="58" cy="38" r="4" fill="#FFB84D" opacity="0.5" />

        {/* Left arm */}
        <ellipse cx="12" cy="55" rx="8" ry="12" fill="#58CC02" transform={mood === "waving" ? "" : ""} />

        {/* Right arm - waving */}
        <ellipse
          cx="68"
          cy={mood === "waving" ? "45" : "55"}
          rx="8"
          ry="12"
          fill="#58CC02"
          className={mood === "waving" ? "animate-wave" : ""}
          style={{ transformOrigin: "68px 60px" }}
        />

        {/* Antenna */}
        <line x1="40" y1="10" x2="40" y2="2" stroke="#3D8200" strokeWidth="3" strokeLinecap="round" />
        <circle cx="40" cy="0" r="4" fill="#FFB84D" />

        {/* Feet */}
        <ellipse cx="30" cy="82" rx="10" ry="6" fill="#3D8200" />
        <ellipse cx="50" cy="82" rx="10" ry="6" fill="#3D8200" />
      </svg>
    </div>
  )
}

// Helper component for floating mascot
export function FloatingProspectinho() {
  const [isOpen, setIsOpen] = useState(false)
  const [currentTip, setCurrentTip] = useState(0)

  const tips = [
    "Olá! Sou o Prospectinho! 👋",
    "Dica: Seja específico na busca!",
    "Personalize sua mensagem!",
    "Monitore suas prospecções!",
    "Precisando de ajuda? 🤔",
  ]

  const nextTip = () => {
    setCurrentTip((prev) => (prev + 1) % tips.length)
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {isOpen && (
        <div className="absolute bottom-full right-0 mb-4 w-64 bg-card text-card-foreground p-4 rounded-2xl shadow-xl border-2 border-primary/20 animate-in fade-in slide-in-from-bottom-4">
          <p className="text-sm font-medium mb-3">{tips[currentTip]}</p>
          <button onClick={nextTip} className="text-xs text-primary hover:underline font-semibold">
            Próxima dica →
          </button>
          <div className="absolute -bottom-2 right-8 w-4 h-4 bg-card border-b-2 border-r-2 border-primary/20 rotate-45" />
        </div>
      )}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded-full"
        aria-label="Abrir ajuda do Prospectinho"
      >
        <Prospectinho size="md" mood={isOpen ? "excited" : "waving"} />
      </button>
    </div>
  )
}
