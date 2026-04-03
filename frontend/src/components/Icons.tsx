import React from 'react';

interface IconProps {
  size?: number;
  className?: string;
}

export const BookOpen: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M2 4c0 0 2.5-1 5.5-1S12 4 12 4s2-1 4.5-1S22 4 22 4v14c0 0-2.5-1-5.5-1S12 18 12 18s-2-1-4.5-1S2 18 2 18V4z" />
    <path d="M12 4v14" />
    <path d="M5 7h3" />
    <path d="M5 10h3" />
    <path d="M5 13h3" />
    <path d="M16 7h3" />
    <path d="M16 10h3" />
    <path d="M16 13h3" />
  </svg>
);

export const Cross: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M12 2v20" />
    <path d="M6 7h12" />
  </svg>
);

export const Flame: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M12 22c-4-2-7-5.5-7-10 0-3.5 2-6 4-7.5 0 3 1.5 4.5 3 5.5 0-3 1.5-6 3-8 1 2 2 4 2 6.5 1.5-1 2.5-2.5 2.5-4.5 1.5 2 2.5 4.5 2.5 7.5 0 4.5-3 8.5-7 10.5" />
    <path d="M12 22c-1.5-1.5-2.5-3-2.5-5 0-2 1-3 2.5-4 1.5 1 2.5 2 2.5 4s-1 3.5-2.5 5z" />
  </svg>
);

export const OliveBranch: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M4 20C8 16 12 12 20 4" />
    <ellipse cx="8" cy="11" rx="2" ry="1.2" transform="rotate(-30 8 11)" />
    <ellipse cx="11" cy="8.5" rx="2" ry="1.2" transform="rotate(-30 11 8.5)" />
    <ellipse cx="14.5" cy="6" rx="2" ry="1.2" transform="rotate(-30 14.5 6)" />
    <ellipse cx="6" cy="14" rx="2" ry="1.2" transform="rotate(-30 6 14)" />
    <ellipse cx="10" cy="14" rx="2" ry="1.2" transform="rotate(30 10 14)" />
    <ellipse cx="13" cy="11" rx="2" ry="1.2" transform="rotate(30 13 11)" />
    <ellipse cx="16" cy="8.5" rx="2" ry="1.2" transform="rotate(30 16 8.5)" />
  </svg>
);

export const Scroll: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M18 2c1.1 0 2 .9 2 2s-.9 2-2 2H8c0 0-2 0-2-2s.9-2 2-2h10z" />
    <path d="M6 4v14c0 1.1.9 2 2 2h10c1.1 0 2-.9 2-2" />
    <path d="M20 4v14c0 1.1.9 2 2 2s-2 0-2 0H8c-1.1 0-2-.9-2-2" />
    <circle cx="19" cy="19" r="1.5" />
    <path d="M9 9h6" />
    <path d="M9 12h8" />
    <path d="M9 15h4" />
  </svg>
);

export const Dove: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M18 4c-1 0-3 1-4 3L12 9l-3 1c-2 .5-4 2-5 4l5-2 2 1-4 5h3l3-3c2-1 4-2 5-4l1-3c0-1 0-2-1-3z" />
    <path d="M14 7c1-2 3-3.5 5.5-3.5" />
  </svg>
);

export const OrthodoxCross: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M12 1v22" />
    <path d="M8 5h8" />
    <path d="M6 10h12" />
    <path d="M9 18l6-4" />
  </svg>
);

export const MusicNote: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M9 18V5l12-3v13" />
    <circle cx="6" cy="18" r="3" fill="currentColor" />
    <circle cx="18" cy="15" r="3" fill="currentColor" />
  </svg>
);

export const AngelMoroni: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    {/* Head */}
    <circle cx="12" cy="3.5" r="1.8" />
    {/* Body / robe flowing down */}
    <path d="M12 5.3c0 0-1 1-1.5 3L8 19c0 0 1.5 2 4 2s4-2 4-2l-2.5-10.7c-.5-2-1.5-3-1.5-3z" />
    {/* Right arm raised with trumpet */}
    <path d="M13 8l3.5-3.5" />
    {/* Trumpet */}
    <path d="M16.5 4.5l2.5-1.5" />
    <path d="M18 2l2 1" />
    <path d="M19 3l1.5-.5" />
    {/* Left arm holding book/plates */}
    <path d="M11 9l-2.5 1" />
    <rect x="6.5" y="9" width="2.5" height="1.8" rx="0.3" />
    {/* Base */}
    <path d="M9.5 21h5" />
  </svg>
);

export const QuillPen: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M20 2c-3 2-6 6-8 10l-1 3c-.3 1-.5 2-.3 3l1.5-.5c.8-.3 1.5-.8 2-1.5l1-1.5c3-5 5-9 5-12 0-1 0-1.5-.2-1.5z" />
    <path d="M11 12l-3 6" />
    <path d="M4 22c1-2 2-3.5 4-4" />
  </svg>
);

export const HighlightPen: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M15.5 4l4.5 4.5-8 8H7.5V12z" />
    <path d="M12.5 7l4.5 4.5" />
    <path d="M7.5 16.5L4 22l5.5-3.5" />
    <path d="M3 21l2-2" />
  </svg>
);

export const BookmarkRibbon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M6 2h12a1 1 0 011 1v19l-7-4-7 4V3a1 1 0 011-1z" />
  </svg>
);

export const GearIcon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <circle cx="12" cy="12" r="3" />
    <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 11-4 0v-.09a1.65 1.65 0 00-1.08-1.51 1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 110-4h.09a1.65 1.65 0 001.51-1.08 1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33h.08a1.65 1.65 0 001-1.51V3a2 2 0 114 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82v.08a1.65 1.65 0 001.51 1H21a2 2 0 110 4h-.09a1.65 1.65 0 00-1.51 1z" />
  </svg>
);

export const GlobeIcon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <circle cx="12" cy="12" r="10" />
    <ellipse cx="12" cy="12" rx="4" ry="10" />
    <path d="M2 12h20" />
    <path d="M4 7h16" />
    <path d="M4 17h16" />
  </svg>
);

export const SpeakerIcon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M11 5L6 9H2v6h4l5 4V5z" />
    <path d="M15 9a4 4 0 010 6" />
    <path d="M18 6a8 8 0 010 12" />
  </svg>
);

export const BrainIcon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M12 2a5 5 0 00-4.8 3.5A4 4 0 004 9.5a4.5 4.5 0 00.5 5A4 4 0 005 18a4 4 0 004 4h1v-8" />
    <path d="M12 2a5 5 0 014.8 3.5A4 4 0 0120 9.5a4.5 4.5 0 01-.5 5A4 4 0 0019 18a4 4 0 01-4 4h-1v-8" />
    <path d="M12 2v6" />
    <path d="M7 10h4" />
    <path d="M13 10h4" />
    <path d="M8 15h3" />
    <path d="M13 15h3" />
  </svg>
);

export const SunIcon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <circle cx="12" cy="12" r="5" />
    <path d="M12 1v3M12 20v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M1 12h3M20 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12" />
  </svg>
);

export const MoonIcon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z" />
  </svg>
);

export const SearchIcon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <circle cx="10.5" cy="10.5" r="7.5" />
    <path d="M16 16l5.5 5.5" />
  </svg>
);

export const ChevronLeft: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M15 18l-6-6 6-6" />
  </svg>
);

export const PlayIcon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <polygon points="6,3 20,12 6,21" fill="currentColor" />
  </svg>
);

export const PauseIcon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor" />
    <rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor" />
  </svg>
);

export const StopIcon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <rect x="5" y="5" width="14" height="14" rx="2" fill="currentColor" />
  </svg>
);

export const XIcon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M18 6L6 18" />
    <path d="M6 6l12 12" />
  </svg>
);

export const PlusIcon: React.FC<IconProps> = ({ size = 24, className }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M12 5v14" />
    <path d="M5 12h14" />
  </svg>
);

export const GoldDivider: React.FC<IconProps> = ({ size = 200, className }) => (
  <svg
    width={size}
    height={(size / 200) * 12}
    viewBox="0 0 200 12"
    fill="none"
    stroke="currentColor"
    strokeWidth={1}
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    {/* Left line */}
    <line x1="10" y1="6" x2="92" y2="6" />
    {/* Center diamond */}
    <polygon points="100,1 106,6 100,11 94,6" fill="currentColor" stroke="none" />
    {/* Right line */}
    <line x1="108" y1="6" x2="190" y2="6" />
    {/* Small decorative dots */}
    <circle cx="15" cy="6" r="1" fill="currentColor" stroke="none" />
    <circle cx="185" cy="6" r="1" fill="currentColor" stroke="none" />
  </svg>
);
