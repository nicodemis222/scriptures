import { useState, useRef, useCallback, useEffect } from 'react';
import type { SubTab } from '../data/constants';
import {
  AngelMoroni,
  Cross,
  Flame,
  OliveBranch,
  Scroll,
  Dove,
  OrthodoxCross,
  MusicNote,
  BookOpen,
} from './Icons';

const TAB_ICONS: Record<SubTab, React.FC<{ size?: number; className?: string }>> = {
  'BOOK OF MORMON': AngelMoroni,
  'BIBLE': Cross,
  'D&C': Flame,
  'PEARL OF GREAT PRICE': OliveBranch,
  'COPTIC': Scroll,
  'DEAD SEA SCROLLS': Dove,
  'RUSSIAN ORTHODOX': OrthodoxCross,
  'ANCIENT WITNESSES': BookOpen,
  'HYMNS': MusicNote,
};

interface VolumeNavProps {
  activeTab: SubTab;
  onTabChange: (tab: SubTab) => void;
  tabOrder: SubTab[];
  onReorder: (newOrder: SubTab[]) => void;
}

export function VolumeNav({ activeTab, onTabChange, tabOrder, onReorder }: VolumeNavProps) {
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const dragStartX = useRef(0);
  const isDragging = useRef(false);
  const navRef = useRef<HTMLElement>(null);
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  const hoverIndexRef = useRef(hoverIndex);
  useEffect(() => { hoverIndexRef.current = hoverIndex; }, [hoverIndex]);

  // Fix: use ref in the cleanup to get latest hoverIndex
  const handlePointerDownFixed = useCallback((e: React.PointerEvent, index: number) => {
    dragStartX.current = e.clientX;
    isDragging.current = false;

    const onMove = (ev: PointerEvent) => {
      const dx = Math.abs(ev.clientX - dragStartX.current);
      if (dx > 8 && !isDragging.current) {
        isDragging.current = true;
        setDragIndex(index);
      }
      if (isDragging.current) {
        const tabs = tabRefs.current;
        for (let i = 0; i < tabs.length; i++) {
          const tab = tabs[i];
          if (tab) {
            const rect = tab.getBoundingClientRect();
            if (ev.clientX >= rect.left && ev.clientX <= rect.right) {
              hoverIndexRef.current = i;
              setHoverIndex(i);
              break;
            }
          }
        }
      }
    };

    const onUp = () => {
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp);

      const dropTarget = hoverIndexRef.current;
      if (isDragging.current && dropTarget !== null && dropTarget !== index) {
        const newOrder = [...tabOrder];
        const [moved] = newOrder.splice(index, 1);
        newOrder.splice(dropTarget, 0, moved);
        onReorder(newOrder);
      }

      isDragging.current = false;
      setDragIndex(null);
      setHoverIndex(null);
      hoverIndexRef.current = null;
    };

    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onUp);
  }, [tabOrder, onReorder]);

  return (
    <nav className="volume-nav" ref={navRef}>
      {tabOrder.map((tab, index) => {
        const Icon = TAB_ICONS[tab];
        const classes = [
          'volume-nav-tab',
          activeTab === tab ? 'active' : '',
          dragIndex === index ? 'dragging' : '',
          hoverIndex === index && dragIndex !== null && dragIndex !== index ? 'drag-over' : '',
        ].filter(Boolean).join(' ');

        return (
          <button
            key={tab}
            ref={(el) => { tabRefs.current[index] = el; }}
            className={classes}
            onClick={() => {
              if (!isDragging.current) onTabChange(tab);
            }}
            onPointerDown={(e) => handlePointerDownFixed(e, index)}
            style={{ touchAction: 'none' }}
          >
            <Icon size={18} className="tab-icon" />
            <span>{tab}</span>
          </button>
        );
      })}
    </nav>
  );
}
