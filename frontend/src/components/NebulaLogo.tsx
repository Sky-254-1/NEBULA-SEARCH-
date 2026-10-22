import React from 'react';

interface NebulaLogoProps {
  className?: string;
  size?: number;
  withText?: boolean;
  textColor?: string;
}

/**
 * Nebula Logo Component
 * 
 * A reusable inline-SVG component that displays the Neural Nodes Search Lens logo.
 * Features:
 * - Dark cosmic background (#0b0c10)
 * - Neural network pattern with nodes and connecting lines
 * - Magnifying glass handle at 45-degree angle
 * - Brand gradient: purple (#7c5cfc) → blue (#3b82f6) → indigo (#6366f1)
 */
export const NebulaLogo: React.FC<NebulaLogoProps> = ({
  className = '',
  size = 48,
  withText = false,
  textColor = 'text-white',
}) => {
  const svgSize = size;

  return (
    <div
      className={`flex items-center gap-2 select-none ${className}`}
      style={{ width: withText ? 'auto' : svgSize, height: svgSize }}
      role="img"
      aria-label="Nebula Search - Neural Nodes Search Lens"
    >
      {/* Logo SVG */}
      <svg
        width={svgSize}
        height={svgSize}
        viewBox="0 0 512 512"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="overflow-visible"
        style={{ height: svgSize, width: svgSize }}
      >
        {/* Dark cosmic background */}
        <rect width="512" height="512" rx="120" fill="#0b0c10"/>

        {/* Soft purple glow background */}
        <circle cx="256" cy="256" r="180" fill="url(#glowGradient)" opacity="0.15"/>

        {/* Gradient definitions */}
        <defs>
          <linearGradient id="brandGradient" x1="80" y1="80" x2="432" y2="432" gradientUnits="userSpaceOnUse">
            <stop stopColor="#7c5cfc"/>
            <stop offset="0.5" stopColor="#3b82f6"/>
            <stop offset="1" stopColor="#6366f1"/>
          </linearGradient>

          <linearGradient id="glowGradient" x1="256" y1="76" x2="256" y2="436" gradientUnits="userSpaceOnUse">
            <stop stopColor="#7c5cfc" stopOpacity="0.4"/>
            <stop offset="0.5" stopColor="#3b82f6" stopOpacity="0.2"/>
            <stop offset="1" stopColor="#6366f1" stopOpacity="0.1"/>
          </linearGradient>

          <radialGradient id="nodeGradient" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(256 256) scale(30)">
            <stop stopColor="#7c5cfc"/>
            <stop offset="0.5" stopColor="#3b82f6"/>
            <stop offset="1" stopColor="#6366f1"/>
          </radialGradient>

          <filter id="neuralGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="8" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Neural Network Pattern - nodes and connections */}
        {/* Central node */}
        <circle cx="256" cy="256" r="24" fill="url(#nodeGradient)" filter="url(#neuralGlow)"/>

        {/* Outer ring nodes */}
        <circle cx="256" cy="120" r="16" fill="url(#nodeGradient)" opacity="0.9"/>
        <circle cx="392" cy="184" r="14" fill="url(#nodeGradient)" opacity="0.85"/>
        <circle cx="432" cy="328" r="18" fill="url(#nodeGradient)" opacity="0.95"/>
        <circle cx="328" cy="456" r="16" fill="url(#nodeGradient)" opacity="0.85"/>
        <circle cx="184" cy="456" r="14" fill="url(#nodeGradient)" opacity="0.8"/>
        <circle cx="80" cy="328" r="16" fill="url(#nodeGradient)" opacity="0.85"/>
        <circle cx="120" cy="184" r="14" fill="url(#nodeGradient)" opacity="0.9"/>

        {/* Central secondary nodes */}
        <circle cx="256" cy="184" r="12" fill="url(#nodeGradient)" opacity="0.8"/>
        <circle cx="328" cy="256" r="12" fill="url(#nodeGradient)" opacity="0.8"/>
        <circle cx="256" cy="328" r="12" fill="url(#nodeGradient)" opacity="0.8"/>
        <circle cx="184" cy="256" r="12" fill="url(#nodeGradient)" opacity="0.8"/>

        {/* Connections (neural pathways) */}
        <g stroke="url(#brandGradient)" strokeWidth="3" strokeLinecap="round" opacity="0.6">
          {/* Central connections */}
          <path d="M256 256 L256 184"/>
          <path d="M256 256 L328 256"/>
          <path d="M256 256 L256 328"/>
          <path d="M256 256 L184 256"/>

          {/* Ring connections */}
          <path d="M256 120 L256 184"/>
          <path d="M392 184 L328 256"/>
          <path d="M432 328 L328 256"/>
          <path d="M328 456 L256 328"/>
          <path d="M184 456 L256 328"/>
          <path d="M80 328 L184 256"/>
          <path d="M120 184 L184 256"/>

          {/* Cross connections */}
          <path d="M256 120 L392 184"/>
          <path d="M392 184 L432 328"/>
          <path d="M432 328 L328 456"/>
          <path d="M328 456 L184 456"/>
          <path d="M184 456 L80 328"/>
          <path d="M80 328 L120 184"/>
          <path d="M120 184 L256 120"/>
        </g>

        {/* Neural pulse/energy lines */}
        <g stroke="url(#brandGradient)" strokeWidth="2" strokeLinecap="round" opacity="0.4">
          <path d="M256 256 L432 184" strokeDasharray="4 6"/>
          <path d="M256 256 L80 184" strokeDasharray="4 6"/>
          <path d="M256 256 L432 328" strokeDasharray="4 6"/>
          <path d="M256 256 L80 328" strokeDasharray="4 6"/>
        </g>

        {/* Magnifying glass handle (45-degree angle) */}
        <path d="M424 424 L480 480" stroke="url(#brandGradient)" strokeWidth="8" strokeLinecap="round" opacity="0.8"/>

        {/* Lens circle */}
        <circle cx="256" cy="256" r="140" stroke="url(#brandGradient)" strokeWidth="4" opacity="0.3" fill="none"/>
        <circle cx="256" cy="256" r="136" stroke="url(#brandGradient)" strokeWidth="2" opacity="0.2" fill="none"/>

        {/* Corner accents */}
        <path d="M116 116 L140 116 L116 140" stroke="url(#brandGradient)" strokeWidth="6" strokeLinecap="round" opacity="0.4"/>
        <path d="M396 116 L372 116 L396 140" stroke="url(#brandGradient)" strokeWidth="6" strokeLinecap="round" opacity="0.4"/>
        <path d="M396 396 L372 396 L396 372" stroke="url(#brandGradient)" strokeWidth="6" strokeLinecap="round" opacity="0.4"/>
        <path d="M116 396 L140 396 L116 372" stroke="url(#brandGradient)" strokeWidth="6" strokeLinecap="round" opacity="0.4"/>

        {/* Inner lens highlight */}
        <circle cx="200" cy="200" r="8" fill="#7c5cfc" opacity="0.6" filter="url(#neuralGlow)"/>
      </svg>

      {/* Optional text */}
      {withText && (
        <span className={`font-bold ${textColor}`} style={{ fontSize: size * 0.6 }}>
          Nebula
        </span>
      )}
    </div>
  );
};

export default NebulaLogo;
