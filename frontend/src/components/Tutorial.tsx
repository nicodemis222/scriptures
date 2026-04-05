import { useState } from 'react';
import {
  BookOpen,
  SearchIcon,
  AngelMoroni,
  Cross,
  Flame,
  OliveBranch,
  Dove,
  Scroll,
  OrthodoxCross,
  MusicNote,
  HighlightPen,
  QuillPen,
  SpeakerIcon,
  BrainIcon,
  GlobeIcon,
  MoonIcon,
  GoldDivider,
  BookmarkRibbon,
  ChevronLeft,
} from './Icons';

interface TutorialProps {
  onComplete: () => void;
}

interface TutorialSlide {
  title: string;
  subtitle: string;
  description: string;
  icon: React.ReactNode;
  features?: { icon: React.ReactNode; label: string }[];
}

const SLIDES: TutorialSlide[] = [
  {
    title: 'Welcome to Scriptures',
    subtitle: 'Your personal scripture study companion',
    description:
      'Explore sacred texts from multiple traditions — all in one beautiful, offline app. ' +
      'This brief guide will show you around.',
    icon: <BookOpen size={64} />,
  },
  {
    title: 'Sacred Library',
    subtitle: '8 volumes of scripture at your fingertips',
    description:
      'Browse across multiple canons and traditions. Each volume has its own icon in the navigation bar. ' +
      'Tap any tab to explore its books, chapters, and verses.',
    icon: <BookOpen size={48} />,
    features: [
      { icon: <AngelMoroni size={20} />, label: 'Book of Mormon' },
      { icon: <Cross size={20} />, label: 'Holy Bible (KJV)' },
      { icon: <Flame size={20} />, label: 'Doctrine & Covenants' },
      { icon: <OliveBranch size={20} />, label: 'Pearl of Great Price' },
      { icon: <Dove size={20} />, label: 'Coptic Bible' },
      { icon: <Scroll size={20} />, label: 'Dead Sea Scrolls' },
      { icon: <OrthodoxCross size={20} />, label: 'Russian Orthodox' },
      { icon: <MusicNote size={20} />, label: 'Hymns' },
    ],
  },
  {
    title: 'Navigate with Ease',
    subtitle: 'Books, chapters, and verses',
    description:
      'Select a volume tab, choose a book from the sidebar, pick a chapter from the grid, ' +
      'and read verses in a beautiful, distraction-free layout with drop caps and gold ornamentation.',
    icon: <ChevronLeft size={48} />,
    features: [
      { icon: <span className="tutorial-nav-step">1</span>, label: 'Choose a volume tab' },
      { icon: <span className="tutorial-nav-step">2</span>, label: 'Select a book from the sidebar' },
      { icon: <span className="tutorial-nav-step">3</span>, label: 'Pick a chapter number' },
      { icon: <span className="tutorial-nav-step">4</span>, label: 'Read and study the text' },
    ],
  },
  {
    title: 'Search Across All Scripture',
    subtitle: 'Full-text search powered by FTS5',
    description:
      'Use the search bar to find any word or phrase across all volumes instantly. ' +
      'Results show the full reference and text snippet so you can jump right to the verse.',
    icon: <SearchIcon size={48} />,
  },
  {
    title: 'Highlight & Take Notes',
    subtitle: '5 colored pencils for your study',
    description:
      'Click any verse to reveal the study toolbar. Highlight with five colors — ' +
      'each with a suggested purpose — and add personal notes that are saved automatically.',
    icon: <HighlightPen size={48} />,
    features: [
      { icon: <span className="tutorial-color-dot" style={{ background: 'rgba(197,165,90,0.5)' }} />, label: 'Gold — Key doctrine' },
      { icon: <span className="tutorial-color-dot" style={{ background: 'rgba(196,114,108,0.5)' }} />, label: 'Rose — Promises & covenants' },
      { icon: <span className="tutorial-color-dot" style={{ background: 'rgba(107,163,190,0.5)' }} />, label: 'Sky — Prophecy' },
      { icon: <span className="tutorial-color-dot" style={{ background: 'rgba(127,167,127,0.5)' }} />, label: 'Sage — Commandments' },
      { icon: <span className="tutorial-color-dot" style={{ background: 'rgba(155,142,196,0.5)' }} />, label: 'Lavender — Personal inspiration' },
    ],
  },
  {
    title: 'Study Tools',
    subtitle: 'Notes, bookmarks, and related talks',
    description:
      'Write notes on any verse with the quill icon. Below each chapter, discover related ' +
      'General Conference talks from prophets and apostles, cross-referenced to the scripture you\'re reading.',
    icon: <QuillPen size={48} />,
    features: [
      { icon: <QuillPen size={20} />, label: 'Write study notes on verses' },
      { icon: <BookmarkRibbon size={20} />, label: 'My Study — review all highlights & notes' },
      { icon: <BookOpen size={20} />, label: 'Related talks from prophets & leaders' },
    ],
  },
  {
    title: 'Powerful Features',
    subtitle: 'Read aloud, translate, and explore with AI',
    description:
      'Listen to chapters read aloud using your system\'s text-to-speech. ' +
      'Translate verses into other languages. Ask an AI assistant to explain passages or research themes across all scripture.',
    icon: <BrainIcon size={48} />,
    features: [
      { icon: <SpeakerIcon size={20} />, label: 'Read Aloud — system TTS, verse by verse' },
      { icon: <GlobeIcon size={20} />, label: 'Language — translate to 10+ languages' },
      { icon: <BrainIcon size={20} />, label: 'AI Assistant — powered by local Qwen LLM' },
      { icon: <MoonIcon size={20} />, label: 'Dark Mode — easy on the eyes' },
    ],
  },
  {
    title: 'Begin Your Study',
    subtitle: '"Ask, and it shall be given you; seek, and ye shall find"',
    description:
      'You\'re all set. Select a volume from the tabs above to begin exploring. ' +
      'You can revisit this tutorial anytime from the Settings menu.',
    icon: <GoldDivider size={160} />,
  },
];

export function Tutorial({ onComplete }: TutorialProps) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const slide = SLIDES[currentSlide];
  const isFirst = currentSlide === 0;
  const isLast = currentSlide === SLIDES.length - 1;

  const handleNext = () => {
    if (isLast) {
      onComplete();
    } else {
      setCurrentSlide((s) => s + 1);
    }
  };

  const handlePrev = () => {
    if (!isFirst) setCurrentSlide((s) => s - 1);
  };

  return (
    <div className="tutorial-overlay">
      <div className="tutorial-card ornamental-card">
        {/* Skip button */}
        <button className="tutorial-skip" onClick={onComplete}>
          Skip
        </button>

        {/* Progress dots */}
        <div className="tutorial-progress">
          {SLIDES.map((_, i) => (
            <button
              key={i}
              className={`tutorial-dot${i === currentSlide ? ' active' : ''}${i < currentSlide ? ' completed' : ''}`}
              onClick={() => setCurrentSlide(i)}
              aria-label={`Go to slide ${i + 1}`}
            />
          ))}
        </div>

        {/* Icon */}
        <div className="tutorial-icon">{slide.icon}</div>

        {/* Content */}
        <h2 className="tutorial-title">{slide.title}</h2>
        <p className="tutorial-subtitle">{slide.subtitle}</p>
        <p className="tutorial-description">{slide.description}</p>

        {/* Feature list */}
        {slide.features && (
          <div className="tutorial-features">
            {slide.features.map((f, i) => (
              <div key={i} className="tutorial-feature">
                <span className="tutorial-feature-icon">{f.icon}</span>
                <span className="tutorial-feature-label">{f.label}</span>
              </div>
            ))}
          </div>
        )}

        {/* Navigation */}
        <div className="tutorial-nav">
          <button
            className="tutorial-nav-btn tutorial-prev"
            onClick={handlePrev}
            disabled={isFirst}
          >
            Back
          </button>
          <span className="tutorial-counter">
            {currentSlide + 1} / {SLIDES.length}
          </span>
          <button className="tutorial-nav-btn tutorial-next" onClick={handleNext}>
            {isLast ? 'Get Started' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}
